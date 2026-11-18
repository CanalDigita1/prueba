# Dashboard Canal Digital — prueba

Página: https://canaldigita1.github.io/prueba/

## Actualización diaria de los leads (DARWIN · Metabase)

`scripts/actualizar_leads.py` hace lo mismo que se hacía a mano con el Excel "DARWIN - metabase" (hoja *Consulta*):
excluye Atención al cliente, NO USAR, Formulario Estandar y Orquestrador, calcula etapas, zonas, tiempos de
derivación y contacto, y reescribe los datos de `index.html`. **No publica nombres ni teléfonos** (el teléfono se
reemplaza por un código que solo sirve para unir las conversaciones repetidas de la misma persona).

### Automático (GitHub Actions, todos los días 7:15 a. m.)
En **Settings → Secrets and variables → Actions → New repository secret** crear:

| Secret | Valor |
|---|---|
| `METABASE_URL` | dirección del Metabase de DARWIN, p. ej. `https://xxxx.metabaseapp.com` |
| `METABASE_CARD_ID` | número de la consulta (sale en la dirección: `/question/NNN-...`) |
| `METABASE_API_KEY` | llave de API de Metabase **o** en su lugar `METABASE_USER` y `METABASE_PASSWORD` |
| `LEADS_SALT` | (opcional) cualquier texto secreto para el código de teléfonos |

Para probar: pestaña **Actions → Actualizar leads DARWIN → Run workflow**.

### Manual (con el Excel descargado)
```
python3 scripts/actualizar_leads.py "DARWIN - metabase.xlsx" index.html
```

Las ventas (Power BI / reporte comercial) siguen actualizándose aparte.
