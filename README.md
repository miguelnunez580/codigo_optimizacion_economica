# SOFTWARE PARA LA OPTIMIZACIÓN ECONÓMICA DE INSTALACIONES DE SISTEMAS DE CLIMATIZACIÓN.

El fin de este repositorio es calcular el sistema de climatización más económico para una vivienda/edificio con unas condiciones estructurales particulares.

El programa pedirá una serie de características y activará el optimizador con el sistema de estudio que se le haya pedido. En caso de querer comprarar entre todas las opciones, el programa los simulará individualmente y, tras comparar entre ellas, seleccionará el sistema más económico.

## Antes de comenzar

Antes de comenzar asegurese de instalar todos los paquetes requeridos en este repositorio.

Se recomienda  crear un entorno vitual .venv e instalar por la terminal el fichero requeriments.txt

```pip install -r requirements.txt```

Asímismo, al emplear el sistema de resolución SciPy de pyomo, deberá descargar su paquete desde internet y con URL: https://www.scipopt.org/index.php#download

Este deberá ir en una carpeta de su sistema local y su ruta deberá ir en un archivo .env que se creará en el repositorio principal. Dento de el habrá que escribir en el siguiente formato y con la ruta al archivo scip.exe (Lo mostrado en la siguiente línea es un ejemplo):
```RUTA_ARCHIVO=C:\SCIP\bin\scip.exe```

## Importación de archivos

El usuario tendrá que introducir datos relativos a las características del edificio y a su ubicación que irán guardados en la carpeta Datos. Estos corresponderán a la temperatura exterior de la localización y a las cargas térmicas del edificio.

Todos los archivos deberán estar en formato .csv y conformados de una sola línea (con los datos específicos que se pidan). Además de ello, todos los ficheros tienen que tener una misma longitud para no generar incongruencias en el cálculo.

Por otro lado, en la propia carpeta datos se podrán encontrar archivos por defecto con precios de luz, precios de gas (ambos en frecuencia horaria y a lo largo de una año. Un total de 8760 datos) y precios de inversión. El usuario podrá modificarlos a su caso particular, pero en todo momento deberá respetar el formato y la disposición de estos.

Finalmente, en la ruta principal se tiene el archivo datos_tecnicos.yaml. En él, se dispondrán los datos técnicos de los equipos de cliamtización. Se dejan datos predeterminados, pero que podrán se rmodificados por el usuario.

## Modo de empleo

Para utilizar el software deberá ejecuta el archivo app.py. Saltará un script en su pantalla en el que se pedirán varios inputs de entrada que el usuario tendrá que rellenar y, al presional el boton "calcular", se ejecutará el optimizador.

Todos los inputs a introducir en la interfaz gráfica serán del tipo numérico salvo la opción "Area del tejado (m2)". En dicha casilla se pide el área de tejado disponible para instalar paneles solares en cada agua del tejado; por tanto, la entrada tendrá que ser una lista de áreas (Ejemplo: Tenemos un tejado a 4 aguas, entonces la entrada "Area del tejado (m2)" será empezando desde el azimut pricipal: ```62,98,62,98```)

El resultado final se mostrará en la ventana principal. No obstante, más datos acerca de la solución optima serán guardados en el repositorio; estos estarán compuestos por archivos .csv con el funcionamiento exacto del sistema de climatización y gráficas del modo de operación óptimo.
