"""Pruebas de extremo a extremo del frontend (navegador real con Playwright).

Son opcionales: si Playwright o su navegador no están instalados, se omiten.
Instalación: pip install playwright && python -m playwright install chromium
"""

import os
import threading

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from werkzeug.serving import make_server  # noqa: E402

from fastexpress.api import create_app  # noqa: E402


@pytest.fixture(scope="module")
def servidor():
    app = create_app()
    srv = make_server("127.0.0.1", 0, app)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield app, f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture(scope="module")
def navegador():
    with sync_api.sync_playwright() as p:
        try:
            # CHROMIUM_PATH permite usar un Chromium ya instalado en el equipo.
            browser = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH"))
        except Exception as error:  # navegador no instalado
            pytest.skip(f"Chromium no disponible: {error}")
        yield browser
        browser.close()


@pytest.fixture
def pagina(servidor, navegador):
    app, url = servidor
    cliente = app.test_client()
    page = navegador.new_page()

    # Fuera del puerto 5000 el frontend llama a http://127.0.0.1:5000; se
    # redirige esa llamada a la app de prueba para no depender de otro proceso.
    def a_la_app(route):
        respuesta = cliente.post(
            "/api/cotizaciones",
            data=route.request.post_data,
            content_type="application/json",
        )
        route.fulfill(
            status=respuesta.status_code,
            body=respuesta.get_data(),
            headers={"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        )

    page.route("http://127.0.0.1:5000/api/cotizaciones", a_la_app)
    page.goto(url + "/")
    yield page
    page.close()


def _cotizar(page, peso, cliente="NUEVO", envio="ESTANDAR"):
    page.fill("#peso", peso)
    page.select_option("#tipo_cliente", cliente)
    page.select_option("#tipo_envio", envio)
    page.click("#btn-cotizar")


def test_muestra_desglose_de_cotizacion_valida(pagina):
    _cotizar(pagina, "20", "NUEVO", "ESTANDAR")
    pagina.wait_for_selector("#resultado:not([hidden])")
    assert pagina.text_content("#r-total").replace("\xa0", " ").strip() == "$85,00"


def test_error_de_validacion_oculta_la_cotizacion_anterior(pagina):
    # DEF-03: tras cotizar 20 kg, ingresar 20.01 mostraba el error pero
    # dejaba visible el desglose anterior de $85,00.
    _cotizar(pagina, "20")
    pagina.wait_for_selector("#resultado:not([hidden])")
    _cotizar(pagina, "20.01")
    assert "Límite excedido" in pagina.text_content("#error-peso")
    assert pagina.is_hidden("#resultado")
