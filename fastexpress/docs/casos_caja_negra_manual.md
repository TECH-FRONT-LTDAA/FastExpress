# Ejecución manual de pruebas de caja negra – FastExpress

**Preparación:** levante el backend (`cd backend` → `python -m fastexpress.api`) y abra http://127.0.0.1:5000 o el frontend con Live Server.
**Evidencia:** tome una captura por caso que muestre los datos ingresados y el resultado, y guárdela con el ID del caso (por ejemplo, `CN-05.png`).
Los montos aparecen en la página con coma decimal: $15,00 equivale a $15.00.

## A. Peso: particiones y valores límite (cliente Nuevo, envío Estándar)

| ID | Ref. informe | Peso (kg) | Cliente | Envío | Resultado esperado | Resultado obtenido | ¿Pasa? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CN-01 | CI-P3 | (vacío) | Nuevo | Estándar | Mensaje: "Ingrese un peso numérico." | | |
| CN-02 | BVA-P1 | 0 | Nuevo | Estándar | Mensaje: "El peso mínimo es 0.01 kg." | | |
| CN-03 | CI-P1 | -5 | Nuevo | Estándar | Mensaje: "El peso mínimo es 0.01 kg." | | |
| CN-04 | BVA-P2 | 0.01 | Nuevo | Estándar | Total $5,02 | | |
| CN-05 | BVA-P4 | 4.99 | Nuevo | Estándar | Total $14,98 | | |
| CN-06 | BVA-P5 | 5.00 | Nuevo | Estándar | Total $15,00 (tarifa $2,00/kg) | | |
| CN-07 | BVA-P6 | 5.01 | Nuevo | Estándar | Total $25,04 (tarifa $4,00/kg) | | |
| CN-08 | BVA-P7 | 19.99 | Nuevo | Estándar | Total $84,96 | | |
| CN-09 | BVA-P8 | 20.00 | Nuevo | Estándar | Total $85,00 | | |
| CN-10 | BVA-P9 | 20.01 | Nuevo | Estándar | Mensaje: "Límite excedido: el peso máximo es 20 kg." | | |

## B. Tabla de decisión: Cliente × Envío (peso 10 kg, subtotal $45,00)

| ID | Ref. informe | Peso (kg) | Cliente | Envío | Recargo | Descuento | Total esperado | Resultado obtenido | ¿Pasa? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CN-11 | R1 | 10 | Nuevo | Estándar | $0,00 | $0,00 | $45,00 | | |
| CN-12 | R2 | 10 | Nuevo | Express | $11,25 | $0,00 | $56,25 | | |
| CN-13 | R3 | 10 | Frecuente | Estándar | $0,00 | $4,50 | $40,50 | | |
| CN-14 | R4 | 10 | Frecuente | Express | $11,25 | $5,63 | $50,62 | | |
| CN-15 | R5 | 10 | VIP | Estándar | $0,00 | $9,00 | $36,00 | | |
| CN-16 | R6 | 10 | VIP | Express | $11,25 | $11,25 | $45,00 | | |

## C. Monto mínimo y máximo, y campos obligatorios

| ID | Ref. informe | Peso (kg) | Cliente | Envío | Resultado esperado | Resultado obtenido | ¿Pasa? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CN-17 | BVA-M1 | 0.01 | VIP | Estándar | Total $4,02 (monto mínimo posible) | | |
| CN-18 | BVA-M8 | 20.00 | Nuevo | Express | Total $106,25 (monto máximo posible) | | |
| CN-19 | — | 3 | (sin seleccionar) | Estándar | Mensaje: "Seleccione el tipo de cliente." | | |
| CN-20 | — | 3 | Nuevo | (sin seleccionar) | Mensaje: "Seleccione el tipo de envío." | | |

Nota: los casos CN-01, CN-02, CN-03, CN-10, CN-19 y CN-20 los detiene la validación del frontend antes de llegar a la API. El rechazo del backend (HTTP 400 y 422) ya está cubierto por las pruebas automatizadas de `tests/test_api.py`.
