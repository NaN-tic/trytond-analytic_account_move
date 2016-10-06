# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.analytic_account_move.tests.test_analytic_account_move import suite
except ImportError:
    from .test_analytic_account_move import suite

__all__ = ['suite']
