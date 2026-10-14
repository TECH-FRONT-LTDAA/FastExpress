"""Excepciones de dominio del cotizador.

Cada excepción lleva un ``codigo`` estable que la API devuelve al cliente,
de modo que el frontend y las pruebas no dependan del texto del mensaje.
"""


class CotizacionError(ValueError):
    """Error base de cualquier cotización rechazada."""

    codigo = "COTIZACION_INVALIDA"

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class EntradaInvalidaError(CotizacionError):
    """Dato de entrada con formato o valor no válido (HTTP 400)."""

    codigo = "ENTRADA_INVALIDA"


class PesoInvalidoError(EntradaInvalidaError):
    """Peso no numérico o menor al mínimo permitido (0.01 kg)."""

    codigo = "PESO_INVALIDO"


class TipoClienteInvalidoError(EntradaInvalidaError):
    """Tipo de cliente fuera de NUEVO, FRECUENTE o VIP."""

    codigo = "TIPO_CLIENTE_INVALIDO"


class TipoEnvioInvalidoError(EntradaInvalidaError):
    """Tipo de envío fuera de ESTANDAR o EXPRESS."""

    codigo = "TIPO_ENVIO_INVALIDO"


class LimiteExcedidoError(CotizacionError):
    """Regla de negocio BR-02: peso mayor a 20.00 kg (HTTP 422)."""

    codigo = "LIMITE_EXCEDIDO"
