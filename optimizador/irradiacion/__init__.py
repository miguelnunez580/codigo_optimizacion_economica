"""Modúlo para el cálculo de irradiación de un residencia particular"""
import pandas as pd

from optimizador.irradiacion.irradiacion import obtener_datos_pvgis


def calculo_irradiacion(latitud, longitud, azimut, aguas):
    """Calculo de la radiación incidente en cada una de las caras del tejado de la vivienda

    :param latitud: Latitud de la vivienda
    :param longitud: Longitud de la vivienda
    :param azimut: Azimut de una de las aguas
    :param aguas: nº de aguas de la vivienda
    """
    cont = 0
    irradiacion = pd.DataFrame()
    for i in range(aguas):
        cara = azimut+360/aguas*i
        if cara > 180:
            cont += 1
            cara = azimut-360/aguas*(cont)
        datos_horarios = obtener_datos_pvgis(int(latitud), int(longitud), cara)
        df_resultado = pd.DataFrame(datos_horarios)  # Unidades: W/m^2
        irradiacion.insert(i, f'cara_{i}', df_resultado['Gb(i)'] + df_resultado['Gd(i)'] + df_resultado['Gr(i)'])
    # resultado.to_csv(r'C:\Users\mnbay\Desktop\PVGIS.csv', index=False)
    return irradiacion

