import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Carga y limpieza
df = pd.read_csv('qualifying_results_F1.csv')

def time_to_seconds(time_str):
    if time_str in ['0', None, "", 0, "0"]: return None
    try:
        if ':' in str(time_str):
            parts = str(time_str).split(':')
            return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)
    except: return None

for col in ['Q1', 'Q2', 'Q3']:
    df[col + '_sec'] = df[col].apply(time_to_seconds)

df['Best_Time'] = df['Q3_sec'].fillna(df['Q2_sec']).fillna(df['Q1_sec'])

team_colors = {
    'Ferrari': '#EF1A2D', 'Mercedes': '#00D2BE', 'Red Bull': '#0600EF',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'Williams': '#005AFF', 'Haas': '#FFFFFF', 'RB F1 Team': '#6692FF'
}

app = dash.Dash(__name__, title="F1 Pro Analytics")
server = app.server

app.layout = html.Div(style={
    'backgroundColor': '#0b0b0b', 'minHeight': '100vh', 'color': 'white', 
    'padding': '20px', 'fontFamily': 'Arial'
}, children=[
    
    html.Div([
        html.H1("🏎️ F1 PERFORMANCE HUB", style={'color': '#FF1801', 'textAlign': 'center', 'margin': '0', 'letterSpacing': '3px'}),
        html.P("Análisis de Sesiones y Evolución de Tiempos", style={'textAlign': 'center', 'color': '#888'})
    ], style={'marginBottom': '30px'}),

    # Panel de Filtros Conectados
    html.Div([
        html.Div([
            html.Label("📅 Temporada"),
            dcc.Dropdown(
                id='season-filter',
                options=[{'label': str(i), 'value': i} for i in sorted(df['Season'].unique(), reverse=True)],
                value=2024, clearable=False, style={'color': 'black'}
            ),
        ], style={'width': '20%', 'display': 'inline-block', 'marginRight': '2%'}),
        
        html.Div([
            html.Label("🏁 Circuito"),
            dcc.Dropdown(id='circuit-filter', clearable=False, style={'color': 'black'}),
        ], style={'width': '35%', 'display': 'inline-block', 'marginRight': '2%'}),

        html.Div([
            html.Label("👤 Pilotos Disponibles"),
            dcc.Dropdown(id='driver-filter', multi=True, placeholder="Filtrar por piloto...", style={'color': 'black'}),
        ], style={'width': '38%', 'display': 'inline-block'}),
    ], style={'backgroundColor': '#161616', 'padding': '20px', 'borderRadius': '12px', 'borderLeft': '5px solid #FF1801'}),

    html.Div(id='kpi-container', style={'display': 'flex', 'gap': '15px', 'margin': '20px 0'}),

    # Zona de Gráficas
    html.Div([
        html.Div([
            html.H4("Comparativa de Tiempos Finales", style={'textAlign': 'center', 'color': '#aaa'}),
            dcc.Graph(id='main-graph')
        ], style={'width': '49%', 'backgroundColor': '#161616', 'borderRadius': '12px', 'padding': '10px'}),
        
        html.Div([
            html.H4("Evolución de Clasificación (Q1 → Q3)", style={'textAlign': 'center', 'color': '#aaa'}),
            dcc.Graph(id='evolution-graph')
        ], style={'width': '49%', 'backgroundColor': '#161616', 'borderRadius': '12px', 'padding': '10px'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '20px'}),

    # Tabla Final
    html.Div([
        html.H3("⏱️ Detalle de Sesiones", style={'color': '#FF1801'}),
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
            style_header={'backgroundColor': '#222', 'color': 'white', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#161616', 'color': '#ccc', 'textAlign': 'center', 'padding': '8px'},
            page_size=10
        )
    ])
])

# CALLBACKS PARA FILTROS CONECTADOS
@app.callback(
    [Output('circuit-filter', 'options'), Output('circuit-filter', 'value')],
    Input('season-filter', 'value')
)
def update_circuits(season):
    circs = sorted(df[df['Season'] == season]['CircuitID'].unique())
    options = [{'label': c.replace('_', ' ').title(), 'value': c} for c in circs]
    return options, circs[0]

@app.callback(
    [Output('driver-filter', 'options'), Output('driver-filter', 'value')],
    [Input('season-filter', 'value'), Input('circuit-filter', 'value')]
)
def update_drivers(season, circuit):
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)]
    drivers = sorted(dff['FamilyName'].unique())
    options = [{'label': d, 'value': d} for d in drivers]
    return options, [] # Empieza vacío para mostrar todos

# CALLBACK PRINCIPAL
@app.callback(
    [Output('main-graph', 'figure'),
     Output('evolution-graph', 'figure'),
     Output('results-table', 'data'),
     Output('kpi-container', 'children')],
    [Input('season-filter', 'value'),
     Input('circuit-filter', 'value'),
     Input('driver-filter', 'value')]
)
def update_viz(season, circuit, selected_drivers):
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)].sort_values('Position')
    dff_filtered = dff[dff['FamilyName'].isin(selected_drivers)] if selected_drivers else dff

    # 1. Gráfico de Barras
    fig_bar = px.bar(dff_filtered, x='FamilyName', y='Best_Time', color='ConstructorName',
                    color_discrete_map=team_colors, template='plotly_dark')
    fig_bar.update_yaxes(range=[dff['Best_Time'].min()*0.98, dff['Best_Time'].max()*1.02])
    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 2. Gráfico de Evolución (Líneas)
    # Transformamos los datos para que sean útiles para una gráfica de líneas
    evol_data = []
    for _, row in dff_filtered.iterrows():
        for q in ['Q1_sec', 'Q2_sec', 'Q3_sec']:
            if row[q] > 0:
                evol_data.append({'Piloto': row['FamilyName'], 'Sesion': q.split('_')[0], 'Tiempo': row[q]})
    
    df_evol = pd.DataFrame(evol_data)
    fig_line = px.line(df_evol, x='Sesion', y='Tiempo', color='Piloto', markers=True, 
                      template='plotly_dark', title="Progresión por Sesión")
    fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 3. KPIs
    pole = dff.iloc[0]
    kpis = [
        html.Div([html.Small("POLE POSITION"), html.H2(pole['FamilyName'])], 
                 style={'flex': '1', 'backgroundColor': '#FF1801', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center'}),
        html.Div([html.Small("TIEMPO"), html.H2(f"{pole['Best_Time']:.3f}s")], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center'}),
        html.Div([html.Small("DIFERENCIA P1-ÚLTIMO"), html.H2(f"{dff['Best_Time'].max() - pole['Best_Time']:.2f}s")], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center'})
    ]

    return fig_bar, fig_line, dff.to_dict('records'), kpis

if __name__ == '__main__':
    app.run_server(debug=True)