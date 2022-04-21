==============================
Analytic Account Move Scenario
==============================

Imports::

    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts

Install analytic_account_move::

    >>> config = activate_modules(['analytic_account_move'])

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
    ['Project 1', 'Project 2']

Post the duplicated move and check analytic accounts amounts::

    >>> move2.click('post')
    >>> project1_analytic_acc.reload()
    >>> project1_analytic_acc.debit
    Decimal('4000.00')
    >>> project2_analytic_acc.reload()
    >>> project2_analytic_acc.debit
    Decimal('3000.00')

Delete an analytic account::

    >>> project3_analytic_acc.delete()

Create Move Template::

    >>> MoveTemplate = Model.get('account.move.template')
    >>> MoveLineTemplate = Model.get('account.move.line.template')
    >>> AnalyticLineTemplate = Model.get('analytic_account.line.template')

    >>> move_template = MoveTemplate()
    >>> move_template.name = 'Move Template'
    >>> move_template.journal = journal_expense
    >>> line_template = MoveLineTemplate()
    >>> move_template.lines.append(line_template)
    >>> line_template.operation = 'debit'
    >>> line_template.amount = '10.0'
    >>> line_template.account = expense
    >>> analytic_line_template = AnalyticLineTemplate()
    >>> line_template.analytic_accounts.append(analytic_line_template)
    >>> analytic_line_template.root = root
    >>> analytic_line_template.account = project1_analytic_acc
    >>> line_template = MoveLineTemplate()
    >>> move_template.lines.append(line_template)
    >>> line_template.operation = 'credit'
    >>> line_template.amount = '10.0'
    >>> line_template.account = expense
    >>> move_template.save()

Create Moves from template::

    >>> create = Wizard('account.move.template.create')
    >>> create.form.template = move_template
    >>> create.execute('keywords')
    >>> create.execute('create_')

    >>> m1, _, _ = Move.find([])
    >>> l1, l2 = m1.lines
    >>> analytic_account1, = l1.analytic_accounts
    >>> analytic_account2, = l2.analytic_accounts
    >>> analytic_account1.root.id
    1
    >>> analytic_account1.account
    >>> analytic_account2.root.id
    1
    >>> analytic_account2.account.id
    2
