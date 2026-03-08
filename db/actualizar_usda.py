"""
db/actualizar_usda.py — Descarga datos de USDA y los sube a Supabase

Fuentes:
  - USDA NASS API: huevo para plato, cold storage, incubadoras, ponedoras
  - USDA AMS API:  precios de pollo (pechuga, muslo, entero, etc.)

Uso:
    python db/actualizar_usda.py
"""
import base64
import requests
import pandas as pd
import sqlalchemy as sa
from io import StringIO
from datetime import datetime

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)

NASS_KEY = "A1AF4176-0B34-35B0-86C8-9536D5188318"
AMS_KEY  = "oK/SXE39wQgOhJ+yHboLvM6822oXAK27sEqZeItzuvw="

MESES = {
    "JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
    "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12
}


def mes_num(texto):
    for k, v in MESES.items():
        if k in str(texto).upper():
            return v
    return None


def nass_get(short_desc, year_ge=2018):
    """Descarga datos de USDA NASS API."""
    import urllib.parse
    url = (
        f"https://quickstats.nass.usda.gov/api/api_GET/"
        f"?key={NASS_KEY}"
        f"&short_desc={urllib.parse.quote(short_desc)}"
        f"&agg_level_desc=NATIONAL"
        f"&year__GE={year_ge}"
        f"&format=JSON"
    )
    r = requests.get(url, timeout=30)
    return r.json().get("data", [])


def procesar_nass(data, producto):
    """Convierte datos NASS a DataFrame con fecha y cantidad."""
    filas = []
    for row in data:
        anio = int(row.get("year", 0))
        periodo = row.get("reference_period_desc", "")
        mes = mes_num(periodo)
        valor_str = str(row.get("Value", "")).replace(",", "")
        try:
            valor = float(valor_str)
        except:
            continue
        if mes and anio:
            filas.append({
                "fecha":    datetime(anio, mes, 1).date(),
                "producto": producto,
                "cantidad": valor,
            })
    return pd.DataFrame(filas)


# ══════════════════════════════════════════════════════════════════════════════
# 1. HUEVO PARA PLATO
# ══════════════════════════════════════════════════════════════════════════════
def actualizar_huevo_nass():
    print("📌 Huevo para plato (USDA NASS)...")
    data = nass_get("EGGS, TABLE - PRODUCTION, MEASURED IN EGGS", year_ge=2023)
    df = procesar_nass(data, "huevo plato")
    if df.empty:
        print("  ⚠️  Sin datos")
        return
    subir_nass(df, "huevo_plato", "(fecha, producto)")
    print(f"  ✅ {len(df)} registros subidos")


# ══════════════════════════════════════════════════════════════════════════════
# 2. COLD STORAGE
# ══════════════════════════════════════════════════════════════════════════════
def actualizar_cold_storage():
    print("📌 Cold Storage USA (USDA NASS)...")
    data = nass_get("CHICKENS, COLD STORAGE, FROZEN - STOCKS, MEASURED IN LB", year_ge=2018)
    # Filtrar solo NATIONAL
    data = [r for r in data if r.get("agg_level_desc") == "NATIONAL"]
    df = procesar_nass(data, "cold storage chickens")
    if df.empty:
        print("  ⚠️  Sin datos")
        return
    subir_nass(df, "cold_storage_usa", "(fecha, producto)")
    print(f"  ✅ {len(df)} registros subidos")


# ══════════════════════════════════════════════════════════════════════════════
# 3. INCUBADORAS Y PONEDORAS
# ══════════════════════════════════════════════════════════════════════════════
SERIES_NASS = [
    (
        "CHICKENS, BROILER TYPE - EGGS IN INCUBATORS, MEASURED IN EGGS",
        "incubators, chickens, broiler t",
        "incubadoras_ponedoras",
        2024
    ),
    (
        "CHICKENS, EGG TYPE - EGGS IN INCUBATORS, MEASURED IN EGGS",
        "CHICKENS, EGG TYPE - EGGS IN INCUBATORS, MEASU...",
        "incubadoras_ponedoras",
        2024
    ),
    (
        "CHICKENS, LAYERS, HATCHING, EGG TYPE - INVENTORY",
        "layers hatching egg type",
        "incubadoras_ponedoras",
        2024
    ),
    (
        "CHICKENS, LAYERS, HATCHING, BROILER TYPE - INVENTORY",
        "layers hatching broiler type",
        "incubadoras_ponedoras",
        2024
    ),
]

def actualizar_incubadoras():
    print("📌 Incubadoras y Ponedoras (USDA NASS)...")
    total = 0
    for short_desc, producto, tabla, year_ge in SERIES_NASS:
        data = nass_get(short_desc, year_ge=year_ge)
        df = procesar_nass(data, producto)
        if df.empty:
            print(f"  ⚠️  Sin datos: {producto}")
            continue
        subir_nass(df, tabla, "(fecha, producto)")
        total += len(df)
        print(f"  → {producto}: {len(df)} registros")
    print(f"  ✅ Total: {total} registros subidos")


# ══════════════════════════════════════════════════════════════════════════════
# 4. PRECIOS DE POLLO — USDA AMS
# ══════════════════════════════════════════════════════════════════════════════
def actualizar_pollo_usda():
    print("📌 Precios de pollo (USDA AMS)...")
    token = base64.b64encode(f"{AMS_KEY}:".encode()).decode()
    headers = {"Authorization": f"Basic {token}"}
    url = "https://marsapi.ams.usda.gov/services/v1.2/reports/3646/Report%20Detail"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        data = r.json()
        results = data.get("results", [])
        if not results:
            print("  ⚠️  Sin resultados")
            return
        df = pd.DataFrame(results)
        cols = ["report_date", "item", "region", "condition", "size",
                "low_price", "high_price", "wtd_avg_price", "volume"]
        cols_ok = [c for c in cols if c in df.columns]
        df = df[cols_ok].copy()
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
        for col in ["low_price", "high_price", "wtd_avg_price", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.dropna(subset=["report_date"])
        insertados = 0
        with engine.begin() as conn:
            for _, row in df.iterrows():
                try:
                    conn.execute(sa.text("""
                        INSERT INTO pollo_usda
                            (report_date, item, low_price, high_price, wtd_avg_price, volume)
                        VALUES
                            (:report_date, :item, :low_price, :high_price, :wtd_avg_price, :volume)
                        ON CONFLICT (report_date, item) DO UPDATE SET
                            low_price     = EXCLUDED.low_price,
                            high_price    = EXCLUDED.high_price,
                            wtd_avg_price = EXCLUDED.wtd_avg_price,
                            volume        = EXCLUDED.volume
                    """), {
                        "report_date":   row["report_date"].date(),
                        "item":          str(row.get("item", "")),
                        "low_price":     row.get("low_price"),
                        "high_price":    row.get("high_price"),
                        "wtd_avg_price": row.get("wtd_avg_price"),
                        "volume":        row.get("volume"),
                    })
                    insertados += 1
                except:
                    pass
        print(f"  ✅ {insertados} registros subidos")
    except Exception as e:
        print(f"  ❌ Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — subir DataFrame NASS a Supabase
# ══════════════════════════════════════════════════════════════════════════════
def subir_nass(df, tabla, conflict_key):
    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(sa.text(f"""
                    INSERT INTO {tabla} (fecha, producto, cantidad)
                    VALUES (:fecha, :producto, :cantidad)
                    ON CONFLICT {conflict_key} DO UPDATE SET
                        cantidad = EXCLUDED.cantidad
                """), {
                    "fecha":    row["fecha"],
                    "producto": row["producto"],
                    "cantidad": row["cantidad"],
                })
            except Exception as e:
                print(f"    ❌ {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n🇺🇸 Actualizando datos USDA — {datetime.today().strftime('%Y-%m-%d')}\n")
    actualizar_pollo_usda()
    actualizar_huevo_nass()
    actualizar_cold_storage()
    actualizar_incubadoras()
    print("\n🎉 USDA actualizado correctamente.")


if __name__ == "__main__":
    main()
