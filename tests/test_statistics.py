# =============================================================================
# ms-auditoria | tests/test_statistics.py
# =============================================================================
# Tests para el servicio y endpoints de estadísticas (AUD-RF-014..016).
# =============================================================================

import time
from datetime import datetime, timezone


class TestStatisticsEndpoints:
    """Tests para los endpoints de estadísticas precalculadas."""

    def test_general_stats_empty_returns_zero_records(self, client, auth_headers):
        """Sin datos semilla, las estadísticas devuelven 0 registros."""
        data = client.get(
            "/api/v1/stats?period=diario&page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 0
        assert data["data"]["records"] == []

    def test_general_stats_with_date_filter(self, client, auth_headers):
        """Filtro por fecha funciona correctamente."""
        response = client.get(
            "/api/v1/stats?period=diario&date=2026-02-15&page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_service_stats_nonexistent_service(self, client, auth_headers):
        """Servicio que no existe retorna 0 registros, no 404."""
        data = client.get(
            "/api/v1/stats/ms-nonexistent?period=diario&page=1&page_size=20",
            headers=auth_headers,
        ).json()
        assert data["success"] is True
        assert data["data"]["total_records"] == 0

    def test_general_stats_all_periods(self, client, auth_headers):
        """Los tres periodos válidos retornan 200."""
        for period in ["diario", "semanal", "mensual"]:
            response = client.get(
                f"/api/v1/stats?period={period}&page=1&page_size=20",
                headers=auth_headers,
            )
            assert response.status_code == 200

    def test_service_stats_pagination(self, client, auth_headers):
        """Paginación funciona en estadísticas por servicio."""
        response = client.get(
            "/api/v1/stats/ms-test?period=diario&page=1&page_size=5",
            headers=auth_headers,
        )
        data = response.json()
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 5

    def test_general_stats_invalid_page_size(self, client, auth_headers):
        """page_size > 100 debe rechazarse."""
        response = client.get(
            "/api/v1/stats?period=diario&page=1&page_size=200",
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_general_stats_invalid_page(self, client, auth_headers):
        """page < 1 debe rechazarse."""
        response = client.get(
            "/api/v1/stats?period=diario&page=0&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 422
