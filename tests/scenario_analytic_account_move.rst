==============================
Analytic Account Move Scenario
==============================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install account::

    >>> Module = Model.get('ir.module.module')
    >>> modules = Module.find([
    ...         ('name', '=', 'analytic_account_move'),
    ...         ])
    >>> Module.install([x.id for x in modules], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create fiscal year::

    >>> FiscalYear = Model.get('account.fiscalyear')
    >>> Sequence = Model.get('ir.sequence')
    >>> SequenceStrict = Model.get('ir.sequence.strict')
    >>> fiscalyear = FiscalYear(name='%s' % today.year)
    >>> fiscalyear.start_date = today + relativedelta(month=1, day=1)
    >>> fiscalyear.end_date = today + relativedelta(month=12, day=31)
    >>> fiscalyear.company = company
    >>> post_move_sequence = Sequence(name='%s' % today.year,
    ...     code='account.move', company=company)
    >>> post_move_sequence.save()
    >>> fiscalyear.post_move_sequence = post_move_sequence
    >>> fiscalyear.save()
    >>> FiscalYear.create_period([fiscalyear.id], config.context)
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> AccountTemplate = Model.get('account.account.template')
    >>> Account = Model.get('account.account')
    >>> account_template, = AccountTemplate.find([('parent', '=', None)])
    >>> create_chart = Wizard('account.create_chart')
    >>> create_chart.execute('account')
    >>> create_chart.form.account_template = account_template
    >>> create_chart.form.company = company
    >>> create_chart.execute('create_account')
    >>> receivable, = Account.find([
    ...         ('kind', '=', 'receivable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> payable, = Account.find([
    ...         ('kind', '=', 'payable'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> expense, = Account.find([
    ...         ('kind', '=', 'expense'),
    ...         ('company', '=', company.id),
    ...         ])
    >>> create_chart.form.account_receivable = receivable
    >>> create_chart.form.account_payable = payable
    >>> create_chart.execute('create_properties')

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
    >>> setattr(line, 'analytic_account_%s' % root.id, project1_analytic_acc)
    >>> line = move.lines.new()
    >>> line.account = expense
    >>> line.debit = Decimal(1500)
    >>> setattr(line, 'analytic_account_%s' % root.id, project2_analytic_acc)
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

Move to draft Wage Payment Move::

    >>> journal_expense.update_posted = True
    >>> journal_expense.save()
    >>> move.click('draft')

Check analytic lines has been removed::

    >>> move.reload()
    >>> [l.analytic_lines for l in move.lines]
    [[], [], [], []]
