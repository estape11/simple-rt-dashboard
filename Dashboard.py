import tkinter
import os
from PIL import ImageTk, Image
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import random
from tkinter import messagebox

ejecucion = True
miniValorAceptado = 15

def ObtenerLecturaSensor1():
	temp = {"Presion":random.randint(12, 16),"Hora":ObtenerHora(),"Fecha":ObtenerFecha()}
	return temp

def ObtenerLecturaSensor2():
	temp = {"Presion":random.randint(14, 20),"Hora":ObtenerHora(),"Fecha":ObtenerFecha()}
	return temp

def datosRealTime(canvas):
	global ejecucion, datosSensor1, datosSensor2

	# Datos de las graficas
	datosGraficoSensor1 = {"Hora":[],"Sensor 1":[]}
	datosGraficoSensor2 = {"Hora":[],"Sensor 2":[]}

	# Se crea la instancia del plot
	figuraGraficaRt = plt.Figure(figsize=(5,2))
	eje = figuraGraficaRt.add_subplot(111)

	while ( ejecucion ):
		# Se hace la lectura de los sensores
		lecturaSensor1 = ObtenerLecturaSensor1()
		lecturaSensor2 = ObtenerLecturaSensor2()

		# Se guardan las lecturas
		datosSensor1["Presion"].append(lecturaSensor1["Presion"])
		datosSensor1["Hora"].append(lecturaSensor1["Hora"])
		datosSensor1["Fecha"].append(lecturaSensor1["Fecha"])
		datosSensor1["Suma"] += lecturaSensor1["Presion"]

		datosSensor2["Hora"].append(lecturaSensor2["Hora"])
		datosSensor2["Presion"].append(lecturaSensor2["Presion"])
		datosSensor2["Fecha"].append(lecturaSensor2["Fecha"])
		datosSensor2["Suma"] += lecturaSensor2["Presion"]

		# Se verifica si es una lectura esta debajo del valor aceptado 
		if ( lecturaSensor1["Presion"] < miniValorAceptado ):
			datosSensor1["ConteoBajas"] += 1
		else:
			if ( datosSensor1["ConteoBajas"] != 0 ):
				datosSensor1["ConteoAltas"] += 1
			else:
				datosSensor1["ConteoAltas"] = 0

		if ( lecturaSensor2["Presion"] < miniValorAceptado ):
			datosSensor2["ConteoBajas"] += 1
		else:
			if ( datosSensor2["ConteoBajas"] != 0 ):
				datosSensor2["ConteoAltas"] += 1
			else:
				datosSensor2["ConteoAltas"] = 0

		# Se actualizan los nuevos datos para graficar
		if ( len(datosSensor1["Hora"]) >= 10 ):
			# Toma los ultimos 10
			datosGraficoSensor1["Hora"] = datosSensor1["Hora"][-10:]
			datosGraficoSensor1["Sensor 1"] = datosSensor1["Presion"][-10:]

		else:
			datosGraficoSensor1["Hora"] = datosSensor1["Hora"]
			datosGraficoSensor1["Sensor 1"] = datosSensor1["Presion"]

		if ( len(datosSensor2["Hora"]) >= 10 ):
			# Toma los ultimos 10
			datosGraficoSensor2["Hora"] = datosSensor2["Hora"][-10:]
			datosGraficoSensor2["Sensor 2"] = datosSensor2["Presion"][-10:]

		else:
			datosGraficoSensor2["Hora"] = datosSensor2["Hora"]
			datosGraficoSensor2["Sensor 2"] = datosSensor2["Presion"]

		# Se borran los datos anteriores
		eje.clear()

		# Se actualizan los datos
		eje.axhline(y=miniValorAceptado)
		datosFrame = DataFrame(datosGraficoSensor1, columns=['Hora','Sensor 1'])
		datosFrame2 = DataFrame(datosGraficoSensor2, columns=['Hora','Sensor 2'])
		
		datosFrame = datosFrame[['Hora','Sensor 1']].groupby('Hora').sum()
		datosFrame.plot(kind='line', legend=True, ax=eje, color='c',marker='o', fontsize=6)
		datosFrame2 = datosFrame2[['Hora','Sensor 2']].groupby('Hora').sum()
		datosFrame2.plot(kind='line', legend=True, ax=eje, color='r',marker='o', fontsize=6)

		# Actualiza la grafica
		graficaRt = FigureCanvasTkAgg(figuraGraficaRt, canvas).get_tk_widget().place(x=75,y=330)

		time.sleep(1)

def MonitorAlertas():
	global datosSensor1, datosSensor2, ejecucion
	while ( ejecucion ):
		if ( datosSensor1["ConteoBajas"] >= 5 ) :
			datosSensor1["ConteoBajas"] = 0
			messagebox.showerror("Alerta Sensor 1",
				 f'{ObtenerFecha()} {ObtenerHora()}: '+
				 "Alerta: La presion ha estado en el nivel minimo por 5 minutos, se sufre riesgo de devastecimiento.",
				 icon="warning")

		if ( datosSensor1["ConteoAltas"] >= 3 ):
			datosSensor1["ConteoBajas"] = 0
			datosSensor1["ConteoAltas"] = 0

		if ( datosSensor2["ConteoBajas"] >= 5 ) :
			datosSensor2["ConteoBajas"] = 0
			messagebox.showerror("Alerta Sensor 2",
				 f'{ObtenerFecha()} {ObtenerHora()}: '+
				 "Alerta: La presion ha estado en el nivel minimo por 5 minutos, se sufre riesgo de devastecimiento.",
				 icon="warning")

		if ( datosSensor2["ConteoAltas"] >= 3 ):
			datosSensor2["ConteoBajas"] = 0
			datosSensor2["ConteoAltas"] = 0

		time.sleep(1)

def ObtenerFecha():
	timestampActual = time.localtime(time.time())
	
	temp = ""

	year = timestampActual.tm_year
	temp += str(year) + '-'
	
	mes = timestampActual.tm_mon
	if ( mes < 10 ):
		temp += '0'

	temp += str(mes) + '-'

	dia = timestampActual.tm_mday
	if ( dia < 10 ):
		temp += '0'

	temp += str(dia)

	return temp

def ObtenerHora():
	timestampActual = time.localtime(time.time())
	temp = ""
	hora = timestampActual.tm_hour
	if ( hora < 10 ):
		temp += '0'

	temp += str(hora) + ':'

	minutos = timestampActual.tm_min
	if ( minutos < 10 ):
		temp += '0' 

	temp += str(minutos) + ':'

	segundos = timestampActual.tm_sec
	if ( segundos < 10 ):
		temp += '0'

	temp += str(segundos)

	return temp
		
def main():
	global directorio, ejecucion, datosSensor1, datosSensor2
	directorio = os.path.dirname(os.path.realpath(__file__))

	# Registro de las ultimas ultimas lecturas
	datosSensor1 = {"Hora":[],"Presion":[], "Fecha":[], "ConteoBajas":0, "ConteoAltas":0, "Suma":0}
	datosSensor2 = {"Hora":[],"Presion":[], "Fecha":[], "ConteoBajas":0, "ConteoAltas":0, "Suma":0}

	# Creacion de la ventana
	ventana = tkinter.Tk()
	ventana.geometry('1024x576')
	ventana.resizable(width=False, height=False)
	ventana.title("Sistema de monitoreo en tiempo real | Dashboard")
	canvas = tkinter.Canvas(ventana, width = 1210, height = 610, bg = "white")
	canvas.place(x=-10, y=-10)

	# Fondo del programa
	imagenBg = ImageTk.PhotoImage(Image.open(f'{directorio}/assets/background.png'))
	fondo = tkinter.Label(canvas, image=imagenBg)
	fondo.place(x=8,y=8)

	# Grafico
	hiloDatos = threading.Thread(target=datosRealTime,  args=(canvas,))
	hiloDatos.start()

	# Monitor alerta
	hiloAlerta = threading.Thread(target=MonitorAlertas,)
	hiloAlerta.start()

	ventana.mainloop()

	ejecucion = False
	hiloAlerta.join()
	hiloDatos.join()
	return 0

main()