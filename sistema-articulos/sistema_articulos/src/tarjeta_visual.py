import textwrap
import io
import base64
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from dotenv import load_dotenv
import sys
import os

# Cargar .env desde la carpeta raíz del proyecto
ruta_env = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '.env')

load_dotenv(ruta_env)


UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
print(
    f"Clave Unsplash cargada: {'Sí — ' + UNSPLASH_KEY[:8] + '...' if UNSPLASH_KEY else 'NO ENCONTRADA'}")

# Colores UNIMINUTO
AZUL = (26, 42, 94)
AMARILLO = (255, 209, 0)
BLANCO = (255, 255, 255)


def buscar_imagen_unsplash(palabras_clave, ancho=1200, alto=630):
    if not UNSPLASH_KEY:
        print("  Sin clave Unsplash — usando fondo institucional")
        return None
    try:
        terminos = " ".join(palabras_clave.split()[:4])
        url = "https://api.unsplash.com/photos/random"
        params = {
            "query": terminos,
            "orientation": "landscape",
            "content_filter": "high"
        }
        headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            params["query"] = "academic research university"
            res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            img_url = res.json()["urls"]["regular"]
            img_res = requests.get(img_url, timeout=15)
            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
            img = img.resize((ancho, alto), Image.LANCZOS)
            return img
    except Exception as e:
        print(f"  Error buscando imagen: {e}")
    return None


def extraer_palabras_clave(titulo, area=""):
    traducciones = {
        "educación": "education",
        "ambiental": "environment nature",
        "salud": "health medicine",
        "tecnología": "technology",
        "investigación": "research science",
        "infancias": "children education",
        "sostenibilidad": "sustainability",
        "digital": "digital technology",
        "social": "social community",
        "economía": "economy business",
        "ingeniería": "engineering",
        "administración": "business management",
        "psicología": "psychology mind",
        "derecho": "law justice",
        "arte": "art creativity",
        "ciencia": "science laboratory",
        "datos": "data analytics",
        "inteligencia artificial": "artificial intelligence",
        "comunidad": "community people",
        "universidad": "university campus",
    }
    texto = (titulo + " " + area).lower()
    palabras_en = []
    for es, en in traducciones.items():
        if es in texto:
            palabras_en.append(en)
            if len(palabras_en) >= 2:
                break
    return " ".join(palabras_en) if palabras_en else "academic research"


def generar_tarjeta(titulo, autores, revista, doi,
                    area="", ancho=1200, alto=630):
    print("  Buscando imagen alusiva en Unsplash...", end=" ")
    palabras = extraer_palabras_clave(titulo, area)
    fondo = buscar_imagen_unsplash(palabras, ancho, alto)

    if fondo:
        print("✓ imagen encontrada")
        fondo = fondo.filter(ImageFilter.GaussianBlur(radius=2))
        enhancer = ImageEnhance.Brightness(fondo)
        fondo = enhancer.enhance(0.35)
        img = fondo.copy()
    else:
        print("✓ usando fondo institucional")
        img = Image.new("RGB", (ancho, alto), AZUL)
        draw_bg = ImageDraw.Draw(img)
        for i in range(alto):
            ratio = i / alto
            r = int(26 + (10 - 26) * ratio)
            g = int(42 + (26 - 42) * ratio)
            b = int(94 + (74 - 94) * ratio)
            draw_bg.line([(0, i), (ancho, i)], fill=(r, g, b))

    draw = ImageDraw.Draw(img)

    overlay = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for i in range(alto):
        ratio = i / alto
        alpha = int(200 * ratio) if ratio > 0.3 else int(200 *
                                                         0.3 * (ratio / 0.3))
        draw_ov.line([(0, i), (ancho, i)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        fuente_titulo = ImageFont.truetype("arialbd.ttf", 52)
        fuente_autor = ImageFont.truetype("arial.ttf",   30)
        fuente_revista = ImageFont.truetype("arial.ttf",   24)
        fuente_small = ImageFont.truetype("arial.ttf",   20)
        fuente_logo = ImageFont.truetype("arialbd.ttf", 28)
    except:
        fuente_titulo = ImageFont.load_default()
        fuente_autor = ImageFont.load_default()
        fuente_revista = ImageFont.load_default()
        fuente_small = ImageFont.load_default()
        fuente_logo = ImageFont.load_default()

    draw.rectangle([0, 0, 8, alto], fill=AMARILLO)
    draw.rectangle([0, 0, ancho, 6], fill=AMARILLO)

    draw.rectangle([20, 20, 380, 58], fill=(*AZUL, 200))
    draw.text((30, 26), "  Investigación · UNIMINUTO Regional",
              font=fuente_small, fill=AMARILLO)

    titulo_corto = titulo[:110] + "..." if len(titulo) > 110 else titulo
    lineas = textwrap.wrap(titulo_corto, width=44)
    y_titulo = alto - 220
    for linea in lineas[:3]:
        draw.text((30, y_titulo), linea, font=fuente_titulo, fill=BLANCO)
        y_titulo += 64

    draw.rectangle([30, y_titulo + 6, 180, y_titulo + 10], fill=AMARILLO)

    autores_corto = autores[:80] + "..." if len(autores) > 80 else autores
    draw.text((30, y_titulo + 20), autores_corto,
              font=fuente_autor, fill=(220, 220, 220))

    if revista:
        revista_corto = revista[:65] + "..." if len(revista) > 65 else revista
        draw.text((30, y_titulo + 62), f"📰  {revista_corto}",
                  font=fuente_revista, fill=(180, 180, 180))

    if doi:
        draw.text((30, alto - 36), f"DOI: {doi[:55]}",
                  font=fuente_small, fill=(160, 160, 160))

    draw.text((ancho - 220, alto - 36), "UNIMINUTO",
              font=fuente_logo, fill=AMARILLO)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90, optimize=True)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def guardar_tarjeta_archivo(titulo, autores, revista, doi,
                            area="", ruta_salida="tarjeta.jpg"):
    img_b64 = generar_tarjeta(titulo, autores, revista, doi, area)
    img_bytes = base64.b64decode(img_b64)
    with open(ruta_salida, "wb") as f:
        f.write(img_bytes)
    print(f"✓ Tarjeta guardada en: {ruta_salida}")
    return ruta_salida


if __name__ == "__main__":
    guardar_tarjeta_archivo(
        titulo="Infancias y educación ambiental: tensiones latentes y asunto pendiente",
        autores="Pino Perdomo, Felipe Mauricio",
        revista="Libros Científicos UNIMINUTO",
        doi="10.26620/uniminuto.978-958-763-580-8",
        area="educación ambiental infancias",
        ruta_salida="src/tarjeta_prueba.jpg"
    )
