import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# 1. Cargar y limpiar datos
df = pd.read_csv('qualifying_results_F1.csv')

def time_to_seconds(time_str):
    if time_str == '0' or pd.isna(time_str) or time_str == "":
        return None
    try:
        minutes, seconds = time_str.split(':')
        return int(minutes) * 60 + float(seconds)
    except:
        return float(time_str)

# Convertir tiempos a segundos para graficar
for q in ['Q1', 'Q2', 'Q3']:
    df[q + '_sec'] = df[q].apply(time_to_seconds)

# 2. Inicializar App
app = dash.Dash(__name__)
server = app.server # Necesario para Render

# 3. Diseño (Layout)
app.layout = html.Div([
    html.H1("Análisis de Clasificación F1 (2000-2024)", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Selecciona la Temporada:"),
        dcc.Dropdown(
            id='season-filter',
            options=[{'label': i, 'value': i} for i in sorted(df['Season'].unique(), reverse=True)],
            value=2024
        ),
    ], style={'width': '48%', 'display': 'inline-block'}),

    html.Div([
        html.Label("Selecciona el Circuito:"),
        dcc.Dropdown(id='circuit-filter'),
    ], style={'width': '48%', 'display': 'inline-block'}),

    dcc.Graph(id='main-graph'),
    
    html.Div([
        html.P("Este reporte muestra los tiempos de clasificación. Los valores menores indican mayor velocidad.")
    ])
])

# 4. Callbacks para interactividad
@app.callback(
    Output('circuit-filter', 'options'),
    Input('season-filter', 'value')
)
def set_circuit_options(selected_season):
    dff = df[df['Season'] == selected_season]
    return [{'label': i, 'value': i} for i in dff['CircuitID'].unique()]

@app.callback(
    Output('main-graph', 'output'), # Corregido abajo en la lógica
    Output('main-graph', 'figure'),
    Input('season-filter', 'value'),
    Input('circuit-filter', 'value')
)
def update_graph(season, circuit):
    if not circuit:
        return px.scatter(title="Selecciona un circuito para ver datos")
    
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)]
    
    # Crear gráfico de barras comparativo
    fig = px.bar(
        dff, 
        x='FamilyName', 
        y=['Q1_sec', 'Q2_sec', 'Q3_sec'],
        barmode='group',
        title=f"Tiempos de Clasificación - {circuit} {season}",
        labels={'value': 'Segundos', 'variable': 'Sesión', 'FamilyName': 'Piloto'}
    )
    
    fig.update_layout(yaxis=dict(range=[dff['Q1_sec'].min()*0.9, dff['Q1_sec'].max()*1.1]))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)