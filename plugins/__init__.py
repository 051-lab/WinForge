from pathlib import Path
from loguru import logger

def load_plugins(plugin_dir="plugins"):
    plugins = []
    for f in Path(plugin_dir).glob("*.py"):
        if f.name != "__init__.py":
            logger.info(f"Found plugin: {f.name}")
            plugins.append(f.stem)
    return plugins
