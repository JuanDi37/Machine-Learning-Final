"""Datos sintéticos exclusivos para probar integridad y reproducibilidad."""

from pathlib import Path

import numpy as np
import pandas as pd


def make_fixture(root: Path, days=151):
    """Crear siete tablas; estos datos no son evidencia del supermercado."""
    root.mkdir(parents=True, exist_ok=True)
    tables = {
        "countries": pd.DataFrame(
            {"CountryID": [1], "CountryName": ["Sintético"], "CountryCode": ["XX"]}
        ),
        "cities": pd.DataFrame({"CityID": [1], "CityName": ["Sintética"], "CountryID": [1]}),
        "categories": pd.DataFrame({"CategoryID": [1], "CategoryName": ["Prueba"]}),
        "products": pd.DataFrame(
            {"ProductID": [1], "ProductName": ["Prueba"], "Price": [10.0], "CategoryID": [1]}
        ),
        "customers": pd.DataFrame(
            {"CustomerID": [1, 2, 3], "CityID": [1] * 3, "Address": ["Sintética"] * 3}
        ),
        "employees": pd.DataFrame(
            {
                "EmployeeID": [1, 2, 3],
                "FirstName": ["A", "B", "C"],
                "LastName": ["Prueba"] * 3,
                "CityID": [1] * 3,
                "HireDate": ["2017-01-01"] * 3,
            }
        ),
    }
    rows = []
    rng = np.random.default_rng(42)
    for i, day in enumerate(pd.date_range("2018-01-01", periods=days)):
        for seller in range(1, 4):
            quantity = int(20 + seller * 4 + day.dayofweek * 2 + i // 15 + rng.integers(0, 4))
            rows.append(
                {
                    "SalesID": len(rows) + 1,
                    "SalesPersonID": seller,
                    "CustomerID": seller,
                    "ProductID": 1,
                    "Quantity": quantity,
                    "Discount": 0.1,
                    "TotalPrice": quantity * 9,
                    "SalesDate": str(day),
                    "TransactionNumber": f"SYNTHETIC-{i}-{seller}",
                }
            )
    tables["sales"] = pd.DataFrame(rows)
    for name, table in tables.items():
        table.to_csv(root / f"{name}.csv", index=False)
    return tables
