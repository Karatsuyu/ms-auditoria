# models __init__ — importar todos los modelos para que Alembic los detecte
from app.models.audit_log import AuditLog
from app.models.microservice_token import MicroserviceToken

__all__ = ["AuditLog", "MicroserviceToken"]
