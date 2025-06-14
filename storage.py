# storage.py
import os
import json
from datetime import datetime

def ensure_dir(path: str):
    """
    Crea la carpeta completa si no existe.
    """
    os.makedirs(path, exist_ok=True)


def save_conversation(project: str, mode: str, messages: list, config: dict, description: str = None):
    """
    Guarda una conversación en formato JSON con metadatos.

    Args:
        project: Nombre del proyecto (subcarpeta dentro de CONV_DIR).
        mode: Subcarpeta de modo (codigo, informe, explicacion, etc.).
        messages: Lista de dicts {role, content}.
        config: Diccionario devuelto por load_config().
        description: Texto breve para el nombre de archivo.

    Retorna:
        Ruta completa del archivo guardado.
    """
    # Directorio del proyecto y modo
    base = config.get("CONV_DIR")
    folder = os.path.join(base, project, mode)
    ensure_dir(folder)

    # Timestamp y nombre de archivo
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    desc = f"__{description}" if description else ""
    filename = f"{now}{desc}.json"
    path = os.path.join(folder, filename)

    # Metadatos
    data = {
        "project": project,
        "mode": mode,
        "model": config.get("MODEL"),
        "created": datetime.now().isoformat(),
        "system": next((m["content"] for m in messages if m.get("role") == "system"), ""),
        "temperature": config.get("TEMPERATURE", None),
        "messages": messages
    }

    # Guardar
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return path
