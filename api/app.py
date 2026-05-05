import os
import time
import random
import asyncio
import psutil
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CONTENT_TYPE_LATEST,
    generate_latest,
)
import uvicorn

APP_NAME = os.getenv("APP_NAME", "monitoring-bonus-api")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
PORT = int(os.getenv("PORT", "3000"))

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API REST instrumentada con metricas Prometheus para actividad BONUS",
)

http_requests_total = Counter(
    "http_requests_total",
    "Total de requests HTTP recibidos",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Duracion de los requests HTTP en segundos",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Cantidad de requests HTTP siendo procesados actualmente",
    ["method", "endpoint"],
)

system_cpu_usage = Gauge(
    "system_cpu_usage_percent",
    "Uso de CPU del sistema en porcentaje",
)

system_memory_usage = Gauge(
    "system_memory_usage_percent",
    "Uso de memoria del sistema en porcentaje",
)

app_info = Info("app", "Informacion de la aplicacion")
app_info.info({"name": APP_NAME, "version": APP_VERSION, "language": "python"})

USERS_DB = {
    1: {"id": 1, "name": "Ana", "role": "admin"},
    2: {"id": 2, "name": "Bruno", "role": "user"},
    3: {"id": 3, "name": "Carla", "role": "user"},
}


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    endpoint = request.url.path
    method = request.method

    if endpoint == "/metrics":
        return await call_next(request)

    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    start = time.time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
        http_requests_total.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


@app.get("/")
async def root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "message": "API de monitoreo BONUS - corriendo correctamente",
        "endpoints": [
            "GET /",
            "GET /api/datos",
            "GET /api/lento",
            "GET /api/usuarios",
            "GET /api/usuarios/{id}",
            "POST /api/usuarios",
            "GET /api/error",
            "GET /health",
            "GET /metrics",
        ],
    }


@app.get("/api/datos")
async def get_datos():
    await asyncio.sleep(random.uniform(0.01, 0.08))
    return {
        "items": [{"id": i, "value": random.randint(1, 1000)} for i in range(5)],
        "timestamp": time.time(),
    }


@app.get("/api/lento")
async def get_lento():
    delay = random.uniform(2.0, 3.0)
    await asyncio.sleep(delay)
    return {"message": "respuesta lenta", "delay_seconds": round(delay, 2)}


@app.get("/api/usuarios")
async def list_usuarios():
    await asyncio.sleep(random.uniform(0.02, 0.1))
    return {"usuarios": list(USERS_DB.values()), "total": len(USERS_DB)}


@app.get("/api/usuarios/{user_id}")
async def get_usuario(user_id: int):
    await asyncio.sleep(random.uniform(0.01, 0.05))
    user = USERS_DB.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado")
    return user


@app.post("/api/usuarios")
async def create_usuario(payload: dict):
    await asyncio.sleep(random.uniform(0.05, 0.15))
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Falta el campo 'name'")
    new_id = max(USERS_DB.keys()) + 1 if USERS_DB else 1
    user = {"id": new_id, "name": name, "role": payload.get("role", "user")}
    USERS_DB[new_id] = user
    return JSONResponse(status_code=201, content=user)


@app.get("/api/error")
async def trigger_error():
    if random.random() < 0.7:
        raise HTTPException(status_code=500, detail="Error interno simulado")
    return {"message": "esta vez no fallo"}


@app.get("/health")
async def health():
    return {"status": "ok", "uptime_seconds": time.time() - START_TIME}


@app.get("/metrics")
async def metrics():
    system_cpu_usage.set(psutil.cpu_percent(interval=None))
    system_memory_usage.set(psutil.virtual_memory().percent)
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


START_TIME = time.time()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

