"""Pruebas de errores que cambiarían conclusiones de negocio."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from tests.fixtures import make_fixture
from ventas.modeling import features, scores, train
from ventas.nodes import describe, discover, paths_from_inventory, prepare


@pytest.fixture
def context(tmp_path):
    params = yaml.safe_load(Path("conf/base/parameters.yml").read_text(encoding="utf-8"))["sales"]
    params.update(data_dir=str(tmp_path), chunksize=47, trials=2)
    tables = make_fixture(tmp_path)
    return tmp_path, params, tables


def test_missing_sales_is_explicit(context):
    root, params, _ = context
    (root / "sales.csv").unlink()
    with pytest.raises(ValueError, match="sales"):
        paths_from_inventory(discover(params))


def test_schema_not_filename_and_revenue_conservation(context):
    root, params, tables = context
    (root / "sales.csv").rename(root / "archivo.csv")
    daily, sellers, quality = prepare(discover(params), params)
    assert daily.revenue.sum() == pytest.approx(tables["sales"].TotalPrice.sum())
    assert daily.transactions.sum() == len(tables["sales"])
    assert sellers.revenue.sum() == pytest.approx(daily.revenue.sum())
    assert quality["rows"] == len(tables["sales"])
    summary, monthly, _ = describe(daily, sellers, params)
    assert summary.contribution.sum() == pytest.approx(1)
    assert monthly.complete_month.all()


@pytest.mark.parametrize("fault, message", [
    ("duplicate", "duplicado"), ("orphan", "Referencia"),
    ("discount", "Descuentos"), ("ticket", "múltiples"),
    ("missing_day", "días sin registros"), ("zero_recorded", "cero"),
])
def test_reject_invalid_business_data(context, fault, message):
    root, params, tables = context
    sales = tables["sales"].copy()
    if fault == "duplicate":
        sales.loc[len(sales) - 1, "SalesID"] = sales.loc[0, "SalesID"]
    elif fault == "orphan":
        sales.loc[0, "ProductID"] = 999
    elif fault == "discount":
        sales.loc[0, "Discount"] = 25
    elif fault == "ticket":
        sales.loc[len(sales) - 1, "TransactionNumber"] = sales.loc[0, "TransactionNumber"]
    elif fault == "missing_day":
        sales = sales[sales.SalesDate != sales.SalesDate.iloc[30]]
    elif fault == "zero_recorded":
        sales["TotalPrice"] = 0
        params["revenue_mode"] = "recorded"
    sales.to_csv(root / "sales.csv", index=False)
    with pytest.raises(ValueError, match=message):
        prepare(discover(params), params)


def test_ticket_split_across_chunks_is_counted_once(context):
    root, params, tables = context
    sales = tables["sales"]
    extra = sales.iloc[[0]].copy()
    extra["SalesID"] = sales.SalesID.max() + 1
    pd.concat([sales, extra]).to_csv(root / "sales.csv", index=False)
    daily, _, _ = prepare(discover(params), params)
    assert daily.transactions.sum() == len(sales)
    assert daily.revenue.sum() == pytest.approx(sales.TotalPrice.sum() + extra.TotalPrice.sum())


def test_features_cannot_observe_future():
    history = pd.Series(np.arange(50), index=pd.date_range("2018-01-01", periods=50))
    row = features(history, history.index[-1] + pd.Timedelta(days=7), 7)
    assert row["lag_week"] == history.iloc[-1]
    assert row["last"] == 49
    assert row["mean_7"] == history.iloc[-7:].mean()
    assert scores([0, 0], [1, 2])["wape"] is None


def test_temporal_model_and_artifact(context):
    _, params, _ = context
    daily, _, _ = prepare(discover(params), params)
    artifact, metrics, predictions, trials, forecast = train(daily, params)
    assert len(predictions) == 28
    assert (pd.to_datetime(predictions.origin) < pd.to_datetime(predictions.date)).all()
    assert len(forecast) == 7
    assert np.isfinite(forecast.prediction).all()
    assert (forecast.prediction >= 0).all()
    assert len(trials) == 2
    assert artifact["history"].index[-1] < forecast.date.min()
    assert metrics["holdout_start"] == "2018-05-04"
