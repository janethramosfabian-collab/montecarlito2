import re
import streamlit as st
import numpy as np

def generarVariables(formula):    
    # 1. Extrae los nombres de las variables en formato {{variable}}
    listaVariables = re.findall(r"({{[A-Za-z0-9_]+}})", formula)
    formulaSimulacion = formula
    listaNombreVariables = []
    
    for var in listaVariables:
        nombrevar = var.replace("{{", "").replace("}}", "")
        if nombrevar not in listaNombreVariables:
            listaNombreVariables.append(nombrevar)
        # Sustituye la sintaxis de la variable por la referencia al diccionario 'variables'
        formulaSimulacion = formulaSimulacion.replace(var, f"variables['{nombrevar}']")
    
    # 2. Traducción de sintaxis Excel a NumPy para soporte de condicionales como IF
    # Traduce 'IF(' o 'if(' a 'np.where('
    formulaSimulacion = re.sub(r'\bIF\s*\(', 'np.where(', formulaSimulacion, flags=re.IGNORECASE)
    
    # Reemplaza punto y coma ';' por comas ','
    formulaSimulacion = formulaSimulacion.replace(';', ',')
    
    # Convierte operadores de igualdad de Excel (=) a Python (==), ignorando <=, >=, != o ==
    formulaSimulacion = re.sub(r'(?<![><!=])=(?![=])', '==', formulaSimulacion)

    return formulaSimulacion, listaNombreVariables
