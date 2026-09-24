from dotenv import load_dotenv
from database import conectar
from groq import Groq
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


load_dotenv()

# Configurar cliente Groq
cliente_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generar_publicacion(articulo, red_social):
    """
    Usa IA (Groq/LLaMA) para generar una publicación
    adaptada al tono y formato de cada red social.
    """
    reglas = {
        "linkedin": """
            - Tono profesional y académico
            - Máximo 1300 caracteres
            - Menciona el aporte científico del artículo
            - Termina invitando a leer el artículo completo
            - Incluye 3 hashtags relevantes al final
        """,
        "twitter": """
            - Máximo 260 caracteres en total
            - Primera línea: pregunta o dato impactante
            - Tono directo y llamativo
            - Incluye 2 hashtags cortos
            - Termina con: 'Lee el artículo →'
        """,
        "instagram": """
            - Tono cercano e inspirador
            - Máximo 300 caracteres
            - Primera línea: frase que genere curiosidad
            - Menciona que el enlace está en la bio
            - Incluye 4 hashtags en español
        """,
        "whatsapp": """
            - Tono cercano, como mensaje entre colegas
            - Máximo 400 caracteres
            - Saludo inicial a la comunidad académica
            - Resume el aporte del artículo en 2 líneas
            - Termina con el enlace directo
        """
    }

    prompt = f"""Eres un comunicador científico especializado en
difundir investigación académica en redes sociales.

Genera una publicación para {red_social.upper()} sobre este artículo:

Título: {articulo['titulo']}
Autores: {articulo['autores']}
Resumen: {articulo['resumen']}
Enlace: {articulo['enlace']}

Reglas para {red_social}:
{reglas[red_social]}

Devuelve ÚNICAMENTE el texto de la publicación,
sin explicaciones ni comillas."""

    respuesta = cliente_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )

    return respuesta.choices[0].message.content


def generar_todas_las_publicaciones(articulo_id):
    """
    Genera publicaciones para las 4 redes sociales
    y las guarda en la base de datos con estado 'pendiente'.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, titulo, autores, resumen, enlace
        FROM articulo WHERE id = %s
    """, (articulo_id,))

    fila = cursor.fetchone()
    if not fila:
        print(f"Artículo {articulo_id} no encontrado.")
        cursor.close()
        conn.close()
        return

    articulo = {
        "id":      fila[0],
        "titulo":  fila[1],
        "autores": fila[2],
        "resumen": fila[3],
        "enlace":  fila[4]
    }

    redes = ["linkedin", "twitter", "instagram", "whatsapp"]

    print(f"\nGenerando publicaciones para:")
    print(f"{articulo['titulo'][:70]}...")
    print("-" * 50)

    for red in redes:
        print(f"Generando para {red}...", end=" ", flush=True)
        contenido = generar_publicacion(articulo, red)

        cursor.execute("""
            INSERT INTO publicacion_red
                (articulo_id, red_social, contenido, estado)
            VALUES (%s, %s, %s, 'pendiente')
        """, (articulo_id, red, contenido))

        print("✓")

    conn.commit()
    cursor.close()
    conn.close()
    print("\nPublicaciones guardadas. Esperando aprobación del autor.")


def obtener_publicaciones_pendientes():
    """
    Devuelve todas las publicaciones pendientes de aprobación.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.id,
            a.titulo,
            p.red_social,
            p.contenido,
            p.estado,
            p.fecha_creacion
        FROM publicacion_red p
        JOIN articulo a ON p.articulo_id = a.id
        WHERE p.estado = 'pendiente'
        ORDER BY p.fecha_creacion DESC
    """)

    columnas = ["id", "titulo", "red_social",
                "contenido", "estado", "fecha_creacion"]
    publicaciones = [dict(zip(columnas, fila))
                     for fila in cursor.fetchall()]

    cursor.close()
    conn.close()
    return publicaciones


def aprobar_publicacion(publicacion_id):
    """
    Marca una publicación como aprobada por el autor.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE publicacion_red
        SET estado = 'aprobada'
        WHERE id = %s
    """, (publicacion_id,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Publicación {publicacion_id} aprobada.")


if __name__ == "__main__":
    print("Iniciando generador de contenido con Groq/LLaMA...")
    generar_todas_las_publicaciones(articulo_id=1)

    print("\nPublicaciones pendientes de aprobación:")
    print("=" * 50)

    pendientes = obtener_publicaciones_pendientes()

    for pub in pendientes:
        print(f"\nRED: {pub['red_social'].upper()}")
        print(f"Artículo: {pub['titulo'][:60]}...")
        print(f"Contenido:\n{pub['contenido']}")
        print("-" * 50)
