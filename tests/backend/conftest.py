import os

# Tests never use production settings or send Telegram messages.
os.environ['DATABASE_URL'] = 'postgresql://test:test@127.0.0.1:1/test'
os.environ['BOT_TOKEN'] = ''
os.environ['ENABLE_BOT_POLLING'] = 'false'
os.environ['PORT'] = '0'
