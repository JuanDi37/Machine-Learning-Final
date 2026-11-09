# Validación local

Se ejecutaron los controles en Windows con Python 3.12, el catálogo Kedro y las versiones fijadas en `requirements-lock.txt`.

| Control | Resultado |
|---|---|
| `ruff check .` | Sin errores |
| `ruff format --check .` | Formato validado |
| `pytest -q` | 11 pruebas aprobadas |
| `kedro run --pipelines discovery` | Inventario de los seis CSV generado |
| `kedro run --env ci` | Cinco nodos ejecutados; métricas, modelo, reporte y diapositiva generados |
| Notebook | Ejecutado; muestra inventario y NOTA de transacciones faltantes |
| Diapositiva parcial | Exportada a PDF y PNG; revisada visualmente |

Las pruebas cubren detección por esquema, ausencia de ventas, conservación de importes, claves duplicadas entre lotes, productos desconocidos, descuentos inválidos, tickets inconsistentes, días ausentes, importes registrados en cero, tickets repartidos entre lotes y evaluación temporal. También verifican pronósticos finitos y no negativos e importancia de variables calculada en validación.

**NOTA: la integración completa utiliza datos sintéticos en `data/ci_fixture/`; sus salidas se guardan en `data/ci_output/` y los gráficos y PDF llevan una NOTA visible. No son resultados del supermercado.**

**NOTA: no se puede ejecutar el análisis real completo porque falta la tabla de transacciones.** El diagnóstico reconoce empleados dentro de `sales.csv` y detiene el análisis antes del entrenamiento.

**NOTA: la ejecución de GitHub Actions en el repositorio remoto está pendiente de publicar los cambios; solo se verificó el flujo localmente.**
