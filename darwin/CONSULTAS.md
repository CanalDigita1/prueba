# Consultas a Darwin para `darwin/darwin.json`

Herramienta: conector **Darwin** → `mcp__invoke_tool` con `name: "darwin_conversation__count"` y los `arguments` de abajo (OU Autoplan 3747).
Cada respuesta trae `result.data.groups`. Guardar **todos** los grupos en `darwin/raw/<archivo>`, una línea por grupo con el formato indicado (p. ej. `Lima Centro|407`). Si la respuesta trae `other` con conteo > 0, faltan grupos: avisar.
Luego correr `python3 darwin/build.py "AAAA-MM-DD HH:MM"` (hora Lima). Debe imprimir `OK` sin `AVISO`.

Las fechas cubren noviembre 2026 (hora Lima = UTC-5). Para otro mes, cambiar las dos fechas de inicio/fin en todas las consultas y el campo `periodo` en build.py.
Si se crea un pipeline nuevo en Darwin, agregar su id a la lista que corresponda (Lima / regiones / regiones PC).

## 1. `nuevos_pipeline.txt`  —  línea: `label|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "first", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}], "group_by": {"kind": "pipeline_id"}, "limit": 200}
```

## 2. `recon_pipeline.txt`  —  línea: `label|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "last", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}, {"type": "created_at", "scope": "first", "op": "<", "value": "2026-11-01T05:00:00.000Z"}], "group_by": {"kind": "pipeline_id"}, "limit": 200}
```

## 3. `nuevos_dia.txt`  —  línea: `value|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "first", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}], "group_by": {"kind": "date", "field": "created_at", "bucket": "day", "scope": "first", "timezone": "America/Lima"}, "limit": 60}
```

## 4. `etapas_lima.txt`  —  línea: `label|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "last", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}, {"type": "pipeline_id", "scope": "last", "value": [12093, 12736, 12095, 10522, 12092, 12094, 16146, 16145, 16159, 16160, 16161, 16162, 16163, 16164]}], "group_by": {"kind": "pipeline_stage_id"}, "limit": 200}
```

## 5. `etapas_regiones.txt`  —  línea: `label|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "last", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}, {"type": "pipeline_id", "scope": "last", "value": [15688, 9773, 15998, 14976, 13084, 12334, 10516, 10517, 10519, 10521, 11640, 11641, 11642, 11643, 11644, 11788, 11789, 11790, 9982, 12138, 12139, 12140, 12141, 12342, 12345, 15775]}], "group_by": {"kind": "pipeline_stage_id"}, "limit": 200}
```

## 6. `etapas_regiones_pc.txt`  —  línea: `label|count`

```json
{"ou_id": 3747, "filters": [{"type": "created_at", "scope": "last", "op": "between", "value": ["2026-11-01T05:00:00.000Z", "2026-12-01T04:59:59.999Z"]}, {"type": "pipeline_id", "scope": "last", "value": [16147, 16148, 16149, 16150, 16151, 16152, 16153, 16154, 16155, 16156, 16157, 16158, 16165, 16166, 16167, 16168, 16169]}], "group_by": {"kind": "pipeline_stage_id"}, "limit": 200}
```
