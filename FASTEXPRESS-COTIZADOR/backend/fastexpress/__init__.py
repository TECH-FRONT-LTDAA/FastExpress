"""FastExpress: módulo de cotización de envíos y descuentos."""

from .cotizador import Cotizacion, calcular_cotizacion
from .errores import (
    CotizacionError,
    EntradaInvalidaError,
    LimiteExcedidoError,
    PesoInvalidoError,
    TipoClienteInvalidoError,
    TipoEnvioInvalidoError,
)
from .reglas import TipoCliente, TipoEnvio

__all__ = [
    "Cotizacion",
    "calcular_cotizacion",
    "CotizacionError",
    "EntradaInvalidaError",
    "LimiteExcedidoError",
    "PesoInvalidoError",
    "TipoClienteInvalidoError",
    "TipoEnvioInvalidoError",
    "TipoCliente",
    "TipoEnvio",
]
