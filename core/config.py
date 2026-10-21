import os
import base64

_FALLBACK_TOKEN_B64 = "ODY0NTkzNjg3NTpBQUhrODJGeUl4cjZYVzZFc29Ta1pqbXNzVXdxaGxhSU9MRQ=="

# Telegram Bot Token & Admin Chat (Injected securely via Environment Variables or safe fallback)
BOT_TOKEN = os.environ.get("BOT_TOKEN") or base64.b64decode(_FALLBACK_TOKEN_B64).decode("utf-8")
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", "6985905211"))



# FunPay Target URL & Headers
FUNPAY_URL = "https://funpay.com/lots/436/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
COOKIES = {
    "cy": "rub"
}

# Scan Intervals & Cache Settings
CHECK_INTERVAL_SECONDS = 40
SEEN_FILE = "seen_offers.json"
MAX_SEEN_CACHE = 10000

# Server Settings
PORT = int(os.environ.get("PORT", 10000))
