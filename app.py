import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Cargar y preparar datos
df = pd.read_csv('qualifying_results_F1.csv')

def time_to_seconds(time_str):
    if time_str == '0' or pd.isna(time_str) or time_str == "" or time_str == 0:
        return None
    try:
        if ':' in str(time_str):
            minutes, seconds = str(time_str).split(':')
            return int(minutes) * 60 + float(seconds)
        return float(time_str)
    except:
        return None

# Limpieza de datos
df['Q3_sec'] = df['Q3'].apply(time_to_seconds)
df['Q2_sec'] = df['Q2'].apply(time_to_seconds)
df['Q1_sec'] = df['Q1'].apply(time_to_seconds)

# Diccionario de colores por escudería (puedes ampliarlo)
team_colors = {
    'Ferrari': '#EF1A2D', 'Mercedes': '#00D2BE', 'Red Bull': '#0600EF',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'Williams': '#005AFF', 'AlphaTauri': '#2B4562', 'Haas': '#FFFFFF',
    'Alfa Romeo': '#900000', 'RB F1 Team': '#6692FF', 'Sauber': '#52E252'
}

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={'backgroundColor': '#111', 'color': 'white', 'padding': '20px', 'fontFamily': 'Arial'}, children=[
    html.H1("🏎️ F1 ESTRATEGIA Y VELOCIDAD", style={'textAlign': 'center', 'color': '#FF1801', 'fontSize': '40px'}),
    html.Hr(style={'borderColor': '#444'}),

    # Filtros
    html.Div([
        html.Div([
            html.Label("Temporada:"),
            dcc.Dropdown(
                id='season-filter',
                options=[{'label': i, 'value': i} for i in sorted(df['Season'].unique(), reverse=True)],
                value=2024, style={'color': 'black'}
            ),
        ], style={'width': '45%', 'display': 'inline-block', 'marginRight': '5%'}),
        
        html.Div([
            html.Label("Circuito:"),
            dcc.Dropdown(id='circuit-filter', style={'color': 'black'}),
        ], style={'width': '45%', 'display': 'inline-block'}),
    ], style={'marginBottom': '30px'}),

    # KPIs / Resumen
    html.Div(id='kpi-container', style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'}),

    # Gráfico Principal
    html.Div([
        dcc.Graph(id='main-graph'),
    ], style={'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '10px'}),

    # Tabla de Posiciones
    html.Div([
        html.H3("Top 10 Clasificación Final", style={'marginTop': '30px'}),
        dash_table.DataTable(
            id='results-table',
            columns=[
                {"name": "Pos", "id": "Position"},
                {"name": "Piloto", "id": "FamilyName"},
                {"name": "Escudería", "id": "ConstructorName"},
                {"name": "Q3 (s)", "id": "Q3_sec"}
            ],
            style_header={'backgroundColor': '#333', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#222', 'color': 'white', 'textAlign': 'left'},
            page_size=10
        )
    ])
])

# Callback para actualizar circuitos
@app.callback(
    Output('circuit-filter', 'options'),
    Input('season-filter', 'value')
)
def set_circuit_options(selected_season):
    dff = df[df['Season'] == selected_season]
    return [{'label': i, 'value': i} for i in dff['CircuitID'].unique()]

@app.callback(
    [Output('main-graph', 'figure'),
     Output('results-table', 'data'),
     Output('kpi-container', 'children')],
    [Input('season-filter', 'value'),
     Input('circuit-filter', 'value')]
)
def update_dashboard(season, circuit):
    if not circuit:
        return go.Figure(), [], []

    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)].sort_values('Position')
    
    # 1. Gráfico de barras con colores de equipo
    fig = px.bar(
        dff, x='FamilyName', y='Q3_sec',
        color='ConstructorName',
        color_discrete_map=team_colors,
        title=f"Tiempos de Q3 - Gran Premio de {circuit}",
        template='plotly_dark'
    )
    
    # Ajustar el eje Y para que se noten las diferencias
    min_time = dff['Q3_sec'][dff['Q3_sec'] > 0].min()
    max_time = dff['Q3_sec'][dff['Q3_sec'] > 0].max()
    if min_time and max_time:
        fig.update_yaxes(range=[min_time * 0.98, max_time * 1.02])

    # 2. Datos para la tabla
    table_data = dff.to_dict('records')

    # 3. KPIs (Pole Position)
    pole_driver = dff.iloc[0]['FamilyName']
    pole_team = dff.iloc[0]['ConstructorName']
    
    kpis = [
        html.Div([html.H4("POLE POSITION"), html.P(f"{pole_driver} ({pole_team})")], 
                 style={'border': '2px solid #FF1801', 'padding': '10px', 'borderRadius': '10px', 'width': '200px', 'textAlign': 'center'}),
        html.Div([html.H4("ESTADO"), html.P("Finalizado")], 
                 style={'border': '2px solid #444', 'padding': '10px', 'borderRadius': '10px', 'width': '200px', 'textAlign': 'center'})
    ]

    return fig, table_data, kpis

if __name__ == '__main__':
    app.run_server(debug=True)