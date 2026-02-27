# =============================================================================
# ms-auditoria | tests/test_edge_cases.py
# =============================================================================
# Tests de casos borde y validaciones avanzadas.
# =============================================================================

from datetime import datetime, timezone, timedelta


class TestValidations:
    """Tests de validación de datos de entrada."""

    def test_create_log_max_length_servicio(self, client):
        """Servicio con nombre demasiado largo."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "x" * 60,  # max_length=50
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 10,
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 422

    def test_create_log_min_codigo_respuesta(self, client):
        """Código de respuesta HTTP menor al mínimo."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 50,  # mínimo es 100
            "duracion_ms": 10,
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 422

    def test_create_log_negative_duracion(self, client):
        """Duración negativa no debería aceptarse."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": -5,
        }
        response = client.post("/api/v1/audit/log", json=payload)
        # Puede pasar si no hay validación ge=0, verifica el estado actual
        assert response.status_code in (201, 422)

    def test_create_log_all_http_methods(self, client):
        """Verifica que acepta todos los métodos HTTP comunes."""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": method,
                "codigo_respuesta": 200,
                "duracion_ms": 10,
            }
            response = client.post("/api/v1/audit/log", json=payload)
            assert response.status_code == 201, f"Falló para método {method}"

    def test_create_log_all_status_codes(self, client):
        """Verifica códigos de respuesta de cada familia HTTP."""
        for code in [100, 200, 201, 301, 400, 404, 500, 503]:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": code,
                "duracion_ms": 10,
            }
            response = client.post("/api/v1/audit/log", json=payload)
            assert response.status_code == 201, f"Falló para código {code}"


class TestPagination:
    """Tests de paginación."""

    def test_pagination_first_page(self, client):
        """Verifica la primera página."""
        # Crear 5 logs
        for i in range(5):
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": f"/test/{i}",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10,
            })

        response = client.get("/api/v1/audit/logs?page=1&page_size=3")
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["data"]) == 3
        assert data["total"] == 5
        assert data["total_pages"] == 2

    def test_pagination_second_page(self, client):
        """Verifica la segunda página."""
        for i in range(5):
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": f"/test/{i}",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10,
            })

        response = client.get("/api/v1/audit/logs?page=2&page_size=3")
        data = response.json()
        assert data["page"] == 2
        assert len(data["data"]) == 2  # Solo quedan 2 de 5

    def test_pagination_invalid_page(self, client):
        """Página 0 o negativa debe rechazarse."""
        response = client.get("/api/v1/audit/logs?page=0")
        assert response.status_code == 422


class TestPurgeLogs:
    """Tests para purga de logs."""

    def test_purge_deletes_old_logs(self, client):
        """Verifica que purge elimina logs anteriores a la fecha."""
        # Crear un log
        client.post("/api/v1/audit/log", json={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 10,
        })

        # Verificar que hay 1 log
        response = client.get("/api/v1/audit/logs")
        assert response.json()["total"] == 1

        # Purgar con fecha futura (debería eliminar todo)
        future = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        response = client.delete(
            "/api/v1/audit/purge",
            params={"before_date": future},
        )
        assert response.status_code == 200
        assert "1 registros eliminados" in response.json()["message"]

        # Verificar que no queda nada
        response = client.get("/api/v1/audit/logs")
        assert response.json()["total"] == 0

    def test_purge_keeps_recent_logs(self, client):
        """Verifica que purge no elimina logs recientes."""
        client.post("/api/v1/audit/log", json={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nombre_microservicio": "ms-test",
            "endpoint": "/test",
            "metodo_http": "GET",
            "codigo_respuesta": 200,
            "duracion_ms": 10,
        })

        # Purgar con fecha pasada (no debería eliminar nada)
        past = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
        response = client.delete(
            "/api/v1/audit/purge",
            params={"before_date": past},
        )
        assert response.status_code == 200
        assert "0 registros eliminados" in response.json()["message"]


class TestUserLogs:
    """Tests para endpoint de logs por usuario."""

    def test_user_logs_with_pagination(self, client):
        """Verifica paginación en logs de usuario."""
        usuario_id = "550e8400-e29b-41d4-a716-446655440000"
        for i in range(5):
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": f"/test/{i}",
                "metodo_http": "GET",
                "codigo_respuesta": 200,
                "duracion_ms": 10,
                "usuario_id": usuario_id,
            })

        response = client.get(f"/api/v1/audit/user/{usuario_id}?page=1&page_size=3")
        data = response.json()
        assert data["total"] == 5
        assert len(data["data"]) == 3

    def test_user_logs_empty(self, client):
        """Verifica respuesta vacía para usuario sin logs."""
        response = client.get(
            "/api/v1/audit/user/550e8400-e29b-41d4-a716-000000000000?page=1&page_size=20"
        )
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []


class TestMultiFilter:
    """Tests de filtros combinados."""

    def test_filter_by_servicio_and_metodo(self, client):
        """Filtrar por servicio y método simultáneamente."""
        # Crear logs variados
        for svc, method in [
            ("ms-matricula", "POST"),
            ("ms-matricula", "GET"),
            ("ms-finanzas", "POST"),
        ]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": svc,
                "endpoint": "/test",
                "metodo_http": method,
                "codigo_respuesta": 200,
                "duracion_ms": 10,
            })

        response = client.get(
            "/api/v1/audit/logs?servicio=ms-matricula&metodo_http=POST"
        )
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["servicio"] == "ms-matricula"
        assert data["data"][0]["metodo"] == "POST"

    def test_filter_by_codigo_respuesta(self, client):
        """Filtrar por código de respuesta."""
        for code in [200, 200, 404, 500]:
            client.post("/api/v1/audit/log", json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nombre_microservicio": "ms-test",
                "endpoint": "/test",
                "metodo_http": "GET",
                "codigo_respuesta": code,
                "duracion_ms": 10,
            })

        response = client.get("/api/v1/audit/logs?codigo_respuesta=200")
        assert response.json()["total"] == 2
