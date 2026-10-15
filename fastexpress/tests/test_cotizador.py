"""Pruebas unitarias del algoritmo de cotización (BR-01 a BR-04).

Incluyen particiones de equivalencia, valores límite (BVA) del peso y la
tabla de decisión Tipo de Cliente x Tipo de Envío.
"""

from decimal import Decimal

import pytest

from fastexpress import (
    LimiteExcedidoError,
    PesoInvalidoError,
    TipoCliente,
    TipoClienteInvalidoError,
    TipoEnvio,
    TipoEnvioInvalidoError,
    calcular_cotizacion,
)

D = Decimal


# ---------------------------------------------------------------------------
# BR-01 + BR-02: peso (particiones y valores límite) con NUEVO / ESTANDAR
# para aislar el cálculo por peso.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "peso, tarifa_kg, costo_peso, total",
    [
        ("0.01", "2.00", "0.02", "5.02"),   # límite inferior válido
        ("0.02", "2.00", "0.04", "5.04"),   # límite inferior + 1
        ("2.50", "2.00", "5.00", "10.00"),  # valor típico tramo 1
        ("4.99", "2.00", "9.98", "14.98"),  # límite superior tramo 1 - 1
        ("5.00", "2.00", "10.00", "15.00"), # límite superior tramo 1
        ("5.01", "4.00", "20.04", "25.04"), # límite inferior tramo 2
        ("12.00", "4.00", "48.00", "53.00"),# valor típico tramo 2
        ("19.99", "4.00", "79.96", "84.96"),# límite superior tramo 2 - 1
        ("20.00", "4.00", "80.00", "85.00"),# límite superior permitido
    ],
)
def test_peso_valido_por_tramo(peso, tarifa_kg, costo_peso, total):
    c = calcular_cotizacion(peso, "NUEVO", "ESTANDAR")
    assert c.tarifa_base == D("5.00")
    assert c.tarifa_por_kg == D(tarifa_kg)
    assert c.costo_peso == D(costo_peso)
    assert c.total == D(total)


@pytest.mark.parametrize("peso", ["20.01", "25", "1000"])
def test_peso_mayor_a_20_rechaza_envio(peso):
    with pytest.raises(LimiteExcedidoError) as error:
        calcular_cotizacion(peso, "NUEVO", "ESTANDAR")
    assert error.value.codigo == "LIMITE_EXCEDIDO"


@pytest.mark.parametrize("peso", ["0", "0.00", "0.009", "-0.01", "-5"])
def test_peso_menor_al_minimo_es_invalido(peso):
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion(peso, "NUEVO", "ESTANDAR")


@pytest.mark.parametrize(
    "peso", [None, "", "abc", "5kg", True, False, "NaN", "Infinity", float("inf")]
)
def test_peso_no_numerico_es_invalido(peso):
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion(peso, "NUEVO", "ESTANDAR")


@pytest.mark.parametrize("peso", [3, 3.0, D("3"), " 3 "])
def test_peso_acepta_distintos_tipos_numericos(peso):
    assert calcular_cotizacion(peso, "NUEVO", "ESTANDAR").total == D("11.00")


# ---------------------------------------------------------------------------
# BR-03 + BR-04: tabla de decisión Tipo de Cliente x Tipo de Envío.
# Peso fijo 10 kg -> subtotal = 5 + 10 x 4 = 45.00
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "regla, cliente, envio, recargo, descuento, total",
    [
        ("R1", "NUEVO", "ESTANDAR", "0.00", "0.00", "45.00"),
        ("R2", "NUEVO", "EXPRESS", "11.25", "0.00", "56.25"),
        ("R3", "FRECUENTE", "ESTANDAR", "0.00", "4.50", "40.50"),
        ("R4", "FRECUENTE", "EXPRESS", "11.25", "5.63", "50.62"),
        ("R5", "VIP", "ESTANDAR", "0.00", "9.00", "36.00"),
        ("R6", "VIP", "EXPRESS", "11.25", "11.25", "45.00"),
    ],
)
def test_tabla_de_decision_cliente_envio(regla, cliente, envio, recargo, descuento, total):
    c = calcular_cotizacion("10", cliente, envio)
    assert c.subtotal == D("45.00"), regla
    assert c.recargo == D(recargo), regla
    assert c.descuento == D(descuento), regla
    assert c.total == D(total), regla
    assert c.tipo_cliente == TipoCliente(cliente)
    assert c.tipo_envio == TipoEnvio(envio)


def test_tipos_no_distinguen_mayusculas_ni_espacios():
    c = calcular_cotizacion("1", "  vip ", "express")
    assert c.tipo_cliente is TipoCliente.VIP
    assert c.tipo_envio is TipoEnvio.EXPRESS


def test_acepta_enums_como_entrada():
    c = calcular_cotizacion("1", TipoCliente.FRECUENTE, TipoEnvio.ESTANDAR)
    assert c.porcentaje_descuento == D("0.10")


@pytest.mark.parametrize("cliente", ["", None, "PREMIUM", "VIP1"])
def test_tipo_cliente_invalido(cliente):
    with pytest.raises(TipoClienteInvalidoError):
        calcular_cotizacion("1", cliente, "ESTANDAR")


@pytest.mark.parametrize("envio", ["", None, "URGENTE", "STANDARD"])
def test_tipo_envio_invalido(envio):
    with pytest.raises(TipoEnvioInvalidoError):
        calcular_cotizacion("1", "NUEVO", envio)


def test_peso_se_valida_antes_que_los_tipos():
    with pytest.raises(LimiteExcedidoError):
        calcular_cotizacion("21", "XXX", "YYY")


def test_redondeo_half_up_en_centavos():
    # 1.235 kg x 2 = 2.47; subtotal 7.47; FRECUENTE 10 % = 0.747 -> 0.75
    c = calcular_cotizacion("1.235", "FRECUENTE", "ESTANDAR")
    assert c.costo_peso == D("2.47")
    assert c.descuento == D("0.75")
    assert c.total == D("6.72")


def test_a_dict_serializa_desglose():
    datos = calcular_cotizacion("10", "VIP", "EXPRESS").a_dict()
    assert datos == {
        "peso": 10.0,
        "tipo_cliente": "VIP",
        "tipo_envio": "EXPRESS",
        "tarifa_base": 5.0,
        "tarifa_por_kg": 4.0,
        "costo_peso": 40.0,
        "subtotal": 45.0,
        "porcentaje_recargo": 0.25,
        "recargo": 11.25,
        "porcentaje_descuento": 0.2,
        "descuento": 11.25,
        "total": 45.0,
        "moneda": "USD",
    }


# ---------------------------------------------------------------------------
# Monto (total cotizado): particiones y valores límite de la salida.
# Rango alcanzable: tramo 1 [4.02, 18.75] y tramo 2 [20.03, 106.25].
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "caso, peso, cliente, envio, total",
    [
        ("M1", "0.01", "VIP", "ESTANDAR", "4.02"),     # monto mínimo posible
        ("M2", "0.02", "VIP", "ESTANDAR", "4.03"),     # mínimo + 1 paso
        ("M3", "4.99", "NUEVO", "EXPRESS", "18.73"),   # máximo tramo 1 - 1 paso
        ("M4", "5.00", "NUEVO", "EXPRESS", "18.75"),   # monto máximo tramo 1
        ("M5", "5.01", "VIP", "ESTANDAR", "20.03"),    # monto mínimo tramo 2
        ("M6", "5.02", "VIP", "ESTANDAR", "20.06"),    # mínimo tramo 2 + 1 paso
        ("M7", "19.99", "NUEVO", "EXPRESS", "106.20"), # máximo - 1 paso
        ("M8", "20.00", "NUEVO", "EXPRESS", "106.25"), # monto máximo posible
    ],
)
def test_monto_valores_limite(caso, peso, cliente, envio, total):
    assert calcular_cotizacion(peso, cliente, envio).total == D(total), caso


# ---------------------------------------------------------------------------
# Caja blanca: un caso por cada camino independiente del CFG de
# calcular_cotizacion() (V(G) = 9). Ver el informe técnico, sección 3.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "camino, peso, cliente, envio, esperado",
    [
        ("C1", "0", "NUEVO", "ESTANDAR", PesoInvalidoError),
        ("C2", "25", "NUEVO", "ESTANDAR", LimiteExcedidoError),
        ("C3", "2.50", "NUEVO", "ESTANDAR", "10.00"),
        ("C4", "12", "NUEVO", "ESTANDAR", "53.00"),
        ("C5", "1", "FRECUENTE", "ESTANDAR", "6.30"),
        ("C6", "1", "VIP", "ESTANDAR", "5.60"),
        ("C7", "1", "PREMIUM", "ESTANDAR", TipoClienteInvalidoError),
        ("C8", "1", "NUEVO", "EXPRESS", "8.75"),
        ("C9", "1", "NUEVO", "URGENTE", TipoEnvioInvalidoError),
    ],
)
def test_caminos_independientes_cfg(camino, peso, cliente, envio, esperado):
    if isinstance(esperado, type):
        with pytest.raises(esperado):
            calcular_cotizacion(peso, cliente, envio)
    else:
        assert calcular_cotizacion(peso, cliente, envio).total == D(esperado), camino
