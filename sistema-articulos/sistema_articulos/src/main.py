from repositorio import obtener_articulos, extraer_articulos
from database import crear_tablas, guardar_articulos


def sincronizar():
    """
    Trae los artículos del repositorio de UNIMINUTO
    y los guarda en la base de datos local.
    """
    print("Iniciando sincronización con UNIMINUTO...")

    # Paso 1: crear tablas si no existen
    crear_tablas()

    # Paso 2: traer artículos del repositorio
    datos_crudos = obtener_articulos(cantidad=20)
    articulos = extraer_articulos(datos_crudos)

    if not articulos:
        print("No se obtuvieron artículos.")
        return

    print(f"Artículos obtenidos del repositorio: {len(articulos)}")

    # Paso 3: guardar en la base de datos
    guardar_articulos(articulos)

    print("Sincronización completada.")


if __name__ == "__main__":
    sincronizar()
