import streamlit as st
import openai
import os
from geopy.distance import geodesic
from fpdf import FPDF
import math
import folium
from streamlit_folium import st_folium
import requests
from PIL import Image
from io import BytesIO
import tempfile
import re

# ---------- CONFIGURACIÓN ---------- #
st.set_page_config(page_title="App Turística - Arica y Parinacota", layout="wide")

# ---------- DATOS DE DESTINOS ---------- #
destinos = [
    {"nombre": "Morro de Arica", "lat": -18.477, "lon": -70.330, "tipo": "Cultura", "tiempo": 1.5,
     "region": "Ciudad", "descripcion": "Icono histórico con vista panorámica de la ciudad.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/2c/Morro_de_Arica.jpg"},
    {"nombre": "Playa El Laucho", "lat": -18.486, "lon": -70.318, "tipo": "Playa", "tiempo": 2,
     "region": "Costa", "descripcion": "Playa tranquila ideal para relajarse y tomar sol.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/4/4e/Playa_El_Laucho_Arica.jpg"},
    {"nombre": "Cuevas de Anzota", "lat": -18.533, "lon": -70.353, "tipo": "Naturaleza", "tiempo": 1.5,
     "region": "Costa", "descripcion": "Cuevas naturales con formaciones rocosas únicas.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/7/7e/Cuevas_de_Anzota.jpg"},
    {"nombre": "Playa Chinchorro", "lat": -18.466, "lon": -70.307, "tipo": "Playa", "tiempo": 2.5,
     "region": "Costa", "descripcion": "Famosa playa con actividades de pesca y deportes acuáticos.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Playa_Chinchorro_Arica.jpg"},
    {"nombre": "Humedal del Río Lluta", "lat": -18.425, "lon": -70.324, "tipo": "Naturaleza", "tiempo": 2,
     "region": "Costa", "descripcion": "Ecosistema protegido, ideal para observación de aves.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Humedal_del_Rio_Lluta_Arica.jpg"},
    {"nombre": "Museo de Azapa", "lat": -18.52, "lon": -70.33, "tipo": "Cultura", "tiempo": 1.5,
     "region": "Valle", "descripcion": "Museo arqueológico con momias y artefactos de la cultura Chinchorro.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/e/ea/Museo_Azapa_Arica.jpg"},
    {"nombre": "Valle de Lluta", "lat": -18.43, "lon": -70.32, "tipo": "Naturaleza", "tiempo": 2,
     "region": "Valle", "descripcion": "Hermoso valle con agricultura tradicional y paisajes naturales.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/1/12/Valle_de_Lluta_Arica.jpg"},
    {"nombre": "Catedral de San Marcos", "lat": -18.478, "lon": -70.328, "tipo": "Cultura", "tiempo": 1,
     "region": "Ciudad", "descripcion": "Imponente catedral del centro de Arica, arquitectura neoclásica.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/0/02/Catedral_de_San_Marcos_Arica.jpg"},
    {"nombre": "La Ex Aduana", "lat": -18.479, "lon": -70.329, "tipo": "Cultura", "tiempo": 1,
     "region": "Ciudad", "descripcion": "Edificio histórico que albergó la aduana de la ciudad.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Ex_Aduana_Arica.jpg"},
    {"nombre": "Putre", "lat": -18.195, "lon": -69.559, "tipo": "Cultura", "tiempo": 3,
     "region": "Altiplano", "descripcion": "Pueblo tradicional a orillas del altiplano con cultura Aymara.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/d/d3/Putre_village.jpg"},
    {"nombre": "Parque Nacional Lauca", "lat": -18.243, "lon": -69.352, "tipo": "Naturaleza", "tiempo": 4,
     "region": "Altiplano", "descripcion": "Parque con volcanes, lagunas y fauna típica de la zona.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/2/2c/Parque_Nacional_Lauca_Chile.jpg"},
    {"nombre": "Lago Chungará", "lat": -18.25, "lon": -69.15, "tipo": "Naturaleza", "tiempo": 2,
     "region": "Altiplano", "descripcion": "Lago a gran altitud con vistas espectaculares y flamencos.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Lago_Chungara.jpg"},
    {"nombre": "Salar de Surire", "lat": -18.85, "lon": -69.05, "tipo": "Naturaleza", "tiempo": 3.5,
     "region": "Altiplano", "descripcion": "Salar impresionante con fauna típica del altiplano.",
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/7/74/Salar_de_Surire.jpg"}
]

colores_region = {"Ciudad": "#FFA07A", "Costa": "#87CEEB", "Valle": "#98FB98", "Altiplano": "#DDA0DD"}

# ---------- FUNCIONES ---------- #
def calcular_distancia(d1, d2):
    return geodesic((d1["lat"], d1["lon"]), (d2["lat"], d2["lon"])).km


def generar_itinerario_por_cercania(destinos_seleccionados, dias):
    itinerario = {f"Día {i+1}": [] for i in range(dias)}
    if not destinos_seleccionados:
        return itinerario
    pendientes = destinos_seleccionados.copy()
    dia = 0
    actual = pendientes.pop(0)
    while pendientes:
        itinerario[f"Día {dia+1}"].append(actual)
        if len(itinerario[f"Día {dia+1}"]) >= math.ceil(len(destinos_seleccionados)/dias):
            dia = (dia+1) % dias
        if pendientes:
            siguiente = min(pendientes, key=lambda x: calcular_distancia(actual, x))
            pendientes.remove(siguiente)
            actual = siguiente
    itinerario[f"Día {dia+1}"].append(actual)
    return itinerario


def generar_link_google_maps(destinos_seleccionados):
    base_url = "https://www.google.com/maps/dir/"
    for d in destinos_seleccionados:
        base_url += f"{d['lat']},{d['lon']}/"
    return base_url


def generar_pdf_lujo(itinerario):
    pdf = FPDF('P', 'mm', 'A4')
    pdf.set_auto_page_break(auto=True, margin=15)

    def limpiar_texto(texto):
        texto = re.sub(r'[^\x00-\x7F]+', ' ', texto)
        return texto

    # Portada
    pdf.add_page()
    pdf.set_font("Arial", "B", 28)
    pdf.cell(0, 20, "Itinerario Turístico", ln=True, align="C")
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 15, "Arica y Parinacota", ln=True, align="C")
    try:
        portada_url = "https://upload.wikimedia.org/wikipedia/commons/2/2c/Morro_de_Arica.jpg"
        response = requests.get(portada_url)
        img = Image.open(BytesIO(response.content))
        temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name
        img.thumbnail((500, 500))
        img.save(temp_path)
        pdf.image(temp_path, x=30, y=60, w=150)
    except:
        pass
    pdf.add_page()

    # Tabla de contenido
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Tabla de Contenido", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 14)
    for idx, dia in enumerate(itinerario.keys()):
        pdf.cell(0, 8, f"{idx+1}. {dia}", ln=True)
    pdf.add_page()

    # Itinerario por día
    for dia, lugares in itinerario.items():
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 10, limpiar_texto(dia), ln=True)
        pdf.ln(5)
        for lugar in lugares:
            color = colores_region.get(lugar["region"], "#FFFFFF")
            pdf.set_fill_color(int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
            pdf.set_font("Arial", "B", 16)
            pdf.multi_cell(0, 8, limpiar_texto(f"{lugar['nombre']} ({lugar['region']})"), border=1, fill=True)
            try:
                response = requests.get(lugar["imagen"])
                img = Image.open(BytesIO(response.content))
                temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name

