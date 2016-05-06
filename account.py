# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['AnalyticAccount']


class AnalyticAccount:
    __name__ = 'analytic_account.account'
    __metaclass__ = PoolMeta

    @classmethod
    def delete(cls, accounts):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        super(AnalyticAccount, cls).delete(accounts)
        # Restart the cache on the fields_view_get method
        MoveLine._fields_view_get_cache.clear()

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        accounts = super(AnalyticAccount, cls).create(vlist)
        # Restart the cache on the fields_view_get method
        MoveLine._fields_view_get_cache.clear()
        return accounts

    @classmethod
    def write(cls, accounts, values, *args):
        pool = Pool()
        MoveLine = pool.get('account.move.line')
        super(AnalyticAccount, cls).write(accounts, values, *args)
        # Restart the cache on the fields_view_get method
        MoveLine._fields_view_get_cache.clear()
