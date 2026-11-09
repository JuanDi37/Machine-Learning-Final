# Desempeño de las ventas · Avance parcial

## Introduction

Cynthia, Antonio y Juan Diego. Reto 1 del proyecto final: desempeño de ventas y del personal mediante CRISP-DM. Este reporte documenta la evidencia disponible y la solución implementada.

## Business problem

Gerencia comercial necesita planificar capacidad semanal y priorizar acompañamiento. Pregunta: ¿podemos anticipar siete días de ventas mejor que repetir la semana anterior y detectar diferencias que justifiquen revisar cartera y oportunidades?

## Data

Se verificaron seis CSV por sus columnas. Contienen clientes, países, productos, ciudades, categorías y empleados; sus nombres están cruzados. NOTA: falta la tabla de transacciones. El notebook original contiene una vista previa, no las ventas completas. NOTA: no se ha documentado la moneda ni la definición contable del importe.

## Methods

Carga por lotes, claves únicas, integridad referencial y validación de fechas, cantidades y descuentos. Tickets divididos entre lotes se cuentan una sola vez. Se conservan extremos válidos. Con fuentes completas, el pipeline calcula contribución, ticket, productividad descriptiva y tendencia de 28 días por vendedor.

## Model selection

HistGradientBoostingRegressor compite contra una línea base semanal. Optuna optimiza WAPE en validación expansiva. Los últimos 28 días se reservan para evaluación, con actualización semanal del entrenamiento y parámetros congelados. Umbral: 5% de mejora relativa de WAPE, considerando la simplicidad de la línea base. NOTA: el modelo definitivo y su rendimiento no se pueden determinar sin transacciones reales.

## Results

El inventario confirma seis tablas y ausencia de ventas. La implementación incluye pruebas e integración con fuentes sintéticas aisladas. NOTA: no hay ventas totales, rankings, tendencias, métricas reales ni modelo entrenado sobre el supermercado que reportar. Las salidas sintéticas verifican el software y no constituyen evidencia comercial.

## Business interpretation

La limitación actual es la disponibilidad de transacciones. No se puede concluir que un vendedor tenga mejor desempeño ni afirmar crecimiento o caída. El análisis posterior distinguirá contribución de habilidad, considerando exposición y cartera.

## Recommendations

Gerencia: incorporar transacciones y validar importe, descuento y cobertura. Jefatura: documentar cartera, turnos y stock antes de interpretar diferencias. RR. HH.: evaluar atención, productos, venta complementaria y registro mediante pruebas de trabajo. Validar acompañamiento con un piloto; medir venta incremental y costo antes de atribuir impacto.

## Limitations

NOTA: faltan transacciones, moneda, precios históricos, costos, márgenes, turnos, cuotas, afluencia, stock y asignación de cartera. NOTA: no hay candidatos ni evaluación prospectiva para validar un perfil de contratación. NOTA: cinco meses no permiten inferir estacionalidad anual. No se utilizan edad ni género como predictores.

## Conclusion

La solución está implementada como proyecto Kedro con Optuna, controles, pruebas y GitHub Actions. NOTA: los resultados y recomendaciones sustentadas en ventas reales permanecen pendientes de las transacciones. El protocolo distingue rendimiento predictivo, utilidad comercial y límites causales.
