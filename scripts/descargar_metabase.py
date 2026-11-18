#!/usr/bin/env python3
"""Descarga la consulta de Metabase de DARWIN como CSV (la misma que se baja a mano en Excel).

Variables de entorno (se configuran como "secrets" en GitHub):
  METABASE_URL       p. ej. https://metabase.ejemplo.com  (sin barra final)
  METABASE_CARD_ID   número de la consulta (sale en la dirección: /question/NNN-...)
  y UNA de estas dos formas de acceso:
  METABASE_API_KEY                         (recomendado)
  METABASE_USER + METABASE_PASSWORD        (usuario de Metabase)
Uso: python3 scripts/descargar_metabase.py salida.csv
"""
import json, os, sys, urllib.request

def pedir(url, data=None, headers=None, metodo='POST'):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=metodo)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()

def main():
    salida = sys.argv[1] if len(sys.argv) > 1 else 'metabase.csv'
    base = os.environ['METABASE_URL'].rstrip('/')
    card = os.environ['METABASE_CARD_ID'].strip().split('-')[0]
    h = {'Content-Type': 'application/json'}
    if os.environ.get('METABASE_API_KEY'):
        h['x-api-key'] = os.environ['METABASE_API_KEY']
    else:
        tok = json.loads(pedir(f'{base}/api/session', json.dumps({
            'username': os.environ['METABASE_USER'], 'password': os.environ['METABASE_PASSWORD']}).encode(), h))['id']
        h['X-Metabase-Session'] = tok
    cuerpo = json.dumps({'format_rows': False, 'pivot_results': False}).encode()
    datos = pedir(f'{base}/api/card/{card}/query/csv', cuerpo, h)
    with open(salida, 'wb') as f:
        f.write(datos)
    print(f'OK: {len(datos):,} bytes descargados de la consulta {card}')

if __name__ == '__main__':
    main()
