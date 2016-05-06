# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta

__all__ = ['Account', 'AnalyticAccount']


class Account:
    __name__ = 'account.account'
    __metaclass__ = PoolMeta

    @property
    def analytic_is_required(self, analytic_roots=None):
        try:
            if analytic_roots:
                return len(set([a.id for a in self.analytic_required])
                    & set([a.id for a in analytic_roots])) > 0
            else:
                return len(self.analytic_required) > 0
        except AttributeError:
            pass  # analytic_line_state not installed
        return self.kind in ('revenue', 'expense')


class AnalyticAccount:
    __name__ = 'analytic_account.account'
    __metaclass__ = PoolMeta

    @classmethod
    def delete(cls, accounts):
        pool = Pool()
        Move = pool.get('account.move')
        MoveLine = pool.get('account.move.line')
        super(AnalyticAccount, cls).delete(accounts)
        # Restart the cache on the fields_view_get method
        Move._fields_view_get_cache.clear()
        MoveLine._fields_view_get_cache.clear()

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Move = pool.get('account.move')
        MoveLine = pool.get('account.move.line')
        accounts = super(AnalyticAccount, cls).create(vlist)
        # Restart the cache on the fields_view_get method
        Move._fields_view_get_cache.clear()
        MoveLine._fields_view_get_cache.clear()
        return accounts

    @classmethod
    def write(cls, accounts, values, *args):
        pool = Pool()
        Move = pool.get('account.move')
        MoveLine = pool.get('account.move.line')
        super(AnalyticAccount, cls).write(accounts, values, *args)
        # Restart the cache on the fields_view_get method
        Move._fields_view_get_cache.clear()
        MoveLine._fields_view_get_cache.clear()
