# Actividad BONUS - Monitoreo y Observabilidad en la Nube

| Campo |--------------------Valor---------------------|
|-------|----------------------------------------------|
| Nombre | Oscar Alejandro Morales Calderon |
|Codigo  | 202220010601|
| Repositorio | _URL del repo en GitHub_ |
| Video | _URL del video (YouTube no listado / Drive)_ |

## 1. Descripción

Stack completo de monitoreo y observabilidad para una **API REST** desarrollada en **Python (FastAPI)**, instrumentada con la librería oficial `prometheus-client`. Toda la infraestructura corre con `docker-compose` e incluye:

- API REST con **9 endpoints**.
- **Prometheus** recolectando métricas cada 15 segundos.
- **Grafana** con datasource y **dashboard provisionados automáticamente** (7 paneles).
- **Reglas de alerta** definidas en Prometheus (caída de la API, latencia p95 alta, tasa de errores 5xx).
- **Scripts de tráfico sintético** en PowerShell, Python y Bash.
- **Histogramas con percentiles** (p50 / p95) para latencia.

## 2. Estructura del proyecto

```
ActividadZ/
├── docker-compose.yml
├── README.md
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── prometheus/
│   ├── prometheus.yml
│   └── alerts.yml
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasource.yml
│       └── dashboards/
│           ├── dashboard.yml
│           └── api-dashboard.json
└── scripts/
    ├── generate-traffic.ps1
    ├── generate-traffic.py
    └── generate-traffic.sh
```

## 3. Cómo ejecutar

### Requisitos
- Docker Desktop (o Docker Engine + docker-compose)
- Puertos libres: **3000** (API), **9090** (Prometheus), **3001** (Grafana)

### Pasos

```bash
# 1) Levantar todo el stack
docker-compose up -d --build

# 2) Verificar que los 3 servicios estan corriendo
docker-compose ps

# 3) (En otra terminal) generar trafico
#    PowerShell (Windows)
.\scripts\generate-traffic.ps1

#    Python (multiplataforma)
python scripts/generate-traffic.py

#    Bash (Linux / macOS / Git Bash)
bash scripts/generate-traffic.sh

# 4) Detener todo
docker-compose down

# 5) Detener y borrar datos persistentes
docker-compose down -v
```

### URLs de acceso

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| API | http://localhost:3000 | — |
| API metrics | http://localhost:3000/metrics | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3001 | `admin` / `admin` |

El dashboard se llama **"Monitoreo API - Bonus Cloud Apps"** y aparece automáticamente en Grafana al iniciar (no hay que importarlo manualmente).

## 4. Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información general y listado de endpoints |
| GET | `/api/datos` | Devuelve datos rápidos (~10-80 ms) |
| GET | `/api/lento` | Simula procesamiento lento (2-3 s) |
| GET | `/api/usuarios` | Lista usuarios |
| GET | `/api/usuarios/{id}` | Obtiene un usuario (404 si no existe) |
| POST | `/api/usuarios` | Crea un usuario nuevo |
| GET | `/api/error` | Devuelve 500 el ~70% de las veces |
| GET | `/health` | Healthcheck |
| GET | `/metrics` | Métricas en formato Prometheus |

## 5. Métricas expuestas

| Métrica | Tipo | Labels | Descripción |
|---------|------|--------|-------------|
| `http_requests_total` | Counter | `method`, `endpoint`, `status` | Total de requests recibidos |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Latencia (buckets desde 5 ms a 10 s) |
| `http_requests_in_progress` | Gauge | `method`, `endpoint` | Requests siendo procesados ahora mismo |
| `system_cpu_usage_percent` | Gauge | — | % de CPU del contenedor |
| `system_memory_usage_percent` | Gauge | — | % de memoria del sistema |
| `app_info` | Info | `name`, `version`, `language` | Metadatos de la aplicación |

## 6. Queries PromQL útiles

# Throughput por endpoint
sum by (endpoint) (rate(http_requests_total[1m]))

# Latencia p95 por endpoint
histogram_quantile(0.95, sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[2m])))

## 7. Paneles del dashboard de Grafana

1. **Throughput** — requests por segundo por endpoint (timeseries con leyenda en tabla).
2. **Latencia p50 vs p95** por endpoint (histogram_quantile).
3. **Tasa de errores 5xx (%)** — stat con thresholds (verde / naranja / rojo).
4. **Requests activos** — gauge con el valor actual.
5. **Total de requests** en la última hora.
6. **CPU y Memoria** del sistema en el tiempo.
7. **Requests por código de estado** (barras apiladas).

## 8. Alertas configuradas en Prometheus

Definidas en `prometheus/alerts.yml`:

- **APICaida** — `up{job="monitoring-api"} == 0` durante más de 30 s.
- **LatenciaAltaP95** — p95 de latencia mayor a 1.5 s durante 1 minuto.
- **TasaErrores5xxAlta** — más del 10 % de respuestas 5xx durante 1 minuto.

Se pueden inspeccionar en `http://localhost:9090/alerts`.

## 9. Análisis de datos y posibles optimizaciones

Lo que se observa al generar tráfico:
- El endpoint `/api/lento` domina la **latencia p95** (2-3 s vs ~100 ms del resto).
- `/api/error` infla la **tasa de errores 5xx** (intencional, sirve para validar las alertas).
- `/api/usuarios/999` produce 404 → se distinguen claramente del resto en el panel apilado por status.

Posibles optimizaciones derivadas de las métricas:
- Mover `/api/lento` a un job asíncrono / caché para sacarlo del p95.
- Investigar la causa del 5xx en `/api/error` (en este caso es simulado).
- Si `http_requests_in_progress` crece monotónicamente, se podría escalar horizontalmente la API.

## 10. Cumplimiento de la rúbrica

| Criterio | Cumplido |
|----------|----------|
| API con 3+ endpoints + métricas 
| docker-compose funcional con redes 
| Prometheus configurado y haciendo scrape 
| Dashboard Grafana con 3+ paneles 
| Bonus: más de 5 endpoints 
| Bonus: alertas
| Bonus: histogramas + percentiles 
| Bonus: README documentado

## 11. Solución de problemas

- **El dashboard aparece vacío**: espera ~30 s para el primer scrape y genera tráfico con uno de los scripts.
- **Puerto 3000/3001/9090 ocupado**: cambia el puerto `host` en `docker-compose.yml` (lado izquierdo del `:`).
- **`docker-compose` no reconocido en Windows**: usa `docker compose` (sin guion).
- **PowerShell bloquea el script**: ejecuta `Set-ExecutionPolicy -Scope Process Bypass` antes.
