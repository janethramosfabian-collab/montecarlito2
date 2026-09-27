# Importa las librerías necesarias
import streamlit as st  # Para crear la interfaz web
import pandas as pd  # Para manipular datos en formato tabular
import numpy as np  # Para realizar cálculos numéricos
import plotly.express as px  # Para crear gráficos interactivos
import plotly.graph_objects as go
import montecarlo as mc # Para las funciones de la simulación
from code_editor import code_editor # Para editar el código en la app
import utils as ut  # Para funciones de utilidad personalizadas
import sensibilidad as sens  # Módulo para correlación y tornado

# Configura la página de Streamlit
st.set_page_config(page_title="Simulador de Montecarlo", page_icon="📊", layout="wide")

# Aplica estilos CSS personalizados
ut.local_css("estilos.css")

with open('estilos.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
# Título principal de la aplicación
st.title(':material/analytics: Simulador de Montecarlo')

# Contenedor para los parámetros de la simulación
with st.container(border=True, key="panel-parametros"):
    # Subtítulo para la sección de parámetros
    st.subheader(':blue[:material/function: Parámetros de la simulación]')
    # Crea dos columnas para organizar los elementos
    c1, c2 = st.columns([2, 8], vertical_alignment="center")
    # Columna 1: Input para el nombre de la variable resultado
    with c1:
        parVariableResultado = st.text_input('Variable resultado', 'Resultado')
    # Columna 2: Editor de código para la fórmula de simulación
    with c2:
        st.write('##### Fórmula de la simulación')
        parformula = code_editor('', lang='python', response_mode='blur')
        
    st.info('Ingrese la fórmula de la simulación. Utilice las variables entre llaves dobles. Por ejemplo, si la fórmula es `X1+X2`, debe ingresar `{{X1}}+{{X2}}`', icon=":material/info:")

    # Input para el número de simulaciones
    parNumSimulaciones = st.number_input('Número de simulaciones', min_value=1, value=1000)
    
    # Si se ha ingresado una fórmula
    if parformula:
        # Genera las variables a partir de la fórmula ingresada
        formulaSimulacion, listaNombreVariables = mc.generarVariables(parformula["text"])
        
        # Verifica si se encontraron variables en la fórmula
        if len(listaNombreVariables) == 0:
            st.error("No se encontraron variables en la fórmula. Todas las variables deben tener el formato {{variable}}", icon=":material/warning:")
            st.stop()
            
        # Crea un DataFrame para las variables
        dfBase = pd.DataFrame({'Variable': listaNombreVariables, "Distribucion": "Normal", "Tipo Datos": "Decimales", "Param 1": 0.0000, "Param 2": 0.000,"Param 3": 0.000})
        
        columns = st.columns(2)
        with columns[0]:
            # Data editor para configurar las variables
            dfVariables = st.data_editor(dfBase,
                                        column_config={
                                            "Variable": st.column_config.TextColumn("Variable", disabled=True),
                                            "Distribucion": st.column_config.SelectboxColumn(
                                                "Distribución",
                                                help="Distribución de probabilidad de la simulación",
                                                width="medium",
                                                options=["Normal", "Uniforme", "Binomial", "Triangular", "Exponencial", "Poisson", "Log-Normal"],
                                                required=True,
                                            ),
                                            "Tipo Datos": st.column_config.SelectboxColumn(
                                                "Tipo de Datos",
                                                help="Tipo de datos de la variable",
                                                width="medium",
                                                options=["Entero", "Decimales"],
                                                required=True,
                                            )
                                        },
                                        hide_index=True, use_container_width=True)
            
            # --- PANEL DE ESCENARIOS CONJUNTOS ---
            with st.expander("🔗 Configuración Avanzada: Variables Correlacionadas / Escenarios Conjuntos", expanded=False):
                st.write("Si tus variables dependen de un escenario conjunto (discreto), habilítalo y define tus propias columnas y valores.")
                usar_escenarios = st.checkbox("Habilitar Escenarios Conjuntos para variables dependientes")
                
                dfEscenarios = pd.DataFrame()
                if usar_escenarios:
                    datos_vacia = {
                        "Escenario": ["Escenario 1", "Escenario 2"],
                        "Probabilidad": [0.5, 0.5],
                    }
                    st.info("Agrega las columnas con el nombre exacto de tus variables (ej. el nombre que uses en la fórmula con {{ }}).", icon=":material/info:")
                    dfEscenarios = st.data_editor(pd.DataFrame(datos_vacia), num_rows="dynamic", use_container_width=True)

            # Botón para iniciar la simulación
            btnSimular = st.button('Simular', type="primary")
            
            minValorParametros = dfVariables.apply(lambda x: x["Param 1"] + x["Param 2"]+ x["Param 3"], axis=1).min()
            if minValorParametros == 0:
                st.error("Algunas de las variables tienen los parámetros principales en cero", icon=":material/warning:")
                
        with columns[1]:
            textoDistribuciones = """### Distribuciones
**Normal** Distribución en forma de campana, valores cerca de la media.
* *Param 1:* Media | *Param 2:* Desviación estándar

**Distribución Uniforme:** Resultados en un rango con igual probabilidad.
* *Param 1:* Mínimo | *Param 2:* Máximo

**Distribución Binomial:** Éxitos en ensayos con dos resultados posibles.
* *Param 1:* Ensayos | *Param 2:* Probabilidad

**Distribución Triangular:** Valores más probables en un rango.
* *Param 1:* Mínimo | *Param 2:* Moda | *Param 3:* Máximo

**Exponencial:** Tiempo entre eventos.
* *Param 1:* Escala

**Poisson:** Conteo de eventos en un intervalo.
* *Param 1:* Tasa ($\lambda$)

**Log-Normal:** Variables cuyo logaritmo es normal.
* *Param 1:* Media log | *Param 2:* Desv log
            """
            with st.container(height=300):
                st.info(textoDistribuciones)
                
        # Inicializa el estado de la sesión para el resultado
        if 'resultado' not in st.session_state:
            st.session_state.resultado = pd.DataFrame()

# LÓGICA DE CÁLCULO DE LA SIMULACIÓN
if btnSimular or len(st.session_state.resultado) > 0:
    if minValorParametros == 0 and btnSimular:
        st.stop()
        
    if len(st.session_state.resultado) == 0 or btnSimular:
        variables = dict()
        for index, fila in dfVariables.iterrows():
            var_nombre = fila["Variable"]
            
            if usar_escenarios and not dfEscenarios.empty and var_nombre in dfEscenarios.columns:
                if "Probabilidad" in dfEscenarios.columns:
                    probs = pd.to_numeric(dfEscenarios["Probabilidad"], errors='coerce').fillna(0).values
                    if probs.sum() > 0:
                        probs = probs / probs.sum()
                        escenarios_idx = np.random.choice(dfEscenarios.index, size=parNumSimulaciones, p=probs)
                        valores = pd.to_numeric(dfEscenarios.loc[escenarios_idx, var_nombre], errors='coerce').values
                    else:
                        valores = np.zeros(parNumSimulaciones)
                else:
                    st.error("La tabla de escenarios conjuntos debe incluir una columna llamada 'Probabilidad'.")
                    st.stop()
            else:
                dist = fila["Distribucion"]
                p1 = fila["Param 1"]
                p2 = fila["Param 2"]
                p3 = fila["Param 3"]
                
                if dist == "Normal":
                    valores = np.random.normal(p1, p2, parNumSimulaciones)
                elif dist == "Uniforme":
                    if fila["Tipo Datos"] == "Entero":
                        valores = np.random.randint(int(p1), int(p2) + 1, size=parNumSimulaciones)
                    else:
                        valores = np.random.uniform(p1, p2, parNumSimulaciones)
                elif dist == "Binomial":
                    valores = np.random.binomial(int(p1), p2, parNumSimulaciones)
                elif dist == "Triangular":
                    valores = np.random.triangular(p1, p2, p3, parNumSimulaciones)
                elif dist == "Exponencial":
                    valores = np.random.exponential(scale=p1, size=parNumSimulaciones)
                elif dist == "Poisson":
                    valores = np.random.poisson(lam=p1, size=parNumSimulaciones)
                elif dist == "Log-Normal":
                    valores = np.random.lognormal(mean=p1, sigma=p2, size=parNumSimulaciones)
            
            if fila["Tipo Datos"] == "Entero":
                variables[var_nombre] = np.round(valores).astype(int)
            else:
                variables[var_nombre] = valores.astype(float)

        variables[parVariableResultado] = eval(formulaSimulacion, {"np": np, "variables": variables})
        dfResultado = pd.DataFrame(variables)
        st.session_state.resultado = dfResultado
    else:
        dfResultado = st.session_state.resultado

   # --- BOTÓN DE SIMULACIÓN Y CÁLCULO ---
# Asigna un key único al botón para evitar el StreamlitDuplicateElementId
if st.button("Simular", type="primary", key="btn_simular_principal"):
    # Tu lógica de simulación
    pass
    with st.spinner("Ejecutando simulación de Montecarlo..."):
        # Tu función de simulación aquí
        dfResultado = ejecutar_simulacion(...) # Asegúrate de asignar la variable aquí
        st.session_state['dfResultado'] = dfResultado

# --- SECCIÓN DE RESULTADOS ---
# Verificamos que dfResultado exista en la sesión para evitar NameError
if 'dfResultado' in st.session_state and not st.session_state['dfResultado'].empty:
    dfResultado = st.session_state['dfResultado']
    
    st.subheader('Resultados de la Simulación')

    # UN SOLO CUADRO CONTENEDOR CON BORDES REDONDEADOS
    st.markdown('<div class="window-risk">', unsafe_allow_html=True)

    tabAnalisis, tabSensibilidad, tabDatos = st.tabs(["📊 Histograma y Frecuencia", "🌪️ Sensibilidad (Tornado)", "📋 Datos de Simulaciones"])

    with tabAnalisis:
        if parVariableResultado in dfResultado.columns:
            vals = dfResultado[parVariableResultado].dropna()
            
            col_grafico, col_stats = st.columns([7, 3])
            
            with col_grafico:
                rangoPercentiles = [2.5, 5, 25, 50, 75, 95, 97.5]
                percentiles = np.percentile(vals, rangoPercentiles)
                
                min_val = float(vals.min())
                max_val = float(vals.max())
                if min_val == max_val:
                    max_val += 0.01
                
                parMontoProbabilidad = st.slider('Rango de Delimitadores (Cutoffs)', 
                                                 min_val, max_val,
                                                 (float(percentiles[0]), float(percentiles[-1])))
                
                dfRango = dfResultado[(dfResultado[parVariableResultado] >= parMontoProbabilidad[0]) & 
                                      (dfResultado[parVariableResultado] <= parMontoProbabilidad[1])]
                probabilidadMonto = len(dfRango) / len(dfResultado) if len(dfResultado) > 0 else 0
                
                # Métricas en cajas celestes claras con texto azul oscuro
                m_cols = st.columns(3)
                m_cols[0].metric(label="Probabilidad (Likelihood)", value=f"{probabilidadMonto:,.2%}")
                m_cols[1].metric(label="Corte Inferior", value=f"{parMontoProbabilidad[0]:,.2f}")
                m_cols[2].metric(label="Corte Superior", value=f"{parMontoProbabilidad[1]:,.2f}")
                
                # Gráfico
                fig_hist = go.Figure()
                df_fuera = dfResultado[(dfResultado[parVariableResultado] < parMontoProbabilidad[0]) | 
                                      (dfResultado[parVariableResultado] > parMontoProbabilidad[1])]
                
                fig_hist.add_trace(go.Histogram(x=df_fuera[parVariableResultado], marker=dict(color='#A3E4D7'), showlegend=False))
                fig_hist.add_trace(go.Histogram(x=dfRango[parVariableResultado], marker=dict(color='#2ECC71'), showlegend=False))
                fig_hist.add_vline(x=parMontoProbabilidad[0], line_dash="dash", line_color="#E74C3C", line_width=2)
                fig_hist.add_vline(x=parMontoProbabilidad[1], line_dash="dash", line_color="#E74C3C", line_width=2)

                fig_hist.update_layout(
                    title=dict(text=f"<b>Simulation Results: {parVariableResultado}</b>", font=dict(color='#0f172a', size=16)),
                    barmode='overlay',
                    plot_bgcolor='#ffffff',
                    paper_bgcolor='#ffffff',
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis=dict(title=f"Valores de {parVariableResultado}", gridcolor='#e2e8f0', title_font=dict(color='#1e293b')),
                    yaxis=dict(title="Frecuencia", gridcolor='#e2e8f0', title_font=dict(color='#1e293b')),
                    font=dict(color='#1e293b')
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)

            with col_stats:
                st.markdown("#### Estadísticas")
                st.metric(label="Simulaciones", value=f"{len(dfResultado):,}")
                st.metric(label="Media", value=f"{vals.mean():,.2f}")
                st.metric(label="Desv. Estándar", value=f"{vals.std():,.2f}")
                
                dfPercentiles = pd.DataFrame({"Percentil": [f"{i}%" for i in rangoPercentiles], "Valor": percentiles})
                st.dataframe(dfPercentiles, use_container_width=True, hide_index=True)

    with tabSensibilidad:
        st.markdown("#### Análisis de Sensibilidad (Tornado)")
        df_corr = sens.calcular_sensibilidad(dfResultado, parVariableResultado)
        if not df_corr.empty:
            fig_tornado = sens.generar_grafico_tornado(df_corr)
            st.plotly_chart(fig_tornado, use_container_width=True)

    with tabDatos:
        st.dataframe(dfResultado, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("Haz clic en 'Simular' para generar los resultados.")
