# Diagnóstico de datos disponibles

**NOTA: falta la tabla de transacciones de ventas.** La revisión usa las columnas y el contenido de los seis CSV de la carpeta del proyecto, no sus nombres.

| Archivo existente | Tabla que contiene | Identificador principal |
|---|---|---|
| `categories.csv` | Clientes | CustomerID |
| `cities.csv` | Países | CountryID |
| `countries.csv` | Productos | ProductID |
| `employees.csv` | Ciudades | CityID |
| `products.csv` | Categorías | CategoryID |
| `sales.csv` | Empleados | EmployeeID |

No existe un CSV con SalesID, SalesPersonID, CustomerID, ProductID, Quantity, Discount, TotalPrice, SalesDate y TransactionNumber. El notebook original conserva una vista previa de tres ventas y una dimensión histórica de 6,758,125 filas; no contiene esas transacciones completas. No se utiliza esa vista previa para simular resultados del negocio.

**NOTA: faltan las transacciones para calcular ingresos, unidades, tickets, contribución, tendencia y pronósticos reales.** La ejecución completa se detiene antes del modelado; el pipeline `discovery` sí puede ejecutarse y exportar el inventario verificable.

**NOTA: no se ha documentado la moneda ni la definición contable de TotalPrice.** La vista previa presenta importes en cero. El modo predeterminado reconstruye ingreso estimado con el catálogo y una escala explícita de descuentos; el reporte distingue ese estimado de facturación real.

**NOTA: faltan costos, márgenes, turnos, cuotas, afluencia, stock y asignación de cartera.** Estos elementos impiden atribuir diferencias a habilidad individual, calcular productividad por hora o prometer retorno económico.

**NOTA: no existen datos de candidatos ni resultados prospectivos de contratación.** El perfil de contratación se formula como competencias a evaluar, sin usar atributos demográficos ni presentar asociaciones históricas como evidencia causal.

Los archivos originales permanecen intactos. La detección por esquema evita que sus nombres cruzados produzcan uniones incorrectas.
