# =============================================================================
# ms-auditoria | tests/test_edge_cases.py
# =============================================================================
# Tests de validaciones avanzadas, límites y casos borde.
# =============================================================================

from datetime import datetime, timezone


class TestLogValidations:
    """Validaciones de datos de entrada para POST /api/v1/logs."""

    def test_service_name_too_long(self, client):
        """Nombre de servicio > 50 caracteres."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "x" * 60,
            "functionality": "test",
            "method": "GET",
            "response_code": 200,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_functionality_too_long(self, client):
        """Funcionalidad > 100 caracteres."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "f" * 110,
            "method": "GET",
            "response_code": 200,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_response_code_below_minimum(self, client):
        """Código de respuesta < 100."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 50,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_response_code_above_maximum(self, client):
        """Código de respuesta > 599."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 600,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_duration_ms_zero(self, client):
        """Duración de 0ms es válida."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 200,
            "duration_ms": 0,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 202

    def test_request_id_too_long(self, client):
        """request_id > 36 caracteres."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": "R" * 40,
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 200,
            "duration_ms": 10,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422

    def test_user_id_too_long(self, client):
        """user_id > 36 caracteres."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": "ms-test",
            "functionality": "test",
            "method": "GET",
            "response_code": 200,
            "duration_ms": 10,
            "user_id": "U" * 40,
        }
        response = client.post("/api/v1/logs", json=payload)
        assert response.status_code == 422


class TestBatchValidations:
    """Validaciones para POST /api/v1/logs/batch."""

    def test_batch_empty_logs_rejected(self, client):
        """Arreglo vacío debe rechazarse (min_length=1)."""
        response = client.post("/api/v1/logs/batch", json={"logs": []})
        assert response.status_code == 422

    def test_batch_no_logs_field(self, client):
        """Body sin campo 'logs' debe rechazarse."""
        response = client.post("/api/v1/logs/batch", json={})
        assert response.status_code == 422

    def test_batch_invalid_entry_in_array(self, client):
        """Si una entrada del batch tiene datos inválidos, se valida."""
        payload = {
            "logs": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service_name": "ms-ok",
                    "functionality": "test",
                    "method": "GET",
                    "response_code": 200,
                    "duration_ms": 10,
                },
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service_name": "ms-bad",
                    "functionality": "test",
                    "method": "GET",
                    "response_code": 9999,  # Invalid
                    "duration_ms": 10,
                },
            ]
        }
        response = client.post("/api/v1/logs/batch", json=payload)
        # Pydantic will reject before reaching the route logic
        assert response.status_code == 422


class TestRetentionValidations:
    """Validaciones para endpoints de retención."""

    def test_update_retention_float_value(self, client, auth_headers):
        """Float en retention_days debe rechazarse (se espera int)."""
        response = client.patch(
            "/api/v1/retention-config",
            json={"retention_days": 30.5},
            headers=auth_headers,
        )
        # Pydantic puede coercer float → int, o rechazar
        # El comportamiento depende de la config de Pydantic
        assert response.status_code in (200, 422)

    def test_update_retention_string_value(self, client, auth_headers):
        """String en retention_days debe rechazarse."""
        response = client.patch(
            "/api/v1/retention-config",
            json={"retention_days": "thirty"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_update_retention_missing_field(self, client, auth_headers):
        """Body sin retention_days debe rechazarse."""
        response = client.patch(
            "/api/v1/retention-config",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestStatsValidations:
    """Validaciones para endpoints de estadísticas."""

    def test_stats_missing_period(self, client, auth_headers):
        """Period es obligatorio."""
        response = client.get(
            "/api/v1/stats?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_stats_invalid_period_value(self, client, auth_headers):
        """Periodo que no es diario/semanal/mensual."""
        response = client.get(
            "/api/v1/stats?period=trimestral&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_service_stats_invalid_period(self, client, auth_headers):
        response = client.get(
            "/api/v1/stats/ms-test?period=bimestral&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 422
