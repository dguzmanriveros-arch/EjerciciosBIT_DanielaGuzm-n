import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Carga y limpieza de datos
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
    'Williams': '#005AFF', 'Haas': '#FFFFFF', 'RB F1 Team': '#6692FF',
    'Renault': '#FFF500', 'Red Bull': '#0600EF', 'Sauber': '#006EFF'
}

app = dash.Dash(__name__, title="F1 Grand Prix Analytics")
server = app.server

app.layout = html.Div(style={
    'backgroundColor': '#0b0b0b', 'minHeight': '150vh', 'color': 'white', 
    'padding': '20px', 'fontFamily': 'Arial, sans-serif'
}, children=[
    
    # Encabezado
    html.Div([
        html.H1("🏎️ F1 ULTIMATE ANALYTICS HUB", style={'color': '#FF1801', 'textAlign': 'center', 'margin': '0', 'letterSpacing': '3px', 'fontSize': '40px'}),
        html.P("Reporte Interactivo: Temporadas 2000 - 2024", style={'textAlign': 'center', 'color': '#888', 'fontSize': '18px'})
    ], style={'marginBottom': '40px'}),

    # Sección 1: Filtros
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
            html.Label("👤 Seleccionar Pilotos"),
            dcc.Dropdown(id='driver-filter', multi=True, placeholder="Todos los pilotos...", style={'color': 'black'}),
        ], style={'width': '38%', 'display': 'inline-block'}),
    ], style={'backgroundColor': '#161616', 'padding': '25px', 'borderRadius': '15px', 'borderLeft': '8px solid #FF1801', 'marginBottom': '30px'}),

    # Sección 2: KPIs
    html.Div(id='kpi-container', style={'display': 'flex', 'gap': '15px', 'marginBottom': '30px'}),

    # Sección 3: Gráficas de la Carrera Seleccionada
    html.Div([
        html.Div([
            html.H4("⚡ Comparativa de Velocidad Final", style={'textAlign': 'center'}),
            dcc.Graph(id='main-graph')
        ], style={'width': '49%', 'backgroundColor': '#161616', 'borderRadius': '15px', 'padding': '15px'}),
        
        html.Div([
            html.H4("📈 Evolución Q1 → Q2 → Q3", style={'textAlign': 'center'}),
            dcc.Graph(id='evolution-graph')
        ], style={'width': '49%', 'backgroundColor': '#161616', 'borderRadius': '15px', 'padding': '15px'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '40px'}),

    # Sección 4: HISTÓRICO Y TABLA (Lo que pediste recuperar)
    html.Div([
        # Gráfica de Leyendas
        html.Div([
            html.H3("🏆 Ranking Histórico: Pole Positions", style={'color': '#FF1801', 'textAlign': 'center'}),
            dcc.Graph(id='history-graph')
        ], style={'backgroundColor': '#161616', 'borderRadius': '15px', 'padding': '20px', 'marginBottom': '30px'}),
        
        # Tabla Detallada
        html.Div([
            html.H3("⏱️ Resultados Oficiales de Clasificación", style={'color': '#FF1801'}),
            dash_table.DataTable(
                id='results-table',
                columns=[
                    {"name": "Posición", "id": "Position"},
                    {"name": "Piloto", "id": "FamilyName"},
                    {"name": "Constructor", "id": "ConstructorName"},
                    {"name": "Nacionalidad", "id": "Nationality"},
                    {"name": "Mejor Tiempo (s)", "id": "Best_Time"}
                ],
                style_header={'backgroundColor': '#333', 'color': 'white', 'fontWeight': 'bold', 'textAlign': 'center'},
                style_cell={'backgroundColor': '#161616', 'color': '#ccc', 'textAlign': 'center', 'padding': '12px', 'fontSize': '14px'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#222'}],
                page_size=15
            )
        ], style={'backgroundColor': '#161616', 'padding': '20px', 'borderRadius': '15px'})
    ])
])

# CALLBACKS
@app.callback(
    [Output('circuit-filter', 'options'), Output('circuit-filter', 'value')],
    Input('season-filter', 'value')
)
def update_circs(season):
    circs = sorted(df[df['Season'] == season]['CircuitID'].unique())
    options = [{'label': c.replace('_', ' ').title(), 'value': c} for c in circs]
    default = 'monaco' if 'monaco' in circs else circs[0]
    return options, default

@app.callback(
    [Output('driver-filter', 'options'), Output('driver-filter', 'value')],
    [Input('season-filter', 'value'), Input('circuit-filter', 'value')]
)
def update_drivers_list(season, circuit):
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)]
    drivers = sorted(dff['FamilyName'].unique())
    return [{'label': d, 'value': d} for d in drivers], []

@app.callback(
    [Output('main-graph', 'figure'),
     Output('evolution-graph', 'figure'),
     Output('history-graph', 'figure'),
     Output('results-table', 'data'),
     Output('kpi-container', 'children')],
    [Input('season-filter', 'value'),
     Input('circuit-filter', 'value'),
     Input('driver-filter', 'value')]
)
def update_all_viz(season, circuit, sel_drivers):
    dff = df[(df['Season'] == season) & (df['CircuitID'] == circuit)].sort_values('Position')
    dff_plot = dff[dff['FamilyName'].isin(sel_drivers)] if sel_drivers else dff

    # 1. Gráfico Barras Principal
    fig1 = px.bar(dff_plot, x='FamilyName', y='Best_Time', color='ConstructorName',
                 color_discrete_map=team_colors, template='plotly_dark')
    fig1.update_yaxes(range=[dff['Best_Time'].min()*0.98, dff['Best_Time'].max()*1.02], title="Segundos")
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 2. Gráfico Evolución Q
    evol_data = []
    for _, r in dff_plot.iterrows():
        for q in ['Q1_sec', 'Q2_sec', 'Q3_sec']:
            if r[q] > 0: evol_data.append({'Piloto': r['FamilyName'], 'Sesion': q.split('_')[0], 'Tiempo': r[q]})
    
    fig2 = px.line(pd.DataFrame(evol_data), x='Sesion', y='Tiempo', color='Piloto', markers=True, template='plotly_dark')
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    # 3. Gráfico Histórico (El que pediste recuperar)
    hist_df = df[df['Position'] == 1]['FamilyName'].value_counts().head(12).reset_index()
    hist_df.columns = ['Piloto', 'Poles']
    fig3 = px.bar(hist_df, x='Piloto', y='Poles', color='Poles', color_continuous_scale='Reds', template='plotly_dark')
    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)

    # 4. KPIs
    pole = dff.iloc[0]
    kpis = [
        html.Div([html.Small("POLE POSITION"), html.H2(pole['FamilyName'])], 
                 style={'flex': '1', 'backgroundColor': '#FF1801', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center'}),
        html.Div([html.Small("ESTADÍSTICA"), html.H2(f"{len(dff)} Pilotos")], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center', 'border': '1px solid #444'}),
        html.Div([html.Small("DIFERENCIA P1-P2"), html.H2(f"{dff.iloc[1]['Best_Time'] - pole['Best_Time']:.3f}s")], 
                 style={'flex': '1', 'backgroundColor': '#222', 'padding': '15px', 'borderRadius': '12px', 'textAlign': 'center', 'border': '1px solid #444'})
    ]

    return fig1, fig2, fig3, dff.to_dict('records'), kpis

if __name__ == '__main__':
    app.run_server(debug=True)