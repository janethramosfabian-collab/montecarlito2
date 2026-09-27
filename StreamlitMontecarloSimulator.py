# Importa las librerías necesarias
import streamlit as st  # Para crear la interfaz web
import pandas as pd  # Para manipular datos en formato tabular
import numpy as np  # Para realizar cálculos numéricos
import plotly.express as px  # Para crear gráficos interactivos
import montecarlo as mc # Para las funciones de la simulación
from code_editor import code_editor # Para editar el código en la app
import utils as ut  # Para funciones de utilidad personalizadas
import sensibilidad as sens  # <--- AGREGAR ESTA LÍNEA

# Configura la página de Streamlit
st.set_page_config(page_title="Simulador de Montecarlo", page_icon="📊", layout="wide")

# Aplica estilos CSS personalizados
ut.local_css("estilos.css")

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
        parformula = code_editor('', lang='python', 
                                 response_mode='blur',
                                 )  # Editor de código
    # Muestra un mensaje informativo sobre cómo ingresar la fórmula
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
            st.stop() # Detiene la ejecución si no hay variables
        # Crea un DataFrame para las variables
        dfBase = pd.DataFrame({'Variable': listaNombreVariables, "Distribucion": "Normal", "Tipo Datos": "Decimales", "Param 1": 0.0000, "Param 2": 0.000,"Param 3": 0.000})
        # Crea dos columnas para la edición de variables y la información de distribuciones
        columns = st.columns(2)
        with columns[0]:
            # Data editor para configurar las variables
            dfVariables = st.data_editor(dfBase,
                                        column_config={
                                            "Variable": st.column_config.TextColumn(
                                                "Variable",                                                
                                                disabled=True,
                                            ),
                                            "Distribucion": st.column_config.SelectboxColumn(
                                                "Distribución",
                                                help="Distribución de probabilidad de la simulación",
                                                width="medium",
                                                options=[
                                                    "Normal", "Uniforme", "Binomial", 
                                                    "Triangular", "Exponencial", "Poisson", "Log-Normal"
                                                ],
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
            
            # --- PEGAS AQUÍ EL PRIMER CÓDIGO (EL EXPANDER) ---
# --- PANEL DE ESCENARIOS CONJUNTOS 100% DINÁMICO Y VACÍO ---
            with st.expander("🔗 Configuración Avanzada: Variables Correlacionadas / Escenarios Conjuntos", expanded=False):
                st.write("Si tus variables dependen de un escenario conjunto (discreto), habilítalo y define tus propias columnas y valores.")
                usar_escenarios = st.checkbox("Habilitar Escenarios Conjuntos para variables dependientes")
                
                dfEscenarios = pd.DataFrame()
                if usar_escenarios:
                    # Inicializamos una tabla vacía genérica para que el usuario construya sus propios escenarios
                    datos_vacia = {
                        "Escenario": ["Escenario 1", "Escenario 2"],
                        "Probabilidad": [0.5, 0.5],
                    }
                    st.info("Agrega las columnas con el nombre exacto de tus variables (ej. el nombre que uses en la fórmula con {{ }}).", icon=":material/info:")
                    dfEscenarios = st.data_editor(pd.DataFrame(datos_vacia), num_rows="dynamic", use_container_width=True)
            # -------------------------------------------------------------
            # -------------------------------------------------

            # Botón para iniciar la simulación
            btnSimular = st.button('Simular', type="primary")
            
            # Calcula el valor mínimo de los parámetros
            minValorParametros = dfVariables.apply(lambda x: x["Param 1"] + x["Param 2"]+ x["Param 3"], axis=1).min()
            if minValorParametros == 0:
                st.error("Algunas de las variables tienen los parámetros principales en cero", icon=":material/warning:")
        with columns[1]:
            # Texto informativo actualizado con la nueva caja de herramientas estadísticas
            textoDistribuciones = """### Distribuciones
**Normal** Distribución en forma de campana, valores cerca de la media.
* *Param 1:* Media de la distribución.
* *Param 2:* Desviación estándar de la distribución.	
* **Casos de uso:** Estadísticas, control de calidad, finanzas.

**Distribución Uniforme:** Todos los resultados en un rango tienen igual probabilidad.
* *Param 1:* Valor mínimo del rango.
* *Param 2:* Valor máximo del rango.
* **Casos de uso:** Números aleatorios, tiempos de espera, juegos de azar.

**Distribución Binomial:** Número de éxitos en ensayos con dos resultados posibles.
* *Param 1:* Número de ensayos.
* *Param 2:* Probabilidad de éxito.
* **Casos de uso:** Encuestas, control de calidad, biología.

**Distribución Triangular:** Valores más probables en un rango.
* *Param 1:* Valor mínimo del rango.
* *Param 2:* Valor más probable.
* *Param 3:* Valor máximo del rango.
* **Casos de uso:** Estimaciones, riesgos, incertidumbre.

**Exponencial:** Modela el tiempo entre eventos en un proceso de Poisson.
* *Param 1:* Escala (media / 1 medida de tasa).
* **Casos de uso:** Tiempos de espera, durabilidad de componentes.

**Poisson:** Modela el número de eventos en un intervalo de tiempo o espacio.
* *Param 1:* Tasa media de ocurrencia ($\lambda$).
* **Casos de uso:** Conteo de llamadas, llegadas de clientes, fallas.

**Log-Normal:** Variables cuyo logaritmo está normalmente distribuido.
* *Param 1:* Media logarítmica.
* *Param 2:* Desviación estándar logarítmica.
* **Casos de uso:** Precios de activos financieros, salarios, tamaños de reservas.
            """
            with st.container(height=300):
                st.info(textoDistribuciones)
        # Inicializa el estado de la sesión para el resultado
        if 'resultado' not in st.session_state:
            st.session_state.resultado = pd.DataFrame()

# Contenedor para los resultados de la simulación
with st.container(border=True, key="panel-analisis"):    
    # Si se ha presionado el botón Simular o hay resultados en la sesión    
    if btnSimular or len(st.session_state.resultado) > 0:
        
        # Detiene si los parámetros son cero
        if minValorParametros == 0:
            st.stop()
        # Si no hay resultados en la sesión o se ha presionado el botón Simular
        if len(st.session_state.resultado) == 0 or btnSimular:
            # Declaramos un diccionario para almacenar las variables
            variables = dict()
            # Itera sobre las variables y genera valores aleatorios según la distribución seleccionada
# Itera sobre las variables y genera valores aleatorios según la distribución o escenario personalizado
            for index, fila in dfVariables.iterrows():
                var_nombre = fila["Variable"]
                
                # Si se habilitaron escenarios y el usuario creó una columna con el nombre exacto de la variable
                if usar_escenarios and not dfEscenarios.empty and var_nombre in dfEscenarios.columns:
                    if "Probabilidad" in dfEscenarios.columns:
                        probs = pd.to_numeric(dfEscenarios["Probabilidad"], errors='coerce').fillna(0).values
                        if probs.sum() > 0:
                            probs = probs / probs.sum() # Normalizar
                            escenarios_idx = np.random.choice(dfEscenarios.index, size=parNumSimulaciones, p=probs)
                            valores = pd.to_numeric(dfEscenarios.loc[escenarios_idx, var_nombre], errors='coerce').values
                        else:
                            valores = np.zeros(parNumSimulaciones)
                    else:
                        st.error("La tabla de escenarios conjuntos debe incluir una columna llamada 'Probabilidad'.")
                        st.stop()
                else:
                    # Comportamiento estándar por distribuciones independientes
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
                
                # Manejo limpio y estricto de tipos de datos
                if fila["Tipo Datos"] == "Entero":
                    variables[var_nombre] = np.round(valores).astype(int)
                else:
                    variables[var_nombre] = valores.astype(float)

            # Evalúa la fórmula de simulación
            variables[parVariableResultado] = eval(formulaSimulacion, {"np": np, "variables": variables})
            
            # Crea un DataFrame con los resultados
            dfResultado = pd.DataFrame(variables)
            # Guarda el DataFrame en el estado de la sesión
            st.session_state.resultado = dfResultado
        else:
            # Si ya hay resultados en la sesión, los carga
            dfResultado = st.session_state.resultado
            
        # Subtítulo para la sección de resultados
        # Subtítulo para la sección de resultados
        st.subheader('Resultados de la Simulación')
        
        tabAnalisis, tabSensibilidad, tabDatos = st.tabs(["📊 Histograma y Frecuencia", "🌪️ Sensibilidad (Tornado)", "📋 Datos de Simulaciones"])

        with tabAnalisis:
            if parVariableResultado in dfResultado.columns:
                c1, c2 = st.columns([7, 3])
                with c1:
                    rangoPercentiles = [2.5, 5, 25, 50, 75, 95, 97.5]
                    percentiles = np.percentile(dfResultado[parVariableResultado], rangoPercentiles)
                    dfPercentiles = pd.DataFrame({"Percentil": [f"{i} %" for i in rangoPercentiles], "Valor": percentiles})
                    
                    min_val = float(dfResultado[parVariableResultado].min())
                    max_val = float(dfResultado[parVariableResultado].max())
                    
                    parMontoProbabilidad = st.slider('Rango de Delimitadores (Cutoffs)', 
                                                     min_val, max_val,
                                                     (float(percentiles[0]), float(percentiles[-1])))
                    
                    dfRango = dfResultado[(dfResultado[parVariableResultado] >= parMontoProbabilidad[0]) & 
                                          (dfResultado[parVariableResultado] <= parMontoProbabilidad[1])]
                    probabilidadMonto = len(dfRango) / parNumSimulaciones
                    
                    m_cols = st.columns(3)
                    m_cols[0].metric(label="Probabilidad (Likelihood)", value=f"{probabilidadMonto:,.2%}")
                    m_cols[1].metric(label="Corte Inferior", value=f"{parMontoProbabilidad[0]:,.2f}")
                    m_cols[2].metric(label="Corte Superior", value=f"{parMontoProbabilidad[1]:,.2f}")
                    
                    # Generación del Histograma exacto a @RISK (Verde Esmeralda + Delimitadores Rojos)
                    fig_hist = go.Figure()
                    
                    df_fuera = dfResultado[(dfResultado[parVariableResultado] < parMontoProbabilidad[0]) | 
                                          (dfResultado[parVariableResultado] > parMontoProbabilidad[1])]
                    
                    # Barras de fuera de rango
                    fig_hist.add_trace(go.Histogram(
                        x=df_fuera[parVariableResultado],
                        marker=dict(color='#A3E4D7', line=dict(color='#ffffff', width=0.5)),
                        showlegend=False
                    ))

                    # Barras dentro de rango
                    fig_hist.add_trace(go.Histogram(
                        x=dfRango[parVariableResultado],
                        marker=dict(color='#2ECC71', line=dict(color='#ffffff', width=0.5)),
                        showlegend=False
                    ))

                    # Líneas verticales rojas discontinuas
                    fig_hist.add_vline(x=parMontoProbabilidad[0], line_dash="dash", line_color="#E74C3C", line_width=2)
                    fig_hist.add_vline(x=parMontoProbabilidad[1], line_dash="dash", line_color="#E74C3C", line_width=2)

                    fig_hist.update_layout(
                        title=f"<b>Resultados de Simulación: {parVariableResultado}</b>",
                        barmode='overlay',
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        xaxis=dict(title=f"Valores de {parVariableResultado}", gridcolor='#E2E8F0'),
                        yaxis=dict(title="Frecuencia", gridcolor='#E2E8F0'),
                        font=dict(color='#0F172A')
                    )
                    
                    st.plotly_chart(fig_hist, use_container_width=True, key="chart-histograma-risk")

                with c2:
                    st.markdown("#### Estadísticas")
                    st.metric(label="Simulaciones", value=f"{parNumSimulaciones:,}")
                    st.metric(label="Media", value=f"{dfResultado[parVariableResultado].mean():,.2f}")
                    st.metric(label="Desv. Estándar", value=f"{dfResultado[parVariableResultado].std():,.2f}")
                    st.dataframe(dfPercentiles, use_container_width=True)

        with tabSensibilidad:
            st.markdown("#### Análisis de Sensibilidad (Tornado)")
            df_corr = sens.calcular_sensibilidad(dfResultado, parVariableResultado)
            if not df_corr.empty:
                fig_tornado = sens.generar_grafico_tornado(df_corr)
                st.plotly_chart(fig_tornado, use_container_width=True)
            else:
                st.info("Asegúrate de tener variables aleatorias configuradas para calcular la sensibilidad.")

        with tabDatos:
            st.dataframe(dfResultado, use_container_width=True)
