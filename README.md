# Fixy Data — Dashboard Ejecutivo

Dashboard auto-publicable en GitHub Pages que consolida los reportes de operación, comercial y finanzas de Fixy 2026.

**URL pública:** https://javierbartaburu-dotcom.github.io/datafixy/

**Repositorio:** https://github.com/javierbartaburu-dotcom/datafixy

---

## ¿Qué contiene?

`index.html` — dashboard completo, self-contained, basado en Chart.js (CDN). 8 secciones:

1. **Resumen ejecutivo** — KPIs YTD con tendencia y sparklines.
2. **Operación** — SLA, estados, visitas y días.
3. **Calidad** — buckets de tiempo y umbral de distribuidores.
4. **Comercial** — top clientes, sucursales y churn.
5. **Zonas y servicios** — heatmap por sub-zona × mes.
6. **Finanzas** — P&L Real 2026 a Abril, ingresos.
7. **Discrepancias** — cruce de fuentes con explicación.
8. **Glosario**.

`data.json` — datos consolidados que alimentan el dashboard (queda en el repo por trazabilidad, pero el `index.html` ya los embebe).

---

## Cómo actualizarlo cuando cambien los datos

Cada mes (o cuando se agreguen archivos nuevos a la carpeta de trabajo) se regenera ejecutando:

```bash
python update_dashboard.py
```

Este script:

1. Lee las fuentes desde `~/Escritorio/Base para dashboard offline/` (consulta_guias, SLA mensuales, P&L Real, Tablero).
2. Recalcula todos los KPIs y agregaciones (volumen, SLA, visitas, días, distribuidores, clientes, zonas).
3. Reescribe `index.html` y `data.json` con la información nueva.

Una vez regenerado, se publica al repo:

```bash
git add index.html data.json
git commit -m "Update dashboard — cierre <mes/año>"
git push
```

GitHub Pages refresca el sitio en 30–60 segundos.

---

## Setup inicial del repositorio (una sola vez)

1. Crear el repositorio `datafixy` en GitHub (o usar el existente).
2. Activar GitHub Pages: **Settings → Pages → Source: main branch (root)**.
3. Subir los archivos:

   ```bash
   git clone https://github.com/javierbartaburu-dotcom/datafixy.git
   cd datafixy
   # copiar acá los archivos: index.html, data.json, README.md, update_dashboard.py
   git add .
   git commit -m "Initial dashboard"
   git push
   ```

4. Esperar 1-2 minutos y abrir https://javierbartaburu-dotcom.github.io/datafixy/.

---

## Requisitos para ejecutar `update_dashboard.py`

```bash
pip install pandas openpyxl python-docx matplotlib --break-system-packages
```

(No requiere instalación adicional: el HTML usa Chart.js desde CDN.)

---

## Fuentes leídas

El script asume esta estructura en `~/Escritorio/Base para dashboard offline/`:

```
Base para dashboard offline/
├── Tablero Fixy 2026.xlsx
├── FACTURACION 2026 19.05.26.xlsx
├── Fulfillment 2026 (2).xlsx
├── P&L_FIXY_2026_REAL.xlsx
├── Base de guías procesadas/
│   ├── consulta_guias - 01.2026.xls
│   ├── consulta_guias 02.2026.xls
│   └── ...
└── Reportes SLA 2026/
    ├── export_sla_enero 2026.csv
    ├── export_sla_febrero 2026.csv
    └── ...
```

Si alguno de los archivos no está, el script lo informa y continúa con los disponibles.

---

## Notas

- **SLA**: definición vigente = Entregadas / Total guías. La definición anterior (incluyendo devoluciones con cobro) se muestra como referencia para comparación.
- **Datos al corte**: 22 de Mayo de 2026. Las cifras de Mayo son parciales y están etiquetadas como "Mayo*" en todas las visualizaciones.
- **Privacidad**: el repositorio está pensado para uso interno. Si se hace público, revisar `data.json` (no contiene datos sensibles a nivel guía, solo agregados).

---

_Documento generado automáticamente._
