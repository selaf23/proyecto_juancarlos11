from dotenv import load_dotenv
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


load_dotenv()

REPOSITORIO_URL = os.getenv("REPOSITORIO_URL")

print(f"Conectando a: {REPOSITORIO_URL}")

# Buscar directamente el artículo de interés
UUID = "a451592d-e22a-43c0-ba2f-3c32519727e7"

try:
    # Paso 1: datos del artículo
    url = f"{REPOSITORIO_URL}/server/api/core/items/{UUID}"
    print(f"Consultando: {url}")

    r = requests.get(url, timeout=15)
    print(f"Código de respuesta: {r.status_code}")

    datos = r.json()
    metadatos = datos.get("metadata", {})
    titulo = metadatos.get("dc.title", [{}])[0].get("value", "Sin título")
    print(f"\nTítulo: {titulo}")

    # Paso 2: colección a la que pertenece
    url2 = f"{REPOSITORIO_URL}/server/api/core/items/{UUID}/owningCollection"
    r2 = requests.get(url2, timeout=15)
    col = r2.json()
    print(f"Colección: {col.get('name', 'No encontrada')}")
    print(f"ID colección: {col.get('uuid', '')}")

    # Paso 3: comunidad padre
    col_id = col.get('uuid', '')
    url3 = f"{REPOSITORIO_URL}/server/api/core/collections/{col_id}/parentCommunity"
    r3 = requests.get(url3, timeout=15)
    com = r3.json()
    print(f"Comunidad: {com.get('name', 'No encontrada')}")
    print(f"ID comunidad: {com.get('uuid', '')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
