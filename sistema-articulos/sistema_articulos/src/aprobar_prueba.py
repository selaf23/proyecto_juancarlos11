from database import conectar
from generador_social import obtener_publicaciones_pendientes, aprobar_publicacion
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# Ver publicaciones pendientes
print("Publicaciones pendientes de aprobación:")
print("=" * 50)

pendientes = obtener_publicaciones_pendientes()

for pub in pendientes:
    print(f"\nID: {pub['id']}")
    print(f"Red: {pub['red_social'].upper()}")
    print(f"Contenido: {pub['contenido'][:100]}...")
    print(f"Estado: {pub['estado']}")

# Aprobar interactivamente
print("\n" + "=" * 50)
id_aprobar = input("Escribe el ID de la publicación que quieres aprobar: ")

aprobar_publicacion(int(id_aprobar))

# Verificar que cambió el estado
print("\nVerificando estado actualizado en base de datos...")
conn = conectar()
cursor = conn.cursor()
cursor.execute("""
    SELECT id, red_social, estado
    FROM publicacion_red
    WHERE id = %s
""", (int(id_aprobar),))

fila = cursor.fetchone()
print(f"ID: {fila[0]} | Red: {fila[1]} | Estado: {fila[2]}")
cursor.close()
conn.close()
