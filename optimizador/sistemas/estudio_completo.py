"""Módulo para el cálculo de todos los sistemas de climatización del software"""
import yaml

from optimizador.sistemas import seleccion_sistema


def calculo_todas_opciones(df, irradiacion, placas, aguas, actual, refri):
    """ Función del optimizador que evalua todas las posibles alternativas.

    :param df: Dataframe con todos los parámetros que tienen carácter horario
    :param irradiacion: Resultados de irradiacion incidente en la residencia
    :param placas: Área disponible para las placas solares
    :param aguas: Numero de aguas del tejado de la residencia en estudio
    :param actual: Sistema de climatización instalado en la residencia
    :param refri: Se quiere refrigeración en el sistema
    """
    with open('datos_tecnicos.yaml', "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    resultado_aero_alta = seleccion_sistema('Aerotermia de alta', df, irradiacion, placas, aguas, actual, refri)
    aero_alta = float(resultado_aero_alta['Costo anual'].replace("€", "").strip(
    )) + float(resultado_aero_alta['Inversion'].replace("€", "").strip())/datos['Bomba de calor']['Ciclo de vida']
    resultado_aero_baja = seleccion_sistema('Aerotermia de baja', df, irradiacion, placas, aguas, actual, refri)
    aero_baja = float(resultado_aero_baja['Costo anual'].replace("€", "").strip(
    )) + float(resultado_aero_baja['Inversion'].replace("€", "").strip())/datos['Bomba de calor']['Ciclo de vida']
    resultado_gas = seleccion_sistema("Gas", df, irradiacion, placas, aguas, actual, refri)
    gas = float(resultado_gas['Costo anual'].replace("€", "").strip()) + \
        float(resultado_gas['Inversion'].replace("€", "").strip())/datos['Gas']['Ciclo de vida']
    variables = {'aero_baja': aero_baja, 'aero_alta': aero_alta, 'gas': gas}
    resultados = {
        'aero_baja': resultado_aero_baja,
        'aero_alta': resultado_aero_alta,
        'gas': resultado_gas
    }
    opt = min(variables, key=variables.get)
    return resultados[opt]
