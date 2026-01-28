"""Módulo que prepara un dataframe con los parametros que entran en el solver"""
import os
import shutil
import pandas as pd


def parametros_horarios(precio_luz, precio_gas, cargas, refrigeracion):
    """Adaptación de los datos a un único Dataframe

    :param precio_luz: Datos de precios eléctricos cargados en el script principal
    :param precio_gas: Datos de precios de gas cargados en el script principal
    :param cargas: Datos de cargas térmicas cargados en el script principal
    :param refri: Booleano con el resultado de la casilla refrigeracion del script principal
    """
    # Creo la carpeta de resultados
    if os.path.exists('Resultados'):
        shutil.rmtree('Resultados')
    os.makedirs('Resultados', exist_ok=True)

    # Importo los .csv dle script principal y los agrupo en un mismo DataFrame
    df = pd.DataFrame({'precio_luz': precio_luz, 'precio_gas': precio_gas, 'cargas': cargas})
    # Importo la que va a ser la temperatura exterior a lo largo de un año
    df['T_exterior'] = pd.read_csv('Datos/T_exterior.csv')
    # Introduzco un índice con todas las horas del año 2023 (8760 horas)
    df.index = pd.date_range(start='01-01-2023', freq='h', periods=8760)
    # Genero columna auxiliar para saber si necesito calefacción o refrigeración
    df["climatizacion"] = df["cargas"].apply(lambda x: "Calefaccion" if x >= 0 else "Refrigeracion")
    if not refrigeracion:
        df["cargas"] = df["cargas"].apply(lambda x: 0 if x < 0 else x)
        df.loc[df["climatizacion"] == "Refrigeracion", "precio_luz"] = 0
    return df
