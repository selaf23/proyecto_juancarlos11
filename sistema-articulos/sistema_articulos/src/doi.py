from database import conectar, guardar_articulos
import re
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


CROSSREF_URL = "https://api.crossref.org/works"


def validar_doi(doi):
    """
    Verifica que el DOI tenga el formato correcto.
    Formato válido: 10.XXXX/XXXXX
    """
    doi = doi.strip()

    # Limpiar si viene como URL completa
    if "doi.org/" in doi:
        doi = doi.split("doi.org/")[-1]

    # Validar formato
    patron = r'^10\.\d{4,}/.+$'
    if not re.match(patron, doi):
        return None, "DOI inválido. Formato esperado: 10.XXXX/XXXXX"

    return doi, None


def buscar_por_doi(doi):
    """
    Consulta CrossRef con el DOI y devuelve
    los metadatos completos del artículo.
    CrossRef es gratuito y cubre todas las editoriales.
    """
    doi_limpio, error = validar_doi(doi)
    if error:
        return None, error

    try:
        url = f"{CROSSREF_URL}/{doi_limpio}"
        headers = {
            "User-Agent": "SistemaArticulosUNIMINUTO/1.0 (mailto:repositorio@uniminuto.edu)"}

        print(f"Consultando CrossRef: {doi_limpio}")
        respuesta = requests.get(url, headers=headers, timeout=15)

        if respuesta.status_code == 404:
            return None, "DOI no encontrado en CrossRef. Verifica que sea correcto."

        respuesta.raise_for_status()
        datos = respuesta.json()
        mensaje = datos.get("message", {})

        # Extraer título
        titulos = mensaje.get("title", ["Sin título"])
        titulo = titulos[0] if titulos else "Sin título"

        # Extraer autores
        autores_raw = mensaje.get("author", [])
        autores_lista = []
        for a in autores_raw:
            nombre = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if nombre:
                autores_lista.append(nombre)
        autores = ", ".join(autores_lista) or "Sin autor"

        # Extraer fecha
        fecha_raw = mensaje.get("published", {}).get("date-parts", [[]])
        fecha = str(fecha_raw[0][0]
                    ) if fecha_raw and fecha_raw[0] else "Sin fecha"

        # Extraer resumen
        resumen = mensaje.get("abstract", "Sin resumen")
        # Limpiar tags HTML que a veces vienen en el resumen
        resumen = re.sub(r'<[^>]+>', '', resumen).strip()

        # Extraer revista
        contenedor = mensaje.get("container-title", ["Sin revista"])
        revista = contenedor[0] if contenedor else "Sin revista"

        # Extraer ISSN
        issn_raw = mensaje.get("ISSN", [])
        issn = issn_raw[0] if issn_raw else ""

        # Enlace al artículo
        enlace = mensaje.get("URL", f"https://doi.org/{doi_limpio}")

        articulo = {
            "uuid":    doi_limpio,
            "doi":     doi_limpio,
            "issn":    issn,
            "titulo":  titulo,
            "autores": autores,
            "fecha":   fecha,
            "resumen": resumen[:1000],
            "enlace":  enlace,
            "revista": revista,
            "fuente":  "crossref"
        }

        return articulo, None

    except requests.exceptions.ConnectionError:
        return None, "Error de conexión. Verifica tu internet."
    except Exception as e:
        return None, f"Error consultando CrossRef: {str(e)}"


def buscar_por_issn(issn, cantidad=20):
    """
    Busca todos los artículos de una revista por su ISSN.
    Útil para importar toda la producción de una revista.
    """
    try:
        url = f"{CROSSREF_URL}?filter=issn:{issn}&rows={cantidad}&sort=published&order=desc"
        headers = {"User-Agent": "SistemaArticulosUNIMINUTO/1.0"}

        print(f"Buscando artículos con ISSN: {issn}")
        respuesta = requests.get(url, headers=headers, timeout=15)
        respuesta.raise_for_status()

        datos = respuesta.json()
        items = datos.get("message", {}).get("items", [])

        articulos = []
        for item in items:
            doi = item.get("DOI", "")
            if not doi:
                continue

            titulos = item.get("title", ["Sin título"])
            titulo = titulos[0] if titulos else "Sin título"

            autores_raw = item.get("author", [])
            autores_lista = []
            for a in autores_raw:
                nombre = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if nombre:
                    autores_lista.append(nombre)
            autores = ", ".join(autores_lista) or "Sin autor"

            fecha_raw = item.get("published", {}).get("date-parts", [[]])
            fecha = str(
                fecha_raw[0][0]) if fecha_raw and fecha_raw[0] else "Sin fecha"

            resumen = item.get("abstract", "Sin resumen")
            resumen = re.sub(r'<[^>]+>', '', resumen).strip()

            contenedor = item.get("container-title", ["Sin revista"])
            revista = contenedor[0] if contenedor else "Sin revista"

            enlace = item.get("URL", f"https://doi.org/{doi}")

            articulos.append({
                "uuid":    doi,
                "doi":     doi,
                "issn":    issn,
                "titulo":  titulo,
                "autores": autores,
                "fecha":   fecha,
                "resumen": resumen[:1000],
                "enlace":  enlace,
                "revista": revista,
                "fuente":  "crossref_issn"
            })

        return articulos, None

    except Exception as e:
        return [], f"Error consultando ISSN: {str(e)}"


def registrar_articulo(doi_o_url, registrado_por="administrador"):
    """
    Función principal: recibe un DOI o URL con DOI,
    consulta CrossRef, guarda en la base de datos
    y lo agrega al monitoreo.
    """
    # Limpiar entrada
    entrada = doi_o_url.strip()

    # Si es URL extraer el DOI
    if "doi.org/" in entrada:
        entrada = entrada.split("doi.org/")[-1]

    # Buscar en CrossRef
    articulo, error = buscar_por_doi(entrada)

    if error:
        return {"exito": False, "mensaje": error}

    print(f"Encontrado: {articulo['titulo'][:60]}...")
    print(f"Revista: {articulo['revista']}")
    print(f"Autores: {articulo['autores'][:60]}...")

    # Guardar en base de datos
    guardar_articulos([articulo])

    # Agregar a monitoreo
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO articulo_monitoreado (articulo_uuid, agregado_por)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (articulo["uuid"], registrado_por))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "exito":    True,
        "mensaje":  "Artículo registrado correctamente",
        "articulo": articulo
    }


def registrar_por_issn(issn, registrado_por="administrador"):
    """
    Registra todos los artículos de una revista
    a partir de su ISSN.
    """
    articulos, error = buscar_por_issn(issn)

    if error:
        return {"exito": False, "mensaje": error}

    if not articulos:
        return {"exito": False, "mensaje": "No se encontraron artículos para ese ISSN"}

    guardar_articulos(articulos)

    conn = conectar()
    cursor = conn.cursor()

    for art in articulos:
        cursor.execute("""
            INSERT INTO articulo_monitoreado (articulo_uuid, agregado_por)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (art["uuid"], registrado_por))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "exito":    True,
        "mensaje":  f"{len(articulos)} artículos registrados",
        "total":    len(articulos),
        "articulos": articulos
    }


if __name__ == "__main__":
    from database import crear_tablas
    from database import crear_tabla_monitoreo
    crear_tablas()
    crear_tabla_monitoreo()

    print("="*60)
    print("  REGISTRAR ARTÍCULO POR DOI")
    print("="*60)
    print("Opciones:")
    print("  1. Ingresar DOI   (ej: 10.1016/j.example.2023)")
    print("  2. Ingresar ISSN  (ej: 1234-5678)")
    print()

    opcion = input("¿DOI o ISSN? (d/i): ").strip().lower()

    if opcion == "d":
        doi = input("DOI: ").strip()
        resultado = registrar_articulo(doi)
    else:
        issn = input("ISSN: ").strip()
        resultado = registrar_por_issn(issn)

    if resultado["exito"]:
        print(f"\n✓ {resultado['mensaje']}")
        if "articulo" in resultado:
            art = resultado["articulo"]
            print(f"\nTítulo  : {art['titulo']}")
            print(f"Revista : {art['revista']}")
            print(f"Autores : {art['autores']}")
            print(f"Fecha   : {art['fecha']}")
            print(f"DOI     : {art['doi']}")
            print(f"Enlace  : {art['enlace']}")
    else:
        print(f"\n✗ {resultado['mensaje']}")
