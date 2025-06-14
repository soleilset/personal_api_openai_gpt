# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env si existe
def load_config():
    load_dotenv()
    config = {
        # Clave de API de OpenAI
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        # Modelo por defecto
        "MODEL": os.getenv("GPT_MODEL", "gpt-4"),
        # Carpeta base de conversaciones
        "BASE_DIR": os.getenv("BASE_DIR", os.path.expanduser("~/Proyectos")),
        # Carpeta específica para gpt_api_tool
        "TOOL_DIR": os.getenv("TOOL_DIR", os.path.join(os.getenv("BASE_DIR"), "gpt_api_tool")),
        # Carpeta de almacenamiento de conversaciones
        "CONV_DIR": os.getenv(
            "CONV_DIR",
            os.path.join(os.getenv("TOOL_DIR", os.path.expanduser("~/Proyectos/gpt_api_tool")), "conversations")
        )
    }
    if not config["OPENAI_API_KEY"]:
        raise EnvironmentError("La variable OPENAI_API_KEY no está definida en el entorno.")
    return config