==============================
Analytic Account Move Scenario
==============================

Imports::

    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account::

    >>> Module = Model.get('ir.module')
    >>> module, = Module.find([
    ...         ('name', '=', 'analytic_account_move'),
    ...         ])
    >>> module.click('install')
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> fiscalyear = create_fiscalyear(company)
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> payable = accounts['payable']
    >>> expense = accounts['expense']

Create analytic accounts::

    >>> AnalyticAccount = Model.get('analytic_account.account')
    >>> root = AnalyticAccount(type='root', name='Root')
    >>> root.save()
    >>> project1_analytic_acc = AnalyticAccount(root=root, parent=root,
    ...     name='Project 1')
    >>> project1_analytic_acc.save()
    >>> project2_analytic_acc = AnalyticAccount(root=root, parent=root,
    ...     name='Project 2')
    >>> project2_analytic_acc.save()
    >>> project3_analytic_acc = AnalyticAccount(root=root, parent=root,
    ...     name='Project 3')
    >>> project3_analytic_acc.save()

Create parties::

    >>> Party = Model.get('party.party')
    >>> employee1 = Party(name='Employee 1')
    >>> employee1.save()
    >>> employee2 = Party(name='Employee 2')
    >>> employee2.save()

Create Wage Payment Move::

    >>> Journal = Model.get('account.journal')
    >>> Move = Model.get('account.move')
    >>> journal_expense, = Journal.find([
    ...         ('code', '=', 'EXP'),
    ...         ])
    >>> journal_cash, = Journal.find([
    ...         ('code', '=', 'CASH'),
    ...         ])
    >>> move = Move()
    >>> move.period = period
    >>> move.journal = journal_expense
    >>> move.date = period.start_date
    >>> move.description = 'Wages'
    >>> line = move.lines.new()
    >>> line.account = expense
    >>> line.debit = Decimal(2000)
    >>> entry, = line.analytic_accounts
    >>> entry.account = project1_analytic_acc
    >>> line = move.lines.new()
    >>> line.account = expense
    >>> line.debit = Decimal(1500)
    >>> entry, = line.analytic_accounts
    >>> entry.account = project2_analytic_acc
    >>> line = move.lines.new()
    >>> line.account = payable
    >>> line.credit = Decimal(2000)
    >>> line.party = employee1
    >>> line = move.lines.new()
    >>> line.account = payable
    >>> line.credit = Decimal(1500)
    >>> line.party = employee1
    >>> move.save()

Post Wage Payment Move::

    >>> move.click('post')

Check accounts amounts::

    >>> expense.reload()
    >>> expense.debit
    Decimal('3500.00')
    >>> payable.reload()
    >>> payable.credit
    Decimal('3500.00')

Check analytic accounts amounts::

    >>> project1_analytic_acc.reload()
    >>> project1_analytic_acc.debit
    Decimal('2000.00')
    >>> project2_analytic_acc.reload()
    >>> project2_analytic_acc.debit
    Decimal('1500.00')

Copy the move and check analytic lines has been removed but not the accounts::

    >>> move2 = Move(Move.copy([move.id], config.context)[0])
    >>> [l.analytic_lines for l in move2.lines]
    [[], [], [], []]
    >>> sorted([l.analytic_accounts[0].account.name
    ...         for l in move.lines if l.account.id == expense.id])
    [u'Project 1', u'Project 2']

Post the duplicated move and check analytic accounts amounts::

    >>> move2.click('post')
    >>> project1_analytic_acc.reload()
    >>> project1_analytic_acc.debit
    Decimal('4000.00')
    >>> project2_analytic_acc.reload()
    >>> project2_analytic_acc.debit
    Decimal('3000.00')

Move to draft Wage Payment Move::

    >>> journal_expense.update_posted = True
    >>> journal_expense.save()
    >>> move.click('draft')

Check analytic lines has been removed::

    >>> move.reload()
    >>> [l.analytic_lines for l in move.lines]
    [[], [], [], []]

Check analytic accounts amounts::

    >>> project1_analytic_acc.reload()
    >>> project1_analytic_acc.debit
    Decimal('2000.00')
    >>> project2_analytic_acc.reload()
    >>> project2_analytic_acc.debit
    Decimal('1500.00')

Delete an analytic account::

    >>> project3_analytic_acc.delete()
