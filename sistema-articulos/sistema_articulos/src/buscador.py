from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
import os

load_dotenv()

# Cargar el modelo de lenguaje multilingüe
# La primera vez descarga el modelo (~120MB), luego lo usa desde caché
print("Cargando modelo de lenguaje...")
modelo = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Modelo cargado.")

# Inicializar ChromaDB en una carpeta local
cliente_chroma = chromadb.PersistentClient(path="./chroma_db")

# Crear o cargar la colección de artículos
coleccion = cliente_chroma.get_or_create_collection(
    name="articulos_uniminuto",
    metadata={"hnsw:space": "cosine"}
)


def indexar_articulo(articulo):
    """
    Genera el embedding de un artículo y lo guarda
    en ChromaDB para búsquedas futuras.

    articulo: diccionario con uuid, titulo, resumen
    """
    # Combinar título y resumen para generar el embedding
    texto = f"{articulo['titulo']}. {articulo['resumen']}"

    # Generar el vector numérico que representa el texto
    embedding = modelo.encode(texto).tolist()

    # Guardar en ChromaDB
    coleccion.upsert(
        ids=[articulo["uuid"]],
        embeddings=[embedding],
        documents=[texto],
        metadatas=[{
            "titulo": articulo["titulo"],
            "autores": articulo["autores"],
            "fecha": articulo["fecha"],
            "enlace": articulo["enlace"]
        }]
    )


def indexar_todos(articulos):
    """
    Indexa una lista completa de artículos en ChromaDB.
    """
    print(f"Indexando {len(articulos)} artículos...")

    for art in articulos:
        indexar_articulo(art)

    print(f"Indexación completada. Total en índice: {coleccion.count()}")


def buscar(consulta, cantidad_resultados=5):
    """
    Busca artículos similares a la consulta usando
    similitud semántica.

    consulta: texto libre en español
    cantidad_resultados: cuántos artículos devolver
    """
    # Generar embedding de la consulta del usuario
    embedding_consulta = modelo.encode(consulta).tolist()

    # Buscar los artículos más similares en ChromaDB
    resultados = coleccion.query(
        query_embeddings=[embedding_consulta],
        n_results=cantidad_resultados
    )

    # Organizar los resultados de forma legible
    articulos_encontrados = []

    metadatos = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    for i, meta in enumerate(metadatos):
        # Convertir distancia coseno a porcentaje de similitud
        similitud = round((1 - distancias[i]) * 100, 1)

        articulos_encontrados.append({
            "titulo": meta["titulo"],
            "autores": meta["autores"],
            "fecha": meta["fecha"],
            "enlace": meta["enlace"],
            "similitud": f"{similitud}%"
        })

    return articulos_encontrados


if __name__ == "__main__":
    # Prueba rápida del buscador
    from database import conectar

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT uuid, titulo, autores, fecha, resumen, enlace
        FROM articulo LIMIT 20
    """)
    columnas = [desc[0] for desc in cursor.description]
    articulos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Indexar los artículos
    indexar_todos(articulos)

    # Probar una búsqueda
    print("\nPrueba de búsqueda semántica:")
    print("Consulta: 'proyectos de desarrollo sostenible'")
    print("-" * 50)

    resultados = buscar("proyectos de desarrollo sostenible")

    for i, art in enumerate(resultados, 1):
        print(f"{i}. {art['titulo']}")
        print(f"   Similitud: {art['similitud']}")
        print(f"   Autores: {art['autores']}")
        print()
