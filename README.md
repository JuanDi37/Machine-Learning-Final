# Desempeño de las ventas

**Reto 1 · Cynthia, Antonio y Juan Diego.** Proyecto CRISP-DM para gerencia comercial: anticipar siete días de ventas y analizar generación de ventas, tendencias, contribución y productividad descriptiva del equipo.

**NOTA: falta la tabla de transacciones de ventas en los archivos disponibles.** `sales.csv` contiene empleados; los otros cinco CSV también tienen nombres que no corresponden a sus columnas. El proyecto identifica las tablas por esquema y conserva los archivos originales. No hay resultados reales de ventas ni modelo entrenado sobre el supermercado. Las salidas de CI usan exclusivamente datos sintéticos y no constituyen evidencia de negocio.

## Pregunta y decisión de negocio

¿Podemos anticipar las ventas de los próximos siete días mejor que repetir la semana anterior y detectar diferencias de contribución y tendencia entre vendedores que justifiquen una revisión de cartera, turnos y acompañamiento?

La gerencia comercial utilizaría el pronóstico para planificar capacidad semanal. La jefatura comercial utilizaría el análisis descriptivo para investigar diferencias. RR. HH. utilizaría una rúbrica de competencias, cuya validez debe comprobarse mediante un proceso de selección y seguimiento, porque este dataset no permite aprender un perfil de contratación.

Éxito técnico: reducción relativa de WAPE de al menos 5% frente a la línea base semanal en validación temporal y confirmación en el holdout. La selección se congela usando validación; el holdout determina si existe evidencia para recomendar su uso operativo. También se reportan MAE, RMSE y sesgo. Si el modelo complejo no mejora la validación, se conserva la línea base.

Éxito comercial propuesto: en un piloto, registrar ventas recuperadas y costo de la intervención, comparando equipos con oportunidades similares. No se afirma un aumento de ventas a partir de una mejora de WAPE. **NOTA: no hay costos, márgenes, horas trabajadas ni datos de un piloto para calcular retorno real.**

## Instalación y ejecución

Python 3.12, desde la raíz del repositorio:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-lock.txt
.venv\Scripts\python -m pip install --no-deps -e ".[dev]"
.venv\Scripts\kedro run --pipelines discovery
.venv\Scripts\kedro run
```

En Linux/macOS, los ejecutables del entorno se encuentran en `.venv/bin/`.

`kedro run --pipelines discovery` funciona con los archivos actuales y produce `data/08_reporting/inventario.csv`. La ejecución completa se detiene con una **NOTA** que identifica la tabla faltante. Las fuentes se buscan en la carpeta configurada, su subcarpeta `dataset/` y `data/01_raw/`; no se descarga ni se inventa el dataset. Dos fuentes para una misma tabla se rechazan por ambigüedad. Las siete tablas deben estar presentes y tener claves consistentes.

Los parámetros de ejecución, unidades de descuento, origen del importe, período, semilla, presupuesto Optuna y umbral de aceptación están documentados en `conf/base/parameters.yml`. El catálogo está en `conf/base/catalog.yml`. El notebook `01_desempeno_ventas.ipynb` presenta el diagnóstico y permite ejecutar el mismo pipeline.

## Metodología y controles

1. **Comprensión del negocio:** decisiones, stakeholder y criterios definidos en [el diseño de negocio](docs/diseno_negocio.md).
2. **Comprensión de datos:** inventario por columnas y revisión de siete tablas. [Diagnóstico de las fuentes actuales](docs/diagnostico_datos.md).
3. **Preparación:** lectura de ventas en lotes de 250 mil filas; integridad referencial, claves, descuentos y fechas. Duplicados de SalesID y tickets inconsistentes se detectan en SQLite temporal para acotar memoria. Tickets divididos entre lotes se cuentan una sola vez. Se detiene ante errores que puedan cambiar los resultados.
4. **Modelado:** regresión HistGradientBoosting con relaciones no lineales y regularización; pronóstico directo de horizontes 1 a 7, con variables de calendario, rezagos y medias históricas disponibles al origen. Optuna optimiza WAPE con semilla y ejecución secuencial reproducible. No se usan género, fecha de nacimiento ni identificadores individuales como predictores.
5. **Evaluación:** tres orígenes semanales de validación expansiva y 28 días finales de holdout. Dentro del holdout se actualiza el entrenamiento cada siete días, sin cambiar hiperparámetros. Con enero–mayo completos: validación 13–19, 20–26 de abril y 27 de abril–3 de mayo; holdout 4–31 de mayo. No se usa partición aleatoria ni información del futuro para predecir un bloque.
6. **Implementación:** pipelines Kedro de descubrimiento, preparación, entrenamiento y comunicación. Artefactos de modelo y evidencia exportados en cada ejecución exitosa. La operación propuesta requiere revisión semanal de error y sesgo, y una nueva evaluación temporal antes de cambiar el modelo.

Los extremos válidos se mantienen; no se eliminan ventas altas por superar un percentil. Los faltantes esenciales y cantidades inválidas detienen el pipeline. Los días internos sin registros no se convierten en cero salvo configuración explícita respaldada por verificación del origen. Los meses incompletos no se comparan como si fueran meses completos.

**NOTA: `TotalPrice` aparece en cero en la vista previa del notebook original.** Por defecto se calcula `Quantity × Price × (1 − Discount)` y se rotula siempre como ingreso estimado a precio de catálogo. No se interpreta como facturación auditada ni utilidad. El descuento se interpreta como fracción por configuración explícita; no se adivina su unidad. **NOTA: el catálogo no conserva precios históricos ni una moneda documentada.** Se utilizan unidades monetarias (UM).

## Outputs

Una ejecución completa con transacciones válidas produce:

| Archivo | Uso |
|---|---|
| `data/08_reporting/calidad.json` | Cobertura, importes en cero, diferencias frente al catálogo y advertencias |
| `data/08_reporting/desempeno_vendedores.csv` | Venta, contribución, ticket, descuento ponderado y tendencia de 28 días |
| `data/08_reporting/tendencia_mensual.csv` | Venta mensual, promedio diario y comparabilidad de períodos |
| `data/08_reporting/patron_semanal.csv` | Promedio y dispersión por día de semana |
| `data/08_reporting/metricas_modelo.json` | Comparación, selección y umbral de uso operativo |
| `data/08_reporting/evaluacion_temporal.csv` | Evidencia de predicciones y orígenes del holdout |
| `data/08_reporting/optuna.csv` | Ensayos e hiperparámetros |
| `data/08_reporting/pronostico_7_dias.csv` | Próximos siete días de venta estimada |
| `data/06_models/pronostico.pkl` | Modelo, historia, horizonte y métricas |
| `data/08_reporting/reporte.pdf` | Reporte con las diez secciones solicitadas |
| `data/08_reporting/presentacion.pdf` | Diapositiva única para audiencia de negocio |
| `data/08_reporting/resumen_negocio.json` | KPIs y recomendaciones con escenarios explícitos |

El artefacto pickle se carga únicamente desde ejecuciones propias. El notebook original `intro.ipynb` se conserva como referencia; sus outputs históricos no se usan como fuente de entrenamiento.

La interpretación del candidato incluye importancia por permutación de variables, calculada exclusivamente en validación y expresada como aumento de MAE en UM. **NOTA: pocos días y variables correlacionadas limitan su estabilidad; no representa un efecto causal.**

## Validación automatizada

```powershell
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .
.venv\Scripts\pytest -q
.venv\Scripts\python -m scripts.make_ci_fixture
.venv\Scripts\kedro run --env ci
```

**NOTA: el entorno `ci` genera datos sintéticos identificados como tales y guarda sus salidas en `data/ci_output/`, separadas de los resultados reales.** GitHub Actions instala el proyecto, ejecuta Ruff, pruebas y el pipeline completo en cada push y pull request. Las pruebas comprueban conservación de importes, duplicados entre lotes, referencias, escala de descuentos, tickets, ausencia de días y evaluación temporal. El archivo `requirements-lock.txt` fija las versiones verificadas.

## Alcance y entrega

La solución se limita al desempeño de ventas y del personal. El análisis de clientes y portafolio de productos solo se utiliza para validar las relaciones del dataset. El perfil para contratación se desarrolla como competencias a evaluar, sin atribuir causalidad al desempeño histórico.

**NOTA: la entrega final con métricas reales, modelo entrenado sobre el supermercado y recomendaciones sustentadas está pendiente de las transacciones.** El enlace del repositorio configurado es https://github.com/JuanDi37/Machine-Learning-Final. La configuración de GitHub Actions está incluida; su ejecución remota debe verificarse en GitHub después de publicar los cambios.

El avance documentado se puede revisar en [el reporte parcial](docs/reporte_parcial.pdf), [la diapositiva](docs/presentacion_parcial.pdf) y [su fuente de texto](docs/reporte_parcial.md). Se regeneran con `python -m scripts.partial_report`.

**NOTA: el workflow aún no se ha ejecutado en GitHub; la validación realizada es local.**
