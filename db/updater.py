"""
db/updater.py — Actualización automática de datos
Descarga datos frescos y los inserta en Supabase

Corre automáticamente con Task Scheduler de Windows cada día.
También puedes correrlo manualmente:
    python db/updater.py
"""
import pandas as pd
import sqlalchemy as sa
from datetime import datetime, timedelta
import sys

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)
hoy = datetime.today().strftime("%Y-%m-%d")
print(f"🔄 Actualizando datos — {hoy}\n")


def upsert_df(df, table, conflict_cols):
    """Inserta filas nuevas, ignora duplicados por conflict_cols."""
    if df.empty:
        print(f"  ⚠️  {table}: sin datos nuevos")
        return
    with engine.begin() as conn:
        for _, row in df.iterrows():
            cols = list(row.index)
            vals = list(row.values)
            placeholders = ", ".join([f":{c}" for c in cols])
            conflict = ", ".join(conflict_cols)
            sql = f"""
                INSERT INTO {table} ({", ".join(cols)})
                VALUES ({placeholders})
                ON CONFLICT ({conflict}) DO UPDATE SET
                {", ".join([f"{c} = EXCLUDED.{c}" for c in cols if c not in conflict_cols])}
            """
            conn.execute(sa.text(sql), dict(zip(cols, vals)))
    print(f"  ✅ {table}: {len(df)} filas actualizadas")


# ── 1. Tipo de Cambio — Banxico API ───────────────────────────────────────────
print("📌 Tipo de Cambio (Banxico)...")
try:
    import requests
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/oportuno"
    headers = {"Bmx-Token": "abcdef1234567890abcdef1234567890abcdef12"}
    # Nota: si no tienes token Banxico, usa yfinance como fallback
    raise Exception("Usar yfinance como fallback")
except Exception:
    try:
        import yfinance as yf
        tc_data = yf.download("MXN=X", period="5d", auto_adjust=True)
        if not tc_data.empty:
            tc_df = tc_data[["Close"]].reset_index()
            tc_df.columns = ["fecha", "tc"]
            tc_df["fecha"] = tc_df["fecha"].dt.date
            upsert_df(tc_df, "tipo_cambio", ["fecha"])
        else:
            print("  ⚠️  tipo_cambio: sin datos de yfinance")
    except Exception as e:
        print(f"  ❌ tipo_cambio: {e}")

# ── 2. Maíz CME ───────────────────────────────────────────────────────────────
print("📌 Maíz CME (yfinance)...")
try:
    import yfinance as yf
    maiz_data = yf.download("ZC=F", period="10d", auto_adjust=True)
    if not maiz_data.empty:
        maiz_df = maiz_data[["Close"]].reset_index()
        maiz_df.columns = ["fecha", "close"]
        maiz_df["fecha"] = maiz_df["fecha"].dt.date
        maiz_df["contrato"] = "ZC=F (Corn Front)"
        upsert_df(maiz_df, "maiz_cme", ["fecha"])
    else:
        print("  ⚠️  maiz_cme: sin datos")
except Exception as e:
    print(f"  ❌ maiz_cme: {e}")

# ── 3. Soya CME ───────────────────────────────────────────────────────────────
print("📌 Soya CME (yfinance)...")
try:
    soya_data = yf.download("ZS=F", period="10d", auto_adjust=True)
    if not soya_data.empty:
        soya_df = soya_data[["Close"]].reset_index()
        soya_df.columns = ["fecha", "close"]
        soya_df["fecha"] = soya_df["fecha"].dt.date
        soya_df["contrato"] = "ZS=F (Soybean Front)"
        upsert_df(soya_df, "soya_cme", ["fecha"])
    else:
        print("  ⚠️  soya_cme: sin datos")
except Exception as e:
    print(f"  ❌ soya_cme: {e}")

# ── 4. Pasta de Soya CME ──────────────────────────────────────────────────────
print("📌 Pasta de Soya CME (yfinance)...")
try:
    pasta_data = yf.download("ZM=F", period="10d", auto_adjust=True)
    if not pasta_data.empty:
        pasta_df = pasta_data[["Close"]].reset_index()
        pasta_df.columns = ["fecha", "close"]
        pasta_df["fecha"] = pasta_df["fecha"].dt.date
        pasta_df["contrato"] = "ZM=F (Soybean Meal Front)"
        upsert_df(pasta_df, "pasta_soya_cme", ["fecha"])
    else:
        print("  ⚠️  pasta_soya_cme: sin datos")
except Exception as e:
    print(f"  ❌ pasta_soya_cme: {e}")

# ── 5. Precios USDA ───────────────────────────────────────────────────────────
# Los precios USDA se actualizan semanalmente
# Por ahora se actualizan manualmente desde el Excel
# TODO: conectar a la API de USDA AMS cuando tengan acceso
print("📌 USDA: actualización manual requerida (semanal)")

# ── 6. Precios SNIIM ──────────────────────────────────────────────────────────
# SNIIM requiere scraping o descarga manual
# Por ahora se actualiza desde el Excel manualmente
print("📌 SNIIM: actualización manual requerida (semanal)")

# ── Resumen ───────────────────────────────────────────────────────────────────
print(f"\n✅ Actualización completada — {hoy}")
print("   Variables automáticas: TC, Maíz, Soya, Pasta de Soya")
print("   Variables manuales:    SNIIM, USDA, UNA, Huevo")
