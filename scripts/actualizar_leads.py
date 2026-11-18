#!/usr/bin/env python3
"""Actualiza los datos de leads (const RAW) del dashboard Canal Digital desde la consulta de Metabase de DARWIN.

Entrada: el Excel "DARWIN - metabase" (hoja "Consulta") o un CSV con las mismas columnas.
Salida: reescribe la línea `const RAW = ...` de index.html y las fechas de "snapshot".
No guarda nombres ni teléfonos: el teléfono se reemplaza por un código irreversible (solo sirve para unir
las conversaciones repetidas de la misma persona).

Uso:  python3 scripts/actualizar_leads.py RUTA_EXCEL_O_CSV [index.html]
"""
import csv, datetime as DT, hashlib, json, os, re, sys

EXCLUIR = {'Atención al cliente', 'NO USAR', 'Formulario Estandar', 'Orquestrador', ''}
ETAPA = {'1. Saludo y captura de datos': 'e1', '1. Saludo y captura de datos 2': 'e1',
         '(META) 1. Saludo y captura de datos': 'e1', '2. Intencion de compra': 'e2',
         '3. Ticket del vehiculo': 'e3', '4. Presentacion del plan': 'e4', '5. Calificados': 'e5',
         '6. Seguimiento': 'e6', '7. Visita': 'e7', '8. Cita cierre': 'e8',
         'Escalated': 'esc', 'Escalation': 'esc'}
ZONA = {'Lima': ['Alese Norte', 'Alese Sur', 'Lima Centro', 'Lima Centro PC', 'Lima Norte 1', 'Lima Norte 1 PC',
                 'Lima Norte 2', 'Lima Norte 2 PC', 'Lima Norte 3', 'Lima Norte 3 PC', 'Lima Sur 1', 'Lima Sur 1 PC',
                 'Lima Sur 2', 'Lima Sur 2 PC', 'Lima LinkTower'],
        'Norte': ['Norte Chico', 'Piura', 'Piura PC', 'Chimbote', 'Chimbote PC', 'Trujillo', 'Trujillo PC',
                  'Chiclayo', 'Chiclayo PC', 'Cajamarca', 'Cajamarca PC', 'Huaraz', 'Huaraz PC'],
        'Sur': ['Cusco', 'Cusco PC', 'Arequipa 1', 'Arequipa 1 PC', 'Arequipa 2', 'Arequipa 2 PC', 'Juliaca',
                'Jualiaca PC', 'Tacna', 'Tacna PC', 'Moquegua', 'Moquegua PC', 'Hub Arequipa'],
        'Centro': ['Huancayo', 'Huancayo PC', 'Huanuco', 'Huanuco PC', 'Iquitos', 'Tarapoto', 'Pucallpa', 'Pucallpa PC'],
        'Sur Chico': ['Ica', 'ICA PC']}
ZONA_DE = {p: z for z, ps in ZONA.items() for p in ps}
REGIONES_CON_HUB = ['Ancash', 'Arequipa', 'Cajamarca', 'Callao', 'Cusco', 'Huanuco', 'Ica', 'Junin', 'La Libertad',
                    'Lambayeque', 'Lima', 'Loreto', 'Moquegua', 'Piura', 'Puno', 'San Martin', 'Tacna', 'Ucayali']
SAL = os.environ.get('LEADS_SALT', 'autoplan-dsh-prueba')

def pipeline(p):
    p = (p or '').strip()
    if re.match(r'^Link Tower \d+$', p): return 'Lima LinkTower'
    if p.startswith('Hub Arequipa'): return 'Hub Arequipa'
    return p

def fecha(v):
    if v in (None, ''): return None
    if isinstance(v, DT.datetime): return v
    s = re.sub(r'(Z|[+-]\d{2}:?\d{2})$', '', str(v).strip().replace('T', ' '))
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'):
        try: return DT.datetime.strptime(s[:26], fmt)
        except ValueError: pass
    raise ValueError(f'Fecha no reconocida: {v!r}')

def dia(v): return v.strftime('%Y-%m-%d') if v else None
def txt(v): return (str(v).strip() if v not in (None, '') else None) or None

def leer(ruta):
    if ruta.lower().endswith(('.xlsx', '.xlsm')):
        import openpyxl
        wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
        ws = wb['Consulta'] if 'Consulta' in wb.sheetnames else wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        H = [str(h).strip() if h else '' for h in next(it)]
        return [dict(zip(H, r)) for r in it if r and r[0] not in (None, '')]
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        return [r for r in csv.DictReader(f) if r.get('ID_SESION')]

def construir(filas):
    for r in filas:
        r['_f'] = fecha(r.get('FECHA_PRIMER_MSG_CHAT'))
    snap = max(r['_f'] for r in filas if r['_f'])
    primera = {}
    for r in filas:
        t = txt(r.get('TELEFONO_CLIENTE'))
        if t and r['_f'] and (t not in primera or r['_f'] < primera[t]): primera[t] = r['_f']
    leads = []
    for r in filas:
        c = pipeline(r.get('PIPELINE'))
        if c in EXCLUIR or not r['_f']: continue
        der, hr = fecha(r.get('FECHA_DERIVACION_A_HUMANO')), fecha(r.get('FECHA_PRIMERA_RESPUESTA_HUMANA'))
        ci, ua = fecha(r.get('FECHA_CIERRE_CHAT')), fecha(r.get('FECHA_ULTIMO_MSG_IA'))
        f0, tel = r['_f'], txt(r.get('TELEFONO_CLIENTE'))
        l = {'id': int(float(r['ID_SESION'])), 'c': c, 'z': ZONA_DE.get(c, 'Otros'),
             'g': txt(r.get('ULTIMO_ASIGNADO_POR_IA')) or '(Sin asignar)', 'r': txt(r.get('SMART_REGION')),
             'd': txt(r.get('SMART_DISTRITO_METRO')) or txt(r.get('SMART_DISTRITO')), 'm': txt(r.get('SMART_MARCA')),
             's': ETAPA.get(txt(r.get('ETAPA_ACTUAL')) or ''), 'f': dia(f0),
             'ri': round((hr - der).total_seconds() / 60, 1) if hr and der else None,
             'cp': round((ci - hr).total_seconds() / 60, 1) if hr and ci else None,
             'dm': round((hr - f0).total_seconds() / 86400, 2) if hr else None,
             'mh': hr.strftime('%Y-%m') if hr else None}
        if der:
            l['dd'] = dia(der); l['dv'] = round((snap - der).total_seconds() / 86400, 2)
        l['cl'] = 1 if ci else 0
        if hr: l['hc'] = dia(hr)
        if ua: l['ua'] = dia(ua)
        l['so'] = txt(r.get('SOURCE'))
        l['p'] = ('h' + hashlib.sha256((SAL + tel).encode()).hexdigest()[:12]) if tel else None
        l['pf'] = dia(primera.get(tel)) if tel else l['f']
        leads.append(l)
    leads.sort(key=lambda l: l['f'], reverse=True)
    fs = [l['f'] for l in leads]
    return {'LEADS': leads, 'meses': sorted({f[:7] for f in fs}), 'gestores': sorted({l['g'] for l in leads}),
            'ciudades': sorted({l['c'] for l in leads}), 'regiones': sorted({l['r'] for l in leads if l['r']}),
            'regions_with_hub': REGIONES_CON_HUB, 'fecha_min': min(fs), 'fecha_max': max(fs),
            'snapshot': snap.strftime('%Y-%m-%d %H:%M')}, snap

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    ruta, html = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'index.html')
    filas = leer(ruta)
    if not filas: sys.exit('El archivo no tiene filas.')
    faltan = {'ID_SESION', 'PIPELINE', 'ETAPA_ACTUAL', 'FECHA_PRIMER_MSG_CHAT'} - set(filas[0])
    if faltan: sys.exit(f'Faltan columnas: {sorted(faltan)}')
    raw, snap = construir(filas)
    with open(html, encoding='utf-8') as f: lineas = f.read().split('\n')
    i = next(k for k, l in enumerate(lineas) if l.startswith('const RAW = '))
    lineas[i] = 'const RAW = ' + json.dumps(raw, ensure_ascii=False, separators=(',', ':')) + ';'
    s = '\n'.join(lineas)
    s = re.sub(r'snapshot( al)? \d{2}/\d{2}/\d{4} \d{2}:\d{2}', lambda m: 'snapshot' + (m.group(1) or '') + ' ' + snap.strftime('%d/%m/%Y %H:%M'), s)
    with open(html, 'w', encoding='utf-8') as f: f.write(s)
    print(f"OK: {len(raw['LEADS'])} leads ({raw['fecha_min']} a {raw['fecha_max']}), snapshot {raw['snapshot']}")

if __name__ == '__main__':
    main()
