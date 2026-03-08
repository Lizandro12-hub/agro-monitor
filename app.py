"""
app.py — Agro Monitor UDLAP
Home + módulos (Pollo / Insumos / Macro)
Estilo oscuro tipo terminal / Bloomberg
"""

import dash
from dash import html, dcc, Input, Output, State, callback, ctx
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.loader import (
    get_tipo_cambio,
    get_maiz_front,
    get_pastasoya_front,
    get_pollo_entero_sniim,
    get_pechuga_sanjuan,
    get_pierna_muslo_sanjuan,
    get_pollo_vivo,
    get_kpis,
)
from components.charts import sparkline, GOLD, GREEN, PINK, GOLD2, RED

# ──────────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Monitor Avícola UDLAP",
    update_title=None,
)
server = app.server

# ──────────────────────────────────────────────────────────────────────────────
# COLORES / TEMA
# ──────────────────────────────────────────────────────────────────────────────
BG = "#111111"
CARD = "#1a1a1a"
BORDER = "#2a2a2a"
GRID = "#1e1e1e"
TEXT = "#E8E1D3"
TEXT2 = "#CFC5B3"
TEXT3 = "#A69A86"
TEXT4 = "#7B705F"
ORANGE = "#E8820C"
ORANGE_SOFT = "#F0B35A"
WHITE = "#F4EBD8"
NEG = "#d9534f"
POS = "#5cb85c"

# ──────────────────────────────────────────────────────────────────────────────
# DATOS
# ──────────────────────────────────────────────────────────────────────────────
kpis = get_kpis()
tc_df = get_tipo_cambio()
maiz = get_maiz_front()
pasta = get_pastasoya_front()
pollo = get_pollo_entero_sniim()
pechuga = get_pechuga_sanjuan()
pierna = get_pierna_muslo_sanjuan()
vivo = get_pollo_vivo()

pasta_last = round(pasta["Close"].iloc[-1], 2) if len(pasta) else None
pasta_prev = pasta["Close"].iloc[-2] if len(pasta) > 1 else None
pasta_chg = round((pasta_last - pasta_prev) / pasta_prev * 100, 1) if pasta_prev else None

vivo_g = vivo.dropna(subset=["granja"])
vivo_a = vivo.dropna(subset=["anden"])
vivo_r = vivo.dropna(subset=["rosticero"])

vivo_granja_last = round(vivo_g["granja"].iloc[-1], 2) if len(vivo_g) > 0 else None
vivo_granja_prev = vivo_g["granja"].iloc[-2] if len(vivo_g) > 1 else None
vivo_granja_chg = round((vivo_granja_last - vivo_granja_prev) / vivo_granja_prev * 100, 1) if vivo_granja_prev else None

vivo_anden_last = round(vivo_a["anden"].iloc[-1], 2) if len(vivo_a) > 0 else None
vivo_anden_prev = vivo_a["anden"].iloc[-2] if len(vivo_a) > 1 else None
vivo_anden_chg = round((vivo_anden_last - vivo_anden_prev) / vivo_anden_prev * 100, 1) if vivo_anden_prev else None

rosticero_last = round(vivo_r["rosticero"].iloc[-1], 2) if len(vivo_r) > 0 else None
rosticero_prev = vivo_r["rosticero"].iloc[-2] if len(vivo_r) > 1 else None
rosticero_chg = round((rosticero_last - rosticero_prev) / rosticero_prev * 100, 1) if rosticero_prev else None

# ──────────────────────────────────────────────────────────────────────────────
# FUTUROS PLACEHOLDERS (hasta que metas loaders reales)
# ──────────────────────────────────────────────────────────────────────────────
DIESEL_LAST = None
DIESEL_CHG = None
FLETES_LAST = None
FLETES_CHG = None
TASA_LAST = None
TASA_CHG = None

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def fmt(v, dec=2):
    if v is None:
        return "—"
    return f"{v:,.{dec}f}"

def pct_arrow(c):
    if c is None:
        return html.Span("—", style={"color": TEXT4, "fontSize": "12px", "fontWeight": "700"})
    color = POS if c >= 0 else NEG
    sym = "▲" if c >= 0 else "▼"
    return html.Span(f"{sym} {abs(c):.1f}%", style={"color": color, "fontSize": "12px", "fontWeight": "800"})

def abs_change(curr, prev):
    if curr is None or prev is None:
        return None
    return curr - prev

def safe_last(df, col):
    if df is None or len(df) == 0 or col not in df.columns:
        return None
    s = df[col].dropna()
    return float(s.iloc[-1]) if len(s) else None

def safe_prev(df, col):
    if df is None or len(df) < 2 or col not in df.columns:
        return None
    s = df[col].dropna()
    return float(s.iloc[-2]) if len(s) > 1 else None

def spark(df, x, y, color=GOLD, height=48):
    if df is None or len(df) == 0 or x not in df.columns or y not in df.columns:
        return html.Div("Sin serie", style={"fontSize": "10px", "color": TEXT4, "paddingTop": "8px"})
    return dcc.Graph(
        figure=sparkline(df, x, y, color=color, height=height),
        config={"displayModeBar": False, "staticPlot": True},
        style={"height": f"{height}px"},
    )

def sec_label(txt):
    return html.Div(
        txt,
        style={
            "fontSize": "11px",
            "color": ORANGE,
            "fontWeight": "800",
            "letterSpacing": "1.4px",
            "marginBottom": "8px",
            "marginTop": "6px",
            "borderBottom": f"1px solid {BORDER}",
            "paddingBottom": "4px",
        },
    )

def navbar_button(label, btn_id):
    return html.Button(
        label,
        id=btn_id,
        n_clicks=0,
        style={
            "background": "transparent",
            "border": f"1px solid {BORDER}",
            "color": TEXT2,
            "fontSize": "12px",
            "fontWeight": "700",
            "padding": "7px 12px",
            "borderRadius": "6px",
            "cursor": "pointer",
            "marginLeft": "8px",
        },
    )

def home_module_card(title, subtitle, kpi_lines, btn_id):
    return html.Div(
        [
            html.Div(title, style={"fontSize": "22px", "fontWeight": "900", "color": WHITE, "marginBottom": "4px"}),
            html.Div(subtitle, style={"fontSize": "12px", "color": TEXT3, "marginBottom": "10px"}),
            html.Div(
                [html.Div(f"• {line}", style={"fontSize": "13px", "color": TEXT2, "marginBottom": "5px", "fontWeight": "700"}) for line in kpi_lines],
                style={"marginBottom": "14px"},
            ),
            html.Button(
                "Entrar →",
                id=btn_id,
                n_clicks=0,
                style={
                    "background": ORANGE,
                    "border": "none",
                    "color": "#111",
                    "fontWeight": "900",
                    "fontSize": "12px",
                    "padding": "8px 14px",
                    "borderRadius": "6px",
                    "cursor": "pointer",
                },
            ),
        ],
        style={
            "background": CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "16px",
            "minHeight": "175px",
            "boxShadow": "0 0 0 rgba(0,0,0,0)",
        },
    )

def executive_box(title, value, unit="", change=None, accent=ORANGE):
    return html.Div(
        [
            html.Div(title, style={"fontSize": "11px", "color": TEXT3, "fontWeight": "800", "letterSpacing": "1px", "textTransform": "uppercase"}),
            html.Div(
                [
                    html.Span(fmt(value), style={"fontSize": "28px", "fontWeight": "900", "color": accent}),
                    html.Span(f" {unit}", style={"fontSize": "13px", "color": TEXT3, "fontWeight": "700"}),
                ],
                style={"marginTop": "8px"},
            ),
            html.Div(pct_arrow(change), style={"marginTop": "6px"}),
        ],
        style={
            "background": CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "7px",
            "padding": "12px 14px",
            "height": "110px",
        },
    )

def noticia_card(n):
    return html.A(
        [
            html.Div(
                [
                    html.Span(n["icono"] + " ", style={"color": n["color"], "fontWeight": "800"}),
                    html.Span(
                        n["titulo"],
                        style={
                            "fontSize": "13px",
                            "fontWeight": "800",
                            "color": WHITE,
                            "lineHeight": "1.35",
                        },
                    ),
                ],
                style={"marginBottom": "4px"},
            ),
            html.Div(
                n["resumen"],
                style={"fontSize": "12px", "color": TEXT3, "lineHeight": "1.45", "marginBottom": "4px"},
            ),
            html.Div(
                [
                    html.Span(n["fuente"], style={"color": ORANGE, "fontSize": "11px", "fontWeight": "800"}),
                    html.Span(f" · {n['fecha']}", style={"color": TEXT4, "fontSize": "11px"}),
                    html.Span(" → Leer nota", style={"color": ORANGE, "fontSize": "11px", "marginLeft": "6px", "fontWeight": "700"}),
                ]
            ),
        ],
        href=n["url"],
        target="_blank",
        style={
            "display": "block",
            "padding": "10px 0",
            "borderBottom": "1px solid #222",
            "textDecoration": "none",
        },
    )

def clickable_price_card(label, valor, unidad, cambio, spark_component, color=GOLD, fuente="", card_id=None):
    body = html.Div(
        [
            html.Div(
                label,
                style={
                    "fontSize": "11px",
                    "color": TEXT3,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.8px",
                    "marginBottom": "3px",
                    "fontWeight": "800",
                },
            ),
            html.Div(
                [
                    html.Span(fmt(valor), style={"fontSize": "22px", "fontWeight": "900", "color": color}),
                    html.Span(f" {unidad}", style={"fontSize": "11px", "color": TEXT3, "fontWeight": "700"}),
                ]
            ),
            html.Div(pct_arrow(cambio), style={"marginBottom": "4px"}),
            spark_component,
            html.Div(fuente, style={"fontSize": "10px", "color": TEXT4, "marginTop": "4px", "fontWeight": "700"}),
        ],
        style={
            "background": CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "5px",
            "padding": "10px 12px",
        },
    )

    if card_id is None:
        return body

    return html.Button(
        body,
        id=card_id,
        n_clicks=0,
        style={
            "background": "transparent",
            "border": "none",
            "padding": "0",
            "margin": "0",
            "width": "100%",
            "textAlign": "left",
            "cursor": "pointer",
        },
    )

def detail_stat_box(title, main_value, subtext):
    return html.Div(
        [
            html.Div(title, style={"fontSize": "11px", "color": TEXT3, "fontWeight": "800", "letterSpacing": "1px", "textTransform": "uppercase"}),
            html.Div(main_value, style={"fontSize": "24px", "fontWeight": "900", "color": WHITE, "marginTop": "6px"}),
            html.Div(subtext, style={"fontSize": "11px", "color": TEXT4, "marginTop": "4px", "fontWeight": "700"}),
        ],
        style={
            "background": CARD,
            "border": f"1px solid {BORDER}",
            "borderRadius": "7px",
            "padding": "12px 14px",
            "height": "92px",
        },
    )

def blank_figure(msg="Serie pendiente"):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        annotations=[
            dict(
                text=msg,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16, color=TEXT3),
            )
        ],
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# NOTICIAS
# ──────────────────────────────────────────────────────────────────────────────
NOTICIAS = [
    {
        "titulo": "USDA recorta inventarios finales de maíz y soya para 2024/25",
        "resumen": "Las estimaciones de existencias finales cayeron más de lo esperado, presionando al alza los precios de insumos avícolas.",
        "fuente": "USDA WASDE",
        "fecha": "Mar 2026",
        "color": POS,
        "icono": "▲",
        "url": "https://www.usda.gov",
        "tags": ["insumos", "maiz", "soya", "macro"],
    },
    {
        "titulo": "Peso mexicano opera cerca de 17.50 por dólar ante datos de empleo en EE.UU.",
        "resumen": "La fortaleza del dólar presiona el costo de insumos importados como maíz y soya para el sector avícola.",
        "fuente": "Banxico",
        "fecha": "Mar 2026",
        "color": NEG,
        "icono": "▼",
        "url": "https://www.banxico.org.mx",
        "tags": ["macro", "tc", "insumos"],
    },
    {
        "titulo": "UNA reporta estabilidad en precios del pollo vivo durante primera quincena",
        "resumen": "Los precios en granja se mantienen dentro del rango esperado. La demanda interna sigue firme.",
        "fuente": "UNA México",
        "fecha": "Mar 2026",
        "color": ORANGE,
        "icono": "●",
        "url": "https://una.org.mx",
        "tags": ["pollo", "vivo"],
    },
    {
        "titulo": "Brasil aumenta exportaciones de pollo a Asia; presión sobre precios globales",
        "resumen": "El incremento en exportaciones brasileñas podría afectar los precios internacionales de referencia.",
        "fuente": "Reuters",
        "fecha": "Feb 2026",
        "color": NEG,
        "icono": "▼",
        "url": "https://reuters.com",
        "tags": ["pollo"],
    },
    {
        "titulo": "Clima seco en Midwest EE.UU. amenaza siembra de maíz para ciclo 2025",
        "resumen": "Condiciones de sequía en regiones productoras podrían reducir la oferta y elevar costos de alimento.",
        "fuente": "CME Group",
        "fecha": "Feb 2026",
        "color": POS,
        "icono": "▲",
        "url": "https://cmegroup.com",
        "tags": ["insumos", "maiz", "macro"],
    },
]

def noticias_por_modulo(modulo):
    if modulo == "pollo":
        wanted = {"pollo", "vivo"}
    elif modulo == "insumos":
        wanted = {"insumos", "maiz", "soya"}
    elif modulo == "macro":
        wanted = {"macro", "tc"}
    else:
        return NOTICIAS

    filtered = [n for n in NOTICIAS if wanted.intersection(set(n.get("tags", [])))]
    return filtered if filtered else NOTICIAS

# ──────────────────────────────────────────────────────────────────────────────
# SERIES / META
# ──────────────────────────────────────────────────────────────────────────────
VAR_META = {
    "pollo": {
        "df": pollo,
        "x": "Fecha",
        "y": "precio_semana",
        "name": "Pollo Entero SNIIM",
        "unidad": "MXN/kg",
        "color": GOLD,
        "fuente": "SNIIM / SADER",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "pechuga": {
        "df": pechuga,
        "x": "Fecha",
        "y": "precio_semana",
        "name": "Pechuga (San Juan)",
        "unidad": "MXN/kg",
        "color": PINK,
        "fuente": "Mercado San Juan",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "pierna": {
        "df": pierna,
        "x": "Fecha",
        "y": "precio_semana",
        "name": "Pierna-Muslo (San Juan)",
        "unidad": "MXN/kg",
        "color": GREEN,
        "fuente": "Mercado San Juan",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "vivo_granja": {
        "df": vivo_g,
        "x": "Fecha",
        "y": "granja",
        "name": "Vivo en Granja",
        "unidad": "MXN/kg",
        "color": GOLD,
        "fuente": "UNA México",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "vivo_anden": {
        "df": vivo_a,
        "x": "Fecha",
        "y": "anden",
        "name": "Vivo en Andén",
        "unidad": "MXN/kg",
        "color": GOLD,
        "fuente": "UNA México",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "rosticero": {
        "df": vivo_r,
        "x": "Fecha",
        "y": "rosticero",
        "name": "Rosticero UNA",
        "unidad": "MXN/kg",
        "color": "#C8A040",
        "fuente": "UNA México",
        "modulo": "pollo",
        "compare": "maiz",
    },
    "maiz": {
        "df": maiz,
        "x": "Date",
        "y": "Close",
        "name": "Maíz Amarillo CME (front)",
        "unidad": "USD/bu",
        "color": "#F5C842",
        "fuente": "CME Group",
        "modulo": "insumos",
        "compare": "tc",
    },
    "pasta": {
        "df": pasta,
        "x": "Date",
        "y": "Close",
        "name": "Pasta de Soya CME (front)",
        "unidad": "USD/t",
        "color": PINK,
        "fuente": "CME Group",
        "modulo": "insumos",
        "compare": "maiz",
    },
    "tc": {
        "df": tc_df,
        "x": "Fecha",
        "y": "TC",
        "name": "Tipo de Cambio USD/MXN",
        "unidad": "USD/MXN",
        "color": GOLD2,
        "fuente": "Banxico",
        "modulo": "macro",
        "compare": "maiz",
    },
    # placeholders futuros
    "diesel": {
        "df": None,
        "x": None,
        "y": None,
        "name": "Precio Diésel",
        "unidad": "MXN/L",
        "color": ORANGE_SOFT,
        "fuente": "Pendiente",
        "modulo": "macro",
        "compare": None,
    },
    "fletes": {
        "df": None,
        "x": None,
        "y": None,
        "name": "Índice de Fletes",
        "unidad": "Índice",
        "color": ORANGE_SOFT,
        "fuente": "Pendiente",
        "modulo": "macro",
        "compare": None,
    },
    "tasa": {
        "df": None,
        "x": None,
        "y": None,
        "name": "Tasa de Interés",
        "unidad": "%",
        "color": ORANGE_SOFT,
        "fuente": "Pendiente",
        "modulo": "macro",
        "compare": None,
    },
}

HOME_SUMMARY_ROWS = [
    {"variable": "Tipo de Cambio", "nivel": fmt(kpis["tc"]["valor"]), "unidad": "USD/MXN", "cambio": kpis["tc"]["cambio"], "impacto": "Insumos importados"},
    {"variable": "Maíz", "nivel": fmt(kpis["maiz"]["valor"]), "unidad": "USD/bu", "cambio": kpis["maiz"]["cambio"], "impacto": "Costo alimento"},
    {"variable": "Pasta de soya", "nivel": fmt(pasta_last), "unidad": "USD/t", "cambio": pasta_chg, "impacto": "Costo alimento"},
    {"variable": "Pollo entero", "nivel": fmt(kpis["pollo"]["valor"]), "unidad": "MXN/kg", "cambio": kpis["pollo"]["cambio"], "impacto": "Ingreso principal"},
    {"variable": "Vivo en granja", "nivel": fmt(vivo_granja_last), "unidad": "MXN/kg", "cambio": vivo_granja_chg, "impacto": "Mercado base"},
]

def get_var_stats(var_key):
    meta = VAR_META[var_key]
    df = meta["df"]
    y = meta["y"]
    if df is None or y is None:
        return None, None, None, None, None, None
    s = df[y].dropna()
    if len(s) == 0:
        return None, None, None, None, None, None
    last = float(s.iloc[-1])
    prev = float(s.iloc[-2]) if len(s) > 1 else None
    chg = abs_change(last, prev) if prev is not None else None
    pct = round((last - prev) / prev * 100, 1) if prev not in [None, 0] else None
    mn = round(float(s.min()), 2)
    mx = round(float(s.max()), 2)
    return last, prev, chg, pct, mn, mx

def trim_df_for_period(var_key, n_period):
    meta = VAR_META[var_key]
    df = meta["df"]
    if df is None:
        return None
    if n_period == 999:
        return df
    if var_key in ["maiz", "pasta", "tc"]:
        return df.tail(n_period * 7)
    return df.tail(n_period)

def make_main_figure(var_key, n_period):
    meta = VAR_META[var_key]
    df = trim_df_for_period(var_key, n_period)
    if df is None or len(df) == 0:
        return blank_figure("Serie pendiente")

    x = meta["x"]
    y = meta["y"]
    name = meta["name"]
    unidad = meta["unidad"]
    color = meta["color"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y],
            mode="lines+markers",
            line=dict(color=color, width=2.4),
            marker=dict(size=4),
            fill="tozeroy",
            fillcolor="rgba(232,130,12,0.10)",
            name=name,
            hovertemplate=f"{name}: %{{y:.2f}} {unidad}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
        font=dict(color=TEXT2, size=11),
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=9, color=TEXT4)),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            tickfont=dict(size=9, color=TEXT4),
            title=dict(text=unidad, font=dict(size=10, color=TEXT3)),
        ),
        hovermode="x unified",
        showlegend=False,
    )
    return fig

def make_compare_figure(var_key):
    meta = VAR_META[var_key]
    compare_key = meta.get("compare")
    if compare_key is None or VAR_META[compare_key]["df"] is None:
        return blank_figure("Comparativo pendiente")

    df1 = trim_df_for_period(var_key, 26)
    df2 = trim_df_for_period(compare_key, 26)

    m2 = VAR_META[compare_key]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df1[meta["x"]],
            y=df1[meta["y"]],
            mode="lines+markers",
            line=dict(color=meta["color"], width=2),
            marker=dict(size=3),
            name=f"{meta['name']} ({meta['unidad']})",
            yaxis="y1",
            hovertemplate=f"{meta['name']}: %{{y:.2f}} {meta['unidad']}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df2[m2["x"]],
            y=df2[m2["y"]],
            mode="lines",
            line=dict(color=m2["color"], width=1.6, dash="dot"),
            name=f"{m2['name']} ({m2['unidad']})",
            yaxis="y2",
            hovertemplate=f"{m2['name']}: %{{y:.2f}} {m2['unidad']}<extra></extra>",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=40, t=4, b=0),
        height=230,
        font=dict(color=TEXT2, size=10),
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=8, color=TEXT4)),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID,
            zeroline=False,
            tickfont=dict(size=8, color=meta["color"]),
            title=dict(text=meta["unidad"], font=dict(size=9, color=meta["color"])),
        ),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=8, color=m2["color"]),
            title=dict(text=m2["unidad"], font=dict(size=9, color=m2["color"])),
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9), orientation="h", y=1.10),
        hovermode="x unified",
    )
    return fig

def build_home_table():
    rows = []
    for r in HOME_SUMMARY_ROWS:
        c = r["cambio"]
        color = POS if (c is not None and c >= 0) else NEG
        sym = "▲" if (c is not None and c >= 0) else "▼"
        rows.append(
            html.Tr(
                [
                    html.Td(r["variable"], style=td_style_left()),
                    html.Td(
                        [
                            html.Span(r["nivel"], style={"fontSize": "18px", "fontWeight": "900", "color": WHITE}),
                            html.Span(f" {r['unidad']}", style={"fontSize": "12px", "color": TEXT3, "fontWeight": "700"}),
                        ],
                        style=td_style(),
                    ),
                    html.Td(
                        f"{sym} {abs(c):.1f}%" if c is not None else "—",
                        style={**td_style(), "color": color, "fontWeight": "900", "fontSize": "16px"},
                    ),
                    html.Td(r["impacto"], style={**td_style_left(), "fontWeight": "800", "color": ORANGE_SOFT}),
                ]
            )
        )
    return rows

def td_style():
    return {
        "padding": "12px 14px",
        "borderBottom": f"1px solid {BORDER}",
        "fontSize": "13px",
        "color": TEXT2,
    }

def td_style_left():
    return {
        "padding": "12px 14px",
        "borderBottom": f"1px solid {BORDER}",
        "fontSize": "13px",
        "color": WHITE,
        "fontWeight": "800",
    }

# ──────────────────────────────────────────────────────────────────────────────
# HOME
# ──────────────────────────────────────────────────────────────────────────────
def home_layout():
    tc_fig = go.Figure()
    tc_fig.add_trace(
        go.Scatter(
            x=tc_df["Fecha"],
            y=tc_df["TC"],
            mode="lines+markers",
            line=dict(color=GOLD2, width=2.2),
            marker=dict(size=3),
            fill="tozeroy",
            fillcolor="rgba(232,130,12,0.08)",
            hovertemplate="TC: %{y:.2f} USD/MXN<extra></extra>",
        )
    )
    tc_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=5, b=0),
        height=220,
        font=dict(color=TEXT2, size=11),
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=8, color=TEXT4)),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(size=8, color=TEXT4)),
        hovermode="x unified",
        showlegend=False,
    )

    pollo_vs_maiz = make_compare_figure("pollo")

    noticias_home = NOTICIAS[:4]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                "Resumen Ejecutivo",
                                style={"fontSize": "24px", "fontWeight": "900", "color": WHITE},
                            ),
                            html.Span(" (Sector Avícola)", style={"fontSize": "16px", "color": TEXT3, "fontWeight": "600"}),
                        ],
                        style={"display": "flex", "alignItems": "baseline", "gap": "8px", "marginBottom": "12px"},
                    ),
                    html.Div(
                        [
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Variable", style=td_style_left()),
                                                html.Th("Nivel", style=td_style_left()),
                                                html.Th("Cambio", style=td_style_left()),
                                                html.Th("Impacto en Avícola", style=td_style_left()),
                                            ]
                                        )
                                    ),
                                    html.Tbody(build_home_table()),
                                ],
                                style={
                                    "width": "100%",
                                    "borderCollapse": "collapse",
                                    "background": CARD,
                                    "border": f"1px solid {BORDER}",
                                    "borderRadius": "8px",
                                    "overflow": "hidden",
                                },
                            )
                        ]
                    ),
                ]
            ),

            html.Div(style={"height": "18px"}),

            html.Div(
                [
                    html.Div(
                        [
                            html.Div("¿Qué está moviendo el mercado?", style={"fontSize": "18px", "fontWeight": "900", "color": ORANGE_SOFT, "marginBottom": "10px"}),
                            html.Div(
                                [
                                    html.Div("• USDA recorta inventarios", style={"fontSize": "15px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                                    html.Div("• Clima seco en Iowa / Midwest", style={"fontSize": "15px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                                    html.Div("• Peso presionado por PMI", style={"fontSize": "15px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                                    html.Div("• Demanda firme de pollo", style={"fontSize": "15px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                                ]
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div("Riesgo Actual Sector Avícola", style={"fontSize": "14px", "fontWeight": "800", "color": TEXT2, "marginBottom": "10px"}),
                            html.Div("Moderado", style={
                                "background": ORANGE_SOFT,
                                "color": "#111",
                                "fontWeight": "900",
                                "fontSize": "18px",
                                "padding": "8px 18px",
                                "borderRadius": "999px",
                                "display": "inline-block",
                            }),
                        ],
                        style={
                            "width": "260px",
                            "background": CARD,
                            "border": f"1px solid {BORDER}",
                            "borderRadius": "8px",
                            "padding": "18px",
                            "alignSelf": "center",
                            "textAlign": "center",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "18px",
                    "background": BG,
                    "borderTop": f"1px solid {BORDER}",
                    "paddingTop": "18px",
                },
            ),

            html.Div(style={"height": "22px"}),

            html.Div(
                [
                    home_module_card(
                        "Pollo",
                        "Pollo entero, vivo y partes",
                        [
                            f"Pollo entero: {fmt(kpis['pollo']['valor'])} MXN/kg",
                            f"Vivo granja: {fmt(vivo_granja_last)} MXN/kg",
                            f"Pechuga: {fmt(kpis['pechuga']['valor'])} MXN/kg",
                        ],
                        "go-pollo",
                    ),
                    home_module_card(
                        "Insumos",
                        "Maíz, pasta de soya y costos base",
                        [
                            f"Maíz: {fmt(kpis['maiz']['valor'])} USD/bu",
                            f"Pasta: {fmt(pasta_last)} USD/t",
                            "Costo alimento y presión sobre márgenes",
                        ],
                        "go-insumos",
                    ),
                    home_module_card(
                        "Macro",
                        "Tipo de cambio y variables externas",
                        [
                            f"TC: {fmt(kpis['tc']['valor'])} USD/MXN",
                            "Fletes: pendiente",
                            "Diésel / tasa: pendientes",
                        ],
                        "go-macro",
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "16px"},
            ),

            html.Div(style={"height": "22px"}),

            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Tipo de Cambio USD/MXN", style={"fontSize": "14px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                            dcc.Graph(figure=tc_fig, config={"displayModeBar": False}, style={"height": "220px"}),
                        ],
                        style={
                            "background": CARD,
                            "border": f"1px solid {BORDER}",
                            "borderRadius": "8px",
                            "padding": "14px",
                        },
                    ),
                    html.Div(
                        [
                            html.Div("Pollo Entero vs Maíz CME", style={"fontSize": "14px", "fontWeight": "800", "color": WHITE, "marginBottom": "8px"}),
                            dcc.Graph(figure=pollo_vs_maiz, config={"displayModeBar": False}, style={"height": "220px"}),
                        ],
                        style={
                            "background": CARD,
                            "border": f"1px solid {BORDER}",
                            "borderRadius": "8px",
                            "padding": "14px",
                        },
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "0.9fr 1.1fr", "gap": "16px"},
            ),

            html.Div(style={"height": "22px"}),

            html.Div(
                [
                    html.Div("Noticias / Drivers", style={"fontSize": "16px", "fontWeight": "900", "color": ORANGE_SOFT, "marginBottom": "8px"}),
                    html.Div([noticia_card(n) for n in noticias_home]),
                ],
                style={
                    "background": CARD,
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "8px",
                    "padding": "14px",
                },
            ),
        ],
        style={"padding": "16px 18px", "overflowY": "auto", "height": "calc(100vh - 52px)"},
    )

# ──────────────────────────────────────────────────────────────────────────────
# MODULE SIDEBARS
# ──────────────────────────────────────────────────────────────────────────────
def pollo_sidebar():
    return html.Div(
        [
            sec_label("MACRO"),
            clickable_price_card(
                "Tipo de Cambio",
                kpis["tc"]["valor"],
                "USD/MXN",
                kpis["tc"]["cambio"],
                spark(tc_df, "Fecha", "TC", color=GOLD2),
                color=GOLD2,
                fuente="Banxico",
                card_id="btn-tc",
            ),

            sec_label("INSUMOS"),
            clickable_price_card(
                "Maíz Amarillo CME (front)",
                kpis["maiz"]["valor"],
                "USD/bu",
                kpis["maiz"]["cambio"],
                spark(maiz, "Date", "Close", color="#F5C842"),
                color="#F5C842",
                fuente="CME Group",
                card_id="btn-maiz",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Pasta de Soya CME (front)",
                pasta_last,
                "USD/t",
                pasta_chg,
                spark(pasta, "Date", "Close", color=PINK),
                color=PINK,
                fuente="CME Group",
                card_id="btn-pasta",
            ),

            sec_label("POLLO VIVO / PIE"),
            clickable_price_card(
                "Vivo en Granja",
                vivo_granja_last,
                "MXN/kg",
                vivo_granja_chg,
                spark(vivo_g, "Fecha", "granja", color=GOLD),
                fuente="UNA México",
                card_id="btn-vivo-granja",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Vivo en Andén",
                vivo_anden_last,
                "MXN/kg",
                vivo_anden_chg,
                spark(vivo_a, "Fecha", "anden", color=GOLD),
                fuente="UNA México",
                card_id="btn-vivo-anden",
            ),

            sec_label("POLLO PROCESADO"),
            clickable_price_card(
                "Pollo Entero SNIIM",
                kpis["pollo"]["valor"],
                "MXN/kg",
                kpis["pollo"]["cambio"],
                spark(pollo, "Fecha", "precio_semana", color=GOLD),
                fuente="SNIIM / SADER",
                card_id="btn-pollo",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Pechuga (Mdo. San Juan)",
                kpis["pechuga"]["valor"],
                "MXN/kg",
                kpis["pechuga"]["cambio"],
                spark(pechuga, "Fecha", "precio_semana", color=PINK),
                color=PINK,
                fuente="Mercado San Juan",
                card_id="btn-pechuga",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Pierna-Muslo (Mdo. San Juan)",
                kpis["pierna"]["valor"],
                "MXN/kg",
                kpis["pierna"]["cambio"],
                spark(pierna, "Fecha", "precio_semana", color=GREEN),
                color=GREEN,
                fuente="Mercado San Juan",
                card_id="btn-pierna",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Rosticero UNA",
                rosticero_last,
                "MXN/kg",
                rosticero_chg,
                spark(vivo_r, "Fecha", "rosticero", color="#C8A040"),
                color="#C8A040",
                fuente="UNA México",
                card_id="btn-rosticero",
            ),
        ],
        style={
            "width": "255px",
            "minWidth": "255px",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 52px)",
            "padding": "12px 10px",
            "borderRight": "1px solid #1e1e1e",
        },
    )

def insumos_sidebar():
    return html.Div(
        [
            sec_label("INSUMOS"),
            clickable_price_card(
                "Maíz Amarillo CME (front)",
                kpis["maiz"]["valor"],
                "USD/bu",
                kpis["maiz"]["cambio"],
                spark(maiz, "Date", "Close", color="#F5C842"),
                color="#F5C842",
                fuente="CME Group",
                card_id="btn-maiz",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Pasta de Soya CME (front)",
                pasta_last,
                "USD/t",
                pasta_chg,
                spark(pasta, "Date", "Close", color=PINK),
                color=PINK,
                fuente="CME Group",
                card_id="btn-pasta",
            ),

            sec_label("MACRO RELACIONADO"),
            clickable_price_card(
                "Tipo de Cambio",
                kpis["tc"]["valor"],
                "USD/MXN",
                kpis["tc"]["cambio"],
                spark(tc_df, "Fecha", "TC", color=GOLD2),
                color=GOLD2,
                fuente="Banxico",
                card_id="btn-tc",
            ),
        ],
        style={
            "width": "255px",
            "minWidth": "255px",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 52px)",
            "padding": "12px 10px",
            "borderRight": "1px solid #1e1e1e",
        },
    )

def macro_sidebar():
    return html.Div(
        [
            sec_label("MACRO"),
            clickable_price_card(
                "Tipo de Cambio",
                kpis["tc"]["valor"],
                "USD/MXN",
                kpis["tc"]["cambio"],
                spark(tc_df, "Fecha", "TC", color=GOLD2),
                color=GOLD2,
                fuente="Banxico",
                card_id="btn-tc",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Índice de Fletes",
                FLETES_LAST,
                "Índice",
                FLETES_CHG,
                html.Div("Serie pendiente", style={"fontSize": "10px", "color": TEXT4, "paddingTop": "8px"}),
                color=ORANGE_SOFT,
                fuente="Pendiente",
                card_id="btn-fletes",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Precio Diésel",
                DIESEL_LAST,
                "MXN/L",
                DIESEL_CHG,
                html.Div("Serie pendiente", style={"fontSize": "10px", "color": TEXT4, "paddingTop": "8px"}),
                color=ORANGE_SOFT,
                fuente="Pendiente",
                card_id="btn-diesel",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Tasa de Interés",
                TASA_LAST,
                "%",
                TASA_CHG,
                html.Div("Serie pendiente", style={"fontSize": "10px", "color": TEXT4, "paddingTop": "8px"}),
                color=ORANGE_SOFT,
                fuente="Pendiente",
                card_id="btn-tasa",
            ),
            sec_label("INSUMOS RELACIONADOS"),
            clickable_price_card(
                "Maíz Amarillo CME (front)",
                kpis["maiz"]["valor"],
                "USD/bu",
                kpis["maiz"]["cambio"],
                spark(maiz, "Date", "Close", color="#F5C842"),
                color="#F5C842",
                fuente="CME Group",
                card_id="btn-maiz",
            ),
            html.Div(style={"height": "8px"}),
            clickable_price_card(
                "Pasta de Soya CME (front)",
                pasta_last,
                "USD/t",
                pasta_chg,
                spark(pasta, "Date", "Close", color=PINK),
                color=PINK,
                fuente="CME Group",
                card_id="btn-pasta",
            ),
        ],
        style={
            "width": "255px",
            "minWidth": "255px",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 52px)",
            "padding": "12px 10px",
            "borderRight": "1px solid #1e1e1e",
        },
    )

# ──────────────────────────────────────────────────────────────────────────────
# MODULE CONTENT
# ──────────────────────────────────────────────────────────────────────────────
def module_content(modulo, selected_var, period):
    meta = VAR_META[selected_var]
    last, prev, chg_abs, chg_pct, mn, mx = get_var_stats(selected_var)

    main_fig = make_main_figure(selected_var, period)
    comp_fig = make_compare_figure(selected_var)

    if modulo == "pollo":
        title = "Monitor de Pollo"
        dropdown_options = [
            {"label": "Pollo Entero SNIIM (MXN/kg)", "value": "pollo"},
            {"label": "Pechuga — San Juan (MXN/kg)", "value": "pechuga"},
            {"label": "Pierna-Muslo — San Juan (MXN/kg)", "value": "pierna"},
            {"label": "Pollo Vivo en Granja (MXN/kg)", "value": "vivo_granja"},
            {"label": "Pollo Vivo en Andén (MXN/kg)", "value": "vivo_anden"},
            {"label": "Rosticero UNA (MXN/kg)", "value": "rosticero"},
        ]
        sidebar = pollo_sidebar()
    elif modulo == "insumos":
        title = "Monitor de Insumos"
        dropdown_options = [
            {"label": "Maíz CME front (USD/bu)", "value": "maiz"},
            {"label": "Pasta de Soya CME (USD/t)", "value": "pasta"},
            {"label": "Tipo de Cambio (USD/MXN)", "value": "tc"},
        ]
        sidebar = insumos_sidebar()
    else:
        title = "Indicadores Macro"
        dropdown_options = [
            {"label": "Tipo de Cambio (USD/MXN)", "value": "tc"},
            {"label": "Índice de Fletes (pendiente)", "value": "fletes"},
            {"label": "Precio Diésel (pendiente)", "value": "diesel"},
            {"label": "Tasa de Interés (pendiente)", "value": "tasa"},
            {"label": "Maíz CME front (USD/bu)", "value": "maiz"},
            {"label": "Pasta de Soya CME (USD/t)", "value": "pasta"},
        ]
        sidebar = macro_sidebar()

    noticias = noticias_por_modulo(modulo)

    center = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(title, style={"fontSize": "22px", "fontWeight": "900", "color": WHITE}),
                            html.Span(" (Sector Avícola)", style={"fontSize": "15px", "color": TEXT3, "fontWeight": "600", "marginLeft": "8px"}),
                        ],
                        style={"marginBottom": "10px"},
                    ),
                    html.Div(
                        [
                            detail_stat_box("Serie", meta["name"], meta["fuente"]),
                            detail_stat_box(
                                "Último precio",
                                f"{fmt(last)} {meta['unidad']}" if last is not None else "—",
                                f"Δ abs: {fmt(chg_abs)}" if chg_abs is not None else "Sin dato anterior",
                            ),
                            detail_stat_box(
                                "Cambio",
                                f"{chg_pct:+.1f}%" if chg_pct is not None else "—",
                                f"Min: {fmt(mn)} | Max: {fmt(mx)}" if mn is not None and mx is not None else "Rango pendiente",
                            ),
                        ],
                        style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "10px", "marginBottom": "12px"},
                    ),
                ]
            ),

            html.Div(
                [
                    html.Span("Variable:", style={"fontSize": "12px", "color": TEXT3, "marginRight": "8px", "fontWeight": "700"}),
                    dcc.Dropdown(
                        id="var-select",
                        options=dropdown_options,
                        value=selected_var,
                        clearable=False,
                        style={
                            "backgroundColor": CARD,
                            "color": TEXT,
                            "border": f"1px solid {BORDER}",
                            "fontSize": "12px",
                            "flex": "1",
                        },
                    ),
                    dcc.RadioItems(
                        id="periodo-select",
                        options=[
                            {"label": "8 sem", "value": 8},
                            {"label": "26 sem", "value": 26},
                            {"label": "52 sem", "value": 52},
                            {"label": "Todo", "value": 999},
                        ],
                        value=period,
                        inline=True,
                        style={"fontSize": "12px", "color": TEXT3, "marginLeft": "14px", "fontWeight": "700"},
                        inputStyle={"marginRight": "3px", "accentColor": ORANGE},
                        labelStyle={"marginRight": "10px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginBottom": "10px", "gap": "8px"},
            ),

            dcc.Graph(
                id="main-chart",
                figure=main_fig,
                config={"displayModeBar": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
                style={"height": "340px"},
            ),

            html.Div(style={"height": "1px", "background": GRID, "margin": "12px 0"}),

            html.Div(
                f"Evolución: {meta['name']} vs variable comparativa",
                style={"fontSize": "12px", "color": TEXT3, "marginBottom": "6px", "fontWeight": "800"},
            ),
            dcc.Graph(id="dual-chart", figure=comp_fig, config={"displayModeBar": False}, style={"height": "230px"}),
        ],
        style={
            "flex": "1",
            "padding": "14px 16px",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 52px)",
        },
    )

    right = html.Div(
        [
            sec_label("NOTICIAS DEL MERCADO"),
            html.Div([noticia_card(n) for n in noticias]),
            html.Div(
                "🔗 Conectar fuente de noticias en vivo",
                style={
                    "marginTop": "14px",
                    "textAlign": "center",
                    "fontSize": "10px",
                    "color": "#3a3020",
                    "fontStyle": "italic",
                },
            ),
        ],
        style={
            "width": "290px",
            "minWidth": "290px",
            "padding": "12px 10px",
            "borderLeft": "1px solid #1e1e1e",
            "overflowY": "auto",
            "maxHeight": "calc(100vh - 52px)",
        },
    )

    return html.Div(
        [sidebar, center, right],
        style={"display": "flex", "height": "calc(100vh - 52px)", "overflow": "hidden"},
    )

# ──────────────────────────────────────────────────────────────────────────────
# LAYOUT BASE
# ──────────────────────────────────────────────────────────────────────────────
app.layout = html.Div(
    [
        dcc.Store(id="page-store", data="home"),
        dcc.Store(id="module-store", data="pollo"),
        dcc.Store(id="var-store", data="pollo"),
        dcc.Store(id="period-store", data=26),

        html.Div(
            [
                html.Div(
                    [
                        html.Span("🌿", style={"fontSize": "22px", "marginRight": "8px"}),
                        html.Span("Agro Monitor ", style={"fontSize": "18px", "fontWeight": "900", "color": WHITE}),
                        html.Span("UDLAP", style={"fontSize": "18px", "fontWeight": "900", "color": ORANGE}),
                        html.Span(" · Sector Avícola", style={"fontSize": "13px", "color": TEXT4, "marginLeft": "10px", "fontWeight": "700"}),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                html.Div(
                    [
                        navbar_button("Inicio", "nav-home"),
                        navbar_button("Pollo", "nav-pollo"),
                        navbar_button("Insumos", "nav-insumos"),
                        navbar_button("Macro", "nav-macro"),
                    ],
                    style={"display": "flex", "alignItems": "center"},
                ),
                html.Span(
                    "Uso informativo. No constituye recomendación de inversión.",
                    style={"fontSize": "10px", "color": TEXT4, "fontWeight": "700"},
                ),
            ],
            style={
                "background": BG,
                "borderBottom": f"2px solid {ORANGE}",
                "padding": "10px 20px",
                "display": "grid",
                "gridTemplateColumns": "1fr auto auto",
                "gap": "16px",
                "alignItems": "center",
                "position": "sticky",
                "top": "0",
                "zIndex": "999",
            },
        ),

        html.Div(id="page-content"),
    ],
    style={"background": BG, "minHeight": "100vh", "fontFamily": "'Segoe UI', Arial, sans-serif", "color": TEXT},
)

# ──────────────────────────────────────────────────────────────────────────────
# CALLBACK: NAVEGACIÓN + SELECCIÓN
# ──────────────────────────────────────────────────────────────────────────────
@callback(
    Output("page-store", "data"),
    Output("module-store", "data"),
    Output("var-store", "data"),
    Output("period-store", "data"),

    Input("nav-home", "n_clicks"),
    Input("nav-pollo", "n_clicks"),
    Input("nav-insumos", "n_clicks"),
    Input("nav-macro", "n_clicks"),

    Input("go-pollo", "n_clicks", allow_optional=True),
    Input("go-insumos", "n_clicks", allow_optional=True),
    Input("go-macro", "n_clicks", allow_optional=True),

    Input("btn-tc", "n_clicks", allow_optional=True),
    Input("btn-maiz", "n_clicks", allow_optional=True),
    Input("btn-pasta", "n_clicks", allow_optional=True),
    Input("btn-vivo-granja", "n_clicks", allow_optional=True),
    Input("btn-vivo-anden", "n_clicks", allow_optional=True),
    Input("btn-pollo", "n_clicks", allow_optional=True),
    Input("btn-pechuga", "n_clicks", allow_optional=True),
    Input("btn-pierna", "n_clicks", allow_optional=True),
    Input("btn-rosticero", "n_clicks", allow_optional=True),
    Input("btn-fletes", "n_clicks", allow_optional=True),
    Input("btn-diesel", "n_clicks", allow_optional=True),
    Input("btn-tasa", "n_clicks", allow_optional=True),

    Input("var-select", "value", allow_optional=True),
    Input("periodo-select", "value", allow_optional=True),

    State("page-store", "data"),
    State("module-store", "data"),
    State("var-store", "data"),
    State("period-store", "data"),

    prevent_initial_call=True,
)
def route_state(
    nav_home,
    nav_pollo,
    nav_insumos,
    nav_macro,

    go_pollo,
    go_insumos,
    go_macro,

    btn_tc,
    btn_maiz,
    btn_pasta,
    btn_vivo_granja,
    btn_vivo_anden,
    btn_pollo,
    btn_pechuga,
    btn_pierna,
    btn_rosticero,
    btn_fletes,
    btn_diesel,
    btn_tasa,

    dropdown_var,
    periodo_val,

    page,
    module,
    current_var,
    current_period,
):

    trigger = ctx.triggered_id

    if trigger is None:
        return page, module, current_var, current_period

    # navegación navbar
    if trigger == "nav-home":
        return "home", module, current_var, current_period

    if trigger == "nav-pollo":
        return "module", "pollo", "pollo", current_period

    if trigger == "nav-insumos":
        return "module", "insumos", "maiz", current_period

    if trigger == "nav-macro":
        return "module", "macro", "tc", current_period

    # home → módulos
    if trigger == "go-pollo":
        return "module", "pollo", "pollo", current_period

    if trigger == "go-insumos":
        return "module", "insumos", "maiz", current_period

    if trigger == "go-macro":
        return "module", "macro", "tc", current_period

    # botones laterales
    card_map = {
        "btn-tc": ("module", "macro", "tc"),
        "btn-maiz": ("module", "insumos", "maiz"),
        "btn-pasta": ("module", "insumos", "pasta"),
        "btn-vivo-granja": ("module", "pollo", "vivo_granja"),
        "btn-vivo-anden": ("module", "pollo", "vivo_anden"),
        "btn-pollo": ("module", "pollo", "pollo"),
        "btn-pechuga": ("module", "pollo", "pechuga"),
        "btn-pierna": ("module", "pollo", "pierna"),
        "btn-rosticero": ("module", "pollo", "rosticero"),
        "btn-fletes": ("module", "macro", "fletes"),
        "btn-diesel": ("module", "macro", "diesel"),
        "btn-tasa": ("module", "macro", "tasa"),
    }

    if trigger in card_map:
        p, m, v = card_map[trigger]
        return p, m, v, current_period

    # dropdown variable
    if trigger == "var-select":
        if dropdown_var is None:
            return page, module, current_var, current_period

        selected_module = VAR_META[dropdown_var]["modulo"]
        return "module", selected_module, dropdown_var, current_period

    # radio periodo
    if trigger == "periodo-select":
        if periodo_val is None:
            return page, module, current_var, current_period

        return page, module, current_var, periodo_val

    return page, module, current_var, current_period
# ──────────────────────────────────────────────────────────────────────────────
# CALLBACK: RENDER PÁGINA
# ──────────────────────────────────────────────────────────────────────────────
@callback(
    Output("page-content", "children"),
    Input("page-store", "data"),
    Input("module-store", "data"),
    Input("var-store", "data"),
    Input("period-store", "data"),
)
def render_page(page, module, selected_var, period):
    if page == "home":
        return home_layout()
    return module_content(module, selected_var, period)

# ──────────────────────────────────────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)