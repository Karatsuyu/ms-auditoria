# =============================================================================
# ms-auditoria | tests/test_audit_routes.py
# =============================================================================
# Tests de integración para los endpoints de auditoría.
# =============================================================================

from datetime import datetime, timezone


class TestHealthCheck:
    """Tests para el endpoint de health check."""

    def test_health_check(self, client):
        response = client.get("/api/v1/audit/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "running" in data["message"]


class TestCreateAuditLog:
    """Tests para la creación de logs de auditoría."""

    def test_create_log_success(self, client):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-matricula",
            "endpoint": "/api/v1/matricula/inscribir",
            "metodo_http": "POST",
            "codigo_respuesta": 201,
            "duracion_ms": 150,
            "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
            "detalle": '{"accion": "inscripcion", "materia": "Desarrollo de Software 3"}',
            "ip_origen": "192.168.1.100",
            "request_id": "req-test-001",
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["servicio"] == "ms-matricula"
        assert data["data"]["endpoint"] == "/api/v1/matricula/inscribir"
        assert data["data"]["metodo"] == "POST"
        assert data["data"]["codigo_respuesta"] == 201

    def test_create_log_minimal(self, client):
        """Test con datos mínimos requeridos."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-finanzas",
            "endpoint": "/api/v1/pagos",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 50,
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["usuario_id"] is None

    def test_create_log_invalid_codigo(self, client):
        """Test con código de respuesta inválido."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 999,  # Inválido: máximo 599
            "duracion_ms": 10,
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 422  # Validation error

    def test_create_log_missing_fields(self, client):
        """Test con campos obligatorios faltantes."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 422


class TestCreateBatchLogs:
    """Tests para la creación de logs en batch."""

    def test_create_batch_success(self, client):
        logs = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": f"ms-service-{i}",
                "endpoint": f"/api/v1/test/{i}",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10 + i,
            }
            for i in range(5)
        ]
        response = client.post("/api/v1/audit/log/batch", json=logs)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 5


class TestGetAuditLogs:
    """Tests para la consulta de logs."""

    def test_get_logs_empty(self, client):
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    def test_get_logs_with_data(self, client):
        # Crear un log primero
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-academico",
            "endpoint": "/api/v1/notas",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 80,
        }
        client.post("/api/v1/audit/log", json=payload)

        # Consultar
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["servicio"] == "ms-academico"

    def test_get_logs_filter_by_servicio(self, client):
        # Crear logs de diferentes servicios
        for svc in ["ms-matricula", "ms-finanzas", "ms-matricula"]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": svc,
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10,
            })

        # Filtrar solo ms-matricula
        response = client.get("/api/v1/audit/logs?servicio=ms-matricula")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetAuditLogById:
    """Tests para obtener log por ID."""

    def test_get_by_id_success(self, client):
        # Crear log
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 10,
        }
        create_response = client.post("/api/v1/audit/log", json=payload)
        log_id = create_response.json()["data"]["id"]

        # Obtener por ID
        response = client.get(f"/api/v1/audit/log/{log_id}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == log_id

    def test_get_by_id_not_found(self, client):
        response = client.get("/api/v1/audit/log/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 404


class TestTraceRequest:
    """Tests para trazabilidad por Request-ID."""

    def test_trace_request(self, client):
        request_id = "trace-test-001"
        for i in range(3):
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": f"ms-service-{i}",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10,
                "request_id": request_id,
            })

        response = client.get(f"/api/v1/audit/trace/{request_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3


class TestStatistics:
    """Tests para estadísticas."""

    def test_get_stats_empty(self, client):
        response = client.get("/api/v1/audit/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_registros"] == 0

    def test_get_stats_with_data(self, client):
        # Crear algunos logs
        for svc in ["ms-matricula", "ms-finanzas", "ms-matricula"]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": svc,
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 100,
            })

        response = client.get("/api/v1/audit/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_registros"] == 3


class TestRootEndpoint:
    """Tests para el endpoint raíz."""

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["microservicio"] == "ms-auditoria"
        assert data["version"] == "1.0.0"
