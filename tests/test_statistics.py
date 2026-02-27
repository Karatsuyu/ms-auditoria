# =============================================================================
# ms-auditoria | tests/test_statistics.py
# =============================================================================
# Tests unitarios detallados para el servicio de estadísticas.
# =============================================================================

from datetime import datetime, timezone


class TestStatisticsDetailed:
    """Tests detallados para el endpoint de estadísticas."""

    def test_stats_logs_por_servicio(self, client):
        """Verifica el conteo correcto por servicio."""
        services = ["ms-matricula"] * 3 + ["ms-finanzas"] * 2 + ["ms-academico"]
        for svc in services:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": svc,
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 100,
            })

        response = client.get("/api/v1/audit/stats")
        data = response.json()["data"]

        assert data["total_registros"] == 6

        # logs_por_servicio debe estar ordenado por total desc
        por_svc = data["logs_por_servicio"]
        assert por_svc[0]["servicio"] == "ms-matricula"
        assert por_svc[0]["total"] == 3
        assert por_svc[1]["servicio"] == "ms-finanzas"
        assert por_svc[1]["total"] == 2

    def test_stats_error_rate(self, client):
        """Verifica cálculo de tasa de errores."""
        # 3 exitosos + 2 errores para ms-test
        for code in [200, 200, 200, 500, 404]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": code,
                "duracion_ms": 100,
            })

        response = client.get("/api/v1/audit/stats")
        data = response.json()["data"]

        tasa = data["tasa_errores_por_servicio"]
        ms_test = next(t for t in tasa if t["servicio"] == "ms-test")
        assert ms_test["total"] == 5
        assert ms_test["errors"] == 2
        assert ms_test["error_rate"] == 40.0  # 2/5 * 100

    def test_stats_duration_average(self, client):
        """Verifica promedio de duración."""
        durations = [100, 200, 300]
        for d in durations:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": d,
            })

        response = client.get("/api/v1/audit/stats")
        data = response.json()["data"]

        dur = data["duracion_promedio_por_servicio"]
        ms_test = next(d for d in dur if d["servicio"] == "ms-test")
        assert ms_test["avg_duration_ms"] == 200.0  # (100+200+300)/3
        assert ms_test["total_requests"] == 3

    def test_stats_logs_por_codigo(self, client):
        """Verifica conteo por código de respuesta."""
        for code in [200, 200, 201, 404, 500]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": code,
                "duracion_ms": 50,
            })

        response = client.get("/api/v1/audit/stats")
        data = response.json()["data"]

        por_codigo = {c["codigo_respuesta"]: c["total"] for c in data["logs_por_codigo_respuesta"]}
        assert por_codigo[200] == 2
        assert por_codigo[201] == 1
        assert por_codigo[404] == 1
        assert por_codigo[500] == 1
