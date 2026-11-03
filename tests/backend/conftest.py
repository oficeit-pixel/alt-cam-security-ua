import os

# Tests never use production settings or send Telegram messages.
os.environ['DATABASE_URL'] = 'postgresql://test:test@127.0.0.1:1/test'
os.environ['BOT_TOKEN'] = ''
os.environ['ENABLE_BOT_POLLING'] = 'false'
os.environ['PORT'] = '0'
# Never call a real LLM from tests (the box/CI may have a key); real smoke test: scripts/ai_smoke.py
for _name in ('LLM_API_KEY', 'GEMINI_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL'):
    os.environ.pop(_name, None)
