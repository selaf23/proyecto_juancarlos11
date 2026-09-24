from database import conectar
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def crear_usuario(nombre, correo, rol="investigador", area_interes=""):
    """
    Crea un usuario con rol definido.
    rol: 'investigador' o 'administrador'
    """
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO usuario (nombre, correo, rol, area_interes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (correo) DO UPDATE SET
            nombre       = EXCLUDED.nombre,
            rol          = EXCLUDED.rol,
            area_interes = EXCLUDED.area_interes
        RETURNING id, nombre, correo, rol
    """, (nombre, correo, rol, area_interes))

    fila = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "id":     fila[0],
        "nombre": fila[1],
        "correo": fila[2],
        "rol":    fila[3]
    }


def listar_usuarios():
    """Lista todos los usuarios registrados."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, correo, rol, area_interes, fecha_registro
        FROM usuario ORDER BY fecha_registro DESC
    """)

    columnas = ["id", "nombre", "correo",
                "rol", "area_interes", "fecha_registro"]
    usuarios = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    cursor.close()
    conn.close()
    return usuarios


def obtener_publicaciones_por_rol(usuario_id, rol):
    """
    Devuelve publicaciones según el rol.
    - investigador: solo ve publicaciones de sus artículos, máx 72h
    - administrador: ve todas las pendientes sin restricción de tiempo
    """
    conn = conectar()
    cursor = conn.cursor()

    if rol == "administrador":
        cursor.execute("""
            SELECT
                p.id,
                a.titulo,
                a.autores,
                p.red_social,
                p.contenido,
                p.estado,
                p.fecha_creacion,
                CASE
                    WHEN NOW() > p.fecha_creacion + INTERVAL '72 hours'
                    THEN TRUE ELSE FALSE
                END as vencida
            FROM publicacion_red p
            JOIN articulo a ON p.articulo_id = a.id
            WHERE p.estado = 'pendiente'
            ORDER BY p.fecha_creacion ASC
        """)
    else:
        cursor.execute("""
            SELECT
                p.id,
                a.titulo,
                a.autores,
                p.red_social,
                p.contenido,
                p.estado,
                p.fecha_creacion,
                CASE
                    WHEN NOW() > p.fecha_creacion + INTERVAL '72 hours'
                    THEN TRUE ELSE FALSE
                END as vencida
            FROM publicacion_red p
            JOIN articulo a ON p.articulo_id = a.id
            JOIN usuario u ON u.id = %s
            WHERE p.estado = 'pendiente'
              AND a.autores ILIKE '%%' || u.nombre || '%%'
            ORDER BY p.fecha_creacion ASC
        """, (usuario_id,))

    columnas = ["id", "titulo", "autores", "red_social",
                "contenido", "estado", "fecha_creacion", "vencida"]
    publicaciones = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    cursor.close()
    conn.close()
    return publicaciones


def puede_aprobar(usuario_id, publicacion_id, rol):
    """
    Verifica si un usuario puede aprobar una publicación.
    Modelo 3:
    - Investigador: puede aprobar sus artículos dentro de 72h
    - Administrador: puede aprobar cualquier publicación siempre
    """
    if rol == "administrador":
        return True, "Administrador puede aprobar siempre"

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.fecha_creacion,
            NOW() > p.fecha_creacion + INTERVAL '72 hours' as vencida
        FROM publicacion_red p
        WHERE p.id = %s
    """, (publicacion_id,))

    fila = cursor.fetchone()
    cursor.close()
    conn.close()

    if not fila:
        return False, "Publicación no encontrada"

    if fila[1]:
        return False, "Plazo de 72 horas vencido. El administrador debe aprobar."

    return True, "Investigador puede aprobar dentro del plazo"


if __name__ == "__main__":
    from database import crear_tablas
    crear_tablas()

    print("="*60)
    print("  GESTIÓN DE USUARIOS")
    print("="*60)

    # Crear usuarios de prueba
    admin = crear_usuario(
        nombre="Administrador Regional",
        correo="admin.regional@uniminuto.edu",
        rol="administrador",
        area_interes="gestión académica e investigación"
    )
    print(f"\n✓ Administrador: {admin['nombre']} (ID: {admin['id']})")

    inv1 = crear_usuario(
        nombre="Pino Perdomo Felipe Mauricio",
        correo="fpino@uniminuto.edu",
        rol="investigador",
        area_interes="educación ambiental e infancias"
    )
    print(f"✓ Investigador:  {inv1['nombre']} (ID: {inv1['id']})")

    # Listar todos
    print("\nUsuarios registrados en el sistema:")
    print("-"*50)
    usuarios = listar_usuarios()
    for u in usuarios:
        print(f"  [{u['rol'].upper()}] {u['nombre']} — {u['correo']}")
