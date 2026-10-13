// Cliente del cotizador FastExpress.
// Validación básica en la UI; la validación definitiva la hace el backend.

// Si la página la sirve Flask (puerto 5000) se usa la ruta relativa; si se abre
// con otro servidor (p. ej. Live Server en el 5500) se apunta al backend local.
const API_BASE = window.location.port === "5000" ? "" : "http://127.0.0.1:5000";
const API_URL = `${API_BASE}/api/cotizaciones`;
const PESO_MIN = 0.01;
const PESO_MAX = 20;

const form = document.getElementById("form-cotizacion");
const seccionResultado = document.getElementById("resultado");
const seccionMensaje = document.getElementById("mensaje");

const usd = new Intl.NumberFormat("es-EC", { style: "currency", currency: "USD" });

function validar(datos) {
  const errores = {};
  const peso = Number(datos.peso);
  if (datos.peso === "" || Number.isNaN(peso)) {
    errores.peso = "Ingrese un peso numérico.";
  } else if (peso < PESO_MIN) {
    errores.peso = `El peso mínimo es ${PESO_MIN} kg.`;
  } else if (peso > PESO_MAX) {
    errores.peso = `Límite excedido: el peso máximo es ${PESO_MAX} kg.`;
  }
  if (!datos.tipo_cliente) errores.tipo_cliente = "Seleccione el tipo de cliente.";
  if (!datos.tipo_envio) errores.tipo_envio = "Seleccione el tipo de envío.";
  return errores;
}

function mostrarErrores(errores) {
  for (const campo of ["peso", "tipo_cliente", "tipo_envio"]) {
    document.getElementById(`error-${campo}`).textContent = errores[campo] || "";
  }
}

function mostrarMensaje(texto) {
  seccionMensaje.textContent = texto;
  seccionMensaje.hidden = false;
  seccionResultado.hidden = true;
}

function mostrarResultado(c) {
  seccionMensaje.hidden = true;
  document.getElementById("r-tarifa_base").textContent = usd.format(c.tarifa_base);
  document.getElementById("r-costo_peso").textContent =
    `${usd.format(c.costo_peso)} (${c.peso} kg × ${usd.format(c.tarifa_por_kg)})`;
  document.getElementById("r-subtotal").textContent = usd.format(c.subtotal);
  document.getElementById("r-recargo").textContent =
    `+ ${usd.format(c.recargo)} (${Math.round(c.porcentaje_recargo * 100)} %)`;
  document.getElementById("r-descuento").textContent =
    `− ${usd.format(c.descuento)} (${Math.round(c.porcentaje_descuento * 100)} %)`;
  document.getElementById("r-total").textContent = usd.format(c.total);
  seccionResultado.hidden = false;
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const datos = Object.fromEntries(new FormData(form));
  const errores = validar(datos);
  mostrarErrores(errores);
  if (Object.keys(errores).length > 0) return;

  try {
    const respuesta = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...datos, peso: Number(datos.peso) }),
    });
    const cuerpo = await respuesta.json();
    if (respuesta.ok) {
      mostrarResultado(cuerpo);
    } else {
      mostrarMensaje(cuerpo.error ? cuerpo.error.mensaje : "No se pudo cotizar.");
    }
  } catch {
    mostrarMensaje(
      "No hay conexión con el servidor de cotizaciones. " +
      "Verifique que el backend esté corriendo en http://127.0.0.1:5000."
    );
  }
});
