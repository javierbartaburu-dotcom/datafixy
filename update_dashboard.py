#!/usr/bin/env python3
"""
Fixy Data — Update script v3

Regenera index.html y data.json del dashboard a partir de las fuentes
en `~/Escritorio/Base para dashboard offline/`.

KPIs principales calculados:
  - % Entregadas guías COD=0 (sin contrarreembolso) por mes y YTD
  - % Entregadas guías COD>0 por mes y YTD
  - % Cumplimiento de objetivo vs target +70% YoY (sobre volumen 2025)
  - Entrega por número de visita (1ra/2da/3ra) con cantidad mes a mes
  - Vista comercial filtrando Vistage y Renata Arg Logística

Uso:
    python update_dashboard.py
Luego:
    git add . && git commit -m "Update" && git push

Publicado en https://javierbartaburu-dotcom.github.io/datafixy/
"""
import os, sys, json, re, csv, collections
from datetime import datetime

# ============ Config ============
HOME = os.path.expanduser("~")
DEFAULT_BASE = os.path.join(HOME, "OneDrive", "Escritorio", "Base para dashboard offline")
if not os.path.isdir(DEFAULT_BASE):
    DEFAULT_BASE = os.path.join(HOME, "Escritorio", "Base para dashboard offline")
BASE = os.environ.get("FIXY_DATA_DIR", DEFAULT_BASE)
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

print(f"Fixy Data — Update v3")
print(f"Fuente: {BASE}")
print(f"Salida: {DASHBOARD_DIR}\n")

if not os.path.isdir(BASE):
    print(f"ERROR: no se encuentra la carpeta de datos {BASE}")
    sys.exit(1)

csv.field_size_limit(10_000_000)

SLA_DIR = os.path.join(BASE, "Reportes SLA 2026")
GUIAS_DIR = os.path.join(BASE, "Base de guías procesadas")
TABLERO_2025 = {1:24606,2:16649,3:17328,4:20604,5:24525,6:27649,7:40948,8:26637,9:29626,10:27295,11:29863,12:38113}
DIAS_MES = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
DIAS_PARCIAL_DEFAULT = 22  # mayo parcial; override por archivo si "parcial" detecta
EXCLUIR_RE = re.compile(r'\b(vistage|renata)\b', re.I)

MESES_NUM = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,
             'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,
             'noviembre':11,'diciembre':12}
MESES_NOM = {v:k.title() for k,v in MESES_NUM.items()}

def find_sla_files():
    out={}
    if not os.path.isdir(SLA_DIR): return out
    for f in os.listdir(SLA_DIR):
        if not f.lower().endswith('.csv') or not f.lower().startswith('export_sla'): continue
        for nombre, num in MESES_NUM.items():
            if nombre in f.lower():
                out[num] = (f, ('Mayo*' if 'parcial' in f.lower() else MESES_NOM[num]), 'parcial' in f.lower())
                break
    return out

def find_guia_files():
    out={}
    if not os.path.isdir(GUIAS_DIR): return out
    for f in os.listdir(GUIAS_DIR):
        if not f.lower().endswith('.xls'): continue
        m = re.search(r'(0[1-9]|1[0-2])\.2026', f)
        if m: out[int(m.group(1))] = f
    return out

SLA_FILES = find_sla_files()
GUIA_FILES = find_guia_files()
MESES = sorted(SLA_FILES.keys())
NOMBRES = [SLA_FILES[m][1] for m in MESES]
print(f"SLA: {MESES}")
print(f"Guias: {sorted(GUIA_FILES.keys())}\n")
if not MESES:
    print("ERROR: sin SLA"); sys.exit(1)

def pf(s):
    if not s: return 0.0
    s = str(s).strip().strip('"').replace(",",".")
    if not s: return 0.0
    try: return float(s)
    except: return 0.0

def pct(sl,q):
    if not sl: return 0
    k=(len(sl)-1)*q; f=int(k); c=min(f+1,len(sl)-1)
    return sl[f] if f==c else sl[f]+(sl[c]-sl[f])*(k-f)

def is_entregada(estado):
    e=(estado or '').upper()
    return 'ENTREGADA' in e or e.startswith('POD')

# ============ SLA processing ============
print("Procesando SLA...")
month_sla = {}
clientes_m = collections.defaultdict(collections.Counter)
sucursales_m = collections.defaultdict(collections.Counter)
zonas_m = collections.defaultdict(collections.Counter)
servicios_m = collections.defaultdict(collections.Counter)

for mes_n in MESES:
    fname, mes_nombre, _ = SLA_FILES[mes_n]
    path = os.path.join(SLA_DIR, fname)
    with open(path,encoding='utf-8',errors='ignore') as fh: first=fh.readline()
    delim = '|' if '|' in first[:200] else ';'
    n=0; ne=0; ndc=0; ndrg=0; nel=0; nint=0; no=0
    nv1=nv2=nv3=0; nrep=0; nev1=nev2=nev3=nesv=0
    dias=[]; buckets=collections.Counter()
    with open(path,encoding='utf-8',errors='ignore',newline='') as fh:
        rdr = csv.reader(fh, delimiter=delim, quotechar='"')
        H = {h.strip().strip('"'): i for i,h in enumerate(next(rdr))}
        for row in rdr:
            if len(row) < max(H.values())+1: continue
            n+=1
            cliente=(row[H["CLIENTE"]] or "").strip().strip('"')
            sucursal=(row[H["SUCURSAL CLIENTE"]] or "").strip().strip('"')
            servicio=(row[H["SERVICIO"]] or "").strip().strip('"')
            grupo=(row[H["GRUPO"]] or "").strip().strip('"').upper()
            sub_dest=(row[H["SUB ZONA DESTINO"]] or "").strip().strip('"').upper() or "SIN ZONA"
            v1=bool((row[H["FECHA PRIMERA VISITA"]] or "").strip().strip('"'))
            v2=bool((row[H["FECHA SEGUNDA VISITA"]] or "").strip().strip('"'))
            v3=bool((row[H["FECHA TERCER VISITA"]] or "").strip().strip('"'))
            if v1: nv1+=1
            if v2: nv2+=1
            if v3: nv3+=1
            frep=(row[H["FECHA REPACTACION"]] or "").strip().strip('"')
            if frep and frep!="0": nrep+=1
            if "ENTREGADA" in grupo: ne+=1
            elif "DEVOLUCION CON COBRO" in grupo: ndc+=1
            elif "DEVOLUCION" in grupo and "RENDICION GENERADA" in grupo: ndrg+=1
            elif "ELIMINADO" in grupo: nel+=1
            elif "INTERIOR PAIS" in grupo: nint+=1
            else: no+=1
            if "ENTREGADA" in grupo:
                if v1 and not v2: nev1+=1
                elif v2 and not v3: nev2+=1
                elif v3: nev3+=1
                else: nesv+=1
            td = pf(row[H["TOTAL DIAS"]])
            if 0<=td<=365:
                dias.append(td)
                if td<=1: buckets["0-1"]+=1
                elif td<=3: buckets["1-3"]+=1
                elif td<=7: buckets["3-7"]+=1
                elif td<=14: buckets["7-14"]+=1
                elif td<=30: buckets["14-30"]+=1
                else: buckets["30+"]+=1
            zonas_m[mes_n][sub_dest]+=1
            servicios_m[mes_n][servicio]+=1
            if cliente: clientes_m[mes_n][cliente]+=1
            if cliente and sucursal: sucursales_m[mes_n][f"{cliente}||{sucursal}"]+=1
    dias.sort()
    et = nev1+nev2+nev3+nesv
    month_sla[mes_n] = dict(
        nombre=mes_nombre, total=n, entregadas=ne, dev_cobro=ndc, dev_rg=ndrg,
        eliminadas=nel, interior=nint, otro=no,
        v1=nv1, v2=nv2, v3=nv3, repactadas=nrep,
        ent_v1=nev1, ent_v2=nev2, ent_v3plus=nev3, ent_sin_visita=nesv,
        sla_correcto=ne/n if n else 0, sla_anterior=(ne+ndc)/n if n else 0,
        pct_1visita=nev1/et if et else 0,
        dias_avg=sum(dias)/len(dias) if dias else 0,
        dias_p50=pct(dias,0.5), dias_p90=pct(dias,0.9),
        dias_max=max(dias) if dias else 0, dias_buckets=dict(buckets),
    )
    print(f"  {mes_nombre}: N={n}, Ent={ne}, SLA={ne/n*100:.1f}%")

# ============ Consulta guias (COD + cumplimiento + filtrado comercial) ============
print("\nProcesando consulta_guias...")
month_cv = {}
clientes_filt_m = collections.defaultdict(collections.Counter)
top_dist_yt = collections.Counter()

for mes_n in MESES:
    if mes_n not in GUIA_FILES:
        month_cv[mes_n] = dict(total=0, entregadas=0, cod0_total=0, cod0_entregadas=0, codpos_total=0, codpos_entregadas=0,
                               filas=0, n_dist=0, importe_sum=0, contrareembolso_sum=0, n_excluidos=0)
        continue
    fn = GUIA_FILES[mes_n]
    path = os.path.join(GUIAS_DIR, fn)
    txt = open(path, encoding='utf-8', errors='ignore').read()
    rows = re.findall(r'<tr>(?!\s*<th)(.*?)</tr>', txt, re.S)
    n=0; ne=0; n_cod0=0; n_cod0_e=0; n_codp=0; n_codp_e=0
    n_filt_total=0; n_filt_ent=0; n_exclu=0
    dist_rec = collections.Counter()
    importe_sum=0; cr_sum=0
    for row in rows:
        cells = re.findall(r'<td>(.*?)</td>', row, re.S)
        if len(cells)<38: continue
        cells = [c.strip() for c in cells]
        estado = cells[4]; cliente=cells[2]; empresa=cells[18] if len(cells)>18 else ""
        importe = pf(cells[16] if len(cells)>16 else "")
        cr_val = pf(cells[37] if len(cells)>37 else "")
        n+=1
        es_e = is_entregada(estado)
        if es_e: ne+=1
        if cr_val==0:
            n_cod0+=1
            if es_e: n_cod0_e+=1
        else:
            n_codp+=1
            if es_e: n_codp_e+=1
        if len(cells)>25 and cells[25]: dist_rec[cells[25]]+=1
        importe_sum += importe
        if cr_val>0: cr_sum += cr_val
        # filtrado comercial
        cli_str = (cliente or '')+' '+(empresa or '')
        if EXCLUIR_RE.search(cli_str):
            n_exclu+=1
            continue
        n_filt_total+=1
        if es_e: n_filt_ent+=1
        if cliente: clientes_filt_m[mes_n][cliente]+=1
    target_2026 = TABLERO_2025.get(mes_n,0)*1.70
    _, _, parcial = SLA_FILES[mes_n]
    if parcial:
        target_prorrateado = target_2026 * DIAS_PARCIAL_DEFAULT / DIAS_MES[mes_n]
    else:
        target_prorrateado = target_2026
    month_cv[mes_n] = dict(
        total=n, entregadas=ne, sla_pct=ne/n if n else 0,
        cod0_total=n_cod0, cod0_entregadas=n_cod0_e, cod0_sla_pct=n_cod0_e/n_cod0 if n_cod0 else 0,
        codpos_total=n_codp, codpos_entregadas=n_codp_e, codpos_sla_pct=n_codp_e/n_codp if n_codp else 0,
        target_2026=target_2026, target_prorrateado=target_prorrateado,
        cumplimiento_pct=n/target_prorrateado if target_prorrateado else 0,
        filas=n, n_dist=len(dist_rec), importe_sum=importe_sum, contrareembolso_sum=cr_sum,
        n_excluidos=n_exclu, total_filtered=n_filt_total, entregadas_filtered=n_filt_ent,
    )
    for nombre,c in dist_rec.most_common(15): top_dist_yt[nombre]+=c
    print(f"  {SLA_FILES[mes_n][1]}: N={n}, COD=0 SLA={month_cv[mes_n]['cod0_sla_pct']*100:.1f}%, Cumpl={month_cv[mes_n]['cumplimiento_pct']*100:.1f}%")

# ============ P&L ============
pl = {'ventas_ytd_abr':0,'utilidad_bruta_ytd_abr':0,'ebitda_ytd_abr':0,'nopat_ytd_abr':0,
      'cv_sobre_ventas':0,'fijos_ytd_abr':0,'margen_ebitda':0,'margen_nopat':0,'margen_bruto':0}
pl_path = os.path.join(BASE,"P&L_FIXY_2026_REAL.xlsx")
if os.path.isfile(pl_path):
    try:
        import openpyxl
        wb=openpyxl.load_workbook(pl_path,read_only=True,data_only=True)
        ws=wb['Dashboard']
        rows=list(ws.iter_rows(values_only=True))
        pl['ventas_ytd_abr']=rows[6][2] or 0
        pl['utilidad_bruta_ytd_abr']=rows[6][5] or 0
        pl['ebitda_ytd_abr']=rows[6][8] or 0
        pl['nopat_ytd_abr']=rows[10][2] or 0
        pl['cv_sobre_ventas']=rows[10][8] or 0
        pl['fijos_ytd_abr']=rows[10][11] or 0
        wb.close()
        v=pl['ventas_ytd_abr'] or 1
        pl['margen_ebitda']=pl['ebitda_ytd_abr']/v
        pl['margen_nopat']=pl['nopat_ytd_abr']/v
        pl['margen_bruto']=pl['utilidad_bruta_ytd_abr']/v
    except Exception as e:
        print(f"  Error P&L: {e}")

# ============ Agregaciones ============
print("\nConsolidando...")
total_y_sla=sum(month_sla[m]['total'] for m in MESES)
ent_y_sla=sum(month_sla[m]['entregadas'] for m in MESES)
sla_y=ent_y_sla/total_y_sla if total_y_sla else 0
total_y_cv=sum(month_cv[m]['total'] for m in MESES)
cod0_y=sum(month_cv[m]['cod0_total'] for m in MESES)
cod0_ent_y=sum(month_cv[m]['cod0_entregadas'] for m in MESES)
codpos_y=sum(month_cv[m]['codpos_total'] for m in MESES)
codpos_ent_y=sum(month_cv[m]['codpos_entregadas'] for m in MESES)
target_y=sum(month_cv[m]['target_prorrateado'] for m in MESES)
cumpl_y=total_y_cv/target_y if target_y else 0
imp_y=sum(month_cv[m]['importe_sum'] for m in MESES)
cod_in_y=sum(month_cv[m]['contrareembolso_sum']*0.01 for m in MESES)
ev1y=sum(month_sla[m]['ent_v1'] for m in MESES)
evty=sum(month_sla[m]['ent_v1']+month_sla[m]['ent_v2']+month_sla[m]['ent_v3plus']+month_sla[m]['ent_sin_visita'] for m in MESES)

totC_filt=collections.Counter()
for m in MESES:
    for c,n in clientes_filt_m[m].items(): totC_filt[c]+=n
top15_filt = totC_filt.most_common(15)
serie_clientes = {c:[clientes_filt_m[m].get(c,0) for m in MESES] for c,_ in top15_filt}
sucC=collections.Counter()
for m in MESES:
    for cs,n in sucursales_m[m].items(): sucC[cs]+=n
zonas_total=collections.Counter()
zonas_ent_real=collections.defaultdict(float)
for m in MESES:
    prop=month_sla[m]['entregadas']/month_sla[m]['total'] if month_sla[m]['total'] else 0
    for z,c in zonas_m[m].items():
        zonas_total[z]+=c; zonas_ent_real[z]+=c*prop
top15_zonas=zonas_total.most_common(15)
top8z=[z for z,_ in zonas_total.most_common(8)]
heatmap=[{'zona':z,'data':[zonas_m[m].get(z,0) for m in MESES]} for z in top8z]
servC=collections.Counter()
for m in MESES:
    for s,c in servicios_m[m].items(): servC[s]+=c
top10_serv=servC.most_common(10)
serv_mes={s:[servicios_m[m].get(s,0) for m in MESES] for s,_ in top10_serv}
churn=[]
for i in range(len(MESES)-1):
    a,b=MESES[i],MESES[i+1]
    sA,sB=set(clientes_m[a].keys()),set(clientes_m[b].keys())
    churn.append({'from':NOMBRES[i],'to':NOMBRES[i+1],'continuan':len(sA&sB),'bajas':len(sA-sB),'altas':len(sB-sA)})

data = {
    'meses':NOMBRES,
    'volumen':[month_sla[m]['total'] for m in MESES],
    'volumen_courier':[month_cv[m]['total'] for m in MESES],
    'sla_correcto':[round(month_sla[m]['sla_correcto']*100,1) for m in MESES],
    'sla_anterior':[round(month_sla[m]['sla_anterior']*100,1) for m in MESES],
    'entregadas':[month_sla[m]['entregadas'] for m in MESES],
    'dev_cobro':[month_sla[m]['dev_cobro'] for m in MESES],
    'dev_rg':[month_sla[m]['dev_rg'] for m in MESES],
    'eliminadas':[month_sla[m]['eliminadas'] for m in MESES],
    'otro':[month_sla[m]['otro'] for m in MESES],
    'cod0_total':[month_cv[m]['cod0_total'] for m in MESES],
    'cod0_entregadas':[month_cv[m]['cod0_entregadas'] for m in MESES],
    'cod0_sla_pct':[round(month_cv[m]['cod0_sla_pct']*100,1) for m in MESES],
    'codpos_total':[month_cv[m]['codpos_total'] for m in MESES],
    'codpos_entregadas':[month_cv[m]['codpos_entregadas'] for m in MESES],
    'codpos_sla_pct':[round(month_cv[m]['codpos_sla_pct']*100,1) for m in MESES],
    'sla_total_courier':[round(month_cv[m]['sla_pct']*100,1) for m in MESES],
    'total_courier':[month_cv[m]['total'] for m in MESES],
    'target_2026':[round(month_cv[m]['target_2026']) for m in MESES],
    'target_prorrateado':[round(month_cv[m]['target_prorrateado']) for m in MESES],
    'cumplimiento_pct':[round(month_cv[m]['cumplimiento_pct']*100,1) for m in MESES],
    'ent_v1':[month_sla[m]['ent_v1'] for m in MESES],
    'ent_v2':[month_sla[m]['ent_v2'] for m in MESES],
    'ent_v3plus':[month_sla[m]['ent_v3plus'] for m in MESES],
    'ent_sin_v':[month_sla[m]['ent_sin_visita'] for m in MESES],
    'pct_v1':[round(month_sla[m]['pct_1visita']*100,1) for m in MESES],
    'dias_avg':[round(month_sla[m]['dias_avg'],2) for m in MESES],
    'dias_p50':[month_sla[m]['dias_p50'] for m in MESES],
    'dias_p90':[month_sla[m]['dias_p90'] for m in MESES],
    'dias_max':[month_sla[m]['dias_max'] for m in MESES],
    'dias_buckets':[month_sla[m]['dias_buckets'] for m in MESES],
    'repactadas':[month_sla[m]['repactadas'] for m in MESES],
    'repact_pct':[round(month_sla[m]['repactadas']/month_sla[m]['total']*100,1) for m in MESES],
    'distribuidores':[month_cv[m]['n_dist'] for m in MESES],
    'top_distribuidores':[{'n':n,'g':g} for n,g in top_dist_yt.most_common(10)],
    'importe_flete':[month_cv[m]['importe_sum'] for m in MESES],
    'ingreso_cod':[month_cv[m]['contrareembolso_sum']*0.01 for m in MESES],
    'top_clientes_filt':[{'cliente':c,'guias':v,'share':round(v/sum(totC_filt.values())*100,2),'serie':serie_clientes[c]} for c,v in top15_filt],
    'top_sucursales':[{'sucursal':cs.replace('||',' | '),'guias':v} for cs,v in sucC.most_common(15)],
    'top_zonas':[{'zona':z,'guias':v,'sla':round(zonas_ent_real[z]/v*100,1) if v else 0,'share':round(v/sum(zonas_total.values())*100,2)} for z,v in top15_zonas],
    'top_servicios':[{'servicio':s,'guias':v,'share':round(v/sum(servC.values())*100,2),'serie':serv_mes[s]} for s,v in top10_serv],
    'churn':churn,'heatmap':heatmap,
    'ytd_volumen':total_y_sla,'ytd_entregadas':ent_y_sla,'ytd_sla':round(sla_y*100,1),
    'ytd_cod0_sla':round(cod0_ent_y/cod0_y*100,1) if cod0_y else 0,
    'ytd_cod0_total':cod0_y,'ytd_cod0_ent':cod0_ent_y,
    'ytd_codpos_sla':round(codpos_ent_y/codpos_y*100,1) if codpos_y else 0,
    'ytd_codpos_total':codpos_y,
    'ytd_cumplimiento':round(cumpl_y*100,1),
    'ytd_target':round(target_y),'ytd_actual_courier':total_y_cv,
    'ytd_pct_v1':round(ev1y/evty*100,1) if evty else 0,
    'ytd_dias_avg':round(sum(month_sla[m]['dias_avg'] for m in MESES)/len(MESES),2),
    'ytd_repact_pct':round(sum(month_sla[m]['repactadas'] for m in MESES)/total_y_sla*100,1) if total_y_sla else 0,
    'ytd_ingreso_total':imp_y+cod_in_y, 'ytd_ingreso_flete':imp_y, 'ytd_ingreso_cod':cod_in_y,
    'ytd_ticket_promedio':(imp_y+cod_in_y)/total_y_sla if total_y_sla else 0,
    'n_excluidos_ytd':sum(month_cv[m]['n_excluidos'] for m in MESES),
    'pl':pl,
    'fecha_corte':datetime.now().strftime('%d de %B de %Y'),
    'fecha_generado':datetime.now().strftime('%Y-%m-%d %H:%M'),
    'github_url':'https://javierbartaburu-dotcom.github.io/datafixy/',
    'repo_url':'https://github.com/javierbartaburu-dotcom/datafixy',
}

DATA_JSON = json.dumps(data, ensure_ascii=False)
data_path = os.path.join(DASHBOARD_DIR, "data.json")
with open(data_path,'w',encoding='utf-8') as f: f.write(DATA_JSON)
print(f"\nOK data.json — {os.path.getsize(data_path)} bytes")

# Reescribir el bloque <script id="data"> dentro de index.html si existe
html_path = os.path.join(DASHBOARD_DIR, "index.html")
if os.path.isfile(html_path):
    txt = open(html_path, encoding='utf-8').read()
    new_txt = re.sub(
        r'(<script id="data" type="application/json">)[\s\S]*?(</script>)',
        lambda m: m.group(1)+'\n'+DATA_JSON+'\n'+m.group(2),
        txt, count=1
    )
    new_txt = re.sub(r'Última actualización: [0-9\- :]+', f'Última actualización: {data["fecha_generado"]}', new_txt)
    new_txt = re.sub(r'Datos al [^<]+<', f'Datos al {data["fecha_corte"]}<', new_txt)
    with open(html_path,'w',encoding='utf-8') as f: f.write(new_txt)
    print(f"OK index.html actualizado — {os.path.getsize(html_path)} bytes")

print("\nListo. Para publicar:")
print("  git add . && git commit -m 'Update dashboard' && git push")
print("\nSitio: https://javierbartaburu-dotcom.github.io/datafixy/")
