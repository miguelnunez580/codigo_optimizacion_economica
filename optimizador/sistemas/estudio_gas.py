"""Módulo para el cálculo de sistemas de climatización por gas"""
import os
import yaml

import numpy as np
import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import seaborn as sns

from dotenv import load_dotenv


def calculo_gas(df, c_i):
    """Funcion para la optimización económica de sistemas de climatización por gas

    :param df: Dataframe con todos los parámetros que tienen carácter horario
    :param c_i: Coste invariable de la instalación sin tener en cuenta el precio de la caldera de gas
    """
    with open('datos_tecnicos.yaml', "r", encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    horas = len(df)

    cargas = df["cargas"].to_numpy()
    precio = df["precio_gas"].to_numpy()
    ef = datos['Gas']['eficiencia']
    # Asegúrate que t_ext tiene la longitud horas; aquí lo preparo como vector:

    model = pyo.ConcreteModel()

    # ---------------------------
    # Sets
    # ---------------------------
    model.H = pyo.RangeSet(0, horas - 1)
    # ---------------------------
    # Parámetros
    # ---------------------------
    model.q_ct = pyo.Param(
        model.H,
        initialize={h: float(cargas[h]) for h in model.H}
    )
    model.precio = pyo.Param(
        model.H,
        initialize={h: float(precio[h]) for h in model.H}
    )
    # ---------------------------
    # Variables
    # ---------------------------
    model.q_cg = pyo.Var(model.H, domain=pyo.NonNegativeReals)
    model.p_gas = pyo.Var(bounds=(0, np.inf))

    def p_maxima(m, h):
        return m.q_cg[h] <= m.p_gas
    model.p_max = pyo.Constraint(model.H, rule=p_maxima)

    def balance_rule(m, h):
        return m.q_cg[h] * ef == m.q_ct[h]
    model.Balance = pyo.Constraint(model.H, rule=balance_rule)

    def coste_operativo(m):
        return sum(m.q_cg[h] * m.precio[h] for h in m.H)
    model.opex = pyo.Expression(rule=coste_operativo)
    model.c_cg = pyo.Expression(expr=0.05968 * model.p_gas)

    model.capex = pyo.Expression(
        expr=model.c_cg + c_i
    )
    model.OBJ = pyo.Objective(
        expr=model.opex + model.capex / datos['Gas']['Ciclo de vida'],
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
    df_results = pd.DataFrame({'Horas': model.H,
                               'cargas': (np.round(pyo.value(model.q_ct[h]), 2) for h in model.H),
                               'Q_cg': (np.round(pyo.value(model.q_cg[h]), 2) for h in model.H)})
    df_results.to_csv("resultados_modelo.csv", index=False)
    resultado = {
        "Costo anual": f"{np.round(pyo.value(model.opex), 2)} €",
        "Potencia Caldera de gas": f"{np.round(pyo.value(model.p_gas)/1000, 2)} kW",
        "Inversion": f"{float(np.round(pyo.value(model.capex), 2))} €"
    }
    df_results.set_index(df.index, inplace=True)
    sns.scatterplot(data=df_results, x=df_results.index, y='Q_cg', s=9, color='grey')
    plt.ylabel('Energia [W·h]')
    plt.xlabel("Año")
    plt.savefig('Todos los datos Gas.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.hour)[['Q_cg']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_cg'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value", color='grey')
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Hora del día", "Energia [W·h]")
    for ax in g.axes.flatten():
        ax.tick_params(axis='x', labelsize=7)
        plt.setp(ax.get_xticklabels(), rotation=90)
    plt.savefig('Discriminación horaria gas.png')
    plt.close()

    data = df_results.groupby(by=df_results.index.month)[['Q_cg']].mean()
    data.reset_index(inplace=True)
    data = pd.melt(data, id_vars=data.columns[0], value_vars=['Q_cg'])
    g = sns.FacetGrid(data, col="variable", sharey=False)
    g.map(sns.barplot, data.columns[0], "value", color='grey')
    g.set_titles(col_template="{col_name}")
    g.set_axis_labels("Mes del año", "Energia [W·h]")
    plt.savefig('Discriminación mensual Gas.png')
    plt.close()
    return resultado
