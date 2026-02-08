import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Cargar y preparar datos
df = pd.read_csv('qualifying_results_F1.csv')

def time_to_seconds(time_str):
    if time_str in ['0', None, "", 0]: return None
    try:
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)
    except: return None

df['Q3_sec'] = df['Q3'].apply(time_to_seconds)
df['Q2_sec'] = df['Q2'].apply(time_to_seconds)
df['Q1_sec'] = df['Q1'].apply(time_to_seconds)

# Mapa de colores para que se vea profesional
team_colors = {
    'Ferrari': '#EF1A2D', 'Mercedes': '#00D2BE', 'Red Bull': '#0600EF',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'Williams': '#005AFF', 'RB F1 Team': '#6692FF', 'Haas': '#FFFFFF'
}

app = dash.Dash(__name__)
server = app.server

# Diseño con Estilo Dark Integrado
app.layout = html.Div(style={
    'backgroundColor': '#111', 'minHeight': '100vh', 'color': 'white', 
    'padding': '20px', 'fontFamily': '"Segoe UI", Roboto, Helvetica, Arial, sans-serif'
}, children=[
    
    html.Div([
        html.H1("🏁 F1 PERFORMANCE ANALYTICS", style={'textAlign': 'center', 'color': '#FF1801', 'letterSpacing': '2px'}),
        html.P("Análisis interactivo de tiempos de clasificación", style={'textAlign': 'center', 'color': '#888'})
    ], style={'marginBottom': '40px'}),

    # Contenedor de Filtros
    html.Div([
        html.Div([
            html.Label("Temporada", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
            dcc.Dropdown(
                id='season-filter',
                options=[{'label': str(i), 'value': i} for i in sorted(df['Season'].unique(), reverse=True)],
                value=2024, # Valor por defecto
                clearable=False,
                style={'color': 'black'}
            ),
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '5%'}),
        
        html.Div([
            html.Label("Circuito / Gran Premio", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
            dcc.Dropdown(
                id='circuit-filter',
                value='monaco', # Valor por defecto para que no inicie vacío
                clearable=False,
                style={'color': 'black'}
            ),
        ], style={'width': '60%', 'display': 'inline-block'}),
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e', 'borderRadius': '10px', 'marginBottom': '30px'}),

    # KPIs
    html.Div(id='kpi-container', style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'}),

    # Gráfico
    html.Div([
        dcc.Loading(
            type="circle",
            children=dcc.Graph(id='main-graph', style={'height': '500px'})
        )
    ], style={'backgroundColor': '#1e1e1e', 'padding': '20px', 'borderRadius': '10px'}),

    # Tabla
    html.Div([
        html.H3("⏱️ Resultados Detallados", style={'marginTop': '40px', 'color': '#FF1801'}),
        dash_table.DataTable(
            id='results-table',
            columns=[
                {"name": "Pos", "id": "Position"},
                {"name": "Piloto", "id": "FamilyName"},
                {"name": "Escudería", "id": "ConstructorName"},
                {"name": "Q1 (s)", "id": "Q1_sec"},
                {"name": "Q2 (s)", "id": "Q2_sec"},
                {"name": "Q3 (s)", "id": "Q3_sec"}
            ],
            style_header={'backgroundColor': '#333', 'color': 'white', 'fontWeight': 'bold', 'border': '1px solid #444'},
            style_cell={'backgroundColor': '#1e1e1e', 'color': '#ddd', 'textAlign': 'center', 'border': '1px solid #333', 'padding': '10px'},
            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#252525'}],
            page_size=10
        )
    ])
])

# Callbacks
@app.callback(
    Output('circuit-filter', 'options'),
    Input('season-filter', 'value')
)
def update_circuits(season):
    circuits = df[df['Season'] == season]['CircuitID'].unique()
    return [{'label': i.replace('_', ' ').title(), 'value': i} for i in circuits]

@app.callback(
    [Output('main-graph', 'figure'),
     Output('results-table', 'data'),
     Output('kpi-container', 'children')],
    [Input('season-filter', 'value'),
     Input('circuit-filter', 'value')]
)
def update_content(season, circuit):
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)].sort_values('Position')
    
    if dff.empty:
        return go.Figure(), [], []

    # Gráfico de Tiempos
    # Usamos Q3 si existe, si no Q1 (para los que no llegaron a Q3)
    dff['Best_Time'] = dff['Q3_sec'].fillna(dff['Q2_sec']).fillna(dff['Q1_sec'])
    
    fig = px.bar(
        dff, x='FamilyName', y='Best_Time',
        color='ConstructorName',
        color_discrete_map=team_colors,
        text_auto='.3f',
        title=f"Mejor Tiempo en Clasificación: GP {circuit.title()} {season}",
        template='plotly_dark'
    )
    
    # Zoom en el eje Y para ver diferencias
    margin = dff['Best_Time'].min() * 0.02
    fig.update_yaxes(range=[dff['Best_Time'].min() - margin, dff['Best_Time'].max() + margin], title="Segundos")
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')

    # KPIs
    pole_row = dff.iloc[0]
    kpis = [
        html.Div([html.Small("POLE POSITION"), html.H3(pole_row['FamilyName'], style={'color': '#FF1801'})], 
                 style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#1e1e1e', 'borderRadius': '10px', 'width': '25%'}),
        html.Div([html.Small("ESCUDERÍA"), html.H3(pole_row['ConstructorName'])], 
                 style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#1e1e1e', 'borderRadius': '10px', 'width': '25%'}),
        html.Div([html.Small("TIEMPO POLE"), html.H3(f"{pole_row['Best_Time']:.3f}s")], 
                 style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#1e1e1e', 'borderRadius': '10px', 'width': '25%'})
    ]

    return fig, dff.to_dict('records'), kpis

if __name__ == '__main__':
    app.run_server(debug=True)