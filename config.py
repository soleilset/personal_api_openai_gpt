# config.py
import os
from dotenv import load_dotenv


def load_config():
    """
    Carga y devuelve la configuración necesaria para la herramienta GPT.
  
    Variables de entorno opcionales:
      - GPT_MODEL: modelo por defecto (p.ej. 'gpt-4')
      - GPT_TEMPERATURE: nivel de aleatoriedad (float)
      - CONV_DIR: ruta para almacenar conversaciones (por defecto: carpeta 'conversations' junto a este archivo)

    Requiere obligatoriamente:
      - OPENAI_API_KEY: clave de API de OpenAI
    """
    # Cargar .env si existe
    load_dotenv()

    # Clave de API (obligatoria)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("La variable OPENAI_API_KEY no está definida en el entorno.")

    # Modelo y temperatura (opcional con valores por defecto)
    model = os.getenv("GPT_MODEL", "gpt-3.5")
    temp_env = os.getenv("GPT_TEMPERATURE")
    temperature = float(temp_env) if temp_env is not None else None

    # Carpeta de conversaciones (por defecto, 'conversations' junto a este archivo)
    default_conv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversations")
    conv_dir = os.getenv("CONV_DIR", default_conv)

    return {
        "OPENAI_API_KEY": api_key,
        "MODEL": model,
        "TEMPERATURE": temperature,
        "CONV_DIR": conv_dir,
    }