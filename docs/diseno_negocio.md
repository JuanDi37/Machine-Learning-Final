# Diseño de negocio · Reto 1

## Comprensión del negocio

La gerencia comercial de la cadena necesita anticipar la demanda monetaria semanal, comprender tendencias y decidir dónde investigar necesidades de acompañamiento del equipo. El equipo del proyecto es Cynthia, Antonio y Juan Diego.

La decisión de capacidad se toma cada semana con horizonte de siete días. La decisión de acompañamiento se apoya en tendencias de 28 días, contribución y contexto de cartera. El análisis no propone despedir ni contratar personas basándose en una clasificación automática.

## Traducción analítica

Pregunta: ¿un modelo que usa historia disponible y calendario puede anticipar siete días de ventas mejor que repetir la semana anterior, y qué diferencias descriptivas entre vendedores merecen revisión operativa?

Tarea de ML: regresión supervisada multihorizonte de ingreso diario agregado. La unidad de análisis del modelo es fecha de origen y horizonte, no empleado. Separar el pronóstico agregado de la evaluación individual reduce el riesgo de interpretar asignación de clientes como talento comercial.

Línea base: pronóstico estacional de siete días. Modelo candidato: HistGradientBoostingRegressor. Con cinco meses de historia, la regularización y una comparación exigente con una regla simple son más justificables que una red profunda. Optuna busca learning rate, iteraciones, hojas, tamaño mínimo de hoja y regularización L2. Se ejecutan 25 ensayos con tres bloques temporales; el presupuesto es configurable.

Métrica principal: WAPE = suma de errores absolutos / suma de ventas observadas. Criterio predefinido: mejorar al menos 5% relativo respecto a la línea base. Métricas secundarias: MAE para interpretar error en UM, RMSE para penalizar fallos grandes y sesgo firmado para detectar sobreestimación. Un denominador cero produce una NOTA explícita y no una división inválida.

La elección del algoritmo usa únicamente validación. El holdout final se reserva para evaluar la decisión; si no confirma la mejora, no se recomienda uso operativo sin revisión. El entrenamiento se actualiza cada siete días, reproduciendo el uso propuesto. Las variables usan exclusivamente observaciones conocidas al origen. No se reporta estacionalidad anual ni intervalos con cobertura no validada.

## Desempeño del personal

| Indicador | Interpretación | Límite |
|---|---|---|
| Venta y participación | Generación y dependencia comercial | Cartera y demanda pueden explicar diferencias |
| Venta por día con ventas | Intensidad en días observados | No equivale a productividad por hora |
| Venta por día de vinculación observado | Venta sobre exposición temporal estimada | NOTA: faltan turnos, ausencias y jornadas |
| Ticket promedio | Valor medio de cada transacción | No equivale a conversión ni rentabilidad |
| Descuento ponderado por importe bruto | Intensidad de descuento sobre la venta | NOTA: falta política comercial y margen |
| Variación de 28 días | Tendencia individual en ventanas comparables | No se calcula con exposición insuficiente |

La contribución se calcula sobre el ingreso total del período y debe sumar 100% cuando el total es positivo. Los empleados sin transacciones se reportan como ausencia de evidencia; no se les asigna automáticamente bajo desempeño. No se presupone que la ciudad del empleado sea la ubicación de una tienda o de sus ventas.

## Perfil para contratación

Este dataset contiene empleados contratados y transacciones, pero carece de candidatos, entrevistas, habilidades, asignación de oportunidades y mediciones antes y después de contratar. **NOTA: no permite estimar qué perfil causará un buen desempeño al contratar.**

RR. HH. puede evaluar cuatro competencias mediante una prueba de trabajo común: atención y resolución de necesidades, conocimiento de productos, venta complementaria pertinente y disciplina en el registro de transacciones. Cada competencia se califica con una rúbrica de 1 a 5 con evidencia observable y dos evaluadores. Su validez debe contrastarse prospectivamente contra desempeño ajustado por oportunidades, conservando criterios de equidad. No se utilizan edad, género ni ubicación residencial como requisitos predictivos.

## Accionables y evaluación de impacto

| Responsable | Acción propuesta | Evidencia necesaria | Medida de éxito |
|---|---|---|---|
| Gerencia comercial | Revisar pronóstico cada semana y ajustar capacidad disponible | Error y sesgo del holdout, disponibilidad operativa | Menor error frente a línea base; cumplimiento de capacidad |
| Jefatura comercial | Investigar caída persistente de 28 días | Cartera, turnos, stock, demanda y descuentos | Causa documentada antes de intervenir |
| Jefatura comercial | Pilotear acompañamiento entre pares comparables | Volumen de oportunidades y exposición similares | Cambio incremental de ventas y costo del programa |
| RR. HH. | Estandarizar prueba de competencias | Rúbrica y seguimiento posterior | Consistencia de evaluadores y validez prospectiva |
| Analítica | Monitorear error y sesgo cada semana | Ventas observadas frente al pronóstico archivado | Identificar deterioro y reevaluar con cortes temporales |

El escenario financiero calcula una fracción hipotética del menor error absoluto durante 28 días. No es una predicción de ventas recuperadas: requiere evidencia de un piloto. **NOTA: faltan costos y márgenes, por lo que no se estima ROI ni utilidad.**

## Estado de la evidencia

**NOTA: no está disponible la tabla de ventas.** No existen métricas reales, ranking de vendedores, hallazgos temporales ni evidencia de superioridad del modelo. Los documentos y el pipeline expresan la decisión, el protocolo y sus controles; las conclusiones comerciales requieren una ejecución con transacciones reales.
