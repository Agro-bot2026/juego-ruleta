# JuegoRuleta - config central
import os

# Base de datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("RULETA_DB", os.path.join(BASE_DIR, "ruleta.db"))

# IA DeepSeek
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# TTS OpenAI (como el bot Descryptor)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TTS_VOICE = os.environ.get("TTS_VOICE", "echo")  # voz masculina natural

# Web
WEB_DIR = os.path.join(os.path.dirname(BASE_DIR), "web")
