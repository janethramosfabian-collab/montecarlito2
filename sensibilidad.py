import pandas as pd
import numpy as np
import plotly.graph_objects as go

def calcular_sensibilidad(df, target_col):
    """
    Calcula la correlación de Spearman entre las variables de entrada y la variable objetivo.
    """
    if df.empty or target_col not in df.columns:
        return pd.DataFrame()

    # Seleccionar únicamente columnas numéricas descartando valores nulos
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    
    if target_col not in numeric_df.columns:
        return pd.DataFrame()

    y = numeric_df[target_col]
    
    # Excluir la variable de resultado de las variables independientes
    feature_cols = [col for col in numeric_df.columns if col != target_col]
    
    if not feature_cols:
        return pd.DataFrame()

    correlations = []
    for col in feature_cols:
        corr_val = numeric_df[col].corr(y, method='spearman')
        if not np.isnan(corr_val):
            correlations.append({"Variable": col, "Correlacion": corr_val})

    df_corr = pd.DataFrame(correlations)
    if not df_corr.empty:
        df_corr = df_corr.sort_values(by="Correlacion", key=abs, ascending=True)
    
    return df_corr


def generar_grafico_tornado(df_corr):
    """
    Genera el gráfico Tornado con estética idéntica a @RISK (Azul/Verde positivo, Rojo negativo).
    """
    colors = ['#E74C3C' if val < 0 else '#2ECC71' for val in df_corr['Correlacion']]

    fig = go.Figure(go.Bar(
        x=df_corr['Correlacion'],
        y=df_corr['Variable'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='#2C3E50', width=1)
        ),
        text=[f"{val:+.3f}" for val in df_corr['Correlacion']],
        textposition='auto',
    ))

    fig.update_layout(
        title="<b>Análisis de Sensibilidad (Correlación de Rangos de Spearman)</b>",
        xaxis=dict(title="Coeficiente de Correlación", range=[-1, 1], zeroline=True, zerolinecolor='#2C3E50', gridcolor='#E0E0E0'),
        yaxis=dict(title="Variables de Entrada"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(color='#2C3E50')
    )
    
    return fig
