"""Registro de pipelines CRISP-DM."""

from kedro.pipeline import Pipeline, node

from ventas import nodes


def register_pipelines() -> dict[str, Pipeline]:
    """Separar descubrimiento, preparación, modelado y comunicación."""
    discovery = Pipeline([node(nodes.discover, "params:sales", "inventory", name="inventariar")])
    preparation = Pipeline(
        [
            node(
                nodes.prepare,
                ["inventory", "params:sales"],
                ["daily", "seller_daily", "quality"],
                name="validar_y_agregar",
            ),
            node(
                nodes.describe,
                ["daily", "seller_daily", "params:sales"],
                ["seller_summary", "monthly", "weekday"],
                name="analizar_desempeno",
            ),
        ]
    )
    modeling = Pipeline(
        [
            node(
                nodes.train,
                ["daily", "params:sales"],
                ["model", "model_metrics", "predictions", "trials", "forecast"],
                name="optimizar_y_evaluar",
            ),
        ]
    )
    reporting = Pipeline(
        [
            node(
                nodes.report,
                [
                    "daily",
                    "seller_summary",
                    "monthly",
                    "weekday",
                    "model_metrics",
                    "predictions",
                    "forecast",
                    "quality",
                    "params:sales",
                ],
                "business_summary",
                name="comunicar_resultados",
            ),
        ]
    )
    return {
        "__default__": discovery + preparation + modeling + reporting,
        "discovery": discovery,
        "preparation": preparation,
        "modeling": modeling,
        "reporting": reporting,
    }
