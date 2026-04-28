from loguru import logger

def check_for_updates(current_version: str) -> dict:
    logger.info(f"Checking updates for v{current_version}")
    return {"update_available": False, "latest": current_version}
