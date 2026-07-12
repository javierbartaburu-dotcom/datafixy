---
name: tablero-fixy-quincenal
description: Regenera el tablero de control Fixy (Ops y Comercial) cada quincena a partir de los archivos fuente.
---

Regenerá el tablero de control de Operaciones y Negocio de Fixy con los datos más recientes. Es una corrida quincenal automática.

PASOS:
1. Trabajá en la carpeta del proyecto: "C:\Users\javier.bartaburu_fix\OneDrive\Documentos\Claude\Projects\TABLERO DE CONTROL NEGOCIO FIXY ARGENTINA". El script de cálculo es `generar_tablero_fixy.py` y usa los archivos de "Base para dashboard offline" (Base de guías procesadas, Reportes SLA 2026, FACTURACION 2026 *.xlsx, Fulfillment 2026 *.xlsx).
2. Detectá los archivos de mes MÁS reciente disponibles en esas carpetas (puede haber un mes nuevo o el mes en curso actualizado). Si el nombre del archivo de FACTURACION cambió (trae fecha), usá el más nuevo.
3. Recalculá los KPIs aplicando los CRITERIOS CONFIRMADOS (no los cambies):
   - Guía procesada = excluye canceladas (CANC), anuladas (ANULADO), dev-rendición (RG) y RETIROS (servicio RETIRO / SPDR / NRET). Los retiros se reportan aparte.
   - POD = solo estado POD-ENTREGADA (Agente Postal NO cuenta).
   - SLA General = POD / procesadas. COD = POD sobre contrarrembolso>0. Anticipado = POD sobre contrarrembolso=0.
   - Semáforos: SLA General/COD verde ≥60, amarillo 50-60, rojo <50. Anticipado verde ≥95, amarillo 90-94,99, rojo <90.
   - Tercerizados (Andreani + JN) se analizan aparte de la flota propia.
   - FAR / 2ª / 3ª visita salen de los Reportes SLA (estado "(POD) - ENTREGADA").
   - Facturación y envíos oficiales + objetivo salen del archivo FACTURACION (hoja del año). Fulfillment: notas de pedido (hoja MATRIZ) y facturación (hoja FACTURACION, columna TOTAL SEMANAL por mes).
   - IMPORTANTE: el mes en curso subestima el SLA (guías en tránsito); marcalo como "en curso, no comparable".
4. Preferí ejecutar `python generar_tablero_fixy.py` (regenera Tablero_Fixy_Datos.xlsx y datos_tablero.json). Si por límites de tiempo no procesa todos los meses de una, procesá al menos el mes en curso y el anterior, y recalculá los datos que alimentan Tablero_Fixy_Datos.xlsx.
5. Actualizá también el dashboard visual `MAQUETADO_Tablero_Ops_Comercial.html` con los valores nuevos (KPIs madre, evolutivos, tabla de variación, tops de clientes, logística inversa, fulfillment).
6. Al terminar, dejá los archivos en la carpeta del proyecto y escribí un resumen ejecutivo BREVE (5-8 líneas) con: SLA general/COD/anticipado del último mes y su variación vs mes anterior, avance del objetivo de envíos y facturación, y 1-2 alertas (por ejemplo caída de SLA, cliente con salto de devoluciones, distribuidor con robos, o desvío del objetivo). Presentá el Excel y el HTML actualizados.

Mantené el branding Fixy (logo color, paleta teal/navy/amarillo) y el orden storytelling del tablero.