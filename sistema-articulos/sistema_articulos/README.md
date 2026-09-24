# Sistema de Visibilización de Producción Académica — UNIMINUTO

Proyecto de grado — [nombre del programa] — UNIMINUTO Regional [nombre]

## Descripción
Sistema inteligente que permite registrar, buscar, recomendar
y difundir artículos académicos de investigadores de UNIMINUTO
en redes sociales, usando inteligencia artificial y la API de
CrossRef para el registro por DOI.

## Funcionalidades
- Registro de artículos por DOI desde cualquier editorial
- Registro de revistas completas por ISSN
- Buscador semántico en lenguaje natural
- Recomendaciones personalizadas por perfil
- Generación automática de contenido para 4 redes sociales
- Bandeja de aprobación con Modelo 3 (investigador 72h → administrador)
- Dashboard de métricas de impacto
- Portal web con roles de investigador y administrador

## Estado del proyecto
- [x] Fase 1 — Conexión con repositorio UNIMINUTO
- [x] Fase 2 — Base de datos PostgreSQL
- [x] Fase 3 — Backend FastAPI + búsqueda semántica
- [x] Fase 4 — Recomendaciones + generador redes sociales
- [x] Fase 5 — Portal web + registro por DOI/ISSN
- [x] Fase 6 — Roles + pruebas + cierre

## Stack tecnológico
- Python 3.13 + FastAPI
- PostgreSQL 18 + ChromaDB
- Sentence-Transformers (NLP)
- Groq/LLaMA (generación de contenido)
- CrossRef API (metadatos por DOI)
- HTML + CSS + JavaScript (portal web)

## Cómo ejecutar
```bash
# Activar entorno virtual
venv\Scripts\activate

# Iniciar servidor
cd src
uvicorn api:app --reload

# Abrir portal
frontend\index.html
```

## Autores
[Nombre del director] · [Nombre de la estudiante]
[Programa académico] — UNIMINUTO Regional [nombre] — [año]