"""
Tests de persistencia: puntos de control (CRUD), historial de alertas y el
estado de la base de datos en /api/health.
"""


def test_health_reporta_base_de_datos(client):
    respuesta = client.get("/api/health")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["database_status"] == "operativo"


def test_punto_por_defecto_sembrado(client):
    respuesta = client.get("/api/puntos")
    assert respuesta.status_code == 200
    nombres = [p["nombre"] for p in respuesta.json()]
    assert "Fundo Pacomarca" in nombres


def test_ciclo_de_vida_de_punto(client):
    # Crear
    creacion = client.post(
        "/api/puntos",
        json={"nombre": "Cancha norte", "lat": -14.86, "lon": -70.93, "notas": "Pradera húmeda"},
    )
    assert creacion.status_code == 201
    punto = creacion.json()
    assert punto["id"] > 0
    assert punto["nombre"] == "Cancha norte"

    # Aparece en el listado
    listado = client.get("/api/puntos").json()
    assert any(p["id"] == punto["id"] for p in listado)

    # Editar solo el nombre
    edicion = client.patch(f"/api/puntos/{punto['id']}", json={"nombre": "Cancha sur"})
    assert edicion.status_code == 200
    assert edicion.json()["nombre"] == "Cancha sur"
    assert edicion.json()["lat"] == punto["lat"]  # sin tocar el resto

    # Eliminar
    borrado = client.delete(f"/api/puntos/{punto['id']}")
    assert borrado.status_code == 204
    assert all(p["id"] != punto["id"] for p in client.get("/api/puntos").json())


def test_punto_inexistente_da_404(client):
    assert client.patch("/api/puntos/9999", json={"nombre": "x"}).status_code == 404
    assert client.delete("/api/puntos/9999").status_code == 404


def test_punto_invalido_da_422(client):
    # Latitud fuera de rango y nombre vacío tras recortar espacios
    respuesta = client.post("/api/puntos", json={"nombre": "  ", "lat": 999, "lon": 0})
    assert respuesta.status_code == 422
    detalle = str(respuesta.json())
    assert "lat" in detalle or "nombre" in detalle


def test_registrar_y_listar_alertas(client):
    creacion = client.post(
        "/api/alertas",
        json={
            "lat": -14.85,
            "lon": -70.92,
            "indice": "biomasa",
            "valor_actual": 700.0,
            "promedio_historico": 980.0,
            "anomalia_pct": -28.6,
            "severidad": "critica",
            "mensaje": "Degradación severa detectada por el job diario.",
        },
    )
    assert creacion.status_code == 201
    alerta = creacion.json()
    assert alerta["severidad"] == "critica"

    listado = client.get("/api/alertas").json()
    assert any(a["id"] == alerta["id"] for a in listado)

    # Filtro por punto inexistente -> 404 al registrar
    respuesta = client.post(
        "/api/alertas",
        json={
            "lat": -14.85,
            "lon": -70.92,
            "valor_actual": 1.0,
            "promedio_historico": 1.0,
            "anomalia_pct": -1.0,
            "punto_id": 9999,
        },
    )
    assert respuesta.status_code == 404


def test_alerta_con_severidad_invalida_da_422(client):
    respuesta = client.post(
        "/api/alertas",
        json={
            "lat": 0,
            "lon": 0,
            "valor_actual": 1,
            "promedio_historico": 1,
            "anomalia_pct": -1,
            "severidad": "catastrófica",
        },
    )
    assert respuesta.status_code == 422
