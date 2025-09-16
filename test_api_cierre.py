# ==test_api_cierre.py #022
import requests
import json
from datetime import date

# --- Configuración ---
BASE_URL = "http://127.0.0.1:8000"  # Dirección de tu servidor uvicorn
FECHA_PRUEBA = "2025-09-15"       # Fecha para la prueba

# --- 1. Crear/Actualizar un Cierre ---
print(f"\n--- 1. Creando/Actualizando Cierre para {FECHA_PRUEBA} ---")
url_crear = f"{BASE_URL}/cierre_ny_bch/"

# Datos de ejemplo para el cierre
datos_cierre = {
    "fecha": FECHA_PRUEBA,
    "tasa_cambio_bch": 24.5600,
    "precio_usd_saco": 152.00, # Este campo se mantiene por ahora
    # --- Precios de Posiciones ICE ---
    "precio_posicion_dic24": 148.50,
    "precio_posicion_mar25": 150.25,
    "precio_posicion_may25": 151.00,
    "precio_posicion_jul25": 151.75,
    "precio_posicion_sep25": 152.50,
    "precio_posicion_dic25": 153.25,
    "precio_posicion_mar26": 154.00,
    "precio_posicion_may26": 154.75,
    "precio_posicion_jul26": 155.50,
    "precio_posicion_sep26": 156.25,
    # --- Fuentes (opcionales, se llenan por defecto) ---
    "fuente_precio": "ICE Futures",
    "fuente_tasa": "Banco Central de Honduras"
}

headers = {'Content-Type': 'application/json'}

try:
    respuesta = requests.post(url_crear, data=json.dumps(datos_cierre), headers=headers)
    print(f"  Estado: {respuesta.status_code}")
    if respuesta.status_code in [200, 201]:
        datos_respuesta = respuesta.json()
        print(f"  ✅ ÉXITO: Cierre creado/actualizado para {datos_respuesta.get('fecha')}")
        print(f"     ID Registro: {datos_respuesta.get('id_registro')}")
        print(f"     Tasa BCH: {datos_respuesta.get('tasa_cambio_bch')}")
        print(f"     Precio Principal: {datos_respuesta.get('precio_usd_saco')}")
        # Mostrar un par de precios de posición como ejemplo
        print(f"     Precio DIC24: {datos_respuesta.get('precio_posicion_dic24')}")
        print(f"     Precio MAR25: {datos_respuesta.get('precio_posicion_mar25')}")
        print(f"     Fuente Precio: {datos_respuesta.get('fuente_precio')}")
        print(f"     Fuente Tasa: {datos_respuesta.get('fuente_tasa')}")
    else:
        print(f"  ❌ ERROR al crear/actualizar: {respuesta.text}")
except Exception as e:
    print(f"  ❌ EXCEPCIÓN al crear/actualizar: {e}")

# --- 2. Obtener el Cierre Creado/Actualizado ---
print(f"\n--- 2. Obteniendo Cierre para {FECHA_PRUEBA} ---")
url_obtener = f"{BASE_URL}/cierre_ny_bch/por_fecha/{FECHA_PRUEBA}"

try:
    respuesta = requests.get(url_obtener)
    print(f"  Estado: {respuesta.status_code}")
    if respuesta.status_code == 200:
        datos_respuesta = respuesta.json()
        print(f"  ✅ ÉXITO: Cierre encontrado para {datos_respuesta.get('fecha')}")
        print(f"     ID Registro: {datos_respuesta.get('id_registro')}")
        print(f"     Tasa BCH: {datos_respuesta.get('tasa_cambio_bch')}")
        print(f"     Precio Principal: {datos_respuesta.get('precio_usd_saco')}")
        # Mostrar un par de precios de posición como ejemplo
        print(f"     Precio DIC24: {datos_respuesta.get('precio_posicion_dic24')}")
        print(f"     Precio MAR25: {datos_respuesta.get('precio_posicion_mar25')}")
        print(f"     Fuente Precio: {datos_respuesta.get('fuente_precio')}")
        print(f"     Fuente Tasa: {datos_respuesta.get('fuente_tasa')}")
        print(f"     Fecha Registro: {datos_respuesta.get('fecha_registro')}")
    elif respuesta.status_code == 404:
        print(f"  ⚠️  ADVERTENCIA: No se encontró cierre para {FECHA_PRUEBA}")
    else:
        print(f"  ❌ ERROR al obtener: {respuesta.text}")
except Exception as e:
    print(f"  ❌ EXCEPCIÓN al obtener: {e}")

# --- 3. Obtener el Último Cierre ---
print(f"\n--- 3. Obteniendo Último Cierre Registrado ---")
url_ultimo = f"{BASE_URL}/cierre_ny_bch/ultimo"

try:
    respuesta = requests.get(url_ultimo)
    print(f"  Estado: {respuesta.status_code}")
    if respuesta.status_code == 200:
        datos_respuesta = respuesta.json()
        print(f"  ✅ ÉXITO: Último cierre registrado")
        print(f"     Fecha: {datos_respuesta.get('fecha')}")
        print(f"     ID Registro: {datos_respuesta.get('id_registro')}")
        print(f"     Tasa BCH: {datos_respuesta.get('tasa_cambio_bch')}")
        print(f"     Precio Principal: {datos_respuesta.get('precio_usd_saco')}")
        # Mostrar un par de precios de posición como ejemplo
        print(f"     Precio DIC24: {datos_respuesta.get('precio_posicion_dic24')}")
        print(f"     Precio MAR25: {datos_respuesta.get('precio_posicion_mar25')}")
        print(f"     Fuente Precio: {datos_respuesta.get('fuente_precio')}")
        print(f"     Fuente Tasa: {datos_respuesta.get('fuente_tasa')}")
        print(f"     Fecha Registro: {datos_respuesta.get('fecha_registro')}")
    elif respuesta.status_code == 404:
        print(f"  ⚠️  ADVERTENCIA: No hay cierres registrados aún")
    else:
        print(f"  ❌ ERROR al obtener el último: {respuesta.text}")
except Exception as e:
    print(f"  ❌ EXCEPCIÓN al obtener el último: {e}")

print("\n--- Fin de la prueba ---")
