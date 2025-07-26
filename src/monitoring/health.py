from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time
import psutil
import os

app = FastAPI()
start_time = time.time()

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    checks = {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - start_time,
        "version": "1.0.0"
    }
    
    return JSONResponse(content=checks, status_code=200)

@app.get("/metrics")
async def metrics():
    """Простые метрики"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    return {
        "bot_uptime_seconds": time.time() - start_time,
        "bot_memory_usage_bytes": memory_info.rss,
        "bot_cpu_percent": process.cpu_percent(),
    }