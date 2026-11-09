"""Comunicación de resultados para gerencia comercial."""

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


def _text_page(title, paragraphs):
    figure = plt.figure(figsize=(8.27, 11.69), facecolor="white")
    figure.text(0.08, 0.94, title, fontsize=19, weight="bold", color="#143b55")
    y = 0.88
    for heading, body in paragraphs:
        figure.text(0.08, y, heading, fontsize=12, weight="bold")
        wrapped = "\n".join(textwrap.fill(line, 95) for line in body.splitlines())
        figure.text(0.08, y - 0.025, wrapped, fontsize=10, va="top", linespacing=1.5)
        y -= 0.065 + 0.019 * len(wrapped.splitlines())
    return figure


def write_report(daily, sellers, monthly, weekday, predictions, forecast, metrics, result, output_dir):
    """Exportar reporte breve, gráficos e infografía de una página."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "DejaVu Sans", "axes.titlesize": 12})
    quality = result["quality"]
    wape = metrics["holdout_selected"]["wape"]
    wape_text = f"{wape:.1%}" if wape is not None else "NOTA: WAPE indefinida por ingreso cero"
    status = "Cumple el umbral técnico" if metrics["deployment_gate_passed"] else "Requiere revisión antes de uso operativo"
    with PdfPages(output / "reporte.pdf") as pdf:
        page = _text_page("Desempeño de las ventas", [
            ("Introduction", "Reto 1 | Cynthia, Antonio y Juan Diego. Metodología CRISP-DM. "
             "Análisis comercial de la cadena de supermercados."),
            ("Business problem", "La gerencia comercial necesita planificar capacidad semanal y "
             "priorizar acompañamiento. Pregunta: ¿podemos anticipar siete días de ventas "
             "mejor que repetir la semana anterior y detectar diferencias de desempeño comercial?"),
            ("Data", f"{quality['rows']:,} líneas entre {quality['start']} y {quality['end']}. "
             f"{quality['observed_sellers']} vendedores observados. {quality['revenue_label']}. "
             "NOTA: moneda no documentada; se utilizan unidades monetarias (UM)."),
            ("Methods", "Carga por lotes, claves únicas, integridad referencial, validación de "
             "fechas, cantidades y descuentos. Se conservan extremos válidos. "
             "Análisis de contribución, ticket promedio, productividad y tendencia de 28 días."),
            ("Model selection", "HistGradientBoosting con búsqueda Optuna frente a línea base "
             "semanal. Validación expansiva de tres bloques; últimos 28 días reservados. "
             "Se exige al menos 5% de mejora relativa de WAPE para justificar complejidad. "
             f"Selección por validación: {metrics['selected_model']}. {status}."),
        ])
        pdf.savefig(page)
        plt.close(page)
        fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27), constrained_layout=True)
        axes[0, 0].plot(pd.to_datetime(daily.date), daily.revenue, alpha=0.35, label="Diario")
        axes[0, 0].plot(pd.to_datetime(daily.date), daily.revenue.rolling(7).mean(), label="Media 7 días")
        axes[0, 0].set_title("Tendencia de ventas (UM)")
        axes[0, 0].legend()
        top = sellers.head(10).sort_values("contribution")
        axes[0, 1].barh(top.seller.astype(str), top.contribution * 100, color="#168a8a")
        axes[0, 1].set_title("Contribución de vendedores (%)")
        axes[0, 1].set_xlabel("Participación en ingreso; no mide habilidad causal")
        axes[1, 0].bar(weekday.weekday, weekday.revenue_mean, color="#168a8a")
        axes[1, 0].set_xticks(range(7), ["L", "M", "X", "J", "V", "S", "D"])
        axes[1, 0].set_title("Venta promedio por día de semana (UM)")
        for column, label in [("actual", "Observado"), ("baseline", "Línea base"),
                              ("selected", "Seleccionado")]:
            axes[1, 1].plot(pd.to_datetime(predictions.date), predictions[column], label=label)
        axes[1, 1].set_title(f"Evaluación futura | WAPE {wape_text}")
        axes[1, 1].legend(fontsize=8)
        for axis in axes.flat:
            axis.tick_params(axis="x", labelrotation=25)
        fig.suptitle("Results | Tendencias, contribución y evaluación", fontsize=18)
        fig.savefig(output / "resultados.png", dpi=160)
        pdf.savefig(fig)
        plt.close(fig)
        page = _text_page("Decisiones comerciales", [
            ("Business interpretation", f"Venta total: {result['revenue']:,.2f} UM. "
             f"Tickets: {result['transactions']:,}. Ticket promedio: {result['ticket_value']:,.2f} UM. "
             f"Los tres vendedores de mayor contribución concentran {result['top3_seller_share']:.1%}. "
             "La concentración describe dependencia comercial; no prueba superioridad individual."),
            ("Recommendations", "Gerencia: revisar pronóstico semanal y contrastar capacidad disponible. "
             "Jefatura comercial: comparar carteras y turnos antes de diseñar acompañamiento. "
             "RR. HH.: evaluar atención, conocimiento de productos y venta complementaria mediante "
             "pruebas de trabajo. Validar el acompañamiento con un piloto y una métrica de negocio."),
            ("Limitations", "NOTA: faltan turnos, cuotas, costos, afluencia, stock y asignación de "
             "cartera. No se puede estimar rentabilidad, productividad por hora ni impacto causal. "
             "NOTA: cinco meses no permiten aprender estacionalidad anual. "
             "NOTA: no hay datos de candidatos ni desempeño posterior a su contratación; "
             "no se puede validar un perfil predictivo. Se excluyen género y edad del modelo. "
             "NOTA: los precios de catálogo no son precios históricos auditados."),
            ("Conclusion", f"{status}. El pronóstico es una herramienta de planificación; "
             "la evaluación individual requiere contexto operativo. La mejora comercial se "
             "medirá en un piloto mediante ventas recuperadas y costo de la intervención, "
             "sin confundir reducción del error con ingreso adicional."),
        ])
        pdf.savefig(page)
        plt.close(page)
    fig = plt.figure(figsize=(16, 9), facecolor="#f2f6fa")
    fig.text(0.04, 0.93, "DESEMPEÑO DE LAS VENTAS", fontsize=27, weight="bold", color="#143b55")
    fig.text(0.04, 0.88, "Cynthia · Antonio · Juan Diego | Gerencia comercial | CRISP-DM", fontsize=13)
    cards = [
        (0.04, 0.77, "DECISIÓN", "Planificar siete días de ventas y priorizar acompañamiento."),
        (0.36, 0.77, "EVIDENCIA", f"Ventas: {result['revenue']:,.0f} UM\nTickets: {result['transactions']:,}\nWAPE futuro: {wape_text}"),
        (0.69, 0.77, "MODELO", f"{metrics['selected_model']}\nOptuna + validación temporal\n{status}"),
        (0.04, 0.49, "ACCIONABLES", "Gerencia: planificación semanal.\nJefatura: revisar cartera y turnos.\nRR. HH.: pruebas de competencias."),
        (0.36, 0.49, "LÍMITES", "NOTA: faltan costos, turnos y cuotas.\nNOTA: no hay estacionalidad anual.\nNo se infiere causalidad ni perfil demográfico."),
        (0.69, 0.49, "VALIDACIÓN DE NEGOCIO", "Piloto de acompañamiento.\nMedir venta recuperada y costo.\nRevisar error y sesgo semanalmente."),
    ]
    for x, y, title, body in cards:
        fig.text(x, y, title, fontsize=15, weight="bold", color="#168a8a")
        wrapped = "\n".join(textwrap.fill(line, 43) for line in body.splitlines())
        fig.text(x, y - 0.05, wrapped, fontsize=12, va="top", linespacing=1.7)
    fig.text(0.04, 0.14, "CSV → validación y agregación → análisis → Optuna → evaluación temporal → reporte",
             fontsize=15, color="#143b55")
    fig.text(0.04, 0.07, f"{quality['revenue_label']} | NOTA: moneda no documentada (UM).", fontsize=11)
    fig.savefig(output / "presentacion.pdf", bbox_inches="tight")
    fig.savefig(output / "presentacion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
