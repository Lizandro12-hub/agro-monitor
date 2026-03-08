# 🌿 Agro Monitor UDLAP — Sector Avícola

Monitor de precios agrícolas tipo Infosel para el sector avícola mexicano.

---

## ⚡ Instalación rápida

```bash
# 1. Clonar / descomprimir el proyecto
cd agro_monitor

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Asegurarse de que el Excel esté en data/
#    → data/precios_.xlsx

# 4. Correr la app
python app.py

# 5. Abrir en el navegador
#    http://localhost:8050
```

---

## 🗂️ Estructura del proyecto

```
agro_monitor/
│
├── app.py                  ← App principal + navbar + routing
├── requirements.txt
│
├── data/
│   ├── precios_.xlsx       ← Excel con todas las series de datos
│   └── loader.py           ← Funciones de carga y limpieza de datos
│
├── pages/
│   ├── dashboard.py        ← Pantalla principal (home)
│   ├── monitor_pollo.py    ← Monitor de Pollo detallado
│   ├── monitor_insumos.py  ← Maíz, Soya, TC, Pasta de Soya
│   ├── indicadores_macro.py  ← (próxima página)
│   ├── resumen_ejecutivo.py  ← (próxima página)
│   ├── mercado.py            ← (próxima página)
│   └── escenarios.py         ← (próxima página)
│
├── components/
│   └── charts.py           ← Gráficas reutilizables (sparkline, line, area, etc.)
│
└── assets/
    └── style.css           ← Estilos globales (fondo oscuro, dorado UDLAP)
```

---

## 📊 Páginas disponibles

| Ruta | Descripción |
|---|---|
| `/` | Dashboard principal — resumen de todos los módulos |
| `/monitor-pollo` | Precios pollo MX (SNIIM, San Juan) y EE.UU. (USDA) |
| `/monitor-insumos` | Maíz, Soya, Pasta de Soya, Tipo de Cambio |
| `/indicadores-macro` | TC, Banxico, Inflación, Petróleo *(próxima)* |
| `/resumen-ejecutivo` | Tabla de variables + semáforo de riesgo *(próxima)* |
| `/mercado` | Noticias y drivers del mercado *(próxima)* |
| `/escenarios` | Pronóstico alcista/base/bajista *(próxima)* |

---

## 🔧 Agregar nuevas fuentes de datos

En `data/loader.py` agrega una función nueva siguiendo el patrón:

```python
def get_mi_serie() -> pd.DataFrame:
    df = _read("nombre_hoja_excel")
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df.dropna(subset=["Fecha"]).sort_values("Fecha")
```

---

## 🚀 Deploy en producción

```bash
# Con gunicorn (Railway, Render, Heroku)
gunicorn app:server -b 0.0.0.0:8050
```

---

## 📌 Próximas funcionalidades sugeridas

- [ ] Actualización automática de datos (scheduler APScheduler o cron)
- [ ] Módulo de alertas por email/WhatsApp cuando precio cruza umbral
- [ ] Descarga de informe semanal en PDF
- [ ] Módulo de escenarios con modelo de pronóstico (Prophet / ARIMA)
- [ ] Login para acceso controlado
