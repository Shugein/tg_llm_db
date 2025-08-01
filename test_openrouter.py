# #!/usr/bin/env python3
# """Тест OpenRouter API"""

# import asyncio
# import os
# from dotenv import load_dotenv

# # Загружаем переменные окружения
# load_dotenv()

# from src.bot.services.openrouter import openrouter_generate_async

# async def test_openrouter():
#     """Тестирование OpenRouter API"""
    
#     api_key = os.getenv("OPENROUTER_API_KEY")
#     model = os.getenv("DEFAULT_MODEL", "mistralai/mistral-small-3.2-24b-instruct:free")
    
#     print(f"Testing OpenRouter API...")
#     print(f"API Key: {api_key[:20]}..." if api_key else "No API Key")
#     print(f"Model: {model}")
    
#     try:
#         result = await openrouter_generate_async(
#             prompt="Привет! Как дела?",
#             model=model,
#             max_tokens=100,
#             temperature=0.7
#         )
        
#         print("\n✅ SUCCESS!")
#         print(f"Response: {result['content']}")
#         print(f"Model used: {result.get('model', 'Unknown')}")
#         print(f"Usage: {result.get('usage', {})}")
        
#     except Exception as e:
#         print(f"\n❌ ERROR: {e}")
#         print(f"Type: {type(e).__name__}")

# if __name__ == "__main__":
#     asyncio.run(test_openrouter())