import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

# Leer credenciales del archivo .env
DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     os.getenv("DB_PORT"),
    "dbname":   os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}


def conectar():
    """
    Abre una conexión con PostgreSQL y la devuelve.
    Siempre usar dentro de un bloque try/finally
    para cerrarla correctamente.
    """
    return psycopg2.connect(**DB_CONFIG)


def crear_tablas():
    """
    Crea las cuatro tablas del sistema si no existen.
    Se puede ejecutar varias veces sin error gracias
    a IF NOT EXISTS.
    """
    conn = conectar()
    cursor = conn.cursor()

    # Tabla de artículos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articulo (
            id          SERIAL PRIMARY KEY,
            uuid        VARCHAR(200) UNIQUE NOT NULL,
            doi         VARCHAR(200),
            issn        VARCHAR(50),
            titulo      TEXT NOT NULL,
            autores     TEXT,
            fecha       VARCHAR(20),
            resumen     TEXT,
            enlace      TEXT,
            revista     TEXT,
            fuente      VARCHAR(50) DEFAULT 'doi',
            registrado_por VARCHAR(100) DEFAULT 'administrador',
            fecha_carga TIMESTAMP DEFAULT NOW()
        );
    """)

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id              SERIAL PRIMARY KEY,
            nombre          VARCHAR(200) NOT NULL,
            correo          VARCHAR(200) UNIQUE NOT NULL,
            rol             VARCHAR(50),
            area_interes    TEXT,
            fecha_registro  TIMESTAMP DEFAULT NOW()
        );
    """)

    # Tabla de métricas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrica (
            id              SERIAL PRIMARY KEY,
            articulo_id     INTEGER REFERENCES articulo(id),
            tipo_evento     VARCHAR(50),
            origen          VARCHAR(100),
            fecha_evento    TIMESTAMP DEFAULT NOW()
        );
    """)

    # Tabla de publicaciones en redes sociales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publicacion_red (
            id              SERIAL PRIMARY KEY,
            articulo_id     INTEGER REFERENCES articulo(id),
            red_social      VARCHAR(50),
            contenido       TEXT,
            estado          VARCHAR(20) DEFAULT 'pendiente',
            fecha_creacion  TIMESTAMP DEFAULT NOW(),
            fecha_publicacion TIMESTAMP
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tablas creadas correctamente.")


def guardar_articulos(articulos):
    """
    Recibe la lista de artículos que viene de repositorio.py
    y los guarda en la base de datos.
    Si el artículo ya existe (mismo uuid) lo actualiza,
    no lo duplica.
    """
    conn = conectar()
    cursor = conn.cursor()

    guardados = 0
    actualizados = 0

    for art in articulos:
        cursor.execute("""
            INSERT INTO articulo (uuid, titulo, autores, fecha, resumen, enlace)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (uuid) DO UPDATE SET
                titulo  = EXCLUDED.titulo,
                autores = EXCLUDED.autores,
                resumen = EXCLUDED.resumen;
        """, (
            art["uuid"],
            art["titulo"],
            art["autores"],
            art["fecha"],
            art["resumen"],
            art["enlace"]
        ))

        if cursor.rowcount == 1:
            guardados += 1
        else:
            actualizados += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Artículos guardados: {guardados}")
    print(f"Artículos actualizados: {actualizados}")


def crear_tabla_monitoreo():
    """
    Tabla para registrar qué artículos se monitorean
    manualmente por la regional.
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articulo_monitoreado (
            id              SERIAL PRIMARY KEY,
            articulo_uuid   VARCHAR(100) REFERENCES articulo(uuid),
            agregado_por    VARCHAR(200),
            fecha_agregado  TIMESTAMP DEFAULT NOW(),
            activo          BOOLEAN DEFAULT TRUE
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tabla de monitoreo creada.")


if __name__ == "__main__":
    print("Creando tablas en la base de datos...")
    crear_tablas()
