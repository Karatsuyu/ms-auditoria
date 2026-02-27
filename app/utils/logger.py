# =============================================================================
# ms-auditoria | utils/logger.py
# =============================================================================
# Logger estructurado para el microservicio.
# Formato JSON para integración con herramientas de monitoreo (ELK, Grafana).
# =============================================================================

import logging
import json
import sys
from datetime import datetime, timezone

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Formateador que produce logs en formato JSON estructurado."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "ms-auditoria",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Agregar campos extra si existen
        if hasattr(record, "__dict__"):
            extras = {
                k: v
                for k, v in record.__dict__.items()
                if k not in logging.LogRecord(
                    "", 0, "", 0, "", (), None
                ).__dict__
                and k not in ("message", "msg", "args")
            }
            if extras:
                log_entry["extra"] = extras

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_logger() -> logging.Logger:
    """Configura y retorna el logger principal del microservicio."""
    _logger = logging.getLogger("ms-auditoria")
    _logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Evitar duplicar handlers si se llama múltiples veces
    if not _logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        _logger.addHandler(handler)

    return _logger


logger = setup_logger()
