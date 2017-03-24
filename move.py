# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.modules.analytic_account import AnalyticMixin

__all__ = ['Move', 'MoveLine', 'AnalyticAccountEntry',
    'MoveLineTemplate', 'AnalyticAccountLineTemplate']


class Move:
    __metaclass__ = PoolMeta
    __name__ = 'account.move'

    @classmethod
    @ModelView.button
    def post(cls, moves):
        cls.create_analytic_lines(moves)
        super(Move, cls).post(moves)

    @classmethod
    def create_analytic_lines(cls, moves):
        for move in moves:
            for line in move.lines:
                if (line.analytic_accounts and
                    line.set_analytic_lines(
                        line.analytic_accounts
                    )
                ):
                    line.save()

    @classmethod
    @ModelView.button
    def draft(cls, moves):
        pool = Pool()
        AnalyticLine = pool.get('analytic_account.line')

        super(Move, cls).draft(moves)

        to_delete = []
        for move in moves:
            for line in move.lines:
                if line.analytic_accounts:
                    to_delete += [al for al in line.analytic_lines]
        if to_delete:
            AnalyticLine.delete(to_delete)


class MoveLine(AnalyticMixin):
    __metaclass__ = PoolMeta
    __name__ = 'account.move.line'

    @classmethod
    def __setup__(cls):
        super(MoveLine, cls).__setup__()
        cls.analytic_accounts.help = ('Fill it if you want to generate '
            'analytic lines when post the move.\n'
            'Normally, it isn\'t necessary when the move is generated from '
            'another document which will have the analytics configuration.\n'
            'If you set draft a move with analytic accounts, the analytic '
            'lines are deleted to be generated again when post it.')

    def set_analytic_lines(self, analytic_accounts):
        pool = Pool()
        AnalyticLine = pool.get('analytic_account.line')

        analytic_lines = []
        for entry in analytic_accounts:
            if not entry.account:
                continue
            analytic_line = AnalyticLine()
            analytic_line.name = (self.description if self.description
                else self.move_description)
            analytic_line.debit = self.debit
            analytic_line.credit = self.credit
            analytic_line.account = entry.account
            analytic_line.journal = self.journal
            analytic_line.date = self.date
            analytic_line.party = self.party
            analytic_line.active = True
            analytic_lines.append(analytic_line)
        self.analytic_lines = analytic_lines
        return True

    @classmethod
    def copy(cls, lines, default=None):
        lines_w_aa = []
        lines_wo_aa = []
        for line in lines:
            if line.analytic_accounts:
                lines_w_aa.append(line)
            else:
                lines_wo_aa.append(line)

        new_records = []
        if lines_w_aa:
            if default:
                new_default = default.copy()
            else:
                new_default = {}
            new_default['analytic_lines'] = None
            new_records += super(MoveLine, cls).copy(lines_w_aa,
                default=new_default)
        if lines_wo_aa:
            new_records += super(MoveLine, cls).copy(lines_wo_aa,
                default=default)

        return new_records


class AnalyticAccountEntry:
    __metaclass__ = PoolMeta
    __name__ = 'analytic.account.entry'

    @classmethod
    def _get_origin(cls):
        origins = super(AnalyticAccountEntry, cls)._get_origin()
        return origins + ['account.move.line']

    @fields.depends('origin')
    def on_change_with_company(self, name=None):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        company = super(AnalyticAccountEntry, self).on_change_with_company(
            name)
        if isinstance(self.origin, MoveLine):
            if self.origin.move:
                return self.origin.move.company.id
        return company

    @classmethod
    def search_company(cls, name, clause):
        domain = super(AnalyticAccountEntry, cls).search_company(name, clause),
        return ['OR',
            domain,
            [('origin.move.company',) + tuple(clause[1:]) +
                ('account.move.line',)],
            ]


class MoveLineTemplate:
    __metaclass__ = PoolMeta
    __name__ = 'account.move.line.template'
    analytic_accounts = fields.One2Many('analytic_account.line.template', 'line',
        'Analytic Accounts')

    def get_line(self, values):
        line = super(MoveLineTemplate, self).get_line(values)

        analytic_accounts = []
        for a in self.analytic_accounts:
            analytic_accounts.append({
                    'root': a.root.id,
                    'account': a.account.id,
                    })
        if analytic_accounts:
            line.analytic_accounts = analytic_accounts

        return line


class AnalyticAccountLineTemplate(ModelSQL, ModelView):
    'Analytic Account Line Template'
    __name__ = 'analytic_account.line.template'
    company = fields.Many2One('company.company', 'Company', required=True)
    line = fields.Many2One('account.move.line.template', 'Line', required=True)
    root = fields.Many2One('analytic_account.account', 'Root Analytic',
        domain=[
            If(~Eval('company'),
                # No constraint if the origin is not set
                (),
                ('company', '=', Eval('company', -1))),
            ('type', '=', 'root'),
            ],
        depends=['company'])
    account = fields.Many2One('analytic_account.account', 'Account',
        ondelete='RESTRICT',
        states={
            'required': Eval('required', False),
            },
        domain=[
            ('root', '=', Eval('root')),
            ('type', '=', 'normal'),
            ],
        depends=['root', 'required', 'company'])
    required = fields.Function(fields.Boolean('Required'),
        'on_change_with_required')

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('root')
    def on_change_with_required(self, name=None):
        if self.root:
            return self.root.mandatory
        return False
