"""
db/migrar_excel.py — Sube todo el Excel histórico a Supabase
Corre UNA SOLA VEZ después de setup.py

Uso:
    python db/migrar_excel.py
"""
import pandas as pd
import sqlalchemy as sa
from pathlib import Path

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

EXCEL_PATH = Path(__file__).parent.parent / "data" / "precios_.xlsx"

engine = sa.create_engine(DB_URL)


def read(sheet, **kwargs):
    return pd.read_excel(EXCEL_PATH, sheet_name=sheet, **kwargs)


def upsert(df, table, if_exists="append"):
    """Sube un DataFrame a Supabase, ignorando duplicados."""
    df.to_sql(table, engine, if_exists=if_exists, index=False,
              method="multi", chunksize=500)
    print(f"  ✅ {table}: {len(df)} filas subidas")


print("🚀 Iniciando migración del Excel a Supabase...\n")

# ── Tipo de cambio ────────────────────────────────────────────────────────────
print("📌 Tipo de cambio...")
tc = read("Banxico_TC")
tc["Fecha"] = pd.to_datetime(tc["Fecha"], dayfirst=True, errors="coerce")
tc = tc.dropna().rename(columns={"Fecha": "fecha", "TC": "tc"})
upsert(tc, "tipo_cambio", if_exists="replace")

# ── Maíz CME ──────────────────────────────────────────────────────────────────
print("📌 Maíz CME...")
maiz = read("Maiz front")
maiz["Date"] = pd.to_datetime(maiz["Date"], errors="coerce")
maiz = maiz.dropna(subset=["Date", "Close"]).rename(
    columns={"Date": "fecha", "Close": "close"})
if "Contract" in maiz.columns:
    maiz = maiz.rename(columns={"Contract": "contrato"})
else:
    maiz["contrato"] = "ZC=F"
upsert(maiz[["fecha", "close", "contrato"]], "maiz_cme", if_exists="replace")

# ── Soya CME ──────────────────────────────────────────────────────────────────
print("📌 Soya CME...")
soya = read("soya front")
soya["Date"] = pd.to_datetime(soya["Date"], errors="coerce")
soya = soya.dropna(subset=["Date", "Close"]).rename(
    columns={"Date": "fecha", "Close": "close", "Contract": "contrato"})
upsert(soya[["fecha", "close", "contrato"]], "soya_cme", if_exists="replace")

# ── Pasta de Soya CME ─────────────────────────────────────────────────────────
print("📌 Pasta de Soya CME...")
pasta = read("pastasoya front")
pasta["Date"] = pd.to_datetime(pasta["Date"], errors="coerce")
pasta = pasta.dropna(subset=["Date", "Close"]).rename(
    columns={"Date": "fecha", "Close": "close", "Contract": "contrato"})
upsert(pasta[["fecha", "close", "contrato"]], "pasta_soya_cme", if_exists="replace")

# ── Pollo entero SNIIM ────────────────────────────────────────────────────────
print("📌 Pollo entero SNIIM...")
pollo = read("Pollo entero SNIIM")
pollo["Fecha"] = pd.to_datetime(pollo["Fecha"], errors="coerce")
pollo = pollo.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(pollo[["fecha", "precio_semana"]], "pollo_entero_sniim", if_exists="replace")

# ── Pechuga San Juan ──────────────────────────────────────────────────────────
print("📌 Pechuga San Juan...")
pechuga = read("Pechuga_SanJuan")
pechuga["Fecha"] = pd.to_datetime(pechuga["Fecha"], errors="coerce")
pechuga = pechuga.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(pechuga[["fecha", "precio_semana"]], "pechuga_sanjuan", if_exists="replace")

# ── Pierna-Muslo San Juan ─────────────────────────────────────────────────────
print("📌 Pierna-Muslo San Juan...")
pierna = read("Pierna_Muslo_SanJuan")
pierna["Fecha"] = pd.to_datetime(pierna["Fecha"], errors="coerce")
pierna = pierna.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(pierna[["fecha", "precio_semana"]], "pierna_muslo_sanjuan", if_exists="replace")

# ── Vísceras San Juan ─────────────────────────────────────────────────────────
print("📌 Vísceras San Juan...")
visceras = read("Vísceras_SanJuan")
visceras["Fecha"] = pd.to_datetime(visceras["Fecha"], errors="coerce")
visceras = visceras.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(visceras[["fecha", "precio_semana"]], "visceras_sanjuan", if_exists="replace")

# ── Retazo San Juan ───────────────────────────────────────────────────────────
print("📌 Retazo San Juan...")
retazo = read("Retazo_SanJuan")
retazo["Fecha"] = pd.to_datetime(retazo["Fecha"], errors="coerce")
retazo = retazo.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(retazo[["fecha", "precio_semana"]], "retazo_sanjuan", if_exists="replace")

# ── Pollo vivo UNA ────────────────────────────────────────────────────────────
print("📌 Pollo vivo UNA...")
granja = read("Pollo_vivo_en_granja")[["Fecha", "precio_semana"]].rename(
    columns={"Fecha": "fecha", "precio_semana": "granja"})
anden = read("Pollo_vivo_en_anden")[["Fecha", "precio_semana"]].rename(
    columns={"Fecha": "fecha", "precio_semana": "anden"})
rostic = read("Pollo_rosticero")[["Fecha", "precio_semana"]].rename(
    columns={"Fecha": "fecha", "precio_semana": "rosticero"})
for d in [granja, anden, rostic]:
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
vivo = granja.merge(anden, on="fecha", how="outer").merge(rostic, on="fecha", how="outer")
vivo = vivo.dropna(subset=["fecha"]).sort_values("fecha")
upsert(vivo, "pollo_vivo_una", if_exists="replace")

# ── Huevo UNA ─────────────────────────────────────────────────────────────────
print("📌 Huevo UNA...")
huevo = read("Precios Huevo UNA MX")
huevo["Fecha"] = pd.to_datetime(huevo["Fecha"], errors="coerce")
huevo = huevo.dropna(subset=["Fecha", "precio_semana"]).rename(
    columns={"Fecha": "fecha"})
upsert(huevo[["fecha", "precio_semana"]], "huevo_una", if_exists="replace")

# ── Huevo SNIIM ───────────────────────────────────────────────────────────────
print("📌 Huevo SNIIM...")
hb = read("huevo blanco sniim")
hr = read("huevo rojo sniim")
huevo_sniim = pd.concat([hb, hr])
huevo_sniim["Fecha"] = pd.to_datetime(huevo_sniim["Fecha"], errors="coerce")
huevo_sniim = huevo_sniim.dropna(subset=["Fecha"]).rename(columns={
    "Fecha": "fecha", "Producto": "producto", "Presentacion": "presentacion",
    "PrecioFrecuente": "precio_frecuente", "PrecioMin": "precio_min",
    "PrecioMax": "precio_max", "PrecioProm": "precio_prom",
})
upsert(huevo_sniim, "huevo_sniim", if_exists="replace")

# ── USDA precios pollo ────────────────────────────────────────────────────────
print("📌 USDA precios pollo...")
usda_frames = []
for sheet, item_name in [("Pollo_entero_USDA ", "WOG"),
                          ("Pechuga_USDA", "Breast - B/S"),
                          ("Muslo_USDA ", "Leg quarters - Bulk")]:
    df = read(sheet)
    df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
    df = df.dropna(subset=["report_date", "wtd_avg_price"])
    usda_frames.append(df[["report_date", "item", "low_price", "high_price", "wtd_avg_price", "volume"]])
usda = pd.concat(usda_frames).rename(columns={"report_date": "report_date"})
upsert(usda, "pollo_usda", if_exists="replace")

# ── Cold Storage USA ──────────────────────────────────────────────────────────
print("📌 Cold storage USA...")
cold = read("Cold storage ")
cold["date_real"] = pd.to_datetime(cold["date_real"], errors="coerce")
cold = cold.dropna(subset=["date_real", "stocks_lb"]).rename(
    columns={"date_real": "fecha"})
upsert(cold[["fecha", "stocks_lb"]], "cold_storage_usa", if_exists="replace")

print("\n🎉 Migración completa. Todos los datos históricos están en Supabase.")
