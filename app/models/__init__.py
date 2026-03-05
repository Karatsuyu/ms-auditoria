# models __init__ — importar todos los modelos para que Alembic los detecte
from app.models.audit_log import AuditLog
from app.models.microservice_token import MicroserviceToken
from app.models.retention_config import RetentionConfig
from app.models.service_statistics import ServiceStatistics

__all__ = ["AuditLog", "MicroserviceToken", "RetentionConfig", "ServiceStatistics"]
