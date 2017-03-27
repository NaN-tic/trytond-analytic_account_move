# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from trytond.pool import Pool
from .account import *
from .move import *
from .invoice import *


def register():
    Pool.register(
        AnalyticAccount,
        Move,
        MoveLine,
        InvoiceLine,
        module='analytic_account_move', type_='model')