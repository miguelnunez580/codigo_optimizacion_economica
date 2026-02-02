"""Módulo para el cálculo de sistemas de climatización por aire acondicioanado"""
import math
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml
import pyomo.environ as pyo

from dotenv import load_dotenv


def calculo_aire_acondicionado(df, irradiacion, area, n_ps, aguas, c_i):
    """Funcion para la optimización económica de sistemas de climatización por aerotermia

    :param tipo: Módelo de aerotermia seleccionado
    :param df: Dataframe con todos los parámetros que tienen carácter horario
    :param irradiacion: Resultados de irradiacion incidente en la residencia
    :param placas:
    :param aguas: Numero de aguas del tejado de la residencia en estudio
    :param c_i: Coste invariable de la instalacion del nuevo sistema de climatización
    """
    # ---------------------------
    # CARGA DE DATOS (usa tus rutas/objetos)
    # ---------------------------
    with open('datos_tecnicos.yaml', "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    horas = len(df)

    area_tejado = np.array(area) / (1.909 * 1.134)

    cargas = df["cargas"].to_numpy()
    precio = df["precio_luz"].to_numpy()
    climatizacion = df['climatizacion'].to_numpy()

    irradiacion = np.array(irradiacion)

    model = pyo.ConcreteModel()

    # ---------------------------
    # Sets
    # ---------------------------
    model.H = pyo.RangeSet(0, horas - 1)
    model.J = pyo.RangeSet(0, aguas - 1)
    # ---------------------------
    # Parámetros
    # ---------------------------
    model.q_ct = pyo.Param(
        model.H,
        initialize={h: float(cargas[h]) for h in model.H}
    )
    model.climatizacion = pyo.Param(
        model.H,
        initialize={h: str(climatizacion[h]) for h in model.H}
    )
    model.precio = pyo.Param(
        model.H,
        initialize={h: float(precio[h]) for h in model.H}
    )
    model.g = pyo.Param(
        model.H, model.J,
        initialize={(h, j): float(irradiacion[h][j]) for h in model.H for j in model.J}
    )
    cop = float(datos['Aire acondicionado']["cop"])
    err = float(datos['Aire acondicionado']["err"])
    # ---------------------------
    # Variables
    # ---------------------------
    model.p_bdc = pyo.Var(bounds=(0, datos["Bomba de calor"]["Limite"]))
    model.e_red = pyo.Var(model.H, domain=pyo.NonNegativeReals)
    model.vertido_ps = pyo.Var(model.H, domain=pyo.NonNegativeReals)
    if sum(n_ps[j] for j in model.J) > 0:
        model.e_ps = pyo.Param(
            model.H,
            initialize={h: float(sum(irradiacion[h, j] * n_ps[j] * datos['Placas solares']['eficiencia']
                                     for j in model.J)) for h in model.H}
        )
        model.n_ps = pyo.Param(
            model.J, initialize={j: float(n_ps[j]) for j in model.J}
        )
    else:
        model.e_ps = pyo.Var(model.H, domain=pyo.NonNegativeReals)
        model.n_ps = pyo.Var(
            model.J,
            within=pyo.NonNegativeIntegers,
            bounds=lambda m, j: (0, int(area_tejado[j]))
        )

    # ---------------------------
    # Restricciones
    # ---------------------------
        def solar_rule(m, h):
            return m.e_ps[h] <= sum(m.g[h, j] * m.n_ps[j] for j in m.J) * 0.2225
        model.SolarLimit = pyo.Constraint(model.H, rule=solar_rule)

    # Limito la potencia máxima que puede dar la BdC aprovechando electricidad de placas y de red
    def p_maxima(m, h):
        if m.climatizacion[h] == 'Calefaccion':
            return (m.e_ps[h] + m.e_red[h] - m.vertido_ps[h]) * cop <= m.p_bdc
        else:
            return (m.e_ps[h] + m.e_red[h] - m.vertido_ps[h]) * err <= m.p_bdc
    model.p_max = pyo.Constraint(model.H, rule=p_maxima)

    # Ecuación del balance térmico para aire acondicionado
    def balance_rule(m, h):
        if m.climatizacion[h] == 'Calefaccion':
            return (m.e_red[h] + m.e_ps[h] - m.vertido_ps[h]) * cop == m.q_ct[h]
        return (m.e_red[h] + m.e_ps[h] - m.vertido_ps[h]) * err * -1 == m.q_ct[h]
    model.Balance = pyo.Constraint(model.H, rule=balance_rule)

    # ---------------------------
    # Objetivo (solo operación)
    # ---------------------------

    def coste_operativo(m):
        return sum(m.e_red[h] * m.precio[h] for h in m.H)
    model.opex = pyo.Expression(rule=coste_operativo)
    model.n_bdc = pyo.Expression(expr=math.ceil(
        datos['Aire acondicionado']['habitaciones'] / datos['Aire acondicionado']['split']))
    model.c_bdc = pyo.Expression(expr=0.24778 * model.p_bdc)
    model.Coste_ud_interior = pyo.Expression(
        expr=datos['Aire acondicionado']['habitaciones'] * datos['Aire acondicionado']['precio Ud. Interior'])
    model.c_ps = pyo.Expression(expr=311 * sum(model.n_ps[j] for j in model.J))

    model.capex = pyo.Expression(
        expr=model.c_bdc + model.Coste_ud_interior + model.c_ps + c_i
    )

    model.OBJ = pyo.Objective(
        expr=model.opex + model.capex / datos['Bomba de calor']['Ciclo de vida'],
        sense=pyo.minimize
    )
    # ---------------------------
    # SOLVER SCIP
    # ---------------------------
    load_dotenv(dotenv_path=".env")
    opt = pyo.SolverFactory(
        "scip",
        executable=os.getenv("RUTA_ARCHIVO")
    )
    opt.solve(model, tee=True)
    # Guardar estado final
    df_results = pd.DataFrame({'Horas': model.H,
                               'cargas': (np.round(pyo.value(model.q_ct[h]), 2) for h in model.H),
                               'e_red': (np.round(pyo.value(model.e_red[h]), 2) for h in model.H),
                               'e_ps': (np.round(pyo.value(model.e_ps[h]), 2) for h in model.H),
                               'Generacion_solar': (np.round(sum(0.2255 * irradiacion[h] * np.array(
                                   list({j: pyo.value(model.n_ps[j]) for j in model.J}.values()))
                               ), 2) for h in model.H)})
    df_results.to_csv("Resultados/resultados_modelo_Aire acondicionado.csv", index=False)
    resultado = {
        "Costo operativo anual": f"{np.round(pyo.value(model.opex), 2)} €",
        "Potencia Bomba de calor": f"{np.round(pyo.value(model.p_bdc)/1000, 2)} kW",
        "placas": np.array(list({j: pyo.value(model.n_ps[j]) for j in model.J}.values())),
        "Inversion": f"{float(np.round(pyo.value(model.capex), 2))} €"
    }
    df_results.set_index(df.index, inplace=True)
    df_results['climatizacion'] = climatizacion
    df_results["ef"] = df_results["climatizacion"].apply(lambda x: err if x == "Refrigeracion" else cop)
    df_results['Q_ac,el'] = df_results['e_red'] * df_results['ef']
    df_results['Q_ac,ps'] = df_results['e_ps'] * df_results['ef']
    df_results['Q_ac'] = df_results['Q_ac,el'] + df_results['Q_ac,ps']
    sns.scatterplot(data=df_results, x=df_results.index, y='Q_ac', s=9, color='red')
    plt.ylabel('Energia [W·h]')
    plt.xlabel("Año")
    plt.savefig('Resultados/Todos los datos Aire acondicionado.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.hour)[['Q_ac,el', 'Q_ac,ps']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_ac,el', 'Q_ac,ps'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value", color='red')
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Hora del día", "Energia [W·h]")
    for ax in g.axes.flatten():
        ax.tick_params(axis='x', labelsize=7)
        plt.setp(ax.get_xticklabels(), rotation=90)
    plt.savefig('Resultados/Discriminación horaria Aire acondicionado.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.month)[['Q_ac']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_ac'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value", color='red')
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Mes del año", "Energia [W·h]")
    plt.savefig('Resultados/Discriminación mensual Aire acondicionado.png')
    plt.close()
    return resultado
