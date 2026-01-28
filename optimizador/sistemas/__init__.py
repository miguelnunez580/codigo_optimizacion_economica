"""Modulo que seleciona la opción de cálculo"""
import numpy as np
import pandas as pd

from optimizador.sistemas.estudio_aerotermia import calculo_aerotermia
from optimizador.sistemas.estudio_aire_acondicionado import calculo_aire_acondicionado
from optimizador.sistemas.estudio_gas import calculo_gas


def seleccion_sistema(nuevo, df, irradiacion, placas, aguas, actual, refri):
    """Función que selecciona la poción de estudio seleccionada

    :param nuevo: Opción de estudio seleccionado en el script principal
    :param df: Dataframe con todos los parámetros que tienen carácter horario
    :param irradiacion: Resultados de irradiacion incidente en la residencia
    :param placas: Selección de la opción paneles solares
    :param aguas: Numero de aguas del tejado de la residencia en estudio
    :param inversion: Coste de la instalacion del nuevo sistema de climatización
    :param refri: Booleano con el resultado de la casilla refrigeracion del script principal
    """
    df_inversion = pd.read_csv('Datos/inversion.csv', sep=';', index_col=0)
    df_ayudas = pd.read_csv('Datos/ayudas.csv', sep=';')
    inversion = max(df_inversion.loc[actual, nuevo] - df_ayudas[nuevo].iloc[0], 0)
    if refri and nuevo == "Gas":
        df_calefaccion = df.loc[df['climatizacion'] == 'Calefaccion']
        df_refrigeracion = df.loc[df['climatizacion'] == 'Refrigeracion']
        resultado_calefaccion = calculo_gas(df_calefaccion, df_inversion.loc[actual, nuevo])
        resultado_refrigeracion = calculo_aire_acondicionado(
            df_refrigeracion, irradiacion, placas, [0]*aguas,
            aguas, df_inversion.loc[actual, 'Aire acondicionado'])
        resultado = {
            "Costo anual": f"{np.round(float(resultado_calefaccion["Costo anual"].replace("€", "").strip()) +
                               float(resultado_refrigeracion["Costo anual"].replace("€", "").strip()), 2)} €",
            "Potencia Caldera de gas": resultado_calefaccion["Potencia Caldera de gas"],
            "Potencia Aire acondicionado": resultado_refrigeracion["Potencia Bomba de calor"],
            "Placas solares": resultado_refrigeracion["placas"],
            "Inversion": f"{np.round((float(resultado_calefaccion["Inversion"].replace("€", "").strip()) +
                             float(resultado_refrigeracion["Inversion"].replace("€", "").strip())), 2)} €"
        }
    elif nuevo == "Gas" and not refri:
        resultado = calculo_gas(df, inversion)
    elif refri and nuevo == "Aerotermia de alta":
        df_calefaccion = df.loc[df['climatizacion'] == 'Calefaccion']
        df_refrigeracion = df.loc[df['climatizacion'] == 'Refrigeracion']
        resultado_calefaccion = calculo_aerotermia(
            nuevo, df_calefaccion, irradiacion, placas, aguas, df_inversion.loc[actual, nuevo])
        ps = resultado_calefaccion["Placas"]
        resultado_refrigeracion = calculo_aire_acondicionado(
            df_refrigeracion, irradiacion, placas, ps, aguas, df_inversion.loc[actual, 'Aire acondicionado'])
        resultado = {
            "Costo anual": f"{np.round(float(resultado_calefaccion["Costo anual"].replace("€", "").strip()) +
                                       float(resultado_refrigeracion["Costo anual"].replace("€", "").strip()), 2)} €",
            "Potencia Aerotermia de alta": resultado_calefaccion["Potencia Aerotermia de alta"],
            "Volumen deposito de inercia": resultado_calefaccion["Volumen deposito de inercia"],
            "Potencia Aire acondicionado": resultado_refrigeracion["Potencia Bomba de calor"],
            "Placas solares": resultado_calefaccion["Placas"],
            "Inversion": f"{np.round((float(resultado_calefaccion["Inversion"].replace("€", "").strip()) +
                                      float(resultado_refrigeracion["Inversion"].replace("€", "").strip())), 2)} €"
        }
    elif nuevo == "Aerotermia de alta" and not refri:
        resultado = calculo_aerotermia(nuevo, df, irradiacion, placas, aguas, df_inversion.loc[actual, nuevo])
    elif nuevo == "Aerotermia de baja":
        resultado = calculo_aerotermia(nuevo, df, irradiacion, placas, aguas, df_inversion.loc[actual, nuevo])
    elif nuevo == "Aire acondicionado":
        resultado = calculo_aire_acondicionado(df, irradiacion, placas, [0]*aguas, aguas, df_inversion.loc[actual, nuevo])
    else:
        resultado = 'No se seleciono ninguna opción correcta'
    return resultado
