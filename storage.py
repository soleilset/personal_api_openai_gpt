# storage.py
import os
import json
from datetime import datetime

def ensure_dir(path: str):
    """
    Crea la carpeta completa si no existe.
    """
    os.makedirs(path, exist_ok=True)

def save_conversation(mode: str, messages: list, config: dict, description: str = None):
    """
    Guarda una conversación de un solo turno en formato JSON con metadatos.

    Args:
        mode: Subcarpeta de modo (codigo, informe, explicacion, etc.).
        messages: Lista de dicts {role, content} (prompt + respuesta).
        config: Diccionario devuelto por load_config().
        description: Texto breve para el nombre de archivo. (Opcional)

    Retorna:
        Ruta completa del archivo JSON guardado.
    """
    # Directorio de conversaciones y modo
    conv_dir = config.get("CONV_DIR")
    folder = os.path.join(conv_dir, mode)
    ensure_dir(folder)

    # Derivar nombre de proyecto desde la ruta del módulo
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_name = os.path.basename(project_root)

    # Timestamp y nombre de archivo
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    desc = f"__{description}" if description else ""
    filename = f"{now}{desc}.json"
    path = os.path.join(folder, filename)

    # Construir datos con metadatos
    data = {
        "project": project_name,
        "mode": mode,
        "model": config.get("MODEL"),
        "created": datetime.now().isoformat(),
        "system": next((m['content'] for m in messages if m.get('role') == 'system'), ""),
        "temperature": config.get("TEMPERATURE"),
        "messages": messages
    }

    # Guardar como JSON estructurado
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path