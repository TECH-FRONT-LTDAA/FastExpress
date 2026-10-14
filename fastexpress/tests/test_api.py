"""Pruebas de la API REST de FastExpress."""

import pytest

from fastexpress.api import create_app


@pytest.fixture
def cliente():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _cotizar(cliente, **datos):
    return cliente.post("/api/cotizaciones", json=datos)


def test_salud(cliente):
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "ok"


def test_tarifas_expone_reglas(cliente):
    datos = cliente.get("/api/tarifas").get_json()
    assert datos["tarifa_base"] == 5.0
    assert datos["peso"]["maximo_kg"] == 20.0
    assert datos["descuentos_cliente"]["VIP"] == 0.2
    assert datos["recargos_envio"]["EXPRESS"] == 0.25


def test_cotizacion_exitosa(cliente):
    respuesta = _cotizar(cliente, peso=10, tipo_cliente="VIP", tipo_envio="EXPRESS")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["subtotal"] == 45.0
    assert cuerpo["total"] == 45.0
    assert cuerpo["moneda"] == "USD"


def test_limite_excedido_responde_422(cliente):
    respuesta = _cotizar(cliente, peso=20.01, tipo_cliente="NUEVO", tipo_envio="ESTANDAR")
    assert respuesta.status_code == 422
    assert respuesta.get_json()["error"]["codigo"] == "LIMITE_EXCEDIDO"


@pytest.mark.parametrize(
    "datos, codigo",
    [
        ({"peso": 0, "tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "PESO_INVALIDO"),
        ({"peso": "abc", "tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "PESO_INVALIDO"),
        ({"tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "PESO_INVALIDO"),
        ({"peso": 1, "tipo_cliente": "OTRO", "tipo_envio": "ESTANDAR"}, "TIPO_CLIENTE_INVALIDO"),
        ({"peso": 1, "tipo_cliente": "NUEVO", "tipo_envio": "OTRO"}, "TIPO_ENVIO_INVALIDO"),
    ],
)
def test_entradas_invalidas_responden_400(cliente, datos, codigo):
    respuesta = _cotizar(cliente, **datos)
    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]["codigo"] == codigo


@pytest.mark.parametrize("cuerpo", ["no es json", "[1, 2, 3]", ""])
def test_cuerpo_no_objeto_json_responde_400(cliente, cuerpo):
    respuesta = cliente.post(
        "/api/cotizaciones", data=cuerpo, content_type="application/json"
    )
    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]["codigo"] == "JSON_INVALIDO"


def test_sirve_frontend(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert b"FastExpress" in respuesta.data
    assert cliente.get("/app.js").status_code == 200


def test_permite_cors_para_frontend_externo(cliente):
    respuesta = cliente.options(
        "/api/cotizaciones",
        headers={
            "Origin": "http://127.0.0.1:5500",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.headers["Access-Control-Allow-Origin"] == "*"
    assert "Content-Type" in respuesta.headers["Access-Control-Allow-Headers"]
