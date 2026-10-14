"""API REST de FastExpress (Flask).

Endpoints:
    GET  /api/salud         Verificación de que el servicio está activo.
    GET  /api/tarifas       Reglas de negocio vigentes.
    POST /api/cotizaciones  Calcula una cotización.
    GET  /                  Sirve el frontend.

Códigos de respuesta de POST /api/cotizaciones:
    200 Cotización calculada.
    400 Entrada inválida (JSON mal formado, peso o tipos no válidos).
    422 Envío rechazado por regla de negocio (peso > 20 kg).
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from . import reglas
from .cotizador import calcular_cotizacion
from .errores import EntradaInvalidaError, LimiteExcedidoError

DIRECTORIO_FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def _respuesta_error(codigo: str, mensaje: str, estado_http: int):
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), estado_http


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)

    @app.after_request
    def permitir_cors(respuesta):
        # Permite usar el frontend desde otro origen local (p. ej. Live Server).
        respuesta.headers["Access-Control-Allow-Origin"] = "*"
        respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
        respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return respuesta

    @app.get("/api/salud")
    def salud():
        return jsonify({"estado": "ok", "servicio": "FastExpress"})

    @app.get("/api/tarifas")
    def tarifas():
        return jsonify(
            {
                "moneda": "USD",
                "tarifa_base": float(reglas.TARIFA_BASE),
                "peso": {
                    "minimo_kg": float(reglas.PESO_MINIMO),
                    "maximo_kg": float(reglas.PESO_MAXIMO),
                    "tramos": [
                        {
                            "hasta_kg": float(reglas.PESO_LIMITE_TRAMO_1),
                            "tarifa_por_kg": float(reglas.TARIFA_KG_TRAMO_1),
                        },
                        {
                            "hasta_kg": float(reglas.PESO_MAXIMO),
                            "tarifa_por_kg": float(reglas.TARIFA_KG_TRAMO_2),
                        },
                    ],
                },
                "descuentos_cliente": {
                    "NUEVO": float(reglas.DESCUENTO_NUEVO),
                    "FRECUENTE": float(reglas.DESCUENTO_FRECUENTE),
                    "VIP": float(reglas.DESCUENTO_VIP),
                },
                "recargos_envio": {
                    "ESTANDAR": float(reglas.RECARGO_ESTANDAR),
                    "EXPRESS": float(reglas.RECARGO_EXPRESS),
                },
            }
        )

    @app.post("/api/cotizaciones")
    def crear_cotizacion():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return _respuesta_error(
                "JSON_INVALIDO", "El cuerpo debe ser un objeto JSON.", 400
            )
        try:
            cotizacion = calcular_cotizacion(
                datos.get("peso"),
                datos.get("tipo_cliente"),
                datos.get("tipo_envio"),
            )
        except LimiteExcedidoError as error:
            return _respuesta_error(error.codigo, error.mensaje, 422)
        except EntradaInvalidaError as error:
            return _respuesta_error(error.codigo, error.mensaje, 400)
        return jsonify(cotizacion.a_dict()), 200

    @app.get("/")
    def inicio():
        return send_from_directory(DIRECTORIO_FRONTEND, "index.html")

    @app.get("/<path:archivo>")
    def estaticos(archivo):
        return send_from_directory(DIRECTORIO_FRONTEND, archivo)

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app().run(host="127.0.0.1", port=5000, debug=True)
