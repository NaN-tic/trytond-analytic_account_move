# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['InvoiceLine']


class InvoiceLine:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice.line'

    def get_move_line(self):
        AnalyticAccountEntry = Pool().get('analytic.account.entry')

        lines = super(InvoiceLine, self).get_move_line()

        if self.analytic_accounts:
            for line in lines:
                line.analytic_lines = []

                entries = []
                for aline in self.analytic_accounts:
                    entry = AnalyticAccountEntry()
                    entry.root = aline.root
                    entry.account = aline.account
                    entries.append(entry)
                    line.analytic_accounts = entries

        return lines
