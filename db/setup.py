"""
db/setup.py — Crea todas las tablas en Supabase
Corre UNA SOLA VEZ para inicializar la base de datos

Uso:
    python db/setup.py
"""
import sqlalchemy as sa

# ─── PON TU PASSWORD AQUÍ ─────────────────────────────────────────────────────
DB_URL = "postgresql://postgres.sasgprylblnrxbokfjdf:Agromonitor2026@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
# ─────────────────────────────────────────────────────────────────────────────

engine = sa.create_engine(DB_URL)

SQL = """
-- Tipo de cambio Banxico
CREATE TABLE IF NOT EXISTS tipo_cambio (
    fecha       DATE PRIMARY KEY,
    tc          FLOAT NOT NULL
);

-- Futuros Maíz CME
CREATE TABLE IF NOT EXISTS maiz_cme (
    fecha       DATE PRIMARY KEY,
    close       FLOAT NOT NULL,
    contrato    TEXT
);

-- Futuros Soya CME
CREATE TABLE IF NOT EXISTS soya_cme (
    fecha       DATE PRIMARY KEY,
    close       FLOAT NOT NULL,
    contrato    TEXT
);

-- Pasta de Soya CME
CREATE TABLE IF NOT EXISTS pasta_soya_cme (
    fecha       DATE PRIMARY KEY,
    close       FLOAT NOT NULL,
    contrato    TEXT
);

-- Pollo entero SNIIM
CREATE TABLE IF NOT EXISTS pollo_entero_sniim (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Pechuga Mercado San Juan
CREATE TABLE IF NOT EXISTS pechuga_sanjuan (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Pierna-Muslo Mercado San Juan
CREATE TABLE IF NOT EXISTS pierna_muslo_sanjuan (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Vísceras Mercado San Juan
CREATE TABLE IF NOT EXISTS visceras_sanjuan (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Retazo Mercado San Juan
CREATE TABLE IF NOT EXISTS retazo_sanjuan (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Pollo vivo (granja, andén, rosticero) UNA
CREATE TABLE IF NOT EXISTS pollo_vivo_una (
    fecha           DATE PRIMARY KEY,
    granja          FLOAT,
    anden           FLOAT,
    rosticero       FLOAT
);

-- Huevo blanco UNA
CREATE TABLE IF NOT EXISTS huevo_una (
    fecha           DATE PRIMARY KEY,
    precio_semana   FLOAT NOT NULL
);

-- Huevo SNIIM (blanco y rojo)
CREATE TABLE IF NOT EXISTS huevo_sniim (
    fecha               DATE,
    producto            TEXT,
    presentacion        TEXT,
    precio_frecuente    FLOAT,
    precio_min          FLOAT,
    precio_max          FLOAT,
    precio_prom         FLOAT,
    PRIMARY KEY (fecha, producto, presentacion)
);

-- Precios pollo USDA EE.UU.
CREATE TABLE IF NOT EXISTS pollo_usda (
    report_date     DATE,
    item            TEXT,
    low_price       FLOAT,
    high_price      FLOAT,
    wtd_avg_price   FLOAT,
    volume          FLOAT,
    PRIMARY KEY (report_date, item)
);

-- Cold storage EE.UU.
CREATE TABLE IF NOT EXISTS cold_storage_usa (
    fecha       DATE PRIMARY KEY,
    stocks_lb   FLOAT
);
"""

with engine.connect() as conn:
    for stmt in SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(sa.text(stmt))
    conn.commit()

print("✅ Todas las tablas creadas en Supabase correctamente.")
