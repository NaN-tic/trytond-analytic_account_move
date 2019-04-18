# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['Invoice', 'InvoiceLine']


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def cancel(cls, invoices):
        AnalyticLine = Pool().get('analytic_account.line')

        to_remove = []
        for invoice in invoices:
            if not invoice.move:
                continue
            for line in invoice.move.lines:
                if line.analytic_lines:
                    to_remove += line.analytic_lines
        if to_remove:
            AnalyticLine.delete(to_remove)

        super(Invoice, cls).cancel(invoices)


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    def get_move_lines(self):
        AnalyticAccountEntry = Pool().get('analytic.account.entry')

        lines = super(InvoiceLine, self).get_move_lines()

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
