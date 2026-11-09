"""Nodos de carga, control de calidad y análisis comercial con memoria acotada."""

import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd

from ventas.modeling import train as train

SCHEMAS = {
    "sales": {
        "SalesID",
        "SalesPersonID",
        "CustomerID",
        "ProductID",
        "Quantity",
        "Discount",
        "TotalPrice",
        "SalesDate",
        "TransactionNumber",
    },
    "products": {"ProductID", "ProductName", "Price", "CategoryID"},
    "employees": {"EmployeeID", "FirstName", "LastName", "CityID", "HireDate"},
    "customers": {"CustomerID", "CityID", "Address"},
    "categories": {"CategoryID", "CategoryName"},
    "cities": {"CityID", "CityName", "CountryID"},
    "countries": {"CountryID", "CountryName", "CountryCode"},
}


def discover(params: dict) -> pd.DataFrame:
    """Identificar tablas por esquema, sin confiar en los nombres de archivo."""
    root = Path(params["data_dir"]).resolve()
    files = set(root.glob("*.csv"))
    for folder in (root / "dataset", root / "data" / "01_raw"):
        files.update(folder.glob("*.csv"))
    rows = []
    for path in sorted(files):
        columns = set(pd.read_csv(path, nrows=0).columns)
        matches = [name for name, required in SCHEMAS.items() if required <= columns]
        rows.append(
            {
                "archivo": str(path),
                "tabla": matches[0] if len(matches) == 1 else "desconocida",
                "bytes": path.stat().st_size,
                "columnas": ", ".join(sorted(columns)),
            }
        )
    return pd.DataFrame(rows, columns=["archivo", "tabla", "bytes", "columnas"])


def paths_from_inventory(inventory: pd.DataFrame) -> dict:
    """Exigir una fuente inequívoca por tabla antes de analizar ventas."""
    known = inventory[inventory.tabla != "desconocida"]
    duplicates = known.loc[known.tabla.duplicated(False), "tabla"].unique().tolist()
    missing = sorted(set(SCHEMAS) - set(known.tabla))
    if missing or duplicates:
        raise ValueError(
            f"NOTA: Fuentes incompletas o ambiguas. Faltantes: {missing}; "
            f"tablas repetidas: {duplicates}. Consulte inventario.csv."
        )
    return dict(zip(known.tabla, known.archivo, strict=True))


def _dimension(path: str, key: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df[key].isna().any() or df[key].duplicated().any():
        raise ValueError(f"NOTA: Clave primaria nula o duplicada: {key}.")
    values = pd.to_numeric(df[key], errors="raise")
    if not np.isfinite(values).all() or (values % 1 != 0).any():
        raise ValueError(f"NOTA: Clave no entera: {key}.")
    df[key] = values.astype("int64")
    return df


def _references(child: pd.DataFrame, foreign: str, parent: pd.DataFrame, key: str):
    if child[foreign].isna().any() or not child[foreign].isin(parent[key]).all():
        raise ValueError(f"NOTA: Referencia ausente o desconocida: {foreign} -> {key}.")


def prepare(inventory: pd.DataFrame, params: dict):
    """Validar todas las filas; agregar por lotes y deduplicar tickets en disco."""
    paths = paths_from_inventory(inventory)
    products = _dimension(paths["products"], "ProductID")
    employees = _dimension(paths["employees"], "EmployeeID")
    customers = _dimension(paths["customers"], "CustomerID")
    categories = _dimension(paths["categories"], "CategoryID")
    cities = _dimension(paths["cities"], "CityID")
    countries = _dimension(paths["countries"], "CountryID")
    for child, fk, parent, pk in [
        (products, "CategoryID", categories, "CategoryID"),
        (employees, "CityID", cities, "CityID"),
        (customers, "CityID", cities, "CityID"),
        (cities, "CountryID", countries, "CountryID"),
    ]:
        _references(child, fk, parent, pk)
    products["Price"] = pd.to_numeric(products.Price, errors="raise")
    if not np.isfinite(products.Price).all() or (products.Price < 0).any():
        raise ValueError("NOTA: El catálogo contiene precios inválidos.")
    hires = pd.to_datetime(employees.HireDate, errors="raise")
    if hires.isna().any():
        raise ValueError("NOTA: Fecha de contratación ausente.")
    hire_map = pd.Series(hires.dt.normalize().values, index=employees.EmployeeID)
    mode = params["revenue_mode"]
    if mode not in {"recorded", "catalog_estimate"}:
        raise ValueError("NOTA: revenue_mode debe ser recorded o catalog_estimate.")
    if params["discount_scale"] not in {"fraction", "percent"}:
        raise ValueError("NOTA: discount_scale debe ser fraction o percent.")
    aggregated, n_rows, zero_totals, deviations = [], 0, 0, 0
    with tempfile.TemporaryDirectory(prefix="ventas-") as tmp:
        with closing(sqlite3.connect(str(Path(tmp) / "quality.sqlite"))) as db:
            db.execute("CREATE TABLE ids (id INTEGER PRIMARY KEY)")
            db.execute(
                "CREATE TABLE tickets (ticket TEXT, date TEXT, seller INTEGER, "
                "customer INTEGER, PRIMARY KEY(ticket, date, seller, customer))"
            )
            for chunk in pd.read_csv(
                paths["sales"], chunksize=params["chunksize"], dtype={"TransactionNumber": "string"}
            ):
                required = list(SCHEMAS["sales"])
                if chunk[required].isna().any().any():
                    raise ValueError(
                        "NOTA: Ventas contiene valores faltantes en columnas obligatorias."
                    )
                for key in ["SalesID", "SalesPersonID", "ProductID", "CustomerID"]:
                    values = pd.to_numeric(chunk[key], errors="raise")
                    if not np.isfinite(values).all() or (values % 1 != 0).any():
                        raise ValueError(f"NOTA: Identificador inválido: {key}.")
                    chunk[key] = values.astype("int64")
                try:
                    db.executemany("INSERT INTO ids VALUES (?)", ((int(x),) for x in chunk.SalesID))
                except sqlite3.IntegrityError as exc:
                    raise ValueError(
                        "NOTA: SalesID duplicado: se detiene para evitar doble conteo."
                    ) from exc
                _references(chunk, "ProductID", products, "ProductID")
                _references(chunk, "SalesPersonID", employees, "EmployeeID")
                _references(chunk, "CustomerID", customers, "CustomerID")
                dates = pd.to_datetime(chunk.SalesDate, errors="raise").dt.normalize()
                if not dates.between(
                    pd.Timestamp(params["expected_start"]), pd.Timestamp(params["expected_end"])
                ).all():
                    raise ValueError("NOTA: Ventas fuera del período configurado.")
                if (dates < chunk.SalesPersonID.map(hire_map)).any():
                    raise ValueError("NOTA: Se encontraron ventas anteriores a la contratación.")
                for key in ["Quantity", "Discount", "TotalPrice"]:
                    chunk[key] = pd.to_numeric(chunk[key], errors="raise")
                    if not np.isfinite(chunk[key]).all():
                        raise ValueError(f"NOTA: Valor no finito en {key}.")
                if (chunk.Quantity <= 0).any() or (chunk.Quantity % 1 != 0).any():
                    raise ValueError(
                        "NOTA: Cantidades no positivas o fraccionarias; revisar devoluciones."
                    )
                discount = chunk.Discount / (100 if params["discount_scale"] == "percent" else 1)
                if not discount.between(0, 1).all():
                    raise ValueError("NOTA: Descuentos fuera de escala; no se infiere su unidad.")
                gross = chunk.Quantity * chunk.ProductID.map(products.set_index("ProductID").Price)
                estimate = gross * (1 - discount)
                if (chunk.TotalPrice < 0).any():
                    raise ValueError("NOTA: TotalPrice negativo; revisar devoluciones.")
                zero_totals += int(chunk.TotalPrice.eq(0).sum())
                deviations += int(
                    (~np.isclose(chunk.TotalPrice, estimate, rtol=0.01, atol=0.01)).sum()
                )
                revenue = chunk.TotalPrice if mode == "recorded" else estimate
                tickets = chunk.TransactionNumber.str.strip()
                if tickets.eq("").any():
                    raise ValueError("NOTA: TransactionNumber vacío.")
                ticket_rows = pd.DataFrame(
                    {
                        "ticket": tickets,
                        "date": dates.dt.strftime("%Y-%m-%d"),
                        "seller": chunk.SalesPersonID,
                        "customer": chunk.CustomerID,
                    }
                ).drop_duplicates()
                db.executemany(
                    "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?, ?)",
                    ticket_rows.itertuples(index=False, name=None),
                )
                frame = pd.DataFrame(
                    {
                        "date": dates,
                        "seller": chunk.SalesPersonID,
                        "revenue": revenue,
                        "gross": gross,
                        "discount_value": gross * discount,
                        "units": chunk.Quantity,
                        "lines": 1,
                    }
                )
                aggregated.append(frame.groupby(["date", "seller"], observed=True).sum())
                n_rows += len(chunk)
            if not n_rows:
                raise ValueError("NOTA: La tabla de ventas está vacía.")
            conflict = db.execute(
                "SELECT ticket FROM tickets GROUP BY ticket HAVING COUNT(*) > 1 LIMIT 1"
            ).fetchone()
            if conflict:
                raise ValueError(
                    "NOTA: Un ticket pertenece a múltiples fechas, vendedores o clientes."
                )
            ticket_counts = pd.read_sql_query(
                "SELECT date, seller, COUNT(*) AS transactions, "
                "COUNT(DISTINCT customer) AS customers FROM tickets GROUP BY date, seller",
                db,
            )
    if mode == "recorded" and zero_totals == n_rows:
        raise ValueError(
            "NOTA: TotalPrice es cero en todas las filas; no permite medir ingresos reales."
        )
    seller_daily = pd.concat(aggregated).groupby(level=[0, 1]).sum().reset_index()
    ticket_counts["date"] = pd.to_datetime(ticket_counts.date)
    seller_daily = seller_daily.merge(ticket_counts, on=["date", "seller"], validate="one_to_one")
    daily = seller_daily.groupby("date")[
        ["revenue", "gross", "discount_value", "units", "lines", "transactions"]
    ].sum()
    calendar = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    absent = calendar.difference(daily.index)
    if len(absent) and not params["missing_days_are_zero"]:
        raise ValueError(
            f"NOTA: Hay {len(absent)} días sin registros. No se imputan ceros sin confirmar."
        )
    daily = daily.reindex(calendar, fill_value=0).rename_axis("date").reset_index()
    seller_daily["hire_date"] = seller_daily.seller.map(hire_map)
    quality = {
        "synthetic_data": params["synthetic_data"],
        "rows": n_rows,
        "zero_totalprice_rows": zero_totals,
        "totalprice_vs_catalog_mismatches": deviations,
        "revenue_mode": mode,
        "revenue_label": "Ingreso registrado"
        if mode == "recorded"
        else "Ingreso estimado a precio de catálogo",
        "currency": "NOTA: moneda no documentada; unidades monetarias (UM)",
        "missing_days_filled": len(absent),
        "outliers_removed": 0,
        "start": str(daily.date.min().date()),
        "end": str(daily.date.max().date()),
        "observed_sellers": int(seller_daily.seller.nunique()),
        "catalog_sellers": len(employees),
        "sellers_without_transactions": sorted(
            set(employees.EmployeeID.tolist()) - set(seller_daily.seller.tolist())
        ),
        "notes": [
            "No se eliminan ventas extremas válidas.",
            "NOTA: Price no conserva precios históricos; no es facturación auditada.",
            "NOTA: faltan costos, turnos, cuotas, afluencia y asignación de cartera.",
        ],
    }
    return daily, seller_daily, quality


def describe(daily: pd.DataFrame, seller_daily: pd.DataFrame, params: dict):
    """Contribución, tendencia y productividad descriptiva sin atribución causal."""
    daily, sellers = daily.copy(), seller_daily.copy()
    daily["date"] = pd.to_datetime(daily.date)
    sellers["date"] = pd.to_datetime(sellers.date)
    sellers["hire_date"] = pd.to_datetime(sellers.hire_date)
    end = daily.date.max()
    summary = sellers.groupby("seller").agg(
        revenue=("revenue", "sum"),
        units=("units", "sum"),
        transactions=("transactions", "sum"),
        active_days=("date", "nunique"),
        hire_date=("hire_date", "first"),
        gross=("gross", "sum"),
        discount_value=("discount_value", "sum"),
    )
    summary["contribution"] = (
        summary.revenue / summary.revenue.sum() if summary.revenue.sum() else 0
    )
    summary["revenue_per_active_day"] = summary.revenue / summary.active_days
    summary["ticket_value"] = summary.revenue / summary.transactions
    summary["weighted_discount"] = summary.discount_value / summary.gross.replace(0, np.nan)
    summary["observed_employment_days"] = (
        end - summary.hire_date.clip(lower=daily.date.min())
    ).dt.days + 1
    summary["revenue_per_observed_employment_day"] = (
        summary.revenue / summary.observed_employment_days
    )
    recent = sellers[sellers.date > end - pd.DateOffset(days=28)].groupby("seller").revenue.sum()
    previous = (
        sellers[
            (sellers.date > end - pd.DateOffset(days=56))
            & (sellers.date <= end - pd.DateOffset(days=28))
        ]
        .groupby("seller")
        .revenue.sum()
    )
    summary["recent_28d"] = recent.reindex(summary.index, fill_value=0)
    summary["previous_28d"] = previous.reindex(summary.index, fill_value=0)
    summary["growth_28d"] = summary.recent_28d / summary.previous_28d.replace(0, np.nan) - 1
    if len(daily) < 56:
        summary["growth_28d"] = np.nan
    summary.loc[summary.observed_employment_days < 56, "growth_28d"] = np.nan
    summary["sufficient_history"] = summary.active_days >= params["min_seller_days"]
    monthly = daily.groupby(daily.date.dt.to_period("M").astype(str)).agg(
        revenue=("revenue", "sum"),
        transactions=("transactions", "sum"),
        units=("units", "sum"),
        observed_days=("date", "size"),
    )
    monthly.index.name = "month"
    monthly["calendar_days"] = pd.PeriodIndex(monthly.index, freq="M").days_in_month
    monthly["complete_month"] = monthly.observed_days == monthly.calendar_days
    monthly["revenue_per_day"] = monthly.revenue / monthly.observed_days
    monthly["growth_complete_month"] = monthly.revenue.pct_change(fill_method=None).where(
        monthly.complete_month & monthly.complete_month.shift(1, fill_value=False)
    )
    weekday = daily.groupby(daily.date.dt.dayofweek).agg(
        revenue_mean=("revenue", "mean"),
        revenue_std=("revenue", "std"),
        observed_days=("date", "size"),
        transactions_mean=("transactions", "mean"),
    )
    weekday.index.name = "weekday"
    return (
        summary.sort_values("revenue", ascending=False).reset_index(),
        monthly.reset_index(),
        weekday.reset_index(),
    )


def report(daily, sellers, monthly, weekday, metrics, predictions, forecast, quality, params):
    """Generar evidencia y escenarios de negocio, sin presentar correlación como impacto."""
    from ventas.reporting import write_report

    result = {
        "revenue": float(daily.revenue.sum()),
        "units": int(daily.units.sum()),
        "transactions": int(daily.transactions.sum()),
        "ticket_value": float(daily.revenue.sum() / daily.transactions.sum()),
        "top3_seller_share": float(sellers.head(3).contribution.sum()),
        "selected_model": metrics["selected_model"],
        "deployment_gate_passed": metrics["deployment_gate_passed"],
        "quality": quality,
        "recommendations": [
            "Planificar capacidad semanal con el pronóstico y revisar error cada semana.",
            "Revisar cartera, turnos y afluencia antes de atribuir diferencias a vendedores.",
            "Usar pares comparables y un piloto para evaluar acompañamiento comercial.",
            "Contratar mediante pruebas de atención, venta complementaria y disciplina comercial; "
            "este dataset no valida un perfil predictivo de contratación.",
        ],
    }
    gap = max(0.0, metrics["holdout_baseline"]["mae"] - metrics["holdout_selected"]["mae"])
    result["scenario"] = {
        "description": "Escenario de valor de una mejor planificación, sin atribución causal",
        "daily_error_reduction_um": gap,
        "assumed_recovery_fraction": params["recovery_fraction"],
        "illustrative_28d_value_um": gap * 28 * params["recovery_fraction"],
        "action_cost_um": params["action_cost"],
        "eligible_for_pilot": metrics["deployment_gate_passed"],
        "condition": (
            "Solo aplicable si un piloto demuestra ventas recuperadas; "
            "NOTA: no hay costos para estimar utilidad."
        ),
    }
    write_report(
        daily,
        sellers,
        monthly,
        weekday,
        predictions,
        forecast,
        metrics,
        result,
        params["output_dir"],
    )
    return json.loads(json.dumps(result, default=str))
