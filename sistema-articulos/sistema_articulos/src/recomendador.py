import numpy as np
from database import conectar
from buscador import coleccion, modelo
from sentence_transformers import SentenceTransformer
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def obtener_perfil_usuario(usuario_id):
    """
    Construye el perfil de intereses del usuario
    combinando su área declarada y su historial.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Traer datos del usuario
    cursor.execute("""
        SELECT area_interes FROM usuario WHERE id = %s
    """, (usuario_id,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        return None

    area_interes = usuario[0] or ""

    # Traer artículos que el usuario ha visto
    cursor.execute("""
        SELECT a.titulo, a.resumen
        FROM metrica m
        JOIN articulo a ON m.articulo_id = a.id
        WHERE m.articulo_id IS NOT NULL
        ORDER BY m.fecha_evento DESC
        LIMIT 10
    """)
    historial = cursor.fetchall()
    cursor.close()
    conn.close()

    # Construir texto del perfil
    textos = [area_interes]
    for titulo, resumen in historial:
        textos.append(f"{titulo}. {resumen or ''}")

    # Generar embedding promedio del perfil
    embeddings = modelo.encode(textos)
    perfil_vector = np.mean(embeddings, axis=0).tolist()

    return perfil_vector


def recomendar_articulos(usuario_id, cantidad=5):
    """
    Recomienda artículos personalizados para un usuario
    basándose en su perfil de intereses.
    """
    perfil = obtener_perfil_usuario(usuario_id)

    if perfil is None:
        return {"error": "Usuario no encontrado"}

    # Buscar artículos similares al perfil del usuario
    resultados = coleccion.query(
        query_embeddings=[perfil],
        n_results=cantidad
    )

    articulos_recomendados = []
    metadatos = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    for i, meta in enumerate(metadatos):
        similitud = round((1 - distancias[i]) * 100, 1)
        articulos_recomendados.append({
            "titulo": meta["titulo"],
            "autores": meta["autores"],
            "fecha": meta["fecha"],
            "enlace": meta["enlace"],
            "relevancia": f"{similitud}%"
        })

    return articulos_recomendados


def registrar_evento(articulo_id, tipo_evento, origen="web"):
    """
    Registra cuando un usuario ve o descarga un artículo.
    Esto alimenta el sistema de métricas y mejora
    las recomendaciones futuras.

    tipo_evento: 'vista', 'descarga', 'guardado'
    origen: 'web', 'linkedin', 'instagram', 'whatsapp'
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO metrica (articulo_id, tipo_evento, origen)
        VALUES (%s, %s, %s)
    """, (articulo_id, tipo_evento, origen))

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    # Prueba: crear un usuario de ejemplo y recomendar
    conn = conectar()
    cursor = conn.cursor()

    # Insertar usuario de prueba si no existe
    cursor.execute("""
        INSERT INTO usuario (nombre, correo, rol, area_interes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (correo) DO NOTHING
        RETURNING id
    """, (
        "Estudiante Prueba",
        "prueba@uniminuto.edu",
        "estudiante",
        "desarrollo sostenible y medio ambiente"
    ))

    resultado = cursor.fetchone()
    conn.commit()

    if resultado:
        usuario_id = resultado[0]
        print(f"Usuario creado con ID: {usuario_id}")
    else:
        cursor.execute(
            "SELECT id FROM usuario WHERE correo = %s",
            ("prueba@uniminuto.edu",)
        )
        usuario_id = cursor.fetchone()[0]
        print(f"Usuario existente con ID: {usuario_id}")

    cursor.close()
    conn.close()

    print(f"\nRecomendaciones para el usuario {usuario_id}:")
    print("-" * 50)

    recomendaciones = recomendar_articulos(usuario_id)

    for i, art in enumerate(recomendaciones, 1):
        print(f"{i}. {art['titulo']}")
        print(f"   Relevancia: {art['relevancia']}")
        print(f"   Autores: {art['autores']}")
        print()
