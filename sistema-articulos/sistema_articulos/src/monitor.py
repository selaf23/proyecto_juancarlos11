from database import conectar, guardar_articulos
from dotenv import load_dotenv
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


load_dotenv()

REPOSITORIO_URL = os.getenv("REPOSITORIO_URL")


def extraer_uuid_de_url(entrada):
    """
    Acepta cualquiera de estos formatos:
    - URL completa: https://repository.uniminuto.edu/items/a451592d-...
    - Solo el UUID: a451592d-e22a-43c0-ba2f-3c32519727e7
    """
    entrada = entrada.strip()

    # Si es una URL completa extraer el UUID al final
    if "repository.uniminuto.edu/items/" in entrada:
        uuid = entrada.split("/items/")[-1].strip("/")
        return uuid

    # Si ya es un UUID directamente
    if len(entrada) == 36 and entrada.count("-") == 4:
        return entrada

    return None


def buscar_articulo_por_uuid(uuid):
    """
    Consulta la API de DSpace y trae los metadatos
    completos de un artículo por su UUID.
    """
    try:
        # Datos del artículo
        url = f"{REPOSITORIO_URL}/server/api/core/items/{uuid}"
        r = requests.get(url, timeout=15)

        if r.status_code == 404:
            return None, "Artículo no encontrado en el repositorio"

        r.raise_for_status()
        datos = r.json()

        metadatos = datos.get("metadata", {})

        titulo = metadatos.get("dc.title", [{}])[0].get("value", "Sin título")

        autores_raw = metadatos.get("dc.contributor.author", [])
        autores = ", ".join([a.get("value", "")
                            for a in autores_raw]) or "Sin autor"

        fecha_raw = metadatos.get("dc.date.issued", [{}])
        fecha = fecha_raw[0].get(
            "value", "Sin fecha") if fecha_raw else "Sin fecha"

        resumen_raw = metadatos.get("dc.description.abstract", [{}])
        resumen = resumen_raw[0].get(
            "value", "Sin resumen") if resumen_raw else "Sin resumen"

        enlace = f"{REPOSITORIO_URL}/items/{uuid}"

        articulo = {
            "uuid":    uuid,
            "titulo":  titulo,
            "autores": autores,
            "fecha":   fecha,
            "resumen": resumen,
            "enlace":  enlace
        }

        return articulo, None

    except Exception as e:
        return None, str(e)


def agregar_a_monitoreo(uuid, agregado_por="administrador"):
    """
    Agrega un artículo a la lista de monitoreo
    de la regional. Si ya existe lo activa de nuevo.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Verificar si ya está en monitoreo
    cursor.execute("""
        SELECT id, activo FROM articulo_monitoreado
        WHERE articulo_uuid = %s
    """, (uuid,))

    existente = cursor.fetchone()

    if existente:
        if existente[1]:
            cursor.close()
            conn.close()
            return "ya_existe"
        else:
            # Reactivar
            cursor.execute("""
                UPDATE articulo_monitoreado
                SET activo = TRUE, fecha_agregado = NOW()
                WHERE articulo_uuid = %s
            """, (uuid,))
            conn.commit()
            cursor.close()
            conn.close()
            return "reactivado"

    # Agregar nuevo
    cursor.execute("""
        INSERT INTO articulo_monitoreado
            (articulo_uuid, agregado_por)
        VALUES (%s, %s)
    """, (uuid, agregado_por))

    conn.commit()
    cursor.close()
    conn.close()
    return "agregado"


def obtener_articulos_monitoreados():
    """
    Devuelve todos los artículos que están siendo
    monitoreados por la regional.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.uuid,
            a.titulo,
            a.autores,
            a.fecha,
            a.resumen,
            a.enlace,
            m.fecha_agregado,
            m.agregado_por
        FROM articulo a
        JOIN articulo_monitoreado m ON a.uuid = m.articulo_uuid
        WHERE m.activo = TRUE
        ORDER BY m.fecha_agregado DESC
    """)

    columnas = ["id", "uuid", "titulo", "autores", "fecha",
                "resumen", "enlace", "fecha_agregado", "agregado_por"]

    articulos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()
    conn.close()
    return articulos


def agregar_articulo_completo(entrada, agregado_por="administrador"):
    """
    Función principal: recibe URL o UUID, busca el artículo,
    lo guarda en la base de datos y lo agrega al monitoreo.
    """
    # Extraer UUID de la entrada
    uuid = extraer_uuid_de_url(entrada)

    if not uuid:
        return {
            "exito": False,
            "mensaje": "Formato no válido. Pega la URL completa o el UUID del artículo."
        }

    print(f"Buscando artículo: {uuid}")

    # Buscar en el repositorio
    articulo, error = buscar_articulo_por_uuid(uuid)

    if error:
        return {"exito": False, "mensaje": error}

    print(f"Encontrado: {articulo['titulo'][:60]}...")

    # Guardar en base de datos
    guardar_articulos([articulo])

    # Agregar a monitoreo
    estado = agregar_a_monitoreo(uuid, agregado_por)

    mensajes = {
        "agregado":   "Artículo agregado al monitoreo correctamente.",
        "ya_existe":  "Este artículo ya estaba en monitoreo.",
        "reactivado": "Artículo reactivado en el monitoreo."
    }

    return {
        "exito":    True,
        "mensaje":  mensajes[estado],
        "articulo": articulo,
        "estado":   estado
    }


if __name__ == "__main__":
    # Prueba interactiva
    from database import crear_tabla_monitoreo
    crear_tabla_monitoreo()

    print("="*60)
    print("  AGREGAR ARTÍCULO AL MONITOREO DE LA REGIONAL")
    print("="*60)
    print("Pega la URL o UUID del artículo del repositorio UNIMINUTO")
    print("Ejemplo: https://repository.uniminuto.edu/items/a451592d-...")
    print()

    entrada = input("URL o UUID: ").strip()
    resultado = agregar_articulo_completo(entrada)

    if resultado["exito"]:
        art = resultado["articulo"]
        print(f"\n✓ {resultado['mensaje']}")
        print(f"\nTítulo  : {art['titulo']}")
        print(f"Autores : {art['autores']}")
        print(f"Fecha   : {art['fecha']}")
        print(f"Enlace  : {art['enlace']}")
    else:
        print(f"\n✗ {resultado['mensaje']}")

    print("\nArticulos monitoreados actualmente:")
    print("-"*50)
    monitoreados = obtener_articulos_monitoreados()
    for i, art in enumerate(monitoreados, 1):
        print(f"{i}. {art['titulo'][:60]}...")
        print(f"   Agregado: {art['fecha_agregado']}")

