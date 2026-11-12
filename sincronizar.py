"""Publica SOLO documentos marcados PUBLICAR_QR=SI desde Excel privado en M365.
Requisitos: pip install requests openpyxl
No imprime ni almacena el Excel completo. Los cambios se publican por GitHub Pages.
"""
import hashlib
import io
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
from openpyxl import load_workbook

OUTPUT = Path('site')
BASE_URL = os.environ.get('PUBLIC_SITE_URL','').rstrip('/')+'/'
REQUIRED = ['MS_TENANT_ID','MS_CLIENT_ID','MS_CLIENT_SECRET','MS_DRIVE_ID','MS_ITEM_ID']

def normal(s):
    s = unicodedata.normalize('NFD', str(s or ''))
    return ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn').strip().lower()

def value(row, col):
    return row[col] if col is not None and col < len(row) else None

def strval(v):
    if v is None: return ''
    if isinstance(v,float) and v.is_integer(): return str(int(v))
    return str(v).strip()

def codebase(code, rev):
    # Conservative rule: remove an appended revision only if it EXACTLY equals the Rev column.
    # Other coding conventions must be manually reviewed before production.
    code,rev = code.strip(),rev.strip()
    if rev and code.upper().endswith('-'+rev.upper()):
        return code[:-(len(rev)+1)]
    return code

def qrkey(project,base):
    # Stable as long as project name and base code stay the same.
    return hashlib.sha256((project+'\x1f'+base).encode('utf-8')).hexdigest()[:20]

def fetch_excel():
    missing=[v for v in REQUIRED if not os.environ.get(v)]
    if missing: raise RuntimeError('Faltan secretos: '+', '.join(missing))
    url='https://login.microsoftonline.com/'+os.environ['MS_TENANT_ID']+'/oauth2/v2.0/token'
    auth=requests.post(url,data={'client_id':os.environ['MS_CLIENT_ID'], 'client_secret':os.environ['MS_CLIENT_SECRET'], 'grant_type':'client_credentials', 'scope':'https://graph.microsoft.com/.default'},timeout=30)
    auth.raise_for_status()
    access=auth.json()['access_token']
    u='https://graph.microsoft.com/v1.0/drives/'+os.environ['MS_DRIVE_ID']+'/items/'+os.environ['MS_ITEM_ID']+'/content'
    resp=requests.get(u, headers={'Authorization':'Bearer '+access},timeout=90)
    resp.raise_for_status()
    return io.BytesIO(resp.content)

def main():
    wb=load_workbook(fetch_excel(),read_only=True,data_only=True)
    records={}; problems=[]; reviewed=0; selected=0
    for ws in wb.worksheets:
        head=None
        for i,row in enumerate(ws.iter_rows(max_row=min(ws.max_row,15),values_only=True),1):
            names={normal(v):j for j,v in enumerate(row) if v is not None}
            if 'codigo' in names and ('rev' in names or 'revision' in names):
                head=(i,names)
                break
        if not head:
            problems.append(f'{ws.title}: no se encontró encabezado Codigo/Rev en primeras 15 filas')
            continue
        start,heads=head
        codei=heads['codigo']; revi=heads.get('rev',heads.get('revision'))
        titlei=heads.get('titulo'); flagi=heads.get('publicar_qr')
        if flagi is None:
            problems.append(f'{ws.title}: no existe columna PUBLICAR_QR (se omite todo este proyecto)')
            continue
        for n,row in enumerate(ws.iter_rows(min_row=start+1,values_only=True),start+1):
            code=strval(value(row,codei)); rev=strval(value(row,revi))
            if not code: continue
            reviewed+=1
            flag=normal(value(row,flagi))
            if flag not in ('si','sí'): continue
            selected+=1
            if not rev:
                problems.append(f'{ws.title} fila {n}: revision vacía, NO PUBLICADO')
                continue
            base=codebase(code,rev)
            uid=qrkey(ws.title,base)
            if uid in records:
                problems.append(f'{ws.title} fila {n}: QR duplicado, detenga publicación')
                raise ValueError('QR duplicado; revise códigos bases en '+ws.title)
            records[uid]={'id':uid, 'proyecto':ws.title, 'codigo':code, 'codigo_base':base,'descripcion':strval(value(row,titlei)), 'revision':rev,'estado':'REGISTRADO'}
    wb.close()
    if selected==0:
        raise ValueError('Ninguna fila PUBLICAR_QR=SI. Por seguridad no se publica un conjunto vacío.')
    if selected!=len(records):
        raise ValueError('Filas marcadas SI sin publicar; revise errores. Publicación cancelada.')
    OUTPUT.mkdir(exist_ok=True)
    manifest={'actualizado':datetime.now(timezone.utc).isoformat(),'planos':records}
    (OUTPUT/'planos.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Publicados: {len(records)} de {reviewed} registros; {len(problems)} observaciones')
    for item in problems: print('AVISO:',item)
    print('IMPORTANTE: antes de imprimir QR, validar si los sufijos de código son revisiones.')
    if BASE_URL!='/' and BASE_URL.startswith('https://'):
        import csv
        with open('urls_qr.csv','w',newline='',encoding='utf-8-sig') as f:
            writer=csv.writer(f);writer.writerow(['Proyecto','Codigo base','Codigo actual','Revision','QR permanente URL'])
            for d in records.values(): writer.writerow([d['proyecto'],d['codigo_base'],d['codigo'],d['revision'],BASE_URL+'?'+urlencode({'id':d['id']})])

if __name__=='__main__': main()
