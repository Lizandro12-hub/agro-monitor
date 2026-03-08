"""
db/actualizar_sniim_huevo.py — Descarga precios de huevo del SNIIM y los sube a Supabase

Scraping equivalente a la función Power Query original.
Descarga huevo blanco y rojo para el mes/año indicado.

Uso:
    python db/actualizar_sniim_huevo.py              # mes actual
    python db/actualizar_sniim_huevo.py 2026 2        # febrero 2026
"""
import sys
import time
import requests
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from bs4 import BeautifulSoup

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)

BASE_URL = "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp"

PRODUCTOS = {
    "0": "Huevo Blanco y Rojo",
    "1": "Huevo Blanco",
    "2": "Huevo Rojo",
}

DESTINO  = "100"   # Central de Abasto de Iztapalapa D.F.
REG_PAG  = "100"


def get_page(anio, mes, sem, pag, prod):
    """Descarga una página de resultados de SNIIM."""
    params = {
        "RegPag":  REG_PAG,
        "al":      "",
        "del":     "",
        "anio":    str(anio),
        "mes":     str(mes).zfill(2),
        "sem":     str(sem),
        "pag":     str(pag),
        "prod":    prod,
        "destino": DESTINO,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.economia-sniim.gob.mx/SNIIM-Pecuarios-Nacionales/e_Hue.asp",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9",
        "Cookie": "_ga=GA1.3.1595028401.1769446871; _ga_N4181LDPL7=GS2.3.s1772490517$o5$g0$t1772490517$j60$l0$h0; ASPSESSIONIDQAABRRTB=MGCGOMABLNMCPILNHEIPCMBI; ASPSESSIONIDSADAQQTA=CPNBAEOAKLGJCBCFBFHGACHF",
    }
    try:
        r = requests.get(BASE_URL, params=params, headers=headers, timeout=15)
        r.encoding = "latin-1"
        return r.text
    except Exception as e:
        print(f"    ⚠️  Error al descargar pág {pag} sem {sem}: {e}")
        return None


def parsear_tabla(html):
    """Extrae la tabla de precios del HTML de SNIIM."""
    if not html:
        return pd.DataFrame()
    soup = BeautifulSoup(html, "html.parser")

    def to_num(s):
        try:
            return float(str(s).replace(",", "").replace("$", "").strip())
        except:
            return None

    def to_date(s):
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                return datetime.strptime(str(s).strip(), fmt).date()
            except:
                pass
        return None

    # Buscar filas con clase "Datos" — así viene la data en SNIIM
    filas = []
    for tr in soup.find_all("tr"):
        celdas = tr.find_all("td", class_="Datos")
        if len(celdas) >= 5:
            filas.append({
                "Fecha":          to_date(celdas[0].get_text(strip=True)),
                "Producto":       celdas[1].get_text(strip=True),
                "Presentacion":   celdas[2].get_text(strip=True),
                "PrecioFrecuente": to_num(celdas[3].get_text(strip=True)),
                "PrecioMin":      to_num(celdas[4].get_text(strip=True)),
                "PrecioMax":      to_num(celdas[5].get_text(strip=True)) if len(celdas) > 5 else None,
            })

    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas)
    df = df[df["Fecha"].notna()].copy()
    return df


def descargar_producto(anio, mes, prod, nombre):
    """Descarga todos los datos de un producto para el mes dado."""
    print(f"  📌 {nombre} ({prod}) — {mes:02d}/{anio}")
    frames = []

    for sem in range(1, 6):
        for pag in range(1, 6):
            html = get_page(anio, mes, sem, pag, prod)
            df = parsear_tabla(html)
            if df.empty:
                break  # No hay más páginas para esta semana
            frames.append(df)
            time.sleep(0.3)  # Respetar el servidor de SNIIM

    if not frames:
        print(f"    ⚠️  Sin datos para {nombre} {mes:02d}/{anio}")
        return pd.DataFrame()

    resultado = pd.concat(frames).drop_duplicates()
    print(f"    → {len(resultado)} filas encontradas")
    return resultado


def subir_a_supabase(df):
    """Sube el DataFrame de huevo SNIIM a Supabase."""
    if df.empty:
        return

    cols_necesarias = ["fecha", "producto", "presentacion",
                        "precio_frecuente", "precio_min", "precio_max"]

    # Renombrar columnas
    df = df.rename(columns={
        "Fecha": "fecha",
        "Producto": "producto",
        "Presentacion": "presentacion",
        "PrecioFrecuente": "precio_frecuente",
        "PrecioMin": "precio_min",
        "PrecioMax": "precio_max",
    })

    # Agregar precio_prom si no existe
    if "precio_prom" not in df.columns:
        df["precio_prom"] = df[["precio_frecuente", "precio_min", "precio_max"]].mean(axis=1)

    df = df[["fecha", "producto", "presentacion",
             "precio_frecuente", "precio_min", "precio_max", "precio_prom"]].copy()
    df = df.dropna(subset=["fecha"])

    insertados = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(sa.text("""
                    INSERT INTO huevo_sniim
                        (fecha, producto, presentacion, precio_frecuente, precio_min, precio_max, precio_prom)
                    VALUES
                        (:fecha, :producto, :presentacion, :precio_frecuente, :precio_min, :precio_max, :precio_prom)
                    ON CONFLICT (fecha, producto, presentacion) DO UPDATE SET
                        precio_frecuente = EXCLUDED.precio_frecuente,
                        precio_min       = EXCLUDED.precio_min,
                        precio_max       = EXCLUDED.precio_max,
                        precio_prom      = EXCLUDED.precio_prom
                """), row.to_dict())
                insertados += 1
            except Exception as e:
                print(f"    ❌ Error: {e}")

    print(f"    ✅ {insertados} filas subidas a Supabase")


def main():
    hoy = datetime.today()

    # Parámetros opcionales: año y mes
    if len(sys.argv) >= 3:
        anio = int(sys.argv[1])
        mes  = int(sys.argv[2])
    else:
        anio = hoy.year
        mes  = hoy.month

    print(f"\n🥚 Actualizando Huevo SNIIM — {mes:02d}/{anio}\n")

    todos = []
    for prod, nombre in PRODUCTOS.items():
        df = descargar_producto(anio, mes, prod, nombre)
        todos.append(df)

    df_total = pd.concat(todos) if todos else pd.DataFrame()
    df_total = df_total.drop_duplicates()

    print(f"\n📊 Total: {len(df_total)} filas descargadas")
    subir_a_supabase(df_total)

    # También descargar el mes anterior si estamos en los primeros 7 días
    if hoy.day <= 7 and mes > 1:
        mes_ant = mes - 1
        print(f"\n📅 También actualizando mes anterior ({mes_ant:02d}/{anio})...")
        todos_ant = []
        for prod, nombre in PRODUCTOS.items():
            df = descargar_producto(anio, mes_ant, prod, nombre)
            todos_ant.append(df)
        df_ant = pd.concat(todos_ant) if todos_ant else pd.DataFrame()
        subir_a_supabase(df_ant)

    print(f"\n🎉 Huevo SNIIM actualizado correctamente.")


if __name__ == "__main__":
    main()
