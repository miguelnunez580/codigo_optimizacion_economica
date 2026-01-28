"""Módulo para el cálculo de sistemas de climatización por aerotermia"""
import os
import yaml

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pyomo.environ as pyo

from dotenv import load_dotenv


def calculo_aerotermia(tipo, df, irradiacion, placas, aguas, c_i):
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

    area_tejado = np.array(placas) / (1.909 * 1.134)

    cargas = df["cargas"].to_numpy()
    precio = df["precio_luz"].to_numpy()
    t_ext = df['T_exterior'].to_numpy()
    climatizacion = df['climatizacion'].to_numpy()

    irradiacion = np.array(irradiacion)

    model = pyo.ConcreteModel()

    # ---------------------------
    # Sets
    # ---------------------------
    model.H = pyo.RangeSet(1, horas - 1)
    model.J = pyo.RangeSet(0, aguas - 1)
    # ---------------------------
    # Parámetros
    # ---------------------------
    model.q_ct = pyo.Param(
        model.H,
        initialize={h: float(cargas[h]) for h in model.H}
    )
    model.t_ext = pyo.Param(
        model.H,
        initialize={h: float(t_ext[h]) for h in model.H}
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

    ef = datos["Deposito"]["eficiencia"]
    cop = float(datos[tipo]["cop"])
    err = float(datos[tipo]["err"])
    # ---------------------------
    # Variables
    # ---------------------------
    model.p_bdc = pyo.Var(bounds=(0, datos["Bomba de calor"]["Limite"]))
    model.v_dep = pyo.Var(bounds=(0, datos['Deposito']['Limite']))

    model.e_red = pyo.Var(model.H, bounds=(0, datos["Bomba de calor"]["Limite"]))
    model.e_ps = pyo.Var(model.H, bounds=(0, datos["Bomba de calor"]["Limite"]))
    model.t_int = pyo.Var(model.H, bounds=(5, 85))

    model.n_ps = pyo.Var(
        model.J,
        within=pyo.NonNegativeIntegers,
        bounds=lambda m, j: (0, int(area_tejado[j]))
    )
    # ---------------------------
    # Condiciones de contorno
    # ---------------------------
    model.t_int_prev = pyo.Param(initialize=datos[tipo]['temperatura'])

    # ---------------------------
    # Restricciones
    # ---------------------------
    def solar_rule(m, h):
        return m.e_ps[h] <= sum(m.g[h, j] * m.n_ps[j] for j in m.J) * datos['Placas solares']['eficiencia']
    model.SolarLimit = pyo.Constraint(model.H, rule=solar_rule)

    # Limito la potencia máxima que puede dar la BdC aprovechando electricidad de placas y de red
    def p_maxima(m, h):
        if m.climatizacion[h] == 'Calefaccion':
            return (m.e_ps[h] + m.e_red[h]) * cop <= m.p_bdc
        else:
            return (m.e_ps[h] + m.e_red[h]) * err <= m.p_bdc
    model.p_max = pyo.Constraint(model.H, rule=p_maxima)

    # Ecuación del balance térmico en el depósito de inercia
    def balance_rule(m, h):
        if h == 1:
            return ((m.e_red[h] + m.e_ps[h]) * cop - m.q_ct[h] - m.v_dep * ef * (m.t_int[h] - m.t_ext[h]) ==
                    m.v_dep * 1.136888 * (m.t_int[h] - m.t_int_prev))
        if m.climatizacion[h] == 'Calefaccion':
            return ((m.e_red[h] + m.e_ps[h]) * cop - m.q_ct[h] - m.v_dep * ef * (m.t_int[h] - m.t_ext[h]) ==
                    m.v_dep * 1.136888 * (m.t_int[h] - m.t_int[h-1]))
        return ((m.e_red[h] + m.e_ps[h]) * err * -1 - m.q_ct[h] - m.v_dep * ef * (m.t_int[h] - m.t_ext[h]) ==
                m.v_dep * 1.136888 * (m.t_int[h] - m.t_int[h-1]))
    model.Balance = pyo.Constraint(model.H, rule=balance_rule)

    # Condición temperatura (No puede bajar/subir de la temperatura operacional)
    def temp_lim(m, h):
        if m.climatizacion[h] == 'Calefaccion':
            return m.t_int[h] >= datos[tipo]['temperatura']
        elif m.climatizacion[h] == 'Refrigeracion':
            return m.t_int[h] <= 7.0
    model.temp = pyo.Constraint(model.H, rule=temp_lim)
    # ---------------------------
    # Objetivo (solo operación)
    # ---------------------------

    def coste_operativo(m):
        return sum(m.e_red[h] * m.precio[h] for h in m.H)
    model.opex = pyo.Expression(rule=coste_operativo)

    model.c_bdc = pyo.Expression(expr=0.35849 * model.p_bdc)
    model.c_dep = pyo.Expression(expr=4.08 * model.v_dep)
    model.c_ps = pyo.Expression(expr=311 * sum(model.n_ps[j] for j in model.J))

    model.capex = pyo.Expression(
        expr=model.c_bdc + model.c_dep + model.c_ps + c_i
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
    opt.options['limits/gap'] = 0.01
    opt.solve(model, tee=True)
    # Guardar estado final
    df_results = pd.DataFrame({'cargas': (np.round(pyo.value(model.q_ct[h]), 2) for h in model.H),
                               't_int': (np.round(pyo.value(model.t_int[h]), 2) for h in model.H),
                               'e_red': (np.round(pyo.value(model.e_red[h]), 2) for h in model.H),
                               'e_ps': (np.round(pyo.value(model.e_ps[h]), 2) for h in model.H),
                               'Perdidas_termicas': (np.round(pyo.value(model.v_dep)*ef*(
                                   pyo.value(model.t_int[h]-t_ext[h])), 2) for h in model.H),
                               'Generacion_solar': (np.round(sum(0.2255 * irradiacion[h] * np.array(
                                   list({j: pyo.value(model.n_ps[j]) for j in model.J}.values()))
                               ), 2) for h in model.H)})
    df_results.to_csv(f"Resultados/resultados_modelo_{tipo}.csv", index=False)
    resultado = {
        "Costo anual": f"{np.round(pyo.value(model.opex), 2)} €",
        f"Potencia {tipo}": f"{np.round(pyo.value(model.p_bdc)/1000, 2)} kW",
        "Volumen deposito de inercia": f"{float(np.round(pyo.value(model.v_dep), 2))} L",
        "Placas": np.array(list({j: pyo.value(model.n_ps[j]) for j in model.J}.values())),
        "Inversion": f"{float(np.round(pyo.value(model.capex), 2))}  €"
    }
    df_results.set_index(df.index[1:], inplace=True)
    df_results['climatizacion'] = climatizacion[1:]
    df_results["ef"] = df_results["climatizacion"].apply(lambda x: err if x == "Refrigeracion" else cop)
    df_results['Q_bdc,el'] = df_results['e_red'] * df_results['ef']
    df_results['Q_bdc,ps'] = df_results['e_ps'] * df_results['ef']
    df_results['Q_bdc'] = df_results['Q_bdc,el'] + df_results['Q_bdc,ps']
    df_results['Q_dep'] = pyo.value(model.v_dep) * 1.36888 * (df_results["t_int"])
    sns.scatterplot(data=df_results, x=df_results.index, y='Q_bdc', s=9)
    plt.ylabel('Energia [W·h]')
    plt.xlabel("Año")
    plt.savefig(f'Resultados/Todos los datos {tipo}.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.hour)[['Q_dep', 'Q_bdc,el', 'Q_bdc,ps']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_dep', 'Q_bdc,el', 'Q_bdc,ps'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value")
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Hora del día", "Energia [W·h]")
    for ax in g.axes.flatten():
        ax.tick_params(axis='x', labelsize=7)
        plt.setp(ax.get_xticklabels(), rotation=90)
    g.figure.tight_layout(pad=1)
    plt.savefig(f'Resultados/Discriminación horaria {tipo}.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.month)[['Q_bdc']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_bdc'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value")
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Mes del año", "Energia [W·h]")
    g.figure.tight_layout(pad=1)
    plt.savefig(f'Resultados/Discriminación mensual {tipo}.png')
    plt.close()
    return resultado
