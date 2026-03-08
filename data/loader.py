"""
data/loader.py — Lee datos desde Supabase (PostgreSQL)
Agro Monitor UDLAP — Sector Avícola
"""
import pandas as pd
import sqlalchemy as sa

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)


def _query(sql: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(sa.text(sql), conn)


# ─── TIPO DE CAMBIO ───────────────────────────────────────────────────────────
def get_tipo_cambio() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", tc AS \"TC\" FROM tipo_cambio ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


# ─── GRANOS CME ───────────────────────────────────────────────────────────────
def get_maiz_front() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Date\", close AS \"Close\" FROM maiz_cme ORDER BY fecha")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_soya_front() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Date\", close AS \"Close\" FROM soya_cme ORDER BY fecha")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_pastasoya_front() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Date\", close AS \"Close\" FROM pasta_soya_cme ORDER BY fecha")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


# ─── PRECIOS POLLO MX ────────────────────────────────────────────────────────
def get_pollo_entero_sniim() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", precio_semana FROM pollo_entero_sniim ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def get_pechuga_sanjuan() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", precio_semana FROM pechuga_sanjuan ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def get_pierna_muslo_sanjuan() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", precio_semana FROM pierna_muslo_sanjuan ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def get_pollo_vivo() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", granja, anden, rosticero FROM pollo_vivo_una ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


# ─── HUEVO ───────────────────────────────────────────────────────────────────
def get_huevo_una() -> pd.DataFrame:
    df = _query("SELECT fecha AS \"Fecha\", precio_semana FROM huevo_una ORDER BY fecha")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


def get_huevo_blanco_sniim() -> pd.DataFrame:
    df = _query("""
        SELECT fecha AS \"Fecha\", presentacion AS \"Presentacion\",
               precio_frecuente AS \"PrecioFrecuente\"
        FROM huevo_sniim
        WHERE producto ILIKE '%blanco%'
        ORDER BY fecha
    """)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df


# ─── PRECIOS USDA ────────────────────────────────────────────────────────────
def get_pollo_usda() -> pd.DataFrame:
    df = _query("""
        SELECT report_date, wtd_avg_price
        FROM pollo_usda WHERE item = 'WOG'
        ORDER BY report_date
    """)
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df


def get_pechuga_usda() -> pd.DataFrame:
    df = _query("""
        SELECT report_date, wtd_avg_price
        FROM pollo_usda WHERE item = 'Breast - B/S'
        ORDER BY report_date
    """)
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df


def get_muslo_usda() -> pd.DataFrame:
    df = _query("""
        SELECT report_date, wtd_avg_price
        FROM pollo_usda WHERE item = 'Leg quarters - Bulk'
        ORDER BY report_date
    """)
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df


# ─── KPIs PARA DASHBOARD ─────────────────────────────────────────────────────
def get_kpis() -> dict:
    def last_and_chg(df, col, date_col="Fecha"):
        s = df[[date_col, col]].dropna()
        if len(s) < 2:
            return None, None
        last = float(s[col].iloc[-1])
        prev = float(s[col].iloc[-2])
        chg = (last - prev) / prev * 100 if prev != 0 else 0
        return round(last, 2), round(chg, 2)

    tc      = get_tipo_cambio()
    maiz    = get_maiz_front()
    soya    = get_soya_front()
    pollo   = get_pollo_entero_sniim()
    pechuga = get_pechuga_sanjuan()
    pierna  = get_pierna_muslo_sanjuan()
    huevo   = get_huevo_una()

    tc_v,      tc_c      = last_and_chg(tc,      "TC")
    maiz_v,    maiz_c    = last_and_chg(maiz,    "Close", "Date")
    soya_v,    soya_c    = last_and_chg(soya,    "Close", "Date")
    pollo_v,   pollo_c   = last_and_chg(pollo,   "precio_semana")
    pechuga_v, pechuga_c = last_and_chg(pechuga, "precio_semana")
    pierna_v,  pierna_c  = last_and_chg(pierna,  "precio_semana")
    huevo_v,   huevo_c   = last_and_chg(huevo,   "precio_semana")

    return {
        "tc":      {"valor": tc_v,      "cambio": tc_c,      "unidad": "USD/MXN"},
        "maiz":    {"valor": maiz_v,    "cambio": maiz_c,    "unidad": "USD/bu"},
        "soya":    {"valor": soya_v,    "cambio": soya_c,    "unidad": "USD/bu"},
        "pollo":   {"valor": pollo_v,   "cambio": pollo_c,   "unidad": "MXN/kg"},
        "pechuga": {"valor": pechuga_v, "cambio": pechuga_c, "unidad": "MXN/kg"},
        "pierna":  {"valor": pierna_v,  "cambio": pierna_c,  "unidad": "MXN/kg"},
        "huevo":   {"valor": huevo_v,   "cambio": huevo_c,   "unidad": "MXN/kg"},
    }
