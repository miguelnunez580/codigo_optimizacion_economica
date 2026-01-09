""" Módulo para obtener resultados de sistemas de calefacción """
from optimizador.parametros_horarios import parametros_horarios
from optimizador.sistemas import seleccion_sistema
from .sistemas.estudio_completo import calculo_todas_opciones


def inicio_optimizacion(precio_luz, precio_gas, cargas, refri, irradiacion, placas, actual, nuevo, aguas):
    """Función que prepara los argumento de entrada para el cálculo

    :param precio_luz: Datos de precios eléctricos cargados en el script principal
    :param precio_gas: Datos de precios de gas cargados en el script principal
    :param cargas: Datos de cargas térmicas cargados en el script principal
    :param refri: Booleano con el resultado de la casilla refrigeracion del script principal
    :param irradiacion: Resultados de irradiacion incidente en la residencia
    :param placas:
    :param actual: Sistema de climatización instalado en la residencia
    :param nuevo: Opción de estudio seleccionado en el script principal
    :param aguas: Numero de aguas del tejado de la residencia en estudio
    """
    df = parametros_horarios(precio_luz, precio_gas, cargas, refri)
    if nuevo != 'Todas':
        resultado = seleccion_sistema(nuevo, df, irradiacion, placas, aguas, actual, refri)
    else:
        resultado = calculo_todas_opciones(df, irradiacion, placas, aguas, actual, refri)
    return resultado
