"""Exportar reporte y diapositiva del estado real, sin resultados inventados."""

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from ventas.reporting import _text_page


def main():
    """Crear dos artefactos de avance a partir de la evidencia documentada."""
    output = Path("docs")
    source = (output / "reporte_parcial.md").read_text(encoding="utf-8")
    sections = []
    for section in source.split("\n## ")[1:]:
        title, body = section.split("\n", 1)
        sections.append((title, body.strip()))
    with PdfPages(output / "reporte_parcial.pdf") as pdf:
        for start in (0, 5):
            page = _text_page("Desempeño de ventas · Avance", sections[start : start + 5])
            pdf.savefig(page)
            plt.close(page)
    fig = plt.figure(figsize=(16, 9), facecolor="#f2f6fa")
    fig.text(0.04, 0.93, "DESEMPEÑO DE LAS VENTAS", fontsize=27, weight="bold", color="#143b55")
    fig.text(0.04, 0.88, "Cynthia · Antonio · Juan Diego | Avance parcial | CRISP-DM", fontsize=14)
    fig.text(
        0.04,
        0.82,
        "NOTA: faltan transacciones; no hay resultados reales de ventas.",
        color="#a33131",
        fontsize=16,
        weight="bold",
    )
    cards = [
        (
            0.04,
            0.72,
            "PREGUNTA DE NEGOCIO",
            "¿Podemos anticipar siete días de ventas y orientar "
            "el acompañamiento del equipo? Stakeholder: gerencia comercial.",
        ),
        (
            0.37,
            0.72,
            "MODELO Y EVALUACIÓN",
            "Línea base semanal vs. gradient boosting. Optuna, "
            "validación expansiva y holdout de 28 días. Meta: mejorar WAPE al menos 5%.",
        ),
        (
            0.70,
            0.72,
            "EVIDENCIA ACTUAL",
            "Seis tablas detectadas por columnas. Nombres de CSV "
            "cruzados. NOTA: falta la séptima tabla, que contiene las ventas.",
        ),
        (
            0.04,
            0.43,
            "DESEMPEÑO DEL PERSONAL",
            "Generación, contribución, ticket y tendencia de "
            "28 días. NOTA: faltan turnos y cartera para interpretar diferencias.",
        ),
        (
            0.37,
            0.43,
            "ACCIONABLES",
            "Completar y validar fuentes. Planificar semanalmente. "
            "Pilotear acompañamiento. RR. HH.: pruebas de competencias, sin perfil demográfico.",
        ),
        (
            0.70,
            0.43,
            "LÍMITES",
            "NOTA: faltan costos y márgenes para estimar retorno. "
            "NOTA: faltan candidatos y evaluación prospectiva para validar contratación.",
        ),
    ]
    for x, y, heading, body in cards:
        fig.text(x, y, heading, fontsize=14, weight="bold", color="#168a8a")
        fig.text(x, y - 0.045, textwrap.fill(body, 43), va="top", fontsize=12, linespacing=1.6)
    fig.text(
        0.04,
        0.13,
        "CSV → calidad → análisis → Optuna → evaluación temporal → reporte",
        fontsize=16,
        color="#143b55",
    )
    fig.text(
        0.04,
        0.065,
        "Kedro · GitHub Actions · Ruff · pruebas | "
        "NOTA: la validación sintética no constituye evidencia comercial.",
        fontsize=11,
    )
    fig.savefig(output / "presentacion_parcial.pdf", bbox_inches="tight")
    fig.savefig(output / "presentacion_parcial.png", dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
