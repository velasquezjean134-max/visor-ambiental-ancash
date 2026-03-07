import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import os
from branca.element import Template, MacroElement # ¡Nueva herramienta para la leyenda!

# 1. Configuración general de la página
st.set_page_config(page_title="Visor Ambiental Áncash", layout="wide")

# --- MAGIA CSS PARA ELIMINAR ESPACIOS EN BLANCO ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        footer {visibility: hidden;}
        h2 {padding-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

# --- MENSAJE DE BIENVENIDA TEMPORAL (TOAST) ---
if 'bienvenida_mostrada' not in st.session_state:
    st.toast("👋 Bienvenido, active algunos filtros para poder iniciar a visualizar la información.", icon="👋")
    st.session_state['bienvenida_mostrada'] = True

# --- 2. ENCABEZADO INSTITUCIONAL CON LOGOS ---
col_logo1, col_titulo, col_logo2 = st.columns([1.5, 7, 1.5])

with col_logo1:
    if os.path.exists("logo_izquierdo.png"): st.image("logo_izquierdo.png", use_container_width=True)
    else: st.markdown("<div style='text-align: center; color: #ccc; border: 1px dashed #ccc; padding: 10px;'>Logo Izquierdo</div>", unsafe_allow_html=True)

with col_titulo:
    st.markdown("<h2 style='text-align: center; margin-top: 0px;'>Sistema de Información Ambiental Regional - SICAR</h2>", unsafe_allow_html=True)

with col_logo2:
    if os.path.exists("logo_derecho.png"): st.image("logo_derecho.png", use_container_width=True)
    else: st.markdown("<div style='text-align: center; color: #ccc; border: 1px dashed #ccc; padding: 10px;'>Logo Derecho</div>", unsafe_allow_html=True)

st.markdown("---") 

# 3. Cargar Datos y Polígonos
@st.cache_data
def load_data():
    df = pd.read_csv("Datos_Visor_Ancash.csv", low_memory=False) 
    df['Cuenca'] = df['Cuenca'].fillna('Sin Cuenca')
    df['Provincia'] = df['Provincia'].fillna('Sin Provincia')
    df['Distrito'] = df['Distrito'].fillna('Sin Distrito')
    df['Tipo_Dataset'] = df['Tipo_Dataset'].fillna('Registro General')
    df['Entidad'] = df['Entidad'].fillna('No definida')
    
    ancash_poly = gpd.read_file("limite_ancash.geojson")
    cuencas_poly = gpd.read_file("limite_cuencas.geojson")
    provincias_poly = gpd.read_file("limite_provincias.geojson")
    distritos_poly = gpd.read_file("limite_distritos.geojson")
    
    return df, ancash_poly, cuencas_poly, provincias_poly, distritos_poly

df, ancash_poly, cuencas_poly, provincias_poly, distritos_poly = load_data()

COLUMNA_CUENCA_GEOJSON = 'NOMBRE' 
COLUMNA_PROV_GEOJSON = 'PROVINCIA'     
COLUMNA_DIST_GEOJSON = 'DISTRITO'    

provincias_ancash = [str(p).upper().strip() for p in provincias_poly[COLUMNA_PROV_GEOJSON].dropna().unique()]
distritos_ancash = [str(d).upper().strip() for d in distritos_poly[COLUMNA_DIST_GEOJSON].dropna().unique()]

# 4. Panel Lateral Izquierdo (Filtros Nativos)
st.sidebar.header("Filtros de Búsqueda")

datasets_unicos = sorted([str(t) for t in df['Tipo_Dataset'].unique() if pd.notna(t)])
dataset_sel = st.sidebar.multiselect("1. Seleccione el Tipo de Información:", datasets_unicos, placeholder="Elija opciones...")

if dataset_sel: df_filt = df[df['Tipo_Dataset'].isin(dataset_sel)]
else: df_filt = df 

cuencas_unicas = sorted([str(c) for c in df_filt['Cuenca'].unique() if pd.notna(c)])
cuencas_sel = st.sidebar.multiselect("2. Seleccione la(s) Cuenca(s):", cuencas_unicas, placeholder="Elija opciones...")

if cuencas_sel: 
    df_filt = df_filt[df_filt['Cuenca'].isin(cuencas_sel)]
    cuencas_para_dibujar = cuencas_sel
else: cuencas_para_dibujar = []

if cuencas_sel: provincias_disponibles = df_filt['Provincia'].unique()
else: provincias_disponibles = [p for p in df_filt['Provincia'].unique() if pd.notna(p) and str(p).upper().strip() in provincias_ancash]

provincias_unicas = sorted([str(p) for p in provincias_disponibles if pd.notna(p)])
prov_sel = st.sidebar.multiselect("3. Seleccione la(s) Provincia(s):", provincias_unicas, placeholder="Elija opciones...")

if prov_sel:
    df_filt = df_filt[df_filt['Provincia'].isin(prov_sel)]
    prov_para_dibujar = prov_sel
else: prov_para_dibujar = []

if cuencas_sel or prov_sel: distritos_disponibles = df_filt['Distrito'].unique()
else: distritos_disponibles = [d for d in df_filt['Distrito'].unique() if pd.notna(d) and str(d).upper().strip() in distritos_ancash]

distritos_unicos = sorted([str(d) for d in distritos_disponibles if pd.notna(d)])
distrito_sel = st.sidebar.multiselect("4. Seleccione el/los Distrito(s):", distritos_unicos, placeholder="Elija opciones...")

if distrito_sel:
    df_filt = df_filt[df_filt['Distrito'].isin(distrito_sel)]
    distritos_para_dibujar = distrito_sel
else: distritos_para_dibujar = []

filtros_activos = bool(dataset_sel) or bool(cuencas_sel) or bool(prov_sel) or bool(distrito_sel)

st.sidebar.markdown("---")
ver_panel = st.sidebar.toggle("📂 Activar Panel Derecho de Detalles", value=False)

# --- DIVISIÓN DE PANTALLA CONDICIONAL ---
if ver_panel: col_mapa, col_panel = st.columns([3, 1])
else: 
    col_mapa = st.container()
    col_panel = None

# --- CONSTRUCCIÓN DEL MAPA ---
with col_mapa:
    mapa = folium.Map(location=[-9.52, -77.52], zoom_start=8, tiles=None)

    # Mapas Base
    folium.TileLayer('CartoDB positron', name='Mapa base').add_to(mapa)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Vista satelital', overlay=False
    ).add_to(mapa)
    folium.TileLayer('OpenStreetMap', name='Vista de Google Maps', overlay=False).add_to(mapa)

    folium.GeoJson(ancash_poly, name="Límite Departamental Áncash", style_function=lambda x: {'fillColor': 'transparent', 'color': '#333333', 'weight': 2, 'dashArray': '5, 5'}).add_to(mapa)

    if cuencas_para_dibujar:
        cuencas_sel_upper = [str(c).upper().strip() for c in cuencas_para_dibujar]
        cuenca_filtrada = cuencas_poly[cuencas_poly[COLUMNA_CUENCA_GEOJSON].fillna('').str.upper().str.strip().isin(cuencas_sel_upper)]
        if not cuenca_filtrada.empty: folium.GeoJson(cuenca_filtrada, name="Cuencas", style_function=lambda x: {'fillColor': '#0068c9', 'color': '#0068c9', 'weight': 2, 'fillOpacity': 0.15}).add_to(mapa)

    if prov_para_dibujar:
        prov_sel_upper = [str(p).upper().strip() for p in prov_para_dibujar]
        provincia_filtrada = provincias_poly[provincias_poly[COLUMNA_PROV_GEOJSON].fillna('').str.upper().str.strip().isin(prov_sel_upper)]
        if not provincia_filtrada.empty: folium.GeoJson(provincia_filtrada, name="Provincias", style_function=lambda x: {'fillColor': '#ff7f0e', 'color': '#ff7f0e', 'weight': 2, 'fillOpacity': 0.15}).add_to(mapa)

    if distritos_para_dibujar:
        distrito_sel_upper = [str(d).upper().strip() for d in distritos_para_dibujar]
        distrito_filtrado = distritos_poly[distritos_poly[COLUMNA_DIST_GEOJSON].fillna('').str.upper().str.strip().isin(distrito_sel_upper)]
        if not distrito_filtrado.empty: folium.GeoJson(distrito_filtrado, name="Distritos", style_function=lambda x: {'fillColor': '#2ca02c', 'color': '#2ca02c', 'weight': 2, 'fillOpacity': 0.25}).add_to(mapa)

    # --- LEYENDA DINÁMICA ---
    leyenda_items = ""
    if cuencas_para_dibujar:
        leyenda_items += '&nbsp;<i style="background:#0068c9; width: 12px; height: 12px; float: left; margin-top: 4px; margin-right: 8px; opacity: 0.4; border: 1px solid #0068c9;"></i> Cuencas<br>'
    if prov_para_dibujar:
        leyenda_items += '&nbsp;<i style="background:#ff7f0e; width: 12px; height: 12px; float: left; margin-top: 4px; margin-right: 8px; opacity: 0.4; border: 1px solid #ff7f0e;"></i> Provincias<br>'
    if distritos_para_dibujar:
        leyenda_items += '&nbsp;<i style="background:#2ca02c; width: 12px; height: 12px; float: left; margin-top: 4px; margin-right: 8px; opacity: 0.4; border: 1px solid #2ca02c;"></i> Distritos<br>'
    
    if filtros_activos:
        if leyenda_items != "": leyenda_items += '<hr style="margin: 5px 0px;">'
        leyenda_items += '<div style="margin-bottom: 3px;"><b>Puntos de Monitoreo:</b></div>'
        leyenda_items += '&nbsp;<i style="background:#ff7f0e; border-radius: 50%; width: 10px; height: 10px; float: left; margin-top: 4px; margin-right: 8px;"></i> OEFA<br>'
        leyenda_items += '&nbsp;<i style="background:#2ca02c; border-radius: 50%; width: 10px; height: 10px; float: left; margin-top: 4px; margin-right: 8px;"></i> INAIGEM<br>'
        leyenda_items += '&nbsp;<i style="background:#0068c9; border-radius: 50%; width: 10px; height: 10px; float: left; margin-top: 4px; margin-right: 8px;"></i> Otras Entidades<br>'

    # Solo agregamos la leyenda al mapa si hay algo que mostrar en ella
    if leyenda_items != "":
        template = f"""
        {{% macro html(this, kwargs) %}}
        <div style="position: fixed; bottom: 30px; left: 30px; width: auto; min-width: 150px; height: auto; 
                    border:2px solid grey; z-index:9999; font-size:13px;
                    background-color:white; opacity: 0.9; padding: 10px; border-radius: 5px;">
        <h4 style="margin-top: 0px; margin-bottom: 5px; font-size: 14px;"><b>Leyenda</b></h4>
        {leyenda_items}
        </div>
        {{% endmacro %}}
        """
        macro = MacroElement()
        macro._template = Template(template)
        mapa.get_root().add_child(macro)

    # Puntos
    capa_puntos = folium.FeatureGroup(name="Puntos de Monitoreo")
    if filtros_activos:
        limite_puntos = df_filt.head(4000)
        for idx, row in limite_puntos.iterrows():
            if pd.notna(row.get('Y')) and pd.notna(row.get('X')):
                html_popup = f"<b>{row.get('Tipo_Dataset', '')}</b><br>Active el Panel Derecho y haga clic para detalles."
                color_punto = "#ff7f0e" if "OEFA" in str(row.get('Entidad')) else "#2ca02c" if "INAIGEM" in str(row.get('Entidad')) else "#0068c9"
                
                folium.CircleMarker(
                    location=[row['Y'], row['X']], radius=5,
                    popup=folium.Popup(html_popup, max_width=250),
                    color=color_punto, fill=True, fillOpacity=0.8
                ).add_to(capa_puntos)
        capa_puntos.add_to(mapa)

    folium.LayerControl(position='topright', collapsed=False).add_to(mapa)

    if len(df_filt) > 4000 and filtros_activos:
        st.warning("⚠️ Mostrando solo 4,000 puntos. Usa los filtros para mayor precisión.")

    mapa_interactivo = st_folium(mapa, use_container_width=True, height=800, returned_objects=["last_object_clicked"])

# --- PANEL DERECHO CONDICIONAL ---
if col_panel is not None:
    with col_panel:
        st.markdown("### Panel de Resumen")
        
        if filtros_activos:
            st.info(f" **{len(df_filt)}** registros encontrados en tu búsqueda.")
            
            df_export = df_filt.dropna(axis=1, how='all')
            csv = df_export.to_csv(index=False).encode('utf-8-sig')
            
            st.download_button(
                label="Descargar Base Filtrada (CSV)",
                data=csv,
                file_name='datos_visor_filtrados.csv',
                mime='text/csv',
                use_container_width=True
            )
            
            st.markdown("---")
            st.markdown("### Detalle del Punto")
            
            if mapa_interactivo and mapa_interactivo.get("last_object_clicked"):
                lat_clic = mapa_interactivo["last_object_clicked"]["lat"]
                lon_clic = mapa_interactivo["last_object_clicked"]["lng"]
                
                df_temp = df_filt.copy()
                df_temp['distancia_al_clic'] = (df_temp['Y'] - lat_clic)**2 + (df_temp['X'] - lon_clic)**2
                punto_mas_cercano_idx = df_temp['distancia_al_clic'].idxmin()
                distancia_min = df_temp.loc[punto_mas_cercano_idx, 'distancia_al_clic']
                
                if distancia_min < 0.05:
                    punto = df_temp.loc[punto_mas_cercano_idx]
                    
                    st.write(f"**Tipo:** {punto.get('Tipo_Dataset', '-')}")
                    st.write(f"**Entidad:** {punto.get('Entidad', '-')}")
                    st.write(f"**Cuenca:** {punto.get('Cuenca', '-')}")
                    st.write(f"**Provincia:** {punto.get('Provincia', '-')}")
                    st.write(f"**Distrito:** {punto.get('Distrito', '-')}")
                    
                    with st.expander("➕ Ver Más Información Específica"):
                        campos_excluidos = ['Tipo_Dataset', 'Entidad', 'Cuenca', 'Provincia', 'Distrito', 'X', 'Y', 'distancia_al_clic']
                        
                        for columna in punto.index:
                            if columna not in campos_excluidos:
                                valor = punto[columna]
                                if pd.notna(valor) and str(valor).strip() != "":
                                    st.write(f"**{columna}:** {valor}")
                else:
                    st.write("Haz clic sobre un círculo en el mapa para cargar su información.")
            else:
                st.write("Selecciona filtros y haz clic en un punto del mapa para inspeccionarlo.")
        else:
            st.write("Activa algún filtro a la izquierda para comenzar.")