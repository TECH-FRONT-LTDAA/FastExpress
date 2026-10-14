# FastExpress: Módulo de Cotización de Envíos y Descuentos

Proyecto integrador de Calidad de Software. Backend en Python (Flask), frontend en HTML/JS y pruebas automatizadas con PyTest y pytest-cov.

**Equipo:** Ruben Coronel (Backend), Dilan Ariza (Frontend) y Marcos Arce (QA).

## Estructura

```
fastexpress/
├── backend/fastexpress/
│   ├── reglas.py       # Constantes de negocio BR-01..BR-04 y enums
│   ├── errores.py      # Excepciones de dominio con código estable
│   ├── cotizador.py    # Algoritmo principal: calcular_cotizacion()
│   └── api.py          # API REST (Flask) + servidor del frontend
├── frontend/           # index.html, app.js, styles.css
├── tests/              # test_cotizador.py (unitarias), test_api.py (API)
├── pytest.ini          # Configuración de PyTest + cobertura (mínimo 85 %)
└── requirements.txt
```

## Funcionamiento

1. **Frontend** (`index.html` + `app.js` + `styles.css`): el usuario ingresa peso, tipo de cliente y tipo de envío. `app.js` valida en el navegador (peso entre 0.01 y 20, campos obligatorios) y envía un `POST` con JSON a `http://127.0.0.1:5000/api/cotizaciones`.
2. **API** (`api.py`): recibe el JSON, llama a `calcular_cotizacion()` y traduce el resultado a HTTP: 200 con el desglose, 400 si la entrada es inválida, 422 si el peso supera 20 kg.
3. **Cálculo** (`cotizador.py`): convierte el peso, elige la tarifa por kg (BR-02), el descuento (BR-03) y el recargo (BR-04), y suma la tarifa base (BR-01).
4. **Respuesta**: el frontend pinta la tabla de desglose o el mensaje de error.

Los tres archivos del frontend deben estar en la misma carpeta. Si `app.js` no carga, el formulario se envía como un formulario HTML normal, la URL termina en `?peso=&tipo_cliente=...` y no aparece el desglose.

## Ejecución

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Pruebas + reporte de cobertura (líneas y ramas) en reportes/cobertura/index.html
pytest

# Opcional: pruebas de navegador (tests/test_frontend_e2e.py); se omiten si falta Playwright
# pip install playwright && python -m playwright install chromium

# Levantar la aplicación en http://127.0.0.1:5000 (backend + frontend)
cd backend && python -m fastexpress.api
```

Abra http://127.0.0.1:5000 en el navegador. También puede abrir `frontend/index.html` con Live Server (puerto 5500), siempre que el backend siga corriendo en otra terminal: el frontend detecta el puerto y llama a la API en el 5000.

## Reglas de negocio implementadas

| Regla | Descripción | Implementación |
|---|---|---|
| BR-01 | Tarifa base de $5.00 por orden | `reglas.TARIFA_BASE` |
| BR-02 | 0.01–5.00 kg: $2.00/kg · 5.01–20.00 kg: $4.00/kg · > 20.00 kg: rechazo | `LimiteExcedidoError` (HTTP 422) |
| BR-03 | Descuento NUEVO 0 %, FRECUENTE 10 %, VIP 20 % | `reglas.DESCUENTO_*` |
| BR-04 | Recargo ESTANDAR 0 %, EXPRESS +25 % sobre el subtotal | `reglas.RECARGO_*` |

### Supuestos de diseño (para validar con el docente)

1. **Tarifa por peso no escalonada:** se cobra todo el peso a la tarifa del tramo. Ejemplo: 10 kg = 10 × $4.00 = $40.00.
2. **Orden de cálculo:** subtotal = base + costo por peso; recargo = subtotal × %; descuento = (subtotal + recargo) × %; total = subtotal + recargo − descuento. Al ser porcentajes multiplicativos, el total es el mismo en cualquier orden; solo cambia el monto del descuento mostrado.
3. **Peso mínimo 0.01 kg:** 0, negativos y no numéricos se rechazan con `PESO_INVALIDO` (HTTP 400).
4. **Hueco entre 5.00 y 5.01:** cualquier peso > 5.00 y ≤ 20.00 usa el tramo 2 (p. ej. 5.005 kg).
5. **Redondeo:** a centavos con ROUND_HALF_UP en cada monto intermedio.
6. **Tipos de cliente y envío:** no distinguen mayúsculas ni espacios (`" vip "` = `VIP`).
7. **Orden de validación:** primero el peso, luego cliente y por último envío.

## API REST

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/api/salud` | `{"estado": "ok"}` |
| GET | `/api/tarifas` | Reglas vigentes |
| POST | `/api/cotizaciones` | 200 desglose · 400 entrada inválida · 422 límite excedido |

Ejemplo:

```bash
curl -X POST http://127.0.0.1:5000/api/cotizaciones \
  -H "Content-Type: application/json" \
  -d '{"peso": 3.5, "tipo_cliente": "FRECUENTE", "tipo_envio": "EXPRESS"}'
# subtotal 12.00, recargo 3.00, descuento 1.50, total 13.50
```

Errores: `{"error": {"codigo": "LIMITE_EXCEDIDO", "mensaje": "..."}}`. Códigos: `JSON_INVALIDO`, `PESO_INVALIDO`, `TIPO_CLIENTE_INVALIDO`, `TIPO_ENVIO_INVALIDO`, `LIMITE_EXCEDIDO`.

## Notas para el QA (caja blanca)

`calcular_cotizacion()` en `cotizador.py` es el algoritmo principal para el CFG. Tiene 8 nodos predicado (3 de peso, 3 de cliente, 2 de envío), por lo que **V(G) = P + 1 = 9** caminos independientes. Las conversiones de entrada (`convertir_peso`, `normalizar_texto`) están separadas para no inflar el grafo del algoritmo principal.

Estado actual: 82 pruebas aprobadas, **100 % de cobertura de líneas y ramas** y 20 de 20 casos manuales de caja negra aprobados (evidencias en `docs/evidencias/`).
