# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Move', 'MoveLine']


class AnalyticAccountsMixin:
    __metaclass__ = PoolMeta

    analytic_accounts = fields.Many2One('analytic_account.account.selection',
        'Analytic Accounts',
        states={
            'readonly': Eval('state') != 'draft',
            },
        depends=['state'])

    @classmethod
    def _view_look_dom_arch(cls, tree, type, field_children=None):
        AnalyticAccount = Pool().get('analytic_account.account')
        AnalyticAccount.convert_view(tree)
        return super(AnalyticAccountsMixin, cls)._view_look_dom_arch(
            tree, type,
            field_children=field_children)

    @classmethod
    def fields_get(cls, fields_names=None):
        AnalyticAccount = Pool().get('analytic_account.account')

        fields = super(AnalyticAccountsMixin, cls).fields_get(fields_names)

        analytic_accounts_field = super(AnalyticAccountsMixin, cls).fields_get(
                ['analytic_accounts'])['analytic_accounts']

        fields.update(AnalyticAccount.analytic_accounts_fields_get(
                analytic_accounts_field, fields_names,
                states=cls.analytic_accounts.states,
                required_states=Eval('state') == 'draft'))
        return fields

    @classmethod
    def default_get(cls, fields, with_rec_name=True):
        fields = [x for x in fields if not x.startswith('analytic_account_')]
        return super(AnalyticAccountsMixin, cls).default_get(fields,
            with_rec_name=with_rec_name)

    @classmethod
    def read(cls, ids, fields_names=None):
        if fields_names:
            fields_names2 = [x for x in fields_names
                    if not x.startswith('analytic_account_')]
        else:
            fields_names2 = fields_names

        res = super(AnalyticAccountsMixin, cls).read(ids,
            fields_names=fields_names2)

        if not fields_names:
            fields_names = cls._fields.keys()

        root_ids = []
        for field in fields_names:
            if field.startswith('analytic_account_') and '.' not in field:
                root_ids.append(int(field[len('analytic_account_'):]))
        if root_ids:
            id2record = {}
            for record in res:
                id2record[record['id']] = record
            lines = cls.browse(ids)
            for line in lines:
                for root_id in root_ids:
                    id2record[line.id]['analytic_account_'
                        + str(root_id)] = None
                if not line.analytic_accounts:
                    continue
                for account in line.analytic_accounts.accounts:
                    if account.root.id in root_ids:
                        id2record[line.id]['analytic_account_'
                            + str(account.root.id)] = account.id
                        for field in fields_names:
                            if field.startswith('analytic_account_'
                                    + str(account.root.id) + '.'):
                                ham, field2 = field.split('.', 1)
                                id2record[line.id][field] = account[field2]
        return res

    @classmethod
    def create(cls, vlist):
        Selection = Pool().get('analytic_account.account.selection')
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            selection_vals = {}
            for field in vals.keys():
                if field.startswith('analytic_account_'):
                    if vals[field]:
                        selection_vals.setdefault('accounts', [])
                        selection_vals['accounts'].append(('add',
                                [vals[field]]))
                    del vals[field]
            if vals.get('analytic_accounts'):
                Selection.write([Selection(vals['analytic_accounts'])],
                    selection_vals)
            else:
                selection, = Selection.create([selection_vals])
                vals['analytic_accounts'] = selection.id
        return super(AnalyticAccountsMixin, cls).create(vlist)

    @classmethod
    def write(cls, *args):
        Selection = Pool().get('analytic_account.account.selection')
        actions = iter(args)
        args = []
        for lines, values in zip(actions, actions):
            values = values.copy()
            selection_vals = {}
            for field, value in values.items():
                if field.startswith('analytic_account_'):
                    root_id = int(field[len('analytic_account_'):])
                    selection_vals[root_id] = value
                    del values[field]
            if selection_vals:
                for line in lines:
                    accounts = []
                    if not line.analytic_accounts:
                        # Create missing selection
                        selection, = Selection.create([{}])
                        cls.write([line], {
                                'analytic_accounts': selection.id,
                                })
                    for account in line.analytic_accounts.accounts:
                        if account.root.id in selection_vals:
                            value = selection_vals[account.root.id]
                            if value:
                                accounts.append(value)
                        else:
                            accounts.append(account.id)
                    for account_id in selection_vals.values():
                        if account_id \
                                and account_id not in accounts:
                            accounts.append(account_id)
                    to_remove = list(
                        set((a.id for a in line.analytic_accounts.accounts))
                        - set(accounts))
                    Selection.write([line.analytic_accounts], {
                            'accounts': [
                                ('remove', to_remove),
                                ('add', accounts),
                                ],
                            })
            args.extend((lines, values))
        super(AnalyticAccountsMixin, cls).write(*args)

    @classmethod
    def delete(cls, records):
        Selection = Pool().get('analytic_account.account.selection')

        selection_ids = []
        for record in records:
            if record.analytic_accounts:
                selection_ids.append(record.analytic_accounts.id)

        super(AnalyticAccountsMixin, cls).delete(records)
        Selection.delete(Selection.browse(selection_ids))

    @classmethod
    def copy(cls, records, default=None):
        Selection = Pool().get('analytic_account.account.selection')

        new_records = super(AnalyticAccountsMixin, cls).copy(records,
            default=default)

        for record in new_records:
            if record.analytic_accounts:
                selection, = Selection.copy([record.analytic_accounts])
                cls.write([record], {
                        'analytic_accounts': selection.id,
                        })
        return new_records


class Move(AnalyticAccountsMixin):
    __name__ = 'account.move'
    __metaclass__ = PoolMeta

    @classmethod
    @ModelView.button
    def post(cls, moves):
        cls.create_analytic_lines(moves)
        super(Move, cls).post(moves)

    @classmethod
    def create_analytic_lines(cls, moves):
        for move in moves:
            move._create_analytic_lines()

    def _create_analytic_lines(self):
        move_analytic_accounts = (self.analytic_accounts.accounts
            if self.analytic_accounts else None)
        for line in self.lines:
            if line.analytic_accounts and line.analytic_accounts.accounts:
                line.add_analytic_lines(line.analytic_accounts.accounts)
                line.save()
            elif (move_analytic_accounts
                    and line.account.analytic_is_required):
                line.add_analytic_lines(move_analytic_accounts)
                line.save()

    @classmethod
    @ModelView.button
    def draft(cls, moves):
        pool = Pool()
        AnalyticLine = pool.get('analytic_account.line')

        super(Move, cls).draft(moves)

        to_delete = []
        for move in moves:
            if move.analytic_accounts and move.analytic_accounts.accounts:
                to_delete += [al for l in move.lines
                    for al in l.analytic_lines]
            else:
                for line in move.lines:
                    if (line.analytic_accounts
                            and line.analytic_accounts.accounts):
                        to_delete += [al for al in line.analytic_lines]
        if to_delete:
            AnalyticLine.delete(to_delete)


class MoveLine(AnalyticAccountsMixin):
    __name__ = 'account.move.line'
    __metaclass__ = PoolMeta

    def add_analytic_lines(self, analytic_accounts):
        pool = Pool()
        AnalyticLine = pool.get('analytic_account.line')

        if self.analytic_lines:
            return
        self.analytic_lines = []
        for account in analytic_accounts:
            analytic_line = AnalyticLine()
            analytic_line.name = (self.description if self.description
                else self.move_description)
            analytic_line.debit = self.debit
            analytic_line.credit = self.credit
            analytic_line.account = account
            analytic_line.journal = self.journal
            analytic_line.date = self.date
            # analytic_line.reference = self.invoice.reference
            analytic_line.party = self.party
            self.analytic_lines.append(analytic_line)

    @classmethod
    def copy(cls, lines, default=None):
        lines_w_aa = []
        lines_wo_aa = []
        for line in lines:
            if (line.analytic_accounts and line.analytic_accounts.accounts
                    or line.move and line.move.analytic_accounts
                    and line.move.analytic_accounts.accounts):
                lines_w_aa.append(line)
            else:
                lines_wo_aa.append(line)

        res = []
        if lines_w_aa:
            if default:
                new_default = default.copy()
            else:
                new_default = {}
            new_default['analytic_lines'] = None
            res += super(AnalyticAccountsMixin, cls).copy(lines_w_aa,
                default=new_default)
        if lines_wo_aa:
            res += super(AnalyticAccountsMixin, cls).copy(lines_wo_aa,
                default=default)
        return res
