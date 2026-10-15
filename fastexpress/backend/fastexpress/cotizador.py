"""Algoritmo principal de cotización de envíos FastExpress.

Orden de cálculo:
    1. costo_peso   = peso x tarifa_por_kg            (BR-02)
    2. subtotal     = TARIFA_BASE + costo_peso        (BR-01)
    3. recargo      = subtotal x %recargo             (BR-04)
    4. descuento    = (subtotal + recargo) x %descuento (BR-03)
    5. total        = subtotal + recargo - descuento

Los montos se redondean a centavos con ROUND_HALF_UP en cada paso.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import Enum

from . import reglas
from .errores import (
    LimiteExcedidoError,
    PesoInvalidoError,
    TipoClienteInvalidoError,
    TipoEnvioInvalidoError,
)
from .reglas import TipoCliente, TipoEnvio


@dataclass(frozen=True)
class Cotizacion:
    """Resultado desglosado de una cotización."""

    peso: Decimal
    tipo_cliente: TipoCliente
    tipo_envio: TipoEnvio
    tarifa_base: Decimal
    tarifa_por_kg: Decimal
    costo_peso: Decimal
    subtotal: Decimal
    porcentaje_recargo: Decimal
    recargo: Decimal
    porcentaje_descuento: Decimal
    descuento: Decimal
    total: Decimal

    def a_dict(self) -> dict:
        """Representación serializable a JSON (montos como float)."""
        return {
            "peso": float(self.peso),
            "tipo_cliente": self.tipo_cliente.value,
            "tipo_envio": self.tipo_envio.value,
            "tarifa_base": float(self.tarifa_base),
            "tarifa_por_kg": float(self.tarifa_por_kg),
            "costo_peso": float(self.costo_peso),
            "subtotal": float(self.subtotal),
            "porcentaje_recargo": float(self.porcentaje_recargo),
            "recargo": float(self.recargo),
            "porcentaje_descuento": float(self.porcentaje_descuento),
            "descuento": float(self.descuento),
            "total": float(self.total),
            "moneda": "USD",
        }


def _redondear(monto: Decimal) -> Decimal:
    return monto.quantize(reglas.CENTAVOS, rounding=ROUND_HALF_UP)


def convertir_peso(valor) -> Decimal:
    """Convierte la entrada a Decimal finito o lanza PesoInvalidoError."""
    if isinstance(valor, bool) or valor is None:
        raise PesoInvalidoError("El peso es obligatorio y debe ser numérico.")
    try:
        peso = Decimal(str(valor).strip())
    except (InvalidOperation, ValueError):
        raise PesoInvalidoError(f"El peso '{valor}' no es un número válido.") from None
    if not peso.is_finite():
        raise PesoInvalidoError("El peso debe ser un número finito.")
    return peso


def normalizar_texto(valor) -> str:
    """Pasa a mayúsculas y quita espacios; tolera None devolviendo ''.

    Si recibe un Enum usa su ``value``: desde Python 3.11 ``str()`` de un
    Enum devuelve 'Clase.MIEMBRO' y no el valor.
    """
    if valor is None:
        return ""
    if isinstance(valor, Enum):
        valor = valor.value
    return str(valor).strip().upper()


def calcular_cotizacion(peso, tipo_cliente, tipo_envio) -> Cotizacion:
    """Calcula la cotización de un envío aplicando BR-01 a BR-04.

    Args:
        peso: peso en kg (int, float, Decimal o texto numérico).
        tipo_cliente: NUEVO, FRECUENTE o VIP (no distingue mayúsculas).
        tipo_envio: ESTANDAR o EXPRESS (no distingue mayúsculas).

    Raises:
        PesoInvalidoError: peso no numérico o menor a 0.01 kg.
        LimiteExcedidoError: peso mayor a 20.00 kg.
        TipoClienteInvalidoError / TipoEnvioInvalidoError: tipo desconocido.
    """
    peso = convertir_peso(peso)
    cliente = normalizar_texto(tipo_cliente)
    envio = normalizar_texto(tipo_envio)

    # BR-02: tarifa por kg según el tramo de peso.
    if peso < reglas.PESO_MINIMO:
        raise PesoInvalidoError(
            f"El peso mínimo es {reglas.PESO_MINIMO} kg; se recibió {peso} kg."
        )
    elif peso <= reglas.PESO_LIMITE_TRAMO_1:
        tarifa_por_kg = reglas.TARIFA_KG_TRAMO_1
    elif peso <= reglas.PESO_MAXIMO:
        tarifa_por_kg = reglas.TARIFA_KG_TRAMO_2
    else:
        raise LimiteExcedidoError(
            f"Envío rechazado: el peso máximo es {reglas.PESO_MAXIMO} kg; "
            f"se recibió {peso} kg."
        )

    # BR-03: descuento por tipo de cliente.
    if cliente == TipoCliente.NUEVO.value:
        porcentaje_descuento = reglas.DESCUENTO_NUEVO
    elif cliente == TipoCliente.FRECUENTE.value:
        porcentaje_descuento = reglas.DESCUENTO_FRECUENTE
    elif cliente == TipoCliente.VIP.value:
        porcentaje_descuento = reglas.DESCUENTO_VIP
    else:
        raise TipoClienteInvalidoError(
            f"Tipo de cliente '{tipo_cliente}' no válido. "
            "Use NUEVO, FRECUENTE o VIP."
        )

    # BR-04: recargo por tipo de envío.
    if envio == TipoEnvio.ESTANDAR.value:
        porcentaje_recargo = reglas.RECARGO_ESTANDAR
    elif envio == TipoEnvio.EXPRESS.value:
        porcentaje_recargo = reglas.RECARGO_EXPRESS
    else:
        raise TipoEnvioInvalidoError(
            f"Tipo de envío '{tipo_envio}' no válido. Use ESTANDAR o EXPRESS."
        )

    # BR-01 + cálculo de montos.
    costo_peso = _redondear(peso * tarifa_por_kg)
    subtotal = reglas.TARIFA_BASE + costo_peso
    recargo = _redondear(subtotal * porcentaje_recargo)
    descuento = _redondear((subtotal + recargo) * porcentaje_descuento)
    total = subtotal + recargo - descuento

    return Cotizacion(
        peso=peso,
        tipo_cliente=TipoCliente(cliente),
        tipo_envio=TipoEnvio(envio),
        tarifa_base=reglas.TARIFA_BASE,
        tarifa_por_kg=tarifa_por_kg,
        costo_peso=costo_peso,
        subtotal=subtotal,
        porcentaje_recargo=porcentaje_recargo,
        recargo=recargo,
        porcentaje_descuento=porcentaje_descuento,
        descuento=descuento,
        total=total,
    )
