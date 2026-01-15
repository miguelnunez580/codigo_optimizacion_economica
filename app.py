"""Módulo para lanzar el script principal del repositorio"""
from tkinter import filedialog, ttk, messagebox

import os

import tkinter as tk
import pandas as pd
import numpy as np

from optimizador.irradiacion import calculo_irradiacion
from optimizador import inicio_optimizacion
# Variables globales
archivo_precio = pd.read_csv('Datos/Precio_Electrico.csv', sep=',', usecols=[1])/1000
precio_luz = np.array(archivo_precio.iloc[:])
precio_luz = precio_luz.flatten().tolist()

archivo_precio = pd.read_csv('Datos/Precio_Gas.csv', sep=',', usecols=[1])/1000
precio_gas = np.array(archivo_precio.iloc[:])
precio_gas = precio_gas.flatten().tolist()

cargas = None


def salir():
    """Función para cerrar el script"""
    if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
        ventana.quit()


def cargar_archivos(energia: str):
    """Función que importa archivo de precios electricos/gasistas"""
    global precio_luz, precio_gas, cargas  # pylint: disable=W0603
    archivo = filedialog.askopenfilename(
        title="Selecciona un archivo CSV",
        filetypes=[("Archivos CSV", "*.csv")]
    )
    if archivo and energia == 'Luz':
        nombre_archivo = os.path.basename(archivo)
        etiqueta_archivo_precio.config(text=nombre_archivo)
        df = pd.read_csv(archivo, sep=',', usecols=[1])/1000
        precio_luz = np.array(df.iloc[:]).flatten().tolist()
    elif archivo and energia == 'Gas':
        nombre_archivo = os.path.basename(archivo)
        etiqueta_archivo_precio_gas.config(text=nombre_archivo)
        df = pd.read_csv(archivo, sep=',', usecols=[1])/1000
        precio_gas = np.array(df.iloc[:]).flatten().tolist()
    elif archivo and energia == 'Cargas':
        nombre_archivo = os.path.basename(archivo)
        etiqueta_archivo_cargas.config(text=nombre_archivo)
        df = pd.read_csv(archivo)
        cargas = np.array(df.iloc[:]).flatten().tolist()


def etiquetas_placas(*_ignored):
    """Función que abre desplegable de datos para instalar placas solares"""
    etiquetas = [etiqueta_latitud, etiqueta_longitud,
                 etiqueta_azimut, etiqueta_area, etiqueta_aguas]
    entradas = [entrada_latitud, entrada_longitud,
                entrada_azimut, entrada_area, entrada_aguas]

    if valor_placas.get():
        for i, (etiqueta, entrada) in enumerate(zip(etiquetas, entradas)):
            etiqueta.grid(row=8+i, column=1, padx=5, pady=5, sticky="w")
            entrada.grid(row=8+i, column=2, padx=5, pady=5, sticky="e")

    else:
        for i, (etiqueta, entrada) in enumerate(zip(etiquetas, entradas)):
            etiqueta.grid_forget()
            entrada.grid_forget()


def mostrar(textos):
    """Función que muestra texto en el script principal"""
    for widget in frame_tabla.winfo_children():
        widget.destroy()
    for key, value in textos.items():
        etiqueta_resultado = tk.Label(
            frame_tabla, text=f"{key}: {value}", font=("Arial", 14),
            justify="center", anchor="center", wraplength=600
        )
        etiqueta_resultado.pack(fill="x", padx=10, pady=5)


def optimizador():
    """Función que recoge los datos del script principal y lanza el optimizador"""
    if valor_placas.get():
        lat = entrada_latitud.get("1.0", tk.END).strip()
        lon = entrada_longitud.get("1.0", tk.END).strip()
        azimut = entrada_azimut.get("1.0", tk.END).strip()
        # area = entrada_area.get("1.0", tk.END).strip()
        aguas = entrada_aguas.get("1.0", tk.END).strip()
        irradiacion = calculo_irradiacion(lat, lon, int(azimut), int(aguas))
    else:
        irradiacion = pd.DataFrame({'cara_0': [0]*8760})
        aguas = 1
    if cargas is not None:
        # Guardar datos de entrada
        placas = [62, 98, 62, 98]
        aguas = int(aguas)
        actual = combo.get()
        nuevo = combo_nuevo.get()
        refri = valor_refri.get()
        try:
            datos = inicio_optimizacion(precio_luz, precio_gas, cargas, refri,
                                        irradiacion, placas, actual, nuevo, aguas)
            mostrar(datos)
        except Exception as e:
            mostrar({"Error al ejecutar el optimizador.": "Más información en la terminal"})
            raise Exception(f"Error al ejecutar el optimizador: {e}")

    else:
        mostrar({"Error": "Primero debes cargar el archivo de cargas."})


# Ventana principal
ventana = tk.Tk()
ventana.title("Cálculo de Climatización")
ventana.geometry("1000x600")

frame_superior = tk.Frame(ventana)
frame_superior.pack(pady=10)
frame_tabla = tk.Frame(ventana)
frame_tabla.pack(expand=True, fill='both')

# Comandos propios de un script
boton_salir = tk.Button(frame_tabla, text="Salir", command=salir)
boton_salir.pack(side="right", anchor="s", padx=10, pady=10)
# Preguntas iniciales
combo = ttk.Combobox(frame_superior, values=[
                     # readonly evita escritura libre
                     "Otro", "Gas", "Aerotermia de alta", "Aerotermia de baja"], state="readonly")
combo.current(0)  # Seleccionar la primera opción por defecto
combo.grid(row=0, column=1, padx=5, sticky="w")
combo_nuevo = ttk.Combobox(frame_superior, values=[
                           # readonly evita escritura libre
                           "Gas", "Aerotermia de alta", "Aerotermia de baja", "Aire acondicionado", "Todas"],
                           state="readonly")
combo_nuevo.current(0)  # Seleccionar la primera opción por defecto
combo_nuevo.grid(row=1, column=1, padx=5, sticky="w")

boton_precio = tk.Button(
    frame_superior, text="Cargar precio eléctrico", command=lambda: cargar_archivos("Luz"))
boton_precio.grid(row=2, column=0, padx=5, sticky="w")

boton_precio_gas = tk.Button(
    frame_superior, text="Cargar precio gas", command=lambda: cargar_archivos("Gas"))
boton_precio_gas.grid(row=3, column=0, padx=5, sticky="w")


boton_cargas = tk.Button(
    frame_superior, text="Cargar cargas térmicas", command=lambda: cargar_archivos("Cargas"))
boton_cargas.grid(row=4, column=0, padx=5, sticky="w")

boton_calcular = tk.Button(
    frame_superior, text="Calcular", command=optimizador)
boton_calcular.grid(row=5, column=0, padx=5, sticky="w")

# Refrigeración
valor_refri = tk.BooleanVar()
etiqueta_refri = tk.Label(
    frame_superior, text="¿Quieres un sistema con refrigeración?:")
entrada_refri = tk.Checkbutton(frame_superior, variable=valor_refri, height=1)
etiqueta_refri.grid(row=6, column=0, padx=5, sticky="w")
entrada_refri.grid(row=6, column=1, padx=5, sticky="w")

# Placas
valor_placas = tk.BooleanVar()
etiqueta_placas = tk.Label(frame_superior, text="¿Quieres instalar placas?:")
entrada_placas = tk.Checkbutton(
    frame_superior, height=1, variable=valor_placas)
etiqueta_placas.grid(row=7, column=0, padx=5, sticky="w")
entrada_placas.grid(row=7, column=1, padx=5, sticky="w")
valor_placas.trace_add("write", etiquetas_placas)

# Desplegable sí queremos placas
etiqueta_latitud = tk.Label(frame_superior, text="Latitud (º):")
entrada_latitud = tk.Text(frame_superior, height=1, width=20)
etiqueta_longitud = tk.Label(frame_superior, text="Longitud (º):")
entrada_longitud = tk.Text(frame_superior, height=1, width=20)
etiqueta_azimut = tk.Label(frame_superior, text="Azimut (º):")
entrada_azimut = tk.Text(frame_superior, height=1, width=20)
etiqueta_area = tk.Label(frame_superior, text="Área del tejado (m2):")
entrada_area = tk.Text(frame_superior, height=1, width=20)
etiqueta_aguas = tk.Label(frame_superior, text="Número de aguas:")
entrada_aguas = tk.Text(frame_superior, height=1, width=20)

etiqueta_desplegable = tk.Label(
    frame_superior, text="¿Con que sistema de climatizacion cuentas actualmente?", fg="black")
etiqueta_desplegable.grid(row=0, column=0, padx=5, sticky="w")
etiqueta_desplegable_2 = tk.Label(
    frame_superior, text="¿Que opción quieres estudiar?", fg="black")
etiqueta_desplegable_2.grid(row=1, column=0, padx=5, sticky="w")

etiqueta_archivo_precio = tk.Label(
    frame_superior, text="Ningún archivo de precios cargado. Se usarán valores por defecto", fg="black")
etiqueta_archivo_precio.grid(row=2, column=1, padx=5, sticky="w")

etiqueta_archivo_precio_gas = tk.Label(
    frame_superior, text="Ningún archivo de precios cargado. Se usarán valores por defecto", fg="black")
etiqueta_archivo_precio_gas.grid(row=3, column=1, padx=5, sticky="w")

etiqueta_archivo_cargas = tk.Label(
    frame_superior, text="Ningún archivo de cargas térmicas cargado", fg="black")
etiqueta_archivo_cargas.grid(row=4, column=1, padx=5, sticky="w")


ventana.mainloop()
