# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .account import *
from .move import *


def register():
    Pool.register(
        AnalyticAccount,
        Account,
        Move,
        MoveLine,
        module='analytic_account_move', type_='model')
