# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.modules.analytic_account import AnalyticMixin

__all__ = ['Move', 'MoveLine', 'AnalyticAccountEntry']
__metaclass__ = PoolMeta


class Move:
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
    __name__ = 'account.move.line'

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
        domain = super(AnalyticAccountEntry, cls).search_company(name, clause)
        return ['OR',
            domain,
            [('origin.move.company',) + tuple(clause[1:]) +
                tuple(('account.move.line',))]]
