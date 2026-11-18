#!/usr/bin/env python3
"""Arma darwin/darwin.json a partir de las respuestas de Darwin guardadas en darwin/raw/*.txt.
Cada línea de los .txt es  etiqueta|conteo  (tal como Darwin devuelve label y count).
Uso: python3 darwin/build.py "2026-11-18 07:05"
"""
import json, os, re, sys
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'raw')

def leer(nombre):
    out = []
    with open(os.path.join(RAW, nombre), encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            k, v = ln.rsplit('|', 1)
            out.append((k.strip(), int(v)))
    return out

def bucket(etapa):
    s = etapa.lower()
    if 'escalat' in s:
        return 'esc'
    m = re.match(r'^(\d)\.', s)
    return 'e' + m.group(1) if m else 'otro'

BK = ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'esc', 'otro']

def main():
    corte = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M')
    nuevos = leer('nuevos_pipeline.txt')
    recon = leer('recon_pipeline.txt')
    dia = leer('nuevos_dia.txt')
    etapas = leer('etapas_lima.txt') + leer('etapas_regiones.txt') + leer('etapas_regiones_pc.txt')

    P = {}
    def get(p):
        if p not in P:
            P[p] = {'pipeline': p, 'nuevos': 0, 'recon': 0, **{b: 0 for b in BK}}
        return P[p]
    for p, c in nuevos: get(p)['nuevos'] += c
    for p, c in recon: get(p)['recon'] += c
    for lab, c in etapas:
        p, et = lab.split(' › ', 1)
        get(p)[bucket(et)] += c

    tot_n = sum(c for _, c in nuevos); tot_r = sum(c for _, c in recon); tot_e = sum(c for _, c in etapas)
    if tot_n + tot_r != tot_e:
        print(f'AVISO: nuevos+recontactados ({tot_n + tot_r}) no coincide con la suma por etapa ({tot_e})')

    filas = []
    for r in P.values():
        r['total'] = r['nuevos'] + r['recon']
        r['calificados'] = r['e5'] + r['e6'] + r['e7'] + r['e8'] + r['e9']
        filas.append(r)
    filas.sort(key=lambda r: -r['total'])

    etapas_tot = {b: sum(r[b] for r in filas) for b in BK}
    out = {
        'corte': corte,
        'periodo': 'Noviembre 2026',
        'kpis': {
            'nuevos': tot_n, 'recon': tot_r, 'total': tot_n + tot_r,
            'calificados': sum(r['calificados'] for r in filas),
            'escalados': etapas_tot['esc'],
        },
        'dia': [{'dia': d, 'leads': c} for d, c in dia],
        'etapas': etapas_tot,
        'pipelines': filas,
    }
    with open(os.path.join(BASE, 'darwin.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('OK darwin.json', out['kpis'])

if __name__ == '__main__':
    main()
