# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .move import *


def register():
    Pool.register(
        Move,
        MoveLine,
        AnalyticAccountEntry,
        module='analytic_account_move', type_='model')
