import random
from datetime import datetime, timedelta
from database import conectar
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def generar_datos_prueba():
    conn = conectar()
    cursor = conn.cursor()

    # Obtener artículos monitoreados
    cursor.execute("""
        SELECT a.id FROM articulo a
        JOIN articulo_monitoreado am ON a.uuid = am.articulo_uuid
        WHERE am.activo = TRUE
    """)
    articulos = [fila[0] for fila in cursor.fetchall()]

    if not articulos:
        print("No hay artículos monitoreados. Agrega algunos primero.")
        cursor.close()
        conn.close()
        return

    redes = ["web", "linkedin", "twitter", "instagram", "whatsapp"]
    eventos = ["vista", "descarga"]

    print(f"Generando métricas para {len(articulos)} artículos...")

    for articulo_id in articulos:
        # Generar entre 10 y 50 eventos por artículo
        num_eventos = random.randint(10, 50)
        for _ in range(num_eventos):
            tipo = random.choices(eventos, weights=[70, 30])[0]
            origen = random.choices(redes,   weights=[30, 25, 20, 15, 10])[0]
            # Fecha aleatoria en los últimos 6 meses
            dias = random.randint(0, 180)
            fecha = datetime.now() - timedelta(days=dias)

            cursor.execute("""
                INSERT INTO metrica (articulo_id, tipo_evento, origen, fecha_evento)
                VALUES (%s, %s, %s, %s)
            """, (articulo_id, tipo, origen, fecha))

    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Métricas de prueba generadas correctamente.")


if __name__ == "__main__":
    generar_datos_prueba()
