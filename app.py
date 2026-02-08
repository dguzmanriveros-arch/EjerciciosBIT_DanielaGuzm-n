import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Carga de datos
df = pd.read_csv('qualifying_results_F1.csv')

def time_to_seconds(time_str):
    if time_str in ['0', None, "", 0]: return None
    try:
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)
    except: return None

for col in ['Q1', 'Q2', 'Q3']:
    df[col + '_sec'] = df[col].apply(time_to_seconds)

df['Best_Time'] = df['Q3_sec'].fillna(df['Q2_sec']).fillna(df['Q1_sec'])

# Colores de Escuderías
team_colors = {
    'Ferrari': '#EF1A2D', 'Mercedes': '#00D2BE', 'Red Bull': '#0600EF',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'Williams': '#005AFF', 'Haas': '#FFFFFF', 'RB F1 Team': '#6692FF'
}

app = dash.Dash(__name__, title="F1 Analytics")
server = app.server

# Diseño con CSS embebido para evitar el color blanco al cargar
app.layout = html.Div(style={
    'backgroundColor': '#0b0b0b', 'minHeight': '100vh', 'color': 'white', 
    'padding': '20px', 'fontFamily': 'sans-serif'
}, children=[
    
    # Encabezado
    html.Div([
        html.H1("🏎️ F1 PERFORMANCE ANALYTICS", style={'color': '#FF1801', 'textAlign': 'center', 'margin': '0', 'fontSize': '35px'}),
        html.P("2000 - 2024 Qualifying Data Analysis", style={'textAlign': 'center', 'color': '#666', 'marginTop': '5px'})
    ], style={'paddingBottom': '20px'}),

    # Panel de Control
    html.Div([
        html.Div([
            html.Label("📅 Temporada", style={'display': 'block', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='season-filter',
                options=[{'label': str(i), 'value': i} for i in sorted(df['Season'].unique(), reverse=True)],
                value=2024, clearable=False, style={'color': 'black'}
            ),
        ], style={'width': '20%', 'display': 'inline-block', 'marginRight': '2%'}),
        
        html.Div([
            html.Label("🏁 Selecciona el Circuito", style={'display': 'block', 'marginBottom': '5px', 'color': '#FF1801', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='circuit-filter',
                placeholder="⚠️ Elige un circuito para ver los datos...",
                clearable=False, style={'color': 'black'}
            ),
        ], style={'width': '40%', 'display': 'inline-block', 'marginRight': '2%'}),

        html.Div([
            html.Label("👤 Comparar Pilotos (Opcional)", style={'display': 'block', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='driver-filter',
                options=[{'label': n, 'value': n} for n in sorted(df['FamilyName'].unique())],
                multi=True, placeholder="Todos los pilotos", style={'color': 'black'}
            ),
        ], style={'width': '34%', 'display': 'inline-block'}),
    ], style={'backgroundColor': '#161616', 'padding': '20px', 'borderRadius': '12px', 'border': '1px solid #333'}),

    # Mensaje de Advertencia si no hay selección
    html.Div(id='warning-message', style={'marginTop': '20px'}),

    # Contenedor de Gráficos
    html.Div(id='main-content', children=[
        html.Div(id='kpi-container', style={'display': 'flex', 'gap': '15px', 'margin': '20px 0'}),
        
        html.Div([
            html.Div([
                dcc.Graph(id='main-graph')
            ], style={'width': '68%', 'display': 'inline-block', 'backgroundColor': '#161616', 'borderRadius': '12px'}),
            
            html.Div([
                dcc.Graph(id='history-graph')
            ], style={'width': '30%', 'display': 'inline-block', 'float': 'right', 'backgroundColor': '#161616', 'borderRadius': '12px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between'})
    ]),

    # Tabla de Resultados
    html.Div([
        html.H3("⏱️ Tabla de Tiempos Oficiales", style={'color': '#FF1801', 'marginTop': '30px'}),
        dash_table.DataTable(
            id='results-table',
            columns=[
                {"name": "Pos", "id": "Position"},
                {"name": "Piloto", "id": "FamilyName"},
                {"name": "Escudería", "id": "ConstructorName"},
                {"name": "Mejor Tiempo (s)", "id": "Best_Time"}
            ],
            style_header={'backgroundColor': '#222', 'color': 'white', 'fontWeight': 'bold', 'border': '1px solid #444'},
            style_cell={'backgroundColor': '#161616', 'color': '#ccc', 'textAlign': 'center', 'border': '1px solid #333', 'padding': '8px'},
            page_size=10
        )
    ])
])

# Callbacks
@app.callback(
    [Output('circuit-filter', 'options'), Output('circuit-filter', 'value')],
    Input('season-filter', 'value')
)
def update_circuit_list(season):
    circs = sorted(df[df['Season'] == season]['CircuitID'].unique())
    options = [{'label': c.replace('_', ' ').title(), 'value': c} for c in circs]
    # Intentamos poner Monaco por defecto, si no, el primero de la lista
    default_val = 'monaco' if 'monaco' in circs else circs[0]
    return options, default_val

@app.callback(
    [Output('main-graph', 'figure'),
     Output('history-graph', 'figure'),
     Output('results-table', 'data'),
     Output('kpi-container', 'children'),
     Output('warning-message', 'children')],
    [Input('season-filter', 'value'),
     Input('circuit-filter', 'value'),
     Input('driver-filter', 'value')]
)
def refresh_dashboard(season, circuit, drivers):
    if not circuit:
        msg = html.Div("📍 Por favor, selecciona un circuito en el menú superior para desplegar las estadísticas.", 
                      style={'padding': '20px', 'backgroundColor': '#FF1801', 'borderRadius': '10px', 'textAlign': 'center', 'fontWeight': 'bold'})
        return go.Figure(), go.Figure(), [], [], msg

    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)].sort_values('Position')
    
    # Filtro de pilotos
    dff_plot = dff[dff['FamilyName'].isin(drivers)] if drivers else dff

    # Gráfico 1: Tiempos
    fig1 = px.bar(dff_plot, x='FamilyName', y='Best_Time', color='ConstructorName',
                 color_discrete_map=team_colors, template='plotly_dark', title="Comparativa de Tiempos (s)")
    fig1.update_yaxes(range=[dff['Best_Time'].min()*0.98, dff['Best_Time'].max()*1.02])
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # Gráfico 2: Histórico Poles
    hist_data = df[df['Position'] == 1]['FamilyName'].value_counts().head(10).reset_index()
    hist_data.columns = ['Piloto', 'Poles']
    fig2 = px.bar(hist_data, y='Piloto', x='Poles', orientation='h', title="Top 10 Polemen Histórico",
                 color='Poles', color_continuous_scale='Reds', template='plotly_dark')
    fig2.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # KPIs
    pole = dff.iloc[0]
    kpis = [
        html.Div([html.Small("POLE POSITION"), html.H2(pole['FamilyName'], style={'margin': '0'})], 
                 style={'flex': '1', 'backgroundColor': '#FF1801', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center'}),
        html.Div([html.Small("ESCUDERÍA"), html.H2(pole['ConstructorName'], style={'margin': '0'})], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center', 'border': '1px solid #444'}),
        html.Div([html.Small("DIFERENCIA P1-P2"), html.H2(f"{dff.iloc[1]['Best_Time'] - pole['Best_Time']:.3f}s", style={'margin': '0'})], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center', 'border': '1px solid #444'})
    ]

    return fig1, fig2, dff.to_dict('records'), kpis, None

if __name__ == '__main__':
    app.run_server(debug=True)