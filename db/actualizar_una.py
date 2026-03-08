"""
db/actualizar_una.py — Descarga y procesa el PDF semanal de la UNA automáticamente
No requiere descarga manual — Python busca el PDF más reciente solo.

Uso:
    python db/actualizar_una.py
"""
import re
import io
import requests
import pdfplumber
import sqlalchemy as sa
from datetime import datetime, timedelta

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    "feb": 2, "mar": 3, "abr": 4, "jun": 6, "jul": 7,
    "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


def generar_urls_candidatas():
    """Genera URLs de los últimos 14 días — el reporte sale cada miércoles."""
    urls = []
    hoy = datetime.today()
    for dias_atras in range(0, 14):
        fecha = hoy - timedelta(days=dias_atras)
        anio  = fecha.strftime("%Y")
        mes   = fecha.strftime("%m")
        fecha_corta = fecha.strftime("%y%m%d")
        url = (
            f"https://una.org.mx/wp-content/uploads/{anio}/{mes}/"
            f"Portal-Reporte-semanal-precios-Portal-UNA-{fecha_corta}.pdf"
        )
        urls.append((fecha, url))
    return urls


def descargar_pdf(url):
    """Intenta descargar el PDF. Retorna bytes o None si no existe."""
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and b"%PDF" in r.content[:10]:
            return r.content
    except Exception:
        pass
    return None


def ya_existe_en_supabase(fecha):
    """Verifica si ya tenemos datos de esa semana."""
    with engine.connect() as conn:
        result = conn.execute(sa.text(
            "SELECT COUNT(*) FROM pollo_vivo_una WHERE fecha = :fecha"
        ), {"fecha": fecha}).scalar()
        return result > 0


def extraer_fecha_pdf(texto):
    """Usa la fecha principal del reporte ej: '04 de Marzo de 2026'."""
    patron = r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})"
    m = re.search(patron, texto, re.IGNORECASE)
    if m:
        dia  = int(m.group(1))
        mes  = MESES.get(m.group(2).lower())
        anio = int(m.group(3))
        if mes:
            return datetime(anio, mes, dia).date()
    return None


def limpiar_numero(s):
    if not s or str(s).strip() in ["N/C", "N/D", "", "-", "nd"]:
        return None
    try:
        return float(str(s).replace(",", "").strip())
    except:
        return None


def extraer_datos(pdf_bytes):
    datos = {
        "fecha": None,
        "pollo_vivo_granja": None,
        "pollo_vivo_anden":  None,
        "rosticero":         None,
        "huevo_productor":   None,
    }

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        texto = ""
        for page in pdf.pages:
            texto += page.extract_text() or ""

        # ── Fecha principal del reporte ────────────────────────────────────
        datos["fecha"] = extraer_fecha_pdf(texto)

        # ── Andén y Rosticero — "Promedio Semanal : 32.45  38.69  39.84" ──
        m = re.search(r"Promedio Semanal\s*:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)", texto)
        if m:
            datos["pollo_vivo_anden"] = limpiar_numero(m.group(1))
            datos["rosticero"]        = limpiar_numero(m.group(3))

        # ── Granja — fila "Centro 30.51 ..." ──────────────────────────────
        mc = re.search(r"Centro\s+([\d.]+)", texto)
        if mc:
            datos["pollo_vivo_granja"] = limpiar_numero(mc.group(1))

        # ── Huevo al productor ─────────────────────────────────────────────
        # En el PDF hay dos secciones con "Sur": pollo y huevo
        # Buscamos la SEGUNDA aparición de Sur seguida de números solos en la línea siguiente
        surs = [m.start() for m in re.finditer(r"Sur", texto)]
        for pos in reversed(surs):  # de atrás hacia adelante
            fragmento = texto[pos:pos+200]
            mh = re.search(r"Sur[^\n]*\n([\d.]+)\s+[\d.]+\s+[\d.]+", fragmento)
            if mh:
                valor = limpiar_numero(mh.group(1))
                # El huevo al productor está entre 15 y 60 MXN/kg normalmente
                if valor and 10 < valor < 100:
                    datos["huevo_productor"] = valor
                    break

        # Fallback: buscar el promedio semanal de huevo directamente
        if not datos["huevo_productor"]:
            # Busca patrón: número entre 15-60 seguido de otros números en misma línea
            # justo antes de "Promedio Acumulado en el mes"
            mh2 = re.search(
                r"([\d.]+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s*\nPromedio Acumulado en el mes",
                texto
            )
            if mh2:
                datos["huevo_productor"] = limpiar_numero(mh2.group(1))

    return datos


def subir_a_supabase(datos):
    fecha = datos["fecha"]
    if not fecha:
        print("  ⚠️  No se pudo extraer la fecha del PDF.")
        return False

    print(f"  📋 Datos extraídos:")
    print(f"     Fecha:              {fecha}")
    print(f"     Pollo vivo granja:  {datos['pollo_vivo_granja']} MXN/kg")
    print(f"     Pollo vivo andén:   {datos['pollo_vivo_anden']} MXN/kg")
    print(f"     Rosticero:          {datos['rosticero']} MXN/kg")
    print(f"     Huevo al productor: {datos['huevo_productor']} MXN/kg")

    with engine.begin() as conn:
        conn.execute(sa.text("""
            INSERT INTO pollo_vivo_una (fecha, granja, anden, rosticero)
            VALUES (:fecha, :granja, :anden, :rosticero)
            ON CONFLICT (fecha) DO UPDATE SET
                granja    = EXCLUDED.granja,
                anden     = EXCLUDED.anden,
                rosticero = EXCLUDED.rosticero
        """), {
            "fecha":     fecha,
            "granja":    datos["pollo_vivo_granja"],
            "anden":     datos["pollo_vivo_anden"],
            "rosticero": datos["rosticero"],
        })

        if datos["huevo_productor"]:
            conn.execute(sa.text("""
                INSERT INTO huevo_una (fecha, precio_semana)
                VALUES (:fecha, :precio)
                ON CONFLICT (fecha) DO UPDATE SET
                    precio_semana = EXCLUDED.precio_semana
            """), {"fecha": fecha, "precio": datos["huevo_productor"]})

    print(f"  ✅ Datos de la semana {fecha} guardados en Supabase.")
    return True


def main():
    print(f"🔍 Buscando reporte semanal de la UNA — {datetime.today().strftime('%Y-%m-%d')}\n")

    for fecha_candidata, url in generar_urls_candidatas():
        print(f"  Probando: {url.split('/')[-1]} ...", end=" ", flush=True)
        pdf_bytes = descargar_pdf(url)
        if not pdf_bytes:
            print("no encontrado")
            continue

        print("✅ encontrado!")
        datos = extraer_datos(pdf_bytes)

        if datos["fecha"] and ya_existe_en_supabase(datos["fecha"]):
            print(f"  ℹ️  Ya tenemos datos del {datos['fecha']}. Nada que actualizar.")
            return

        subir_a_supabase(datos)
        return

    print("\n⏳ No hay reporte nuevo disponible todavía. Intenta más tarde.")


if __name__ == "__main__":
    main()
