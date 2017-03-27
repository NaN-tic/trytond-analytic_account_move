# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['InvoiceLine']


class InvoiceLine:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice.line'

    def get_move_line(self):
        lines = super(InvoiceLine, self).get_move_line()
        if self.analytic_accounts:
            for line in lines:
                line.analytic_accounts = self.analytic_accounts
        return lines
