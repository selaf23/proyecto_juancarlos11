from doi import registrar_articulo, registrar_por_issn
from monitor import agregar_articulo_completo, obtener_articulos_monitoreados
from generador_social import (generar_todas_las_publicaciones,
                              obtener_publicaciones_pendientes,
                              aprobar_publicacion)
from recomendador import recomendar_articulos, registrar_evento
from buscador import buscar, indexar_todos
from repositorio import obtener_articulos, extraer_articulos
from database import conectar, crear_tablas, guardar_articulos, crear_tabla_monitoreo
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


app = FastAPI(
    title="Sistema de Artículos Académicos UNIMINUTO",
    description="API para visibilizar y recomendar artículos del repositorio institucional",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Crear tablas al iniciar
crear_tablas()
crear_tabla_monitoreo()


# ── INICIO ───────────────────────────────────────────────────
@app.get("/")
def inicio():
    return {
        "sistema": "Artículos Académicos UNIMINUTO",
        "version": "1.0.0",
        "estado":  "activo"
    }


# ── ARTÍCULOS ────────────────────────────────────────────────
@app.get("/articulos")
def listar_articulos():
    """Devuelve todos los artículos guardados en la base de datos."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, uuid, doi, titulo, autores, fecha, resumen, enlace, revista
            FROM articulo
            ORDER BY fecha_carga DESC
        """)
        columnas = [desc[0] for desc in cursor.description]
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        articulos = [dict(zip(columnas, fila)) for fila in filas]
        return {"total": len(articulos), "articulos": articulos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articulos/{articulo_id}")
def obtener_articulo(articulo_id: int):
    """Devuelve un artículo específico por su ID."""
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, uuid, doi, titulo, autores, fecha, resumen, enlace, revista
            FROM articulo WHERE id = %s
        """, (articulo_id,))
        fila = cursor.fetchone()
        cursor.close()
        conn.close()
        if not fila:
            raise HTTPException(
                status_code=404, detail=f"Artículo {articulo_id} no encontrado")
        columnas = ["id", "uuid", "doi", "titulo", "autores",
                    "fecha", "resumen", "enlace", "revista"]
        return dict(zip(columnas, fila))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── BUSCADOR SEMÁNTICO ───────────────────────────────────────
@app.get("/buscar")
def buscar_articulos(q: str = Query(..., description="Texto de búsqueda en español")):
    """Busca artículos usando similitud semántica."""
    if len(q.strip()) < 3:
        raise HTTPException(
            status_code=400, detail="La búsqueda debe tener al menos 3 caracteres")
    resultados = buscar(q, cantidad_resultados=5)
    return {"consulta": q, "total": len(resultados), "resultados": resultados}


# ── SINCRONIZACIÓN ───────────────────────────────────────────
@app.post("/sincronizar")
def sincronizar_repositorio():
    """Trae artículos del repositorio de UNIMINUTO y los guarda."""
    try:
        crear_tablas()
        datos_crudos = obtener_articulos(cantidad=20)
        articulos = extraer_articulos(datos_crudos)
        if not articulos:
            return {"mensaje": "No se obtuvieron artículos del repositorio"}
        guardar_articulos(articulos)
        indexar_todos(articulos)
        return {"mensaje": "Sincronización completada", "articulos_procesados": len(articulos)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── RECOMENDACIONES ──────────────────────────────────────────
@app.get("/recomendaciones/{usuario_id}")
def obtener_recomendaciones(usuario_id: int):
    """Devuelve artículos recomendados para un usuario."""
    resultado = recomendar_articulos(usuario_id)
    return {"usuario_id": usuario_id, "recomendaciones": resultado}


@app.post("/eventos")
def registrar_evento_usuario(articulo_id: int, tipo: str, origen: str = "web"):
    """Registra cuando un usuario interactúa con un artículo."""
    registrar_evento(articulo_id, tipo, origen)
    return {"mensaje": "Evento registrado"}


# ── PUBLICACIONES EN REDES ───────────────────────────────────
@app.post("/publicaciones/generar/{articulo_id}")
def generar_publicaciones(articulo_id: int):
    """Genera publicaciones para redes sociales usando IA."""
    generar_todas_las_publicaciones(articulo_id)
    return {"mensaje": "Publicaciones generadas, pendientes de aprobación"}


@app.get("/publicaciones/pendientes")
def ver_publicaciones_pendientes():
    """Lista todas las publicaciones pendientes de aprobación."""
    publicaciones = obtener_publicaciones_pendientes()
    return {"total": len(publicaciones), "publicaciones": publicaciones}


@app.post("/publicaciones/aprobar/{publicacion_id}")
def aprobar(publicacion_id: int):
    """Aprueba una publicación para ser difundida."""
    aprobar_publicacion(publicacion_id)
    return {"mensaje": f"Publicación {publicacion_id} aprobada"}


# ── MONITOREO ────────────────────────────────────────────────
@app.post("/monitoreo/agregar")
def agregar_a_monitoreo(url_o_uuid: str, agregado_por: str = "administrador"):
    """Agrega un artículo al monitoreo usando URL o UUID del repositorio."""
    resultado = agregar_articulo_completo(url_o_uuid, agregado_por)
    return resultado


@app.get("/monitoreo/articulos")
def ver_articulos_monitoreados():
    """Lista todos los artículos que la regional está monitoreando."""
    articulos = obtener_articulos_monitoreados()
    return {"total": len(articulos), "articulos": articulos}


@app.delete("/monitoreo/eliminar/{uuid:path}")
def eliminar_de_monitoreo(uuid: str):
    """
    Elimina un artículo del monitoreo de la regional.
    uuid:path permite DOIs con barras como 10.1016/j.example
    No borra el artículo de la base de datos, solo lo desactiva del monitoreo.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE articulo_monitoreado
            SET activo = FALSE
            WHERE articulo_uuid = %s
        """, (uuid,))

        afectados = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if afectados == 0:
            raise HTTPException(
                status_code=404,
                detail="Artículo no encontrado en el monitoreo"
            )

        return {"mensaje": "Artículo eliminado del monitoreo"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── DOI / CROSSREF ───────────────────────────────────────────
@app.post("/doi/registrar")
def registrar_por_doi(doi: str, registrado_por: str = "administrador"):
    """
    Registra un artículo usando su DOI.
    Consulta CrossRef automáticamente para obtener los metadatos.
    """
    resultado = registrar_articulo(doi, registrado_por)
    return resultado


@app.post("/doi/registrar-issn")
def registrar_por_issn_endpoint(issn: str, registrado_por: str = "administrador"):
    """
    Registra todos los artículos recientes de una revista usando su ISSN.
    """
    resultado = registrar_por_issn(issn, registrado_por)
    return resultado


# ── USUARIOS Y ROLES ─────────────────────────────────────────
@app.post("/usuarios/crear")
def crear_nuevo_usuario(
    nombre: str,
    correo: str,
    rol: str = "investigador",
    area_interes: str = ""
):
    """Crea un usuario con rol investigador o administrador."""
    try:
        from roles import crear_usuario
        usuario = crear_usuario(nombre, correo, rol, area_interes)
        return {"mensaje": "Usuario creado", "usuario": usuario}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/usuarios")
def ver_usuarios():
    """Lista todos los usuarios del sistema."""
    try:
        from roles import listar_usuarios
        return {"usuarios": listar_usuarios()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bandeja/{usuario_id}/{rol}")
def bandeja_por_rol(usuario_id: int, rol: str):
    """
    Devuelve publicaciones según el rol.
    investigador: solo sus artículos dentro de 72h
    administrador: todas las pendientes sin restricción
    """
    try:
        from roles import obtener_publicaciones_por_rol
        publicaciones = obtener_publicaciones_por_rol(usuario_id, rol)
        return {
            "usuario_id": usuario_id,
            "rol":        rol,
            "total":      len(publicaciones),
            "publicaciones": publicaciones
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/publicaciones/aprobar-rol/{publicacion_id}/{usuario_id}/{rol}")
def aprobar_con_rol(publicacion_id: int, usuario_id: int, rol: str):
    """
    Aprueba verificando el Modelo 3:
    investigador tiene 72h, luego solo el administrador puede aprobar.
    """
    try:
        from roles import puede_aprobar
        autorizado, motivo = puede_aprobar(usuario_id, publicacion_id, rol)
        if not autorizado:
            raise HTTPException(status_code=403, detail=motivo)
        aprobar_publicacion(publicacion_id)
        return {"mensaje": "Publicación aprobada", "publicacion_id": publicacion_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/metricas")
def obtener_metricas_dashboard():
    """
    Devuelve todas las métricas de los artículos
    monitoreados por la regional para el dashboard.
    """
    try:
        conn = conectar()
        cursor = conn.cursor()

        # Total de eventos por artículo
        cursor.execute("""
            SELECT
                a.id,
                a.titulo,
                a.autores,
                a.doi,
                a.fecha,
                a.revista,
                a.enlace,
                COUNT(m.id) as total_eventos,
                SUM(CASE WHEN m.tipo_evento = 'vista'    THEN 1 ELSE 0 END) as vistas,
                SUM(CASE WHEN m.tipo_evento = 'descarga' THEN 1 ELSE 0 END) as descargas
            FROM articulo a
            JOIN articulo_monitoreado am ON a.uuid = am.articulo_uuid
            LEFT JOIN metrica m ON a.id = m.articulo_id
            WHERE am.activo = TRUE
            GROUP BY a.id, a.titulo, a.autores, a.doi, a.fecha, a.revista, a.enlace
            ORDER BY total_eventos DESC
        """)
        columnas = [desc[0] for desc in cursor.description]
        articulos = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

        # Eventos por red social
        cursor.execute("""
            SELECT
                m.origen,
                COUNT(*) as total
            FROM metrica m
            JOIN articulo a ON m.articulo_id = a.id
            JOIN articulo_monitoreado am ON a.uuid = am.articulo_uuid
            WHERE am.activo = TRUE
            GROUP BY m.origen
            ORDER BY total DESC
        """)
        por_red = [{"red": fila[0], "total": fila[1]}
                   for fila in cursor.fetchall()]

        # Evolución por mes (últimos 6 meses)
        cursor.execute("""
            SELECT
                TO_CHAR(m.fecha_evento, 'YYYY-MM') as mes,
                COUNT(*) as total
            FROM metrica m
            JOIN articulo a ON m.articulo_id = a.id
            JOIN articulo_monitoreado am ON a.uuid = am.articulo_uuid
            WHERE am.activo = TRUE
              AND m.fecha_evento >= NOW() - INTERVAL '6 months'
            GROUP BY mes
            ORDER BY mes ASC
        """)
        evolucion = [{"mes": fila[0], "total": fila[1]}
                     for fila in cursor.fetchall()]

        # Totales generales
        total_vistas = sum(a["vistas"] or 0 for a in articulos)
        total_descargas = sum(a["descargas"] or 0 for a in articulos)
        total_eventos = sum(a["total_eventos"] or 0 for a in articulos)

        cursor.close()
        conn.close()

        return {
            "resumen": {
                "total_articulos":  len(articulos),
                "total_vistas":     total_vistas,
                "total_descargas":  total_descargas,
                "total_eventos":    total_eventos
            },
            "articulos":  articulos,
            "por_red":    por_red,
            "evolucion":  evolucion
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/metricas/registrar")
def registrar_metrica(articulo_id: int, tipo: str, origen: str = "web"):
    """
    Registra una vista o descarga de un artículo.
    tipo: 'vista' o 'descarga'
    origen: 'web', 'linkedin', 'twitter', 'instagram', 'whatsapp'
    """
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO metrica (articulo_id, tipo_evento, origen)
            VALUES (%s, %s, %s)
        """, (articulo_id, tipo, origen))
        conn.commit()
        cursor.close()
        conn.close()
        return {"mensaje": "Métrica registrada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
