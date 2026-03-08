"""
pages_old/monitor_insumos_old.py — Monitor de Insumos (Sector Avícola)
Maíz, Soya, Pasta de Soya, Tipo de Cambio
"""
from dash import html, dcc
import dash

dash.register_page(__name__, path="/monitor-insumos", name="Monitor de Insumos")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.loader import (
    get_maiz_front, get_soya_front, get_pastasoya_front,
    get_tipo_cambio, get_kpis,
)
from components.charts import sparkline, line_chart, GOLD, GREEN, PINK, GOLD2

kpis   = get_kpis()
maiz   = get_maiz_front()
soya   = get_soya_front()
pasta  = get_pastasoya_front()
tc_df  = get_tipo_cambio()

def fmt(v, dec=2):
    if v is None: return "—"
    return f"{v:,.{dec}f}"

def chg_arrow(c):
    if c is None: return ""
    return f"▲ +{c:.1f}%" if c >= 0 else f"▼ {c:.1f}%"

def chg_class(c):
    return "kpi-change-pos" if (c or 0) >= 0 else "kpi-change-neg"


def layout():
    fig_granos = line_chart([
        {"df": maiz,  "x": "Date", "y": "Close", "name": "Maíz Amarillo (USD/bu)",      "color": GOLD},
        {"df": soya,  "x": "Date", "y": "Close", "name": "Soya (USD/bu)",                "color": GREEN},
    ], title="Futuros Granos CME (Últimas 52 semanas)", height=260, n_semanas=365)

    fig_pasta = line_chart([
        {"df": pasta, "x": "Date", "y": "Close", "name": "Pasta de Soya front (USD/t)", "color": PINK},
    ], title="Pasta de Soya CME (USD/t)", height=220, n_semanas=365)

    fig_tc = line_chart([
        {"df": tc_df, "x": "Fecha", "y": "TC", "name": "USD/MXN (Banxico)", "color": GOLD2},
    ], title="Tipo de Cambio USD/MXN — Banxico", height=220, n_semanas=365)

    return html.Div([
        html.Div([
            dcc.Link("← Dashboard", href="/", style={"color": "#E8820C", "fontSize": "13px"}),
        ], style={"marginBottom": "10px"}),

        html.Div("Monitor de Insumos", className="page-title"),
        html.Div("Sector Avícola — Granos, insumos y tipo de cambio", className="page-subtitle"),

        # KPIs
        html.Div([
            html.Div([
                html.Div("Maíz Amarillo CME (front)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["maiz"]["valor"]), className="kpi-value"),
                    html.Span(" USD/bu", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["maiz"]["cambio"]), className=chg_class(kpis["maiz"]["cambio"])),
                dcc.Graph(figure=sparkline(maiz, "Date", "Close"), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Soya CME (front)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["soya"]["valor"]), className="kpi-value"),
                    html.Span(" USD/bu", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["soya"]["cambio"]), className=chg_class(kpis["soya"]["cambio"])),
                dcc.Graph(figure=sparkline(soya, "Date", "Close", color=GREEN), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Pasta de Soya (front)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(pasta["Close"].iloc[-1] if len(pasta) else None), className="kpi-value"),
                    html.Span(" USD/t", className="kpi-unit"),
                ]),
                dcc.Graph(figure=sparkline(pasta, "Date", "Close", color=PINK), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Tipo de Cambio (Banxico)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["tc"]["valor"]), className="kpi-value"),
                    html.Span(" USD/MXN", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["tc"]["cambio"]), className=chg_class(kpis["tc"]["cambio"])),
                dcc.Graph(figure=sparkline(tc_df, "Fecha", "TC", color=GOLD2), config={"displayModeBar": False}),
            ], className="kpi-card"),

        ], style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "12px", "marginBottom": "16px"}),

        # Gráficas
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_granos, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 4"}),

            html.Div([
                dcc.Graph(figure=fig_pasta, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 2"}),

            html.Div([
                dcc.Graph(figure=fig_tc, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 2"}),

        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4,1fr)",
            "gap": "14px",
            "paddingBottom": "60px",
        }),
    ])
