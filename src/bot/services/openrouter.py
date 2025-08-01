import os
import json
import requests
from typing import Dict, Any, List, Optional
from loguru import logger

from ..config import settings

API_URL = "https://openrouter.ai/api/v1/chat/completions"

class OpenRouterError(Exception):
    """Исключение для ошибок OpenRouter API"""
    pass

def openrouter_generate(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    timeout: int = 60,
    stream: bool = False,
    messages: Optional[List[Dict[str, str]]] = None,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Отправляет запрос в OpenRouter API и возвращает ответ.
    
    :param prompt: текст запроса пользователя (используется если messages не указан)
    :param api_key: ключ OpenRouter (если None — берётся из настроек)
    :param model: ID модели (если None — берётся из настроек)
    :param max_tokens: лимит генерируемых токенов
    :param temperature: температура генерации (0.0 - 2.0)
    :param timeout: тайм-аут HTTP-запроса в секундах
    :param stream: флаг для включения потокового режима
    :param messages: список сообщений для контекста (если None, используется prompt)
    :param use_structured_output: использовать структурированный вывод
    :return: dict с ответом от API
    """
    
    # Получаем API ключ
    if api_key is None:
        api_key = settings.openrouter_api_key.get_secret_value()
    if not api_key:
        raise OpenRouterError("API-ключ OpenRouter не задан")
    
    # Получаем модель
    if model is None:
        model = settings.default_model
    
    # Формируем сообщения
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    
    # Базовые параметры запроса
    request_data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None,
        "stream": stream,
    }
    
    # Добавляем структурированный вывод если требуется
    if use_structured_output:
        request_data["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "Ответ на запрос пользователя"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Уверенность в ответе от 0 до 1",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                }
            }
        }
        request_data["structured_outputs"] = True
    
    try:
        logger.debug(f"Sending request to OpenRouter: model={model}, max_tokens={max_tokens}")
        
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Опционально для статистики
                "X-Title": "Telegram LLM Bot"  # Опционально для статистики
            },
            json=request_data,
            timeout=timeout
        )
        
        response.raise_for_status()
        response_data = response.json()
        
        # Проверяем наличие ошибок в ответе
        if "error" in response_data:
            error_msg = response_data["error"].get("message", "Unknown error")
            raise OpenRouterError(f"OpenRouter API error: {error_msg}")
        
        # Извлекаем контент ответа
        if "choices" not in response_data or not response_data["choices"]:
            raise OpenRouterError("No choices in response")
        
        content = response_data["choices"][0]["message"]["content"]
        
        # Если используется структурированный вывод, парсим JSON
        if use_structured_output:
            try:
                structured_content = json.loads(content)
                logger.debug("Successfully parsed structured output")
                return {
                    "content": structured_content,
                    "usage": response_data.get("usage", {}),
                    "model": response_data.get("model", model),
                    "structured": True
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structured output: {e}")
                raise OpenRouterError(f"Invalid JSON in structured response: {e}")
        
        logger.debug("OpenRouter request completed successfully")
        return {
            "content": content,
            "usage": response_data.get("usage", {}),
            "model": response_data.get("model", model),
            "structured": False
        }
        
    except requests.exceptions.Timeout:
        logger.error("OpenRouter request timed out")
        raise OpenRouterError("Request timed out")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter request failed: {e}")
        raise OpenRouterError(f"Request failed: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in openrouter_generate: {e}")
        raise OpenRouterError(f"Unexpected error: {e}")

async def openrouter_generate_async(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    timeout: int = 60,
    stream: bool = False,
    messages: Optional[List[Dict[str, str]]] = None,
    use_structured_output: bool = False
) -> Dict[str, Any]:
    """
    Асинхронная версия openrouter_generate
    """
    import asyncio
    import aiohttp
    
    # Получаем API ключ
    if api_key is None:
        api_key = settings.openrouter_api_key.get_secret_value()
    if not api_key:
        raise OpenRouterError("API-ключ OpenRouter не задан")
    
    # Получаем модель
    if model is None:
        model = settings.default_model
    
    # Формируем сообщения
    if messages is None:
        messages = [{"role": "user", "content": prompt}]
    
    # Базовые параметры запроса
    request_data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None,
        "stream": stream,
    }
    
    # Добавляем структурированный вывод если требуется
    if use_structured_output:
        request_data["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "Ответ на запрос пользователя"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Уверенность в ответе от 0 до 1",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["answer"],
                    "additionalProperties": False
                }
            }
        }
        request_data["structured_outputs"] = True
    
    try:
        logger.debug(f"Sending async request to OpenRouter: model={model}, max_tokens={max_tokens}")
        
        import ssl
        
        # Создаем SSL контекст (для разработки можно отключить проверку)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False  # Для разработки
        ssl_context.verify_mode = ssl.CERT_NONE  # Для разработки
        
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        
        async with aiohttp.ClientSession(
            timeout=timeout_obj,
            connector=aiohttp.TCPConnector(ssl=ssl_context)
        ) as session:
            async with session.post(
                API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "Telegram LLM Bot"
                },
                json=request_data
            ) as response:
                
                response.raise_for_status()
                response_data = await response.json()
                
                # Проверяем наличие ошибок в ответе
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Unknown error")
                    raise OpenRouterError(f"OpenRouter API error: {error_msg}")
                
                # Извлекаем контент ответа
                if "choices" not in response_data or not response_data["choices"]:
                    raise OpenRouterError("No choices in response")
                
                content = response_data["choices"][0]["message"]["content"]
                
                # Если используется структурированный вывод, парсим JSON
                if use_structured_output:
                    try:
                        structured_content = json.loads(content)
                        logger.debug("Successfully parsed structured output")
                        return {
                            "content": structured_content,
                            "usage": response_data.get("usage", {}),
                            "model": response_data.get("model", model),
                            "structured": True
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse structured output: {e}")
                        raise OpenRouterError(f"Invalid JSON in structured response: {e}")
                
                logger.debug("OpenRouter async request completed successfully")
                return {
                    "content": content,
                    "usage": response_data.get("usage", {}),
                    "model": response_data.get("model", model),
                    "structured": False
                }
                
    except asyncio.TimeoutError:
        logger.error("OpenRouter async request timed out")
        raise OpenRouterError("Request timed out")
    
    except aiohttp.ClientError as e:
        logger.error(f"OpenRouter async request failed: {e}")
        raise OpenRouterError(f"Request failed: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in openrouter_generate_async: {e}")
        raise OpenRouterError(f"Unexpected error: {e}")