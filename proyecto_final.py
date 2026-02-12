import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import random
import requests  # <-- Agregado para el nuevo buscador
import plotly.graph_objects as go
from geopy.distance import geodesic

# 1. CONFIGURACIÓN Y ESTILO CSS
st.set_page_config(layout="wide", page_title="RedBank Strategy Dashboard")

st.markdown("""
    <style>
    /* Fondo y Textos Generales */
    .stApp { background-color: #000b1a; color: #ffffff; }
    h1, h2, h3, h4, h5, h6, span, label, p, div { color: #e6f7ff !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Tarjetas (Métricas) */
    div[data-testid="stMetric"] {
        background-color: #001529;
        border: 1px solid #1e3a8a;
        padding: 15px;
        border-radius: 10px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    div[data-testid="stMetricLabel"] p { font-size: 14px !important; color: #94a3b8 !important; }
    div[data-testid="stMetricValue"] div { font-size: 24px !important; color: #38bdf8 !important; word-wrap: break-word; }
    
    /* Inputs y Sidebar */
    div[data-baseweb="select"] > div { background-color: #002140 !important; border: 1px solid #0050b3 !important; }
    div[data-baseweb="input"] > div { background-color: #002140 !important; color: white !important; }
    input { color: white !important; }
    section[data-testid="stSidebar"] { background-color: #001529 !important; border-right: 1px solid #002140; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE BÚSQUEDA PROFESIONAL (MAPBOX) ---
def buscar_direccion_mapbox(query, token):
    # Limpiamos símbolos para el GPS
    query_limpia = query.replace("#", "").replace("-", "")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query_limpia}.json"
    params = {"access_token": token, "country": "co", "limit": 1}
    try:
        r = requests.get(url, params=params)
        datos = r.json()
        if datos['features']:
            lon, lat = datos['features'][0]['center']
            return lat, lon
    except:
        return None
    return None

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos_final():
    try:
        df = pd.read_csv("tus_puntos.csv") 
        df.columns = df.columns.str.strip()
    except:
        return pd.DataFrame(columns=['Nombre', 'Lat', 'Lng', 'Departamento', 'Ciudad'])

    for col in ['Lat', 'Lng']:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '.').astype(float)
            
    cantidad = len(df)
    deptos_ciudades = {
        "Antioquia": ["Medellín", "Envigado"],
        "Cundinamarca": ["Bogotá", "Chía"],
        "Valle del Cauca": ["Cali", "Palmira"]
    }
    
    lista_deptos, lista_ciudades = [], []
    for _ in range(cantidad):
        depto = random.choice(list(deptos_ciudades.keys()))
        lista_deptos.append(depto)
        lista_ciudades.append(random.choice(deptos_ciudades[depto]))
        
    df['Departamento'] = lista_deptos
    df['Ciudad'] = lista_ciudades
    df['Direccion'] = [f"Carrera {random.randint(1,100)} # {random.randint(1,100)}" for _ in range(cantidad)]
    df['Transacciones'] = np.random.randint(500, 3000, size=cantidad)
    df['Recaudo_Actual'] = df['Transacciones'] * np.random.randint(40000, 60000, size=cantidad)

    for i in range(1, 5):
        df[f'Semana_{i}'] = ((df['Recaudo_Actual'] / 4) * np.random.uniform(0.9, 1.1, size=cantidad)).astype(int)

    df['Proyeccion_Mes'] = df['Semana_1'] + df['Semana_2'] + df['Semana_3'] + df['Semana_4']
    df['Score_Confianza'] = np.random.uniform(0.85, 0.99, size=cantidad)

    return df

df_master = cargar_datos_final()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank.png", width=70)
    st.title("RedBank Analytics")
    dir_cliente = st.text_input("📍 Dirección:", "Carrera 28 61-40")
    st.caption("💡 Sugerencia: Usa formato 'Carrera 28 61-40'")
    radio_km = st.slider("Radio (KM):", 1, 15, 5)
    st.divider()
    if not df_master.empty:
        depto_sel = st.multiselect("Filtro Depto:", df_master['Departamento'].unique(), default=df_master['Departamento'].unique())
        ciudad_sel = st.multiselect("Filtro Ciudad:", df_master['Ciudad'].unique(), default=df_master['Ciudad'].unique())
    else:
        depto_sel, ciudad_sel = [], []

# --- LÓGICA GEO ACTUALIZADA ---
TOKEN_MB = "ssss"
location_coords = buscar_direccion_mapbox(dir_cliente, TOKEN_MB)

if location_coords:
    u_lat, u_lon = location_coords
    exito = True
else:
    u_lat, u_lon = 4.6767, -74.0483
    exito = False

# Vista dinámica que mueve el mapa
view_state_movil = pdk.ViewState(latitude=u_lat, longitude=u_lon, zoom=13.5, pitch=45)

if not df_master.empty:
    df_master['Distancia_KM'] = df_master.apply(lambda r: round(geodesic((u_lat, u_lon), (r['Lat'], r['Lng'])).km, 2), axis=1)
    puntos_top = df_master[df_master['Distancia_KM'] <= radio_km].nsmallest(15, 'Distancia_KM')
else:
    puntos_top = pd.DataFrame()

# --- DASHBOARD ---
st.header("🏢 Centro de Inteligencia Territorial")
if not exito: st.warning("⚠️ Dirección no encontrada. Mostrando ubicación por defecto.")

# 1. TARJETAS
m1, m2, m3, m4 = st.columns(4)
if not df_master.empty:
    total_recaudo = df_master['Recaudo_Actual'].sum()
    str_recaudo = f"${total_recaudo/1_000_000_000:.2f} B" if total_recaudo > 1_000_000_000 else f"${total_recaudo/1_000_000:.1f} M"
    m1.metric("Recaudo Global", str_recaudo)
    
    total_tx = df_master['Transacciones'].sum()
    str_tx = f"{total_tx/1_000:.1f} K" if total_tx > 1000 else f"{total_tx}"
    m2.metric("Total Transacciones", str_tx)
    m3.metric("Eficiencia", "94.2%", "+2.1%")
    
    nombre_sede = puntos_top.iloc[0]['Nombre'] if not puntos_top.empty else "N/A"
    m4.metric("Sede Cercana", (nombre_sede[:15] + '..') if len(nombre_sede) > 15 else nombre_sede)

st.divider()

# 2. MAPA Y TABLA
c1, c2 = st.columns([2, 1])
with c1:
    icon_bank = {"url": "https://img.icons8.com/color/96/money-box.png", "width": 128, "height": 128, "anchorY": 128}
    icon_user = {"url": "https://img.icons8.com/color/96/marker.png", "width": 128, "height": 128, "anchorY": 128}
    
    layers = [pdk.Layer("IconLayer", pd.DataFrame({'lat': [u_lat], 'lon': [u_lon], 'icon_data': [icon_user]}), get_icon="icon_data", get_size=50, get_position="[lon, lat]")]
    if not puntos_top.empty:
        puntos_top = puntos_top.copy()
        puntos_top['icon_data'] = [icon_bank] * len(puntos_top)
        layers.append(pdk.Layer("IconLayer", puntos_top, get_icon="icon_data", get_size=42, get_position="[Lng, Lat]", pickable=True))

    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/dark-v10",
        initial_view_state=view_state_movil, # <--- Ahora usa la vista móvil
        layers=layers,
        tooltip={"html": "<b>{Nombre}</b><br/>{Distancia_KM} km"},
        api_keys={"mapbox": TOKEN_MB} 
    ))

with c2:
    st.subheader("Sedes en Radio")
    if not puntos_top.empty:
        st.dataframe(puntos_top[['Nombre', 'Distancia_KM']], hide_index=True, use_container_width=True)

# 3. GRÁFICA
st.divider()
st.subheader("📈 Tendencias y Proyecciones")

meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
recaudo_real = [480, 510, 540, None, None, None]
recaudo_proy = [None, None, None, 530, 610, 680]
operaciones = [1250, 1300, 1420, 1390, 1650, 1900]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=meses, y=recaudo_real, name='Recaudo Real',
    marker_color='#2563eb', text=recaudo_real, textposition='auto',
    textfont=dict(color='white', size=14, family="Arial Black")
))

fig.add_trace(go.Bar(
    x=meses, y=recaudo_proy, name='Proyección',
    marker_color='#9333ea', text=recaudo_proy, textposition='auto',
    textfont=dict(color='white', size=14, family="Arial Black")
))

fig.add_trace(go.Scatter(
    x=meses, y=operaciones, name='Vol. Operaciones', yaxis='y2',
    line=dict(color='#06b6d4', width=4), mode='lines+markers'
))

fig.update_layout(
    template="plotly_dark", 
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="white", family="Segoe UI"), 
    barmode='overlay',
    yaxis=dict(title="Recaudo (M$)", gridcolor='#1f2937', title_font=dict(color="white")),
    yaxis2=dict(title="Operaciones", overlaying='y', side='right', showgrid=False, title_font=dict(color="white")),
    legend=dict(
        orientation="h", 
        y=1.1, 
        x=0.5, 
        xanchor="center",
        font=dict(color="white", size=12)
    )
)
st.plotly_chart(fig, use_container_width=True)

# 4. TABLA PREDICTIVA
st.divider()
st.header("🤖 Proyección Predictiva")
if not df_master.empty:
    df_proy = df_master[(df_master['Departamento'].isin(depto_sel)) & (df_master['Ciudad'].isin(ciudad_sel))].copy()
    max_val = int(df_proy['Proyeccion_Mes'].max()) if not df_proy.empty else 100
    
    st.dataframe(
        df_proy[['Nombre', 'Ciudad', 'Semana_1', 'Semana_2', 'Semana_3', 'Semana_4', 'Proyeccion_Mes', 'Score_Confianza']],
        use_container_width=True, hide_index=True,
        column_config={
            "Proyeccion_Mes": st.column_config.ProgressColumn("Total Mes", format="$%f", min_value=0, max_value=max_val),
            "Score_Confianza": st.column_config.NumberColumn("Confianza", format="%.2f %%")
        }
    )
    st.download_button("📥 Descargar CSV", data=df_proy.to_csv(index=False).encode('utf-8'), file_name='predicciones.csv', mime='text/csv', type="primary")