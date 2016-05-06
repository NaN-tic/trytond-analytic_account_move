#:after:account/account:section:definir_planes_analiticos#

================================================
Introducir manualmente la analítica de un apunte
================================================

Si introducimos manualmente un asiento en el que alguno de sus apuntes debe
llevar analítica asociada, podemos hacerlo de dos formas: introduciendo diréctamente los apuntes analíticos en el campo |analytic_lines| de los apuntes
(solo visible en la vista formulario) o seleccionar las cuentas analíticas en
los campos con el nombre de los diferentes planes analíticos que encontraremos
tanto en el listado de apuntes del asiento como en el formulario del apunte.

Si rellenamos las cuentas (y no introducimos ningun apunte analítico
manualmente), **al confirmar** el asiento se crearán los apuntes analíticos. De
la misma forma, **al volver a borrador** el asiento se borrarán estos apuntes
analíticos, y si lo duplicamos tampoco se copiarán los apuntes analíticos ya
que se crearán automáticamente al confirmar el asiento.

.. |analytic_lines| field:: account.move.line/analytic_lines
