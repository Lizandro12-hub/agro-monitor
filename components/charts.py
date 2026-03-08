"""
components/charts.py — Gráficas reutilizables para Agro Monitor UDLAP
"""
import plotly.graph_objects as go
import pandas as pd

GOLD  = "#E8820C"
GOLD2 = "#F5C842"
GREEN = "#5cb85c"
RED   = "#d9534f"
PINK  = "#C87090"
CREAM = "#E0D8C8"
BG    = "#1e1e1e"
GRID  = "#2a2a2a"


def _hex_to_rgba(hex_color, alpha=0.12):
    """Convierte hex a rgba string que Plotly acepta."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(232,130,12,{alpha})"


def sparkline(df: pd.DataFrame, x_col: str, y_col: str,
              color=GOLD, height=60, name="") -> go.Figure:
    fig = go.Figure()
    df = df.tail(20)
    fig.add_trace(go.Scatter(
        x=df[x_col], y=df[y_col],
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=_hex_to_rgba(color, 0.12),
        name=name, showlegend=False,
        hovertemplate="%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0), height=height,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
    )
    return fig


def line_chart(series: list, title="", height=220, n_semanas=8) -> go.Figure:
    fig = go.Figure()
    for s in series:
        df = s["df"].tail(n_semanas * 7 if "Date" in s["df"].columns else n_semanas)
        fig.add_trace(go.Scatter(
            x=df[s["x"]], y=df[s["y"]],
            mode="lines+markers",
            line=dict(color=s.get("color", GOLD), width=2),
            marker=dict(size=4),
            name=s["name"],
            hovertemplate=f"{s['name']}: %{{y:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=CREAM, size=12), x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30 if title else 8, b=0),
        height=height,
        font=dict(color=CREAM, size=11),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False,
                   tickfont=dict(size=9, color="#6a6050")),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False,
                   tickfont=dict(size=9, color="#6a6050")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                    orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    return fig


def area_chart_dual(df1, df2, x1, y1, name1, x2, y2, name2,
                    title="", height=220, n=52) -> go.Figure:
    fig = go.Figure()
    d1 = df1.tail(n)
    d2 = df2.tail(n)
    fig.add_trace(go.Scatter(
        x=d1[x1], y=d1[y1], name=name1, mode="lines+markers",
        line=dict(color=GOLD, width=2), marker=dict(size=3),
        fill="tozeroy", fillcolor="rgba(232,130,12,0.12)",
        hovertemplate=f"{name1}: %{{y:.2f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d2[x2], y=d2[y2], name=name2, mode="lines+markers",
        line=dict(color=PINK, width=2), marker=dict(size=3),
        fill="tozeroy", fillcolor="rgba(200,112,144,0.10)",
        hovertemplate=f"{name2}: %{{y:.2f}}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=CREAM, size=12), x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30 if title else 8, b=0),
        height=height,
        font=dict(color=CREAM, size=11),
        xaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False,
                   tickfont=dict(size=9, color="#6a6050")),
        yaxis=dict(showgrid=True, gridcolor="#2a2a2a", zeroline=False,
                   tickfont=dict(size=9, color="#6a6050")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10),
                    orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    return fig
