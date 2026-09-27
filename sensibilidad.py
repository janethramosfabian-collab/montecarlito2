import plotly.graph_objects as go
import pandas as pd
import numpy as np

def calcular_sensibilidad(df_variables, variable_resultado):
    """
    Calcula la correlación Spearman entre las variables de entrada y el resultado.
    """
    correlaciones = {}
    y = df_variables[variable_resultado]
    
    for col in df_variables.columns:
        if col != variable_resultado:
            # Correlación de Spearman (rangos)
            corr = df_variables[col].corr(y, method='spearman')
            if not np.isnan(corr):
                correlaciones[col] = corr
                
    df_corr = pd.DataFrame(list(correlaciones.items()), columns=['Variable', 'Correlacion'])
    df_corr = df_corr.sort_values(by='Correlacion', key=abs, ascending=True)
    return df_corr

def generar_grafico_tornado(df_corr):
    """
    Genera el gráfico Tornado con estilo corporativo tech.
    """
    colores = ['#0052CC' if val >= 0 else '#D9381E' for val in df_corr['Correlacion']]
    
    fig = go.Figure(go.Bar(
        x=df_corr['Correlacion'],
        y=df_corr['Variable'],
        orientation='h',
        marker=dict(color=colores, line=dict(color='#FFFFFF', width=1)),
        text=np.round(df_corr['Correlacion'], 3),
        textposition='auto',
        textfont=dict(color='white', size=12, family="Courier New, monospace")
    ))
    
    fig.update_layout(
        title="<b>Análisis de Sensibilidad (Correlación de Rangos)</b>",
        title_font=dict(size=16, color="#E0E6ED"),
        xaxis=dict(title="Coeficiente de Correlación", range=[-1, 1], gridcolor="#2A3447", zerolinecolor="#FFFFFF"),
        yaxis=dict(gridcolor="#2A3447"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#161B22",
        font=dict(color="#C9D1D9"),
        height=380,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
