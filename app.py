import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Configuración general de la página
st.set_page_config(page_title="Visor Ambiental Áncash", layout="wide")
st.title("🌍 Visor de Gestión Ambiental y Recursos Hídricos - Áncash")
st.markdown("Plataforma interactiva para la visualización de derechos de uso, fuentes contaminantes, redes de monitoreo y pasivos ambientales.")

# 2. Cargar los datos
@st.cache_data
def load_data():
    # Cargar el CSV exportado desde QGIS
    df = pd.read_csv("Datos_Visor_Ancash.csv", low_memory=False) 
    
    # Limpiar posibles valores nulos en los filtros principales
    df['Cuenca'] = df['Cuenca'].fillna('Sin Cuenca')
    df['Provincia'] = df['Provincia'].fillna('Sin Provincia')
    df['Tipo_Dataset'] = df['Tipo_Dataset'].fillna('Registro General')
    df['Entidad'] = df['Entidad'].fillna('No definida')
    return df

df = load_data()

# 3. Panel Lateral (Filtros Interactivos)
st.sidebar.header("Filtros de Búsqueda")

# Filtro por Tipo de Dataset (El más importante para separar tu info)
datasets = ["Todos"] + sorted([str(t) for t in df['Tipo_Dataset'].unique() if pd.notna(t)])
dataset_sel = st.sidebar.selectbox("1. Seleccione el Tipo de Información:", datasets)

df_filt = df if dataset_sel == "Todos" else df[df['Tipo_Dataset'] == dataset_sel]

# Filtro por Cuenca (se actualiza según el dataset elegido)
cuencas = ["Todas"] + sorted([str(c) for c in df_filt['Cuenca'].unique() if pd.notna(c)])
cuenca_sel = st.sidebar.selectbox("2. Seleccione la Cuenca:", cuencas)

if cuenca_sel != "Todas":
    df_filt = df_filt[df_filt['Cuenca'] == cuenca_sel]

# Filtro por Entidad (ej. ANA, OEFA)
entidades = ["Todas"] + sorted([str(e) for e in df_filt['Entidad'].unique() if pd.notna(e)])
entidad_sel = st.sidebar.selectbox("3. Seleccione la Entidad:", entidades)

if entidad_sel != "Todas":
    df_filt = df_filt[df_filt['Entidad'] == entidad_sel]

# Conteo Dinámico de Puntos
st.sidebar.markdown("---")
st.sidebar.success(f"📌 **{len(df_filt)}** puntos encontrados en pantalla.")

# 4. Renderizado del Mapa
# Centramos el mapa aproximadamente en Áncash
mapa = folium.Map(location=[-9.52, -77.52], zoom_start=8, tiles="CartoDB positron")

# Límite de seguridad visual (para no colgar el navegador web si se muestran los 35,000 puntos de golpe)
limite_puntos = df_filt.head(4000)

for idx, row in limite_puntos.iterrows():
    # Validar que las coordenadas existan (X = Longitud, Y = Latitud)
    if pd.notna(row.get('Y')) and pd.notna(row.get('X')):
        
        # Diseño de la ventana emergente (Pop-up)
        html_popup = f"""
        <div style="font-family: Arial; font-size: 12px;">
            <h4 style="margin-top: 0px; margin-bottom: 5px; color: #004d99;">{row.get('Tipo_Dataset', '')}</h4>
            <b>Entidad:</b> {row.get('Entidad', '')}<br>
            <b>Cuenca:</b> {row.get('Cuenca', '')}<br>
            <b>Provincia/Distrito:</b> {row.get('Provincia', '')} / {row.get('Distrito', '')}
        </div>
        """
        
        # Asignar un color diferente según la entidad para hacerlo más visual
        color_punto = "#0068c9" # Azul por defecto (ANA)
        if "OEFA" in str(row.get('Entidad')): color_punto = "#ff7f0e" # Naranja
        elif "INAIGEM" in str(row.get('Entidad')): color_punto = "#2ca02c" # Verde
        
        folium.CircleMarker(
            location=[row['Y'], row['X']],
            radius=5,
            popup=folium.Popup(html_popup, max_width=300),
            color=color_punto,
            fill=True,
            fill_opacity=0.8
        ).add_to(mapa)

if len(df_filt) > 4000:
    st.warning("⚠️ Se están mostrando solo los primeros 4,000 puntos en el mapa para mantener la fluidez. Usa los filtros para refinar tu búsqueda.")

# Mostrar el mapa interactivo
st_folium(mapa, width=1200, height=600, returned_objects=[])

# 5. Mostrar la tabla de datos debajo
st.subheader("Base de Datos Filtrada")
st.dataframe(df_filt)