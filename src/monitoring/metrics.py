from prometheus_client import Counter, Histogram, Gauge, start_http_server
from loguru import logger

# Метрики бота
messages_total = Counter('bot_messages_total', 'Total messages processed', ['user_id', 'message_type'])
api_request_duration = Histogram('bot_api_request_duration_seconds', 'API request duration', ['provider', 'model'])
active_users = Gauge('bot_active_users', 'Number of active users')
errors_total = Counter('bot_errors_total', 'Total errors', ['error_type'])

async def start_metrics_server(port: int = 8000):
    """Запустить сервер метрик"""
    start_http_server(port)
    logger.info(f"Metrics server started on port {port}")