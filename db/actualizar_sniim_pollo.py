"""
db/actualizar_sniim_pollo.py — Descarga precios de pollo del SNIIM y los sube a Supabase

Equivalente a la función Power Query original.
Descarga precios semanales de pollo entero, pechuga, pierna-muslo, vísceras y retazo.

Uso:
    python db/actualizar_sniim_pollo.py          # últimas 4 semanas
    python db/actualizar_sniim_pollo.py 12       # últimas 12 semanas
"""
import sys
import time
import requests
import pandas as pd
import sqlalchemy as sa
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)

BASE_URL = "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Ent.asp"

# Productos SNIIM — mismos códigos que Power Query
PRODUCTOS = {
    "P01": ("pollo_entero_sniim",    "Pollo entero"),
    "P02": ("pechuga_sanjuan",       "Pechuga"),
    "P04": ("pierna_muslo_sanjuan",  "Pierna-Muslo"),
    "P07": ("visceras_sanjuan",      "Vísceras"),
    "P08": ("retazo_sanjuan",        "Retazo"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":    "https://www.economia-sniim.gob.mx",
    "Cookie":     "_ga=GA1.3.1595028401.1769446871; _ga_N4181LDPL7=GS2.3.s1772490517$o5$g0$t1772490517$j60$l0$h0; ASPSESSIONIDQAABRRTB=MGCGOMABLNMCPILNHEIPCMBI; ASPSESSIONIDSADAQQTA=CPNBAEOAKLGJCBCFBFHGACHF",
}


def get_semanas(n_semanas=4):
    """Genera las fechas de las últimas N semanas."""
    hoy = date.today()
    semanas = []
    for i in range(n_semanas):
        d = hoy - timedelta(weeks=i)
        semanas.append(d)
    return semanas


def fetch_precio(fecha, prod):
    """Descarga precios de un producto para una fecha específica."""
    params = {
        "prod":    prod,
        "origen":  "0",
        "destino": "DFCDN",
        "del":     str(fecha.day).zfill(2),
        "al":      str(fecha.day).zfill(2),
        "mes":     str(fecha.month).zfill(2),
        "anio":    str(fecha.year),
        "RegPag":  "25",
    }
    try:
        r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        r.encoding = "latin-1"
        return r.text
    except Exception as e:
        return None


def parsear_precios(html):
    """Extrae precios de la tabla HTML de SNIIM y calcula promedio."""
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    precios = []

    for tr in soup.find_all("tr"):
        celdas = tr.find_all("td", class_="Datos")
        if len(celdas) >= 6:
            precio_str = celdas[5].get_text(strip=True)
            try:
                precio = float(precio_str.replace("$", "").replace(",", "").strip())
                if precio > 0:
                    precios.append(precio)
            except:
                pass

    if not precios:
        return None

    return round(sum(precios) / len(precios), 2)


def ya_existe(tabla, fecha):
    """Verifica si ya tenemos datos de esa fecha en Supabase."""
    with engine.connect() as conn:
        result = conn.execute(sa.text(
            f"SELECT COUNT(*) FROM {tabla} WHERE fecha = :fecha"
        ), {"fecha": fecha}).scalar()
        return result > 0


def subir_precio(tabla, fecha, precio):
    """Inserta o actualiza un precio en Supabase."""
    with engine.begin() as conn:
        conn.execute(sa.text(f"""
            INSERT INTO {tabla} (fecha, precio_semana)
            VALUES (:fecha, :precio)
            ON CONFLICT (fecha) DO UPDATE SET
                precio_semana = EXCLUDED.precio_semana
        """), {"fecha": fecha, "precio": precio})


def main():
    n_semanas = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    semanas = get_semanas(n_semanas)

    print(f"\n🐔 Actualizando precios de pollo SNIIM — últimas {n_semanas} semanas\n")

    total = 0
    for prod, (tabla, nombre) in PRODUCTOS.items():
        print(f"  📌 {nombre} ({prod})...")
        actualizados = 0

        for fecha in semanas:
            if ya_existe(tabla, fecha):
                continue

            html = fetch_precio(fecha, prod)
            precio = parsear_precios(html)

            if precio:
                subir_precio(tabla, fecha, precio)
                actualizados += 1
                print(f"    → {fecha}: ${precio}")

            time.sleep(0.3)

        if actualizados > 0:
            print(f"    ✅ {actualizados} semanas actualizadas")
        else:
            print(f"    ℹ️  Ya está al día")

        total += actualizados

    print(f"\n🎉 Listo. Total: {total} registros actualizados en Supabase.")


if __name__ == "__main__":
    main()
