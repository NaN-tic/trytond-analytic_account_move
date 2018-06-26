# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import move
from . import invoice


def register():
    Pool.register(
        move.Move,
        move.MoveLine,
        move.AnalyticAccountEntry,
        move.MoveLineTemplate,
        move.AnalyticAccountLineTemplate,
        module='analytic_account_move', type_='model')
    Pool.register(
        invoice.Invoice,
        invoice.InvoiceLine,
        depends=['account_invoice'],
        module="analytic_account_move", type_='model'
    )
