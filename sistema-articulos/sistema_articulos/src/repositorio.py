import requests
import json
from dotenv import load_dotenv
import os

# Cargar las variables del archivo .env
load_dotenv()

REPOSITORIO_URL = os.getenv("REPOSITORIO_URL")
COMUNIDAD_ID = os.getenv("REPOSITORIO_COMUNIDAD_ACADEMICA")


def obtener_articulos(cantidad=10):
    """
    Consulta la API REST de DSpace 7 de UNIMINUTO
    y devuelve artículos de la comunidad Producción Académica.

    cantidad: cuántos artículos traer (por defecto 10)
    """

    endpoint = f"{REPOSITORIO_URL}/server/api/discover/search/objects"

    parametros = {
        "scope": COMUNIDAD_ID,
        "sort": "dc.date.accessioned,DESC",
        "page": 0,
        "size": cantidad,
        "embed": "thumbnail"
    }

    try:
        print(f"Conectando a: {REPOSITORIO_URL}")
        respuesta = requests.get(endpoint, params=parametros, timeout=15)
        respuesta.raise_for_status()

        datos = respuesta.json()
        return datos

    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar al repositorio.")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP {respuesta.status_code}: {e}")
        return None

    except Exception as e:
        print(f"Error inesperado: {e}")
        return None


def extraer_articulos(datos):
    """
    Procesa la respuesta de DSpace 7 y extrae
    solo los campos que nos interesan de cada artículo.
    """
    if datos is None:
        return []

    try:
        objetos = datos["_embedded"]["searchResult"]["_embedded"]["objects"]
    except KeyError:
        print("La estructura del JSON no es la esperada.")
        print("Respuesta recibida:")
        print(json.dumps(datos, indent=2, ensure_ascii=False)[:500])
        return []

    articulos = []

    for objeto in objetos:
        try:
            item = objeto["_embedded"]["indexableObject"]

            metadatos = item.get("metadata", {})

            titulo = metadatos.get("dc.title", [{}])[
                0].get("value", "Sin título")

            autores_raw = metadatos.get("dc.contributor.author", [])
            autores = [a.get("value", "") for a in autores_raw]
            autores_texto = ", ".join(autores) if autores else "Sin autor"

            fecha_raw = metadatos.get("dc.date.issued", [{}])
            fecha = fecha_raw[0].get(
                "value", "Sin fecha") if fecha_raw else "Sin fecha"

            resumen_raw = metadatos.get("dc.description.abstract", [{}])
            resumen = resumen_raw[0].get("value", "Sin resumen")[
                :200] if resumen_raw else "Sin resumen"

            uuid = item.get("uuid", "")
            enlace = f"{REPOSITORIO_URL}/items/{uuid}" if uuid else "Sin enlace"

            articulos.append({
                "titulo": titulo,
                "autores": autores_texto,
                "fecha": fecha,
                "resumen": resumen + "...",
                "enlace": enlace,
                "uuid": uuid
            })

        except Exception:
            continue

    return articulos


def mostrar_articulos(articulos):
    """
    Imprime en pantalla los artículos de forma legible.
    """
    if not articulos:
        print("No se encontraron artículos.")
        return

    print(f"\n{'='*60}")
    print(f"  Artículos de Producción Académica — UNIMINUTO")
    print(f"  Total encontrados: {len(articulos)}")
    print(f"{'='*60}\n")

    for i, art in enumerate(articulos, 1):
        print(f"{i}. {art['titulo']}")
        print(f"   Autores : {art['autores']}")
        print(f"   Fecha   : {art['fecha']}")
        print(f"   Enlace  : {art['enlace']}")
        print(f"   Resumen : {art['resumen']}")
        print()


if __name__ == "__main__":
    datos_crudos = obtener_articulos(cantidad=5)
    articulos = extraer_articulos(datos_crudos)
    mostrar_articulos(articulos)
