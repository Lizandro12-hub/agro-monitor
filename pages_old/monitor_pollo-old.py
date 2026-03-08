"""
pages_old/monitor_pollo-old.py — Monitor de Pollo (Sector Avícola)
Detalle de precios: SNIIM, Mercado San Juan, USDA, pollo vivo
"""
from dash import html, dcc
import dash

dash.register_page(__name__, path="/monitor-pollo", name="Monitor de Pollo")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.loader import (
    get_pollo_entero_sniim, get_pechuga_sanjuan, get_pierna_muslo_sanjuan,
    get_pollo_vivo, get_maiz_front, get_kpis,
    get_pollo_usda, get_pechuga_usda, get_muslo_usda,
)
from components.charts import (
    sparkline, line_chart, area_chart_dual,
    GOLD, GREEN, RED, PINK, GOLD2,
)

kpis    = get_kpis()
pollo   = get_pollo_entero_sniim()
pechuga = get_pechuga_sanjuan()
pierna  = get_pierna_muslo_sanjuan()
vivo    = get_pollo_vivo()
maiz    = get_maiz_front()
p_usda  = get_pollo_usda()
pe_usda = get_pechuga_usda()
mu_usda = get_muslo_usda()


def fmt(v, dec=2):
    if v is None: return "—"
    return f"{v:,.{dec}f}"

def chg_arrow(c):
    if c is None: return ""
    return f"▲ +{c:.1f}%" if c >= 0 else f"▼ {c:.1f}%"

def chg_class(c):
    return "kpi-change-pos" if (c or 0) >= 0 else "kpi-change-neg"


def layout():
    # Gráfica principal: evolución precios pollo MX
    fig_precios_mx = line_chart([
        {"df": pollo,   "x": "Fecha", "y": "precio_semana", "name": "Pollo Entero SNIIM", "color": GOLD},
        {"df": pechuga, "x": "Fecha", "y": "precio_semana", "name": "Pechuga (San Juan)",  "color": PINK},
        {"df": pierna,  "x": "Fecha", "y": "precio_semana", "name": "Pierna-Muslo",         "color": GREEN},
    ], title="Precios Pollo México (MXN/kg) — Últimas semanas", height=250, n_semanas=52)

    # Gráfica: pollo vivo
    fig_vivo = line_chart([
        {"df": vivo.dropna(subset=["granja"]),  "x": "Fecha", "y": "granja",    "name": "Vivo en Granja",  "color": GOLD},
        {"df": vivo.dropna(subset=["anden"]),   "x": "Fecha", "y": "anden",     "name": "Vivo en Andén",   "color": GOLD2},
        {"df": vivo.dropna(subset=["rosticero"]), "x": "Fecha", "y": "rosticero", "name": "Rosticero UNA", "color": PINK},
    ], title="Pollo Vivo y Rosticero — UNA (MXN/kg)", height=220, n_semanas=52)

    # Gráfica: USDA precios EE.UU.
    fig_usda = line_chart([
        {"df": p_usda,  "x": "report_date", "y": "wtd_avg_price", "name": "Pollo Entero WOG",  "color": GOLD},
        {"df": pe_usda, "x": "report_date", "y": "wtd_avg_price", "name": "Pechuga B/S",        "color": PINK},
        {"df": mu_usda, "x": "report_date", "y": "wtd_avg_price", "name": "Leg Quarters",       "color": GREEN},
    ], title="Precios USDA EE.UU. (Cents/Lb)", height=220, n_semanas=52)

    # Gráfica: precio pollo vs costo alimento (maíz)
    fig_vs = area_chart_dual(
        pollo, maiz,
        "Fecha", "precio_semana", "Precio Pollo SNIIM (MXN/kg)",
        "Date",  "Close",         "Maíz CME front (USD/bu)",
        title="Evolución semanal: Precio del Pollo vs Costo del Alimento",
        height=220, n=40,
    )

    return html.Div([
        html.Div([
            dcc.Link("← Dashboard", href="/", style={"color": "#E8820C", "fontSize": "13px"}),
        ], style={"marginBottom": "10px"}),

        html.Div("Monitor de Pollo", className="page-title"),
        html.Div("Sector Avícola — Precios de mercado México y EE.UU.", className="page-subtitle"),

        # ── Fila KPIs ─────────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Pollo Entero SNIIM", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["pollo"]["valor"]), className="kpi-value"),
                    html.Span(" MXN/kg", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["pollo"]["cambio"]), className=chg_class(kpis["pollo"]["cambio"])),
                dcc.Graph(figure=sparkline(pollo, "Fecha", "precio_semana"), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Pechuga (Mdo. San Juan)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["pechuga"]["valor"]), className="kpi-value"),
                    html.Span(" MXN/kg", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["pechuga"]["cambio"]), className=chg_class(kpis["pechuga"]["cambio"])),
                dcc.Graph(figure=sparkline(pechuga, "Fecha", "precio_semana", color=PINK), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Pierna-Muslo (Mdo. San Juan)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["pierna"]["valor"]), className="kpi-value"),
                    html.Span(" MXN/kg", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["pierna"]["cambio"]), className=chg_class(kpis["pierna"]["cambio"])),
                dcc.Graph(figure=sparkline(pierna, "Fecha", "precio_semana", color=GREEN), config={"displayModeBar": False}),
            ], className="kpi-card"),

            html.Div([
                html.Div("Pollo Entero USDA (último)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(p_usda["wtd_avg_price"].iloc[-1] if len(p_usda) else None), className="kpi-value"),
                    html.Span(" cts/lb", className="kpi-unit"),
                ]),
                dcc.Graph(
                    figure=sparkline(p_usda, "report_date", "wtd_avg_price", color=GOLD2),
                    config={"displayModeBar": False}
                ),
            ], className="kpi-card"),

        ], style={"display": "grid", "gridTemplateColumns": "repeat(4,1fr)", "gap": "12px", "marginBottom": "16px"}),

        # ── Gráficas ──────────────────────────────────────────────────────
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_precios_mx, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 2"}),

            html.Div([
                dcc.Graph(figure=fig_vivo, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 2"}),

            html.Div([
                dcc.Graph(figure=fig_vs, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 3"}),

            html.Div([
                dcc.Graph(figure=fig_usda, config={"displayModeBar": False}),
            ], className="module-card", style={"gridColumn": "span 1"}),

        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4,1fr)",
            "gap": "14px",
            "paddingBottom": "60px",
        }),
    ])
