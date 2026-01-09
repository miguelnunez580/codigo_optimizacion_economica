"""Módulo pra el cálculo de la radiación incidente horaria durante un año"""
import requests


def obtener_datos_pvgis(lat, lon, azimut):
    """Función para la descargar datos de PVGIS vía API

    :param lat: Latitud de la vivienda
    :param lon: Longitud de la vivienda
    :param azimut: Azimut de una de las aguas
    """
    url = "https://re.jrc.ec.europa.eu/api/seriescalc"
    params = {
        "lat": lat,
        "lon": lon,
        "startyear": 2023,
        "endyear": 2023,
        "outputformat": "json",
        "angle": 37,  # si decidiera yo la inclinación
        "aspect": azimut,
        "optimalangles": 0,  # Si hiciera inclinacion fija esto sería 0. 1 si buscaramos optimizar
        "usehorizon": 1,
        # Características de las placas solares
        "pvtechchoice": "crystSi",
        "peakpower": 0.5,
        "loss": 14,
        "components": 1,
        "hourly": 1
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()
        # En el supuesto de que optimice inclinación:
        # angle_optimo = data["inputs"]["mounting_system"]["fixed"]["slope"]["value"]
        return data["outputs"]["hourly"]

    else:
        print(f"Error en la solicitud: {response.status_code}")
        return None
