"""Constantes de negocio del módulo FastExpress (BR-01 a BR-04).

Centralizar los valores aquí permite cambiarlos sin tocar el algoritmo
y facilita que las pruebas usen la misma fuente de verdad.
"""

from decimal import Decimal
from enum import Enum


class TipoCliente(str, Enum):
    """Tipos de cliente reconocidos (BR-03)."""

    NUEVO = "NUEVO"
    FRECUENTE = "FRECUENTE"
    VIP = "VIP"


class TipoEnvio(str, Enum):
    """Tipos de envío reconocidos (BR-04)."""

    ESTANDAR = "ESTANDAR"
    EXPRESS = "EXPRESS"


# BR-01: tarifa base fija por orden (USD).
TARIFA_BASE = Decimal("5.00")

# BR-02: rangos de peso (kg) y tarifa por kg (USD).
PESO_MINIMO = Decimal("0.01")
PESO_LIMITE_TRAMO_1 = Decimal("5.00")
PESO_MAXIMO = Decimal("20.00")
TARIFA_KG_TRAMO_1 = Decimal("2.00")
TARIFA_KG_TRAMO_2 = Decimal("4.00")

# BR-03: porcentaje de descuento por tipo de cliente.
DESCUENTO_NUEVO = Decimal("0.00")
DESCUENTO_FRECUENTE = Decimal("0.10")
DESCUENTO_VIP = Decimal("0.20")

# BR-04: porcentaje de recargo por tipo de envío.
RECARGO_ESTANDAR = Decimal("0.00")
RECARGO_EXPRESS = Decimal("0.25")

# Precisión monetaria: centavos.
CENTAVOS = Decimal("0.01")
