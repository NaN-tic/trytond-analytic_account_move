# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['Invoice']


class Invoice:
    __metaclass__ = PoolMeta
    __name__ = 'account.invoice'

    @classmethod
    def set_analytic_accounts_from_lines(cls, invoices):
        AnalyticAccountEntry = Pool().get('analytic.account.entry')

        to_create = []
        to_delete = []
        for invoice in invoices:
            if not invoice.move:
                continue

            for line in invoice.move.lines:
                analytic_accounts = []
                for analytic_account in line.analytic_accounts:
                    if analytic_account.account:
                        analytic_accounts.append(
                            (analytic_account.root.id, analytic_account.account.id))
                    else:
                        to_delete.append(analytic_account)

                for analytic_line in line.analytic_lines:
                    root = analytic_line.account.root
                    account = analytic_line.account
                    if (root.id, account.id) in analytic_accounts:
                        continue

                    entry = AnalyticAccountEntry()
                    entry.origin = line
                    entry.root = root
                    entry.account = account
                    to_create.append(entry._save_values)

        if to_delete:
            AnalyticAccountEntry.delete(to_delete)
        if to_create:
            AnalyticAccountEntry.create(to_create)

    @classmethod
    def validate_invoice(cls, invoices):
        super(Invoice, cls).validate_invoice(invoices)
        cls.set_analytic_accounts_from_lines(invoices)

    @classmethod
    def post(cls, invoices):
        super(Invoice, cls).post(invoices)
        cls.set_analytic_accounts_from_lines(invoices)
