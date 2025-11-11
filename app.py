import streamlit as st
import pandas as pd
import folium
from folium import PolyLine
from geopy.distance import geodesic
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import requests
from PIL import Image as PILImage
import openai
import os
import re

# --------------------
# CONFIGURACIÓN OPENAI
# --------------------
api_key = os.getenv("OPENAI_API_KEY")

# Clave temporal para pruebas locales
if not api_key:
api_key = "TU_API_KEY_DE_PRUEBA_AQUI"
st.warning("⚠️ Usando API key temporal para pruebas. Para producción, configura la variable de entorno OPENAI_API_KEY.")

openai.api_key = api_key
openai_configured = True if api_key else False

# --------------------
# LISTA AMPLIADA DE ATRACTIVOS
# --------------------
atractivos = [
{"nombre": "Playa Chinchorro", "lat": -18.4726, "lon": -70.3128, "tiempo": 2, "descripcion": "Amplia playa urbana ideal para nadar y disfrutar del sol.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/1/11/Playa_Chinchorro_Arica_2020.jpg"},
{"nombre": "Playa El Laucho", "lat": -18.4872, "lon": -70.3232, "tiempo": 1.5, "descripcion": "Playa céntrica de aguas calmadas, ideal para familias.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Playa_El_Laucho_Arica.jpg"},
{"nombre": "Humedal del Río Lluta", "lat": -18.4395, "lon": -70.3170, "tiempo": 1.5, "descripcion": "Santuario de aves migratorias con senderos y miradores naturales.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/b/bd/Humedal_del_R%C3%ADo_Lluta_-_Arica.jpg"},
{"nombre": "Morro de Arica", "lat": -18.4806, "lon": -70.3273, "tiempo": 2, "descripcion": "Histórico morro con museo y mirador panorámico.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/8/8d/Morro_de_Arica.jpg"},
{"nombre": "Museo de Sitio Colón 10", "lat": -18.4770, "lon": -70.3183, "tiempo": 1.5, "descripcion": "Museo con las momias más antiguas del mundo, cultura Chinchorro.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/f/f3/Museo_de_Sitio_Col%C3%B3n_10_-_Arica.jpg"},
{"nombre": "Cuevas de Anzota", "lat": -18.5358, "lon": -70.3511, "tiempo": 1.5, "descripcion": "Formaciones rocosas junto al mar, historia arqueológica y miradores.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/7/7d/Cuevas_de_Anzota_-_Arica.jpg"},
{"nombre": "Valle de Azapa", "lat": -18.481, "lon": -70.308, "tiempo": 2, "descripcion": "Valle agrícola famoso por olivos, aceitunas y cultura local.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/3/3d/Valle_de_Azapa.jpg"},
{"nombre": "Geoglifos de Lluta", "lat": -18.20, "lon": -70.30, "tiempo": 1.5, "descripcion": "Antiguos dibujos prehispánicos visibles desde miradores en el valle de Lluta.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/5/57/Sajama_National_Park_Bolivia.jpg"},
{"nombre": "Parque Nacional Lauca", "lat": -18.2333, "lon": -69.1667, "tiempo": 4, "descripcion": "Área de altura con lagos, volcanes y fauna altiplánica.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/1/1d/Lago_Chungara_y_volcan_Parinacota.jpg"},
{"nombre": "Putre", "lat": -18.1977, "lon": -69.5593, "tiempo": 3, "descripcion": "Pueblo altiplánico tradicional, base para excursiones al altiplano.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Putre_-_Chile.jpg"},
{"nombre": "Termas de Jurasi", "lat": -18.2255, "lon": -69.5250, "tiempo": 2, "descripcion": "Piscinas termales naturales cerca de Putre, ideal para relajarse en altura.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/5/57/Termas_de_Jurasi_Putre.jpg"},
{"nombre": "Salar de Surire", "lat": -19.366, "lon": -69.383, "tiempo": 3, "descripcion": "Salar andino con flamencos y paisaje altiplánico único.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/5/57/Salar_de_Surire.jpg"},
{"nombre": "Codpa", "lat": -18.1928, "lon": -69.8819, "tiempo": 2, "descripcion": "Valle tradicional con vino artesanal, historia y pueblo rural tranquilo.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/9/91/Codpa_Arica.jpg"},
{"nombre": "Camarones", "lat": -18.200, "lon": -70.500, "tiempo": 2, "descripcion": "Pueblo costero tradicional, conocido por mariscos y ambiente tranquilo.", "imagen_url": "https://upload.wikimedia.org/wikipedia/commons/9/9f/Camarones_Arica.jpg"}
]

# --------------------
# FUNCIONES
# --------------------
def distancia(a, b):
return geodesic((a["lat"], a["lon"]), (b["lat"], b["lon"])).km

def agrupar_por_dia(destinos, dias):
grupos = [[] for _ in range(dias)]
destinos = sorted(destinos, key=lambda x: (x["lat"], x["lon"]))
for idx, d in enumerate(destinos):
grupos[idx % dias].append(d)
for i, grupo in enumerate(grupos):
if len(grupo) > 1:
ordenado = [grupo[0]]
resto = grupo[1:]
while resto:
last = ordenado[-1]
next_dest = min(resto, key=lambda x: distancia(last, x))
ordenado.append(next_dest)
resto.remove(next_dest)
grupos[i] = ordenado
return grupos

def generar_itinerario(destinos, dias):
grupos = agrupar_por_dia(destinos, dias)
itinerario = []
for i, dia_grupo in enumerate(grupos):
for d in dia_grupo:
itinerario.append({
"Día": i + 1,
"Destino": d["nombre"],
"Descripción": d["descripcion"],
"Tiempo estimado (h)": d["tiempo"],
"lat": d["lat"],
"lon": d["lon"],
"imagen_url": d["imagen_url"]
})
return itinerario

def responder_pregunta(pregunta):
if not openai_configured:
return [("Chatbot no disponible: falta API key de OpenAI.", None)]

prompt = f"Actúa como guía turístico experto en Arica y Parinacota y responde claramente: {pregunta}."
try:
response = openai.Completion.create(
engine="text-davinci-003",
prompt=prompt,
temperature=0.6,
max_tokens=400
)
texto = response.choices[0].text.strip()
except Exception as e:
return [(f"Error al llamar a OpenAI: {e}", None)]

resultado = []
for linea in texto.split('\n'):
encontrado = False
for a in atractivos:
if re.search(rf"\b{re.escape(a['nombre'])}\b", linea, re.IGNORECASE):
resultado.append((linea, a.get("imagen_url")))
encontrado = True
break
if not encontrado:
resultado.append((linea, None))
return resultado

# --------------------
# STREAMLIT UI
# --------------------
st.set_page_config(page_title="Asistente Turístico Arica y Parinacota", layout="wide")
st.title("🏔️ Asistente Turístico Interactivo + Chatbot")

dias = st.number_input("Cantidad de días de visita", min_value=1, max_value=10, value=3)

st.subheader("Atractivos Turísticos")
seleccionados = []
num_cols = 3
cols = st.columns(num_cols)
for i, a in enumerate(atractivos):
with cols[i % num_cols]:
try:
response = requests.get(a["imagen_url"])
img_pil = PILImage.open(BytesIO(response.content))
st.image(img_pil, caption=a["nombre"], use_column_width=True)
except:
st.text(a["nombre"])
if st.checkbox(f"Seleccionar", key=a["nombre"]):
seleccionados.append(a)

if st.button("Generar Itinerario"):
if not seleccionados:
st.warning("Selecciona al menos un destino.")
else:
itinerario = generar_itinerario(seleccionados, dias)
st.dataframe(pd.DataFrame(itinerario))
mapa = folium.Map(location=[-18.48, -70.32], zoom_start=8)
line_coords = []
for dest in itinerario:
folium.Marker([dest["lat"], dest["lon"]], popup=dest["Destino"], tooltip=dest["Destino"]).add_to(mapa)
line_coords.append((dest["lat"], dest["lon"]))
if len(line_coords) > 1:
PolyLine(line_coords, color="blue", weight=3).add_to(mapa)
st.components.v1.html(mapa._repr_html_(), height=500)

def generar_pdf(itinerario):
buffer = BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter)
styles = getSampleStyleSheet()
elems = [Paragraph("Itinerario Turístico - Arica y Parinacota", styles['Title']), Spacer(1, 12)]
for item in itinerario:
elems.append(Paragraph(f"Día {item['Día']}: {item['Destino']} ({item['Tiempo estimado (h)']}h)", styles['Heading2']))
elems.append(Paragraph(item['Descripción'], styles['BodyText']))
try:
response = requests.get(item["imagen_url"])
img_pil = PILImage.open(BytesIO(response.content))
img_pil.save(f"/tmp/{item['Destino']}.png")
elems.append(Image(f"/tmp/{item['Destino']}.png", width=400, height=300))
except:
elems.append(Paragraph("Imagen no disponible", styles['BodyText']))
elems.append(Spacer(1, 12))
ruta_texto = " -> ".join([i['Destino'] for i in itinerario])
elems.append(Paragraph(f"Ruta sugerida: {ruta_texto}", styles['Normal']))
doc.build(elems)
buffer.seek(0)
return buffer

pdf_buffer = generar_pdf(itinerario)
st.download_button("📄 Descargar PDF con fotos y ruta", pdf_buffer, "itinerario_arica.pdf")

# --------------------
# CHATBOT
# --------------------
st.subheader("💬 Chatbot turístico con imágenes")
pregunta = st.text_input("Escribe tu pregunta sobre Arica y Parinacota:")
if st.button("Responder"):
if pregunta:
respuesta = responder_pregunta(pregunta)
for linea, img_url in respuesta:
st.markdown(linea)
if img_url:
try:
response = requests.get(img_url)
img_pil = PILImage.open(BytesIO(response.content))
st.image(img_pil, width=300)
except:
pass
