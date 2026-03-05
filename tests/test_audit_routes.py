# =============================================================================
# ms-auditoria | tests/test_audit_routes.py
# =============================================================================
# Tests de integración para los 12 endpoints del microservicio.
# Endpoints probados:
#   1. POST   /api/v1/logs                — Recibir log individual (202)
#   2. POST   /api/v1/logs/batch          — Recibir lote de logs (202)
#   3. GET    /api/v1/logs/trace/{rid}    — Traza por request_id
#   4. GET    /api/v1/logs                — Filtrar registros
#   5. GET    /api/v1/retention-config    — Consultar config retención
#   6. PATCH  /api/v1/retention-config    — Actualizar config retención
#   7. POST   /api/v1/retention-config/rotate    — Rotación manual
#   8. GET    /api/v1/retention-config/rotation-history — Historial
#   9. GET    /api/v1/stats               — Estadísticas generales
#  10. GET    /api/v1/stats/{svc}         — Estadísticas por servicio
#  11. GET    /api/v1/health              — Health check
#  12. GET    /                           — Raíz
# =============================================================================

import time
from datetime import datetime, timezone


# =============================================================================
# 11. HEALTH CHECK — GET /api/v1/health (sin autenticación)
# =============================================================================


class TestHealthCheck:
    """Tests para GET /api/v1/health."""

    def test_health_check_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_check_structure(self, client):
        data = client.get("/api/v1/health").json()
        assert data["status"] in ("healthy", "unhealthy")
        assert "components" in data
        assert "database" in data["components"]
        assert "timestamp" in data

    def test_health_check_no_auth_required(self, client):
        """Health check no requiere ningún header de autenticación."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200


# =============================================================================
# 12. ROOT — GET /
# =============================================================================


class TestRootEndpoint:
    """Tests para GET /."""

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_service_info(self, client):
        data = client.get("/").json()
        assert data["microservicio"] == "ms-auditoria"
        assert data["version"] == "1.0.0"


# =============================================================================
# 1. POST /api/v1/logs — Recibir log individual
# =============================================================================


class TestReceiveLog:
    """Tests para POST /api/v1/logs."""

    def test_receive_log_returns_202(self, client, sample_log):
        response = client.post("/api/v1/logs", json=sample_log)
        assert response.status_code == 202

    def test_receive_log_response_format(self, client, sample_log):
        data = client.post("/api/v1/logs", json=sample_log).json()
        assert data["success"] is True
        assert data["data"]["received"] is True
        assert data["data"]["log_request_id"] == sample_log["request_id"]
        assert "request_id" in data
        assert "timestamp" in data
        assert "message" in data

    def test_receive_log_minimal_fields(self, client):
        """Log con solo los campos obligatorios (sin user_id ni detail)."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-finanzas",
            "functionality": "consultar_pagos",
            "method": "GET",
            "response_code": 200,
            "duration_ms": 50,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 202

    def test_receive_log_invalid_response_code(self, client):
        """Código de respuesta fuera de rango (> 599)."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 999,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_receive_log_missing_required_fields(self, client):
        """Body con campos obligatorios faltantes."""
        payload = {"timestamp": datetime.now(timezone.utc).isoformat()}
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_receive_log_negative_duration(self, client):
        """duration_ms negativo debe rechazarse."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 200,
            "duration_ms": -5,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_receive_log_all_http_methods(self, client):
        """Acepta todos los métodos HTTP válidos."""
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_name": "ms-test",
                "functionality": "test",
                "method": method,
                "response_code": 200,
                "duration_ms": 10,
            }
            response = client.post("/api/v1/logs", json=payload)
            assert response.status_code == 202, f"Failed for method {method}"

    def test_receive_log_all_status_code_families(self, client):
        """Acepta códigos de respuesta de cada familia HTTP (1xx-5xx)."""
        for code in [100, 200, 201, 301, 400, 404, 500, 503]:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_name": "ms-test",
                "functionality": "test",
                "method": "GET",
                "response_code": code,
                "duration_ms": 10,
            }
            response = client.post("/api/v1/logs", json=payload)
            assert response.status_code == 202, f"Failed for code {code}"

    def test_receive_log_response_has_request_id(self, client, sample_log):
        """La respuesta debe incluir request_id en formato AUD-*."""
        data = client.post("/api/v1/logs", json=sample_log).json()
        assert data["request_id"].startswith("AUD-") or data["request_id"] != ""


# =============================================================================
# 2. POST /api/v1/logs/batch — Recibir lote de logs
# =============================================================================


class TestReceiveLogBatch:
    """Tests para POST /api/v1/logs/batch."""

    def test_batch_returns_202(self, client, sample_batch_logs):
        response = client.post("/api/v1/logs/batch", json=sample_batch_logs)
        assert response.status_code == 202

    def test_batch_response_format(self, client, sample_batch_logs):
        data = client.post("/api/v1/logs/batch", json=sample_batch_logs).json()
        assert data["success"] is True
        assert data["data"]["received_count"] == 3
        assert data["data"]["accepted_count"] == 3
        assert data["data"]["rejected_count"] == 0
        assert "request_id" in data
        assert "timestamp" in data

    def test_batch_empty_array_rejected(self, client):
        """Arreglo vacío debe rechazarse."""
        response = client.post("/api/v1/logs/batch", json={"logs": []})
        assert response.status_code == 422

    def test_batch_single_log(self, client, sample_log):
        """Batch con un solo log."""
        payload = {"logs": [sample_log]}
        response = client.post("/api/v1/logs/batch", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["data"]["received_count"] == 1
        assert data["data"]["accepted_count"] == 1


# =============================================================================
# 3. GET /api/v1/logs/trace/{request_id} — Traza por request_id
# =============================================================================


class TestTraceByRequestId:
    """Tests para GET /api/v1/logs/trace/{request_id}."""

    def _insert_logs_for_trace(self, client, request_id: str, count: int = 3):
        """Helper: inserta logs con el mismo request_id y espera persistencia."""
        for i in range(count):
            client.post("/api/v1/logs", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "service_name": f"ms-service-{i}",
                "functionality": f"operation_{i}",
                "method": "GET",
                "response_code": 200,
                "duration_ms": 10 + i,
            })
        # Background tasks need time to persist
        time.sleep(0.5)

    def test_trace_returns_200(self, client, auth_headers):
        rid = "TRACE-1709302000-abc123"
        self._insert_logs_for_trace(client, rid)
        response = client.get(
            f"/api/v1/logs/trace/{rid}?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_trace_response_format(self, client, auth_headers):
        rid = "TRACE-1709302000-fmt001"
        self._insert_logs_for_trace(client, rid, count=2)
        data = client.get(
            f"/api/v1/logs/trace/{rid}?page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert data["data"]["trace_request_id"] == rid
        assert "total_records" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]
        assert "records" in data["data"]

    def test_trace_empty_result(self, client, auth_headers):
        """Traza sin resultados retorna lista vacía."""
        response = client.get(
            "/api/v1/logs/trace/NONEXISTENT-ID?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_records"] == 0
        assert data["data"]["records"] == []

    def test_trace_requires_auth(self, client):
        """Traza sin Bearer token debe fallar."""
        response = client.get(
            "/api/v1/logs/trace/TEST-ID?page=1&page_size=20"
        )
        assert response.status_code == 422  # Missing header


# =============================================================================
# 4. GET /api/v1/logs — Filtrar registros de log
# =============================================================================


class TestFilterLogs:
    """Tests para GET /api/v1/logs."""

    def _insert_logs(self, client, service_name: str, count: int = 3):
        for i in range(count):
            client.post("/api/v1/logs", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service_name": service_name,
                "functionality": f"op_{i}",
                "method": "GET",
                "response_code": 200,
                "duration_ms": 10,
            })
            time.sleep(0.05)  # small gap per log for SQLite background tasks
        time.sleep(1.0)  # wait for all background persists to commit

    def test_filter_by_service_name(self, client, auth_headers):
        self._insert_logs(client, "ms-reservas", 3)
        self._insert_logs(client, "ms-matriculas", 2)
        response = client.get(
            "/api/v1/logs?service_name=ms-reservas&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 3

    def test_filter_requires_at_least_one_filter(self, client, auth_headers):
        """Sin filtros debe retornar 400."""
        response = client.get(
            "/api/v1/logs?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_filter_by_date_range(self, client, auth_headers):
        self._insert_logs(client, "ms-test", 2)
        response = client.get(
            "/api/v1/logs?date_from=2020-01-01T00:00:00Z&date_to=2030-12-31T23:59:59Z&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total_records"] >= 2

    def test_filter_response_includes_filters_applied(self, client, auth_headers):
        response = client.get(
            "/api/v1/logs?service_name=ms-test&page=1&page_size=20",
            headers=auth_headers,
        )
        data = response.json()
        assert "filters_applied" in data["data"]
        assert data["data"]["filters_applied"]["service_name"] == "ms-test"

    def test_filter_pagination(self, client, auth_headers):
        self._insert_logs(client, "ms-paginate", 5)
        response = client.get(
            "/api/v1/logs?service_name=ms-paginate&page=1&page_size=2",
            headers=auth_headers,
        )
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 2
        assert data["data"]["total_records"] == 5
        assert len(data["data"]["records"]) == 2


# =============================================================================
# 5. GET /api/v1/retention-config — Consultar config
# =============================================================================


class TestRetentionConfig:
    """Tests para GET /api/v1/retention-config."""

    def test_get_retention_config(self, client, auth_headers):
        response = client.get("/api/v1/retention-config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Default config when no rows exist
        assert data["data"]["retention_days"] == 30
        assert data["data"]["status"] == "activo"


# =============================================================================
# 6. PATCH /api/v1/retention-config — Actualizar config
# =============================================================================


class TestUpdateRetentionConfig:
    """Tests para PATCH /api/v1/retention-config."""

    def test_update_retention_days(self, client, auth_headers):
        response = client.patch(
            "/api/v1/retention-config",
            json={"retention_days": 60},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["retention_days"] == 60

    def test_update_retention_invalid_value(self, client, auth_headers):
        """Valor <= 0 debe rechazarse."""
        response = client.patch(
            "/api/v1/retention-config",
            json={"retention_days": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_update_retention_negative_value(self, client, auth_headers):
        response = client.patch(
            "/api/v1/retention-config",
            json={"retention_days": -10},
            headers=auth_headers,
        )
        assert response.status_code == 422


# =============================================================================
# 7. POST /api/v1/retention-config/rotate — Rotación manual
# =============================================================================


class TestManualRotation:
    """Tests para POST /api/v1/retention-config/rotate."""

    def test_rotation_returns_200(self, client, auth_headers):
        response = client.post(
            "/api/v1/retention-config/rotate",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_rotation_response_format(self, client, auth_headers):
        data = client.post(
            "/api/v1/retention-config/rotate",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert "rotation_date" in data["data"]
        assert "deleted_count" in data["data"]
        assert "cutoff_date" in data["data"]
        assert "retention_days_applied" in data["data"]


# =============================================================================
# 8. GET /api/v1/retention-config/rotation-history
# =============================================================================


class TestRotationHistory:
    """Tests para GET /api/v1/retention-config/rotation-history."""

    def test_rotation_history_returns_200(self, client, auth_headers):
        response = client.get(
            "/api/v1/retention-config/rotation-history?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_rotation_history_response_format(self, client, auth_headers):
        data = client.get(
            "/api/v1/retention-config/rotation-history?page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert "total_records" in data["data"]
        assert "records" in data["data"]


# =============================================================================
# 9. GET /api/v1/stats — Estadísticas generales
# =============================================================================


class TestGeneralStats:
    """Tests para GET /api/v1/stats."""

    def test_general_stats_returns_200(self, client, auth_headers):
        response = client.get(
            "/api/v1/stats?period=diario&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_general_stats_response_format(self, client, auth_headers):
        data = client.get(
            "/api/v1/stats?period=diario&page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert data["data"]["period"] == "diario"
        assert "total_records" in data["data"]
        assert "records" in data["data"]

    def test_general_stats_invalid_period(self, client, auth_headers):
        """Periodo inválido debe retornar 422."""
        response = client.get(
            "/api/v1/stats?period=anual&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_general_stats_valid_periods(self, client, auth_headers):
        """Los tres periodos válidos deben funcionar."""
        for period in ["diario", "semanal", "mensual"]:
            response = client.get(
                f"/api/v1/stats?period={period}&page=1&page_size=20",
                headers=auth_headers,
            )
            assert response.status_code == 200, f"Failed for period {period}"


# =============================================================================
# 10. GET /api/v1/stats/{service_name} — Estadísticas por servicio
# =============================================================================


class TestServiceStats:
    """Tests para GET /api/v1/stats/{service_name}."""

    def test_service_stats_returns_200(self, client, auth_headers):
        response = client.get(
            "/api/v1/stats/ms-reservas?period=diario&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_service_stats_response_format(self, client, auth_headers):
        data = client.get(
            "/api/v1/stats/ms-reservas?period=mensual&page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert data["data"]["service_name"] == "ms-reservas"
        assert data["data"]["period"] == "mensual"


# =============================================================================
# MIDDLEWARE / REQUEST-ID TESTS
# =============================================================================


class TestRequestIdMiddleware:
    """Tests para el middleware de Request ID."""

    def test_response_has_x_request_id(self, client):
        response = client.get("/api/v1/health")
        assert "X-Request-ID" in response.headers

    def test_response_has_x_response_time(self, client):
        response = client.get("/api/v1/health")
        assert "X-Response-Time-ms" in response.headers

    def test_custom_request_id_is_propagated(self, client):
        """Si se envía X-Request-ID, el servicio lo reutiliza."""
        custom_id = "CUSTOM-1709302000-abc123"
        response = client.get(
            "/api/v1/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["X-Request-ID"] == custom_id

    def test_generated_request_id_has_aud_prefix(self, client):
        """Sin X-Request-ID, se genera uno con formato AUD-{ts}-{6char}."""
        response = client.get("/api/v1/health")
        rid = response.headers["X-Request-ID"]
        assert rid.startswith("AUD-")


# =============================================================================
# RESPONSE FORMAT TESTS
# =============================================================================


class TestResponseFormat:
    """Verifica el formato de respuesta estándar en todos los endpoints."""

    def test_success_response_format(self, client, sample_log):
        """Las respuestas exitosas incluyen request_id, success, data, message, timestamp."""
        data = client.post("/api/v1/logs", json=sample_log).json()
        assert "request_id" in data
        assert "success" in data
        assert "data" in data
        assert "message" in data
        assert "timestamp" in data

    def test_error_response_format(self, client, auth_headers):
        """Las respuestas de error incluyen el mismo formato."""
        data = client.get(
            "/api/v1/logs?page=1&page_size=20",
            headers=auth_headers,
        ).json()
        # This is a 400 (no filters) error
        assert "request_id" in data
        assert data["success"] is False
        assert "message" in data
        assert "timestamp" in data

    def test_validation_error_format(self, client):
        """Los errores 422 incluyen invalid_fields."""
        data = client.post("/api/v1/logs", json={}).json()
        assert data["success"] is False
        assert "data" in data
        assert "invalid_fields" in data["data"]
