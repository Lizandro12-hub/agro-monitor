"""
pages_old/dashboard_old.py — Dashboard principal del Agro Monitor UDLAP
Pantalla de inicio con módulos clickeables al estilo Infosel
"""
from dash import html, dcc, callback, Output, Input
import dash
import plotly.graph_objects as go

# Registro de página
dash.register_page(__name__, path="/", name="Dashboard")

# ─── Imports internos ────────────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.loader import (
    get_kpis, get_tipo_cambio, get_maiz_front, get_soya_front,
    get_pollo_entero_sniim, get_pechuga_sanjuan, get_pierna_muslo_sanjuan,
    get_huevo_una,
)
from components.charts import sparkline, line_chart, area_chart_dual, GOLD, GREEN, RED, PINK

# ─── Datos (cargados una vez al iniciar) ─────────────────────────────────────
kpis   = get_kpis()
tc_df  = get_tipo_cambio()
maiz   = get_maiz_front()
soya   = get_soya_front()
pollo  = get_pollo_entero_sniim()
pechuga = get_pechuga_sanjuan()
pierna  = get_pierna_muslo_sanjuan()
huevo   = get_huevo_una()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def fmt(v, dec=2):
    if v is None: return "—"
    return f"{v:,.{dec}f}"

def chg_class(c):
    if c is None: return "kpi-change-pos"
    return "kpi-change-pos" if c >= 0 else "kpi-change-neg"

def chg_arrow(c):
    if c is None: return ""
    return f"▲ +{c:.1f}%" if c >= 0 else f"▼ {c:.1f}%"

def mini_graph(fig):
    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        className="kpi-chart",
    )

# ─── Noticias del mercado (estáticas de ejemplo — luego puedes conectar API) ─
NOTICIAS = [
    {"icono": "▲", "clase": "arrow-up",
     "titulo": "USDA recorta inventarios de maíz y soya",
     "texto": "El USDA redujo sus estimaciones de inventarios finales elevando los precios de insumos. Se espera un recorte adicional en el próximo reporte mensual."},
    {"icono": "🌾", "clase": "arrow-neu",
     "titulo": "Clima seco disminuye cosecha en el Midwest, USA",
     "texto": "Una ola de calor y sequía afecta la región del Midwest, reduciendo la producción de maíz un 3.1% menos de lo estimado."},
    {"icono": "▼", "clase": "arrow-down",
     "titulo": "Peso mexicano enfrenta presiones por debilidades en PMI",
     "texto": "El índice PMI manufacturero de México cayó a 49.2, generando preocupaciones sobre la economía y depreciando el peso."},
]

# ─── Tabla resumen ejecutivo ──────────────────────────────────────────────────
def tabla_resumen():
    filas = [
        ("Maíz",    fmt(kpis["maiz"]["valor"]),   kpis["maiz"]["unidad"],   kpis["maiz"]["cambio"],   "Costo Alimento ↑"),
        ("Pollo",   fmt(kpis["pollo"]["valor"]),   kpis["pollo"]["unidad"],  kpis["pollo"]["cambio"],  "Ingresos ↑"),
        ("TC",      fmt(kpis["tc"]["valor"]),      kpis["tc"]["unidad"],     kpis["tc"]["cambio"],     "Insumos Importados ↑"),
    ]
    rows = [
        html.Tr([
            html.Th("Variable"), html.Th("Nivel"), html.Th("Cambio"), html.Th("Impacto en Avícola"),
        ])
    ]
    for nombre, nivel, unidad, cambio, impacto in filas:
        chg_cls = "pos" if (cambio or 0) >= 0 else "neg"
        rows.append(html.Tr([
            html.Td(nombre),
            html.Td([html.Span(nivel, className="val"), html.Span(f" {unidad}", style={"fontSize": "10px", "color": "#7a7060"})]),
            html.Td(chg_arrow(cambio), className=chg_cls),
            html.Td(impacto, className="impact"),
        ]))
    return html.Table(rows, className="exec-table")


# ─── Layout ──────────────────────────────────────────────────────────────────
def layout():
    sp_tc    = sparkline(tc_df,  "Fecha", "TC",           color=GOLD)
    sp_maiz  = sparkline(maiz,   "Date",  "Close",        color="#F5C842")
    sp_soya  = sparkline(soya,   "Date",  "Close",        color=GREEN)
    sp_pollo = sparkline(pollo,  "Fecha", "precio_semana", color=GOLD)
    sp_pechuga = sparkline(pechuga, "Fecha", "precio_semana", color=PINK)
    sp_pierna  = sparkline(pierna,  "Fecha", "precio_semana", color="#80C080")
    sp_huevo   = sparkline(huevo,   "Fecha", "precio_semana", color="#C8A040")

    fig_pollo_vs_maiz = area_chart_dual(
        pollo, maiz,
        "Fecha", "precio_semana", "Precio Pollo (MXN/kg)",
        "Date",  "Close",         "Maíz CME (USD/bu)",
        height=180, n=20,
    )

    return html.Div([

        # ── Fila 1: KPIs Macro ─────────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Tipo de Cambio", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["tc"]["valor"]), className="kpi-value"),
                    html.Span("USD/MXN", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["tc"]["cambio"]), className=chg_class(kpis["tc"]["cambio"])),
                mini_graph(sp_tc),
            ], className="kpi-card"),
        ], style={"gridColumn": "span 1"}),

        html.Div([
            html.Div([
                html.Div("Maíz CME (front)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["maiz"]["valor"]), className="kpi-value"),
                    html.Span("USD/bu", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["maiz"]["cambio"]), className=chg_class(kpis["maiz"]["cambio"])),
                mini_graph(sp_maiz),
            ], className="kpi-card"),
        ], style={"gridColumn": "span 1"}),

        html.Div([
            html.Div([
                html.Div("Soya CME (front)", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["soya"]["valor"]), className="kpi-value"),
                    html.Span("USD/bu", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["soya"]["cambio"]), className=chg_class(kpis["soya"]["cambio"])),
                mini_graph(sp_soya),
            ], className="kpi-card"),
        ], style={"gridColumn": "span 1"}),

        html.Div([
            html.Div([
                html.Div("Huevo Blanco UNA", className="kpi-label"),
                html.Div([
                    html.Span(fmt(kpis["huevo"]["valor"]), className="kpi-value"),
                    html.Span("MXN/kg", className="kpi-unit"),
                ]),
                html.Div(chg_arrow(kpis["huevo"]["cambio"]), className=chg_class(kpis["huevo"]["cambio"])),
                mini_graph(sp_huevo),
            ], className="kpi-card"),
        ], style={"gridColumn": "span 1"}),

        # ── Fila 2: Módulo Pollo + Módulo Insumos ─────────────────────────
        html.Div([
            dcc.Link(
                html.Div([
                    html.Div([
                        html.Span("Monitor de Pollo"),
                        html.Span("Ver detalle →", style={"fontSize": "11px", "color": GOLD}),
                    ], className="module-title"),

                    # Sub-KPIs pollo
                    html.Div([
                        html.Div([
                            html.Div("Pollo Entero SNIIM", className="kpi-label"),
                            html.Div([
                                html.Span(fmt(kpis["pollo"]["valor"]), style={"fontSize": "18px", "fontWeight": "700", "color": "#F0E8D0"}),
                                html.Span(" MXN/kg", className="kpi-unit"),
                            ]),
                            html.Div(chg_arrow(kpis["pollo"]["cambio"]), className=chg_class(kpis["pollo"]["cambio"])),
                            mini_graph(sp_pollo),
                        ], style={"flex": "1"}),
                        html.Div([
                            html.Div("Pechuga (Mdo. SJuan)", className="kpi-label"),
                            html.Div([
                                html.Span(fmt(kpis["pechuga"]["valor"]), style={"fontSize": "18px", "fontWeight": "700", "color": "#F0E8D0"}),
                                html.Span(" MXN/kg", className="kpi-unit"),
                            ]),
                            html.Div(chg_arrow(kpis["pechuga"]["cambio"]), className=chg_class(kpis["pechuga"]["cambio"])),
                            mini_graph(sp_pechuga),
                        ], style={"flex": "1"}),
                        html.Div([
                            html.Div("Pierna-Muslo (SJuan)", className="kpi-label"),
                            html.Div([
                                html.Span(fmt(kpis["pierna"]["valor"]), style={"fontSize": "18px", "fontWeight": "700", "color": "#F0E8D0"}),
                                html.Span(" MXN/kg", className="kpi-unit"),
                            ]),
                            html.Div(chg_arrow(kpis["pierna"]["cambio"]), className=chg_class(kpis["pierna"]["cambio"])),
                            mini_graph(sp_pierna),
                        ], style={"flex": "1"}),
                    ], style={"display": "flex", "gap": "12px"}),

                ], className="module-card"),
                href="/monitor-pollo",
            )
        ], style={"gridColumn": "span 2"}),

        html.Div([
            dcc.Link(
                html.Div([
                    html.Div([
                        html.Span("Monitor de Insumos"),
                        html.Span("Ver detalle →", style={"fontSize": "11px", "color": GOLD}),
                    ], className="module-title"),

                    html.Div([
                        html.Div([
                            html.Div("Maíz Amarillo (CME)", className="kpi-label"),
                            html.Div([
                                html.Span(fmt(kpis["maiz"]["valor"]), style={"fontSize": "20px", "fontWeight": "700", "color": "#F0E8D0"}),
                                html.Span(" USD/bu", className="kpi-unit"),
                            ]),
                            html.Div(chg_arrow(kpis["maiz"]["cambio"]), className=chg_class(kpis["maiz"]["cambio"])),
                            mini_graph(sp_maiz),
                        ], style={"flex": "1"}),
                        html.Div([
                            html.Div("Soya CME", className="kpi-label"),
                            html.Div([
                                html.Span(fmt(kpis["soya"]["valor"]), style={"fontSize": "20px", "fontWeight": "700", "color": "#F0E8D0"}),
                                html.Span(" USD/bu", className="kpi-unit"),
                            ]),
                            html.Div(chg_arrow(kpis["soya"]["cambio"]), className=chg_class(kpis["soya"]["cambio"])),
                            mini_graph(sp_soya),
                        ], style={"flex": "1"}),
                    ], style={"display": "flex", "gap": "12px"}),

                ], className="module-card"),
                href="/monitor-insumos",
            )
        ], style={"gridColumn": "span 2"}),

        # ── Fila 3: Gráfica evolución + Resumen Ejecutivo + Noticias ──────
        html.Div([
            html.Div([
                html.Div("Evolución semanal: Precio del Pollo vs Maíz CME", className="module-title"),
                dcc.Graph(
                    figure=fig_pollo_vs_maiz,
                    config={"displayModeBar": False},
                ),
            ], className="module-card"),
        ], style={"gridColumn": "span 2"}),

        html.Div([
            dcc.Link(
                html.Div([
                    html.Div([
                        html.Span("Resumen Ejecutivo"),
                        html.Span("Ver detalle →", style={"fontSize": "11px", "color": GOLD}),
                    ], className="module-title"),
                    tabla_resumen(),
                    html.Div([
                        html.Span("Riesgo Actual Sector Avícola: ", style={"fontSize": "12px", "color": "#7a7060"}),
                        html.Span("Moderado", className="riesgo-badge riesgo-moderado"),
                    ], style={"marginTop": "12px", "textAlign": "right"}),
                ], className="module-card"),
                href="/resumen-ejecutivo",
            ),
        ], style={"gridColumn": "span 1"}),

        html.Div([
            dcc.Link(
                html.Div([
                    html.Div([
                        html.Span("¿Qué está moviendo el mercado?"),
                        html.Span("Ver todo →", style={"fontSize": "11px", "color": GOLD}),
                    ], className="module-title"),
                    html.Div([
                        html.Div([
                            html.Div([
                                html.Span(n["icono"] + " ", className=n["clase"]),
                                html.Span(n["titulo"]),
                            ], className="noticia-titulo"),
                            html.Div(n["texto"], className="noticia-texto"),
                        ], className="noticia-item")
                        for n in NOTICIAS
                    ]),
                ], className="module-card"),
                href="/mercado",
            ),
        ], style={"gridColumn": "span 1"}),

    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(4, 1fr)",
        "gap": "14px",
        "paddingBottom": "60px",
    })
