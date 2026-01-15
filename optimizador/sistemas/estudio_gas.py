"""Módulo para el cálculo de sistemas de climatización por gas"""
import os
import yaml

import numpy as np
import pandas as pd
import pyomo.environ as pyo

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
    model.q_cg = pyo.Var(model.H, bounds=(0, datos["Bomba de calor"]["Limite"]))
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
                               'Q_caldera': (np.round(pyo.value(model.q_cg[h]), 2) for h in model.H)})
    df_results.to_csv("resultados_modelo.csv", index=False)
    resultado = {
        "Costo anual": f"{np.round(pyo.value(model.opex), 2)} €",
        "Potencia Caldera de gas": f"{np.round(pyo.value(model.p_gas), 2)} W",
        "Inversion": f"{float(np.round(pyo.value(model.capex), 2))} €"
    }
    return resultado
