#!/usr/bin/python3

"""
*******************************************************************
				Tecnologico de Costa Rica
*******************************************************************
	Programador: Esteban Aguero Perez (estape11)
	Lenguaje: Python
	Version: 0.10
	Ultima Modificacion: 21/07/2020
	Descripcion:	
			Dashboard de un Monitor en RT (suave)
*******************************************************************
"""

import tkinter
import os
from PIL import ImageTk, Image
import pandas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import random
from tkinter import messagebox
import sys

ejecucion = True
miniValorAceptado = 15
coordenadas = "10.07499,-84.47144"
# Registro de las ultimas ultimas lecturas
datosSensor1 = {"Hora":[],"Presion":[], "Fecha":[], "ConteoBajas":0, "ConteoAltas":0, "Suma":0}
datosSensor2 = {"Hora":[],"Presion":[], "Fecha":[], "ConteoBajas":0, "ConteoAltas":0, "Suma":0}
alertas = []

def main():
	global directorio, ejecucion, datosSensor1, datosSensor2, alertas
	directorio = os.path.dirname(os.path.realpath(__file__))

	# Se cargan los datos anteriores
	try:
		excelSensor1 = pandas.read_excel(f'{directorio}/sensor1.xlsx')
		excelSensor2 = pandas.read_excel(f'{directorio}/sensor2.xlsx')

		datosSensor1["Hora"] = excelSensor1["Hora"].tolist()
		datosSensor1["Presion"] = excelSensor1["Presion"].tolist()
		datosSensor1["Fecha"] = excelSensor1["Fecha"].tolist()

		datosSensor2["Hora"] = excelSensor2["Hora"].tolist()
		datosSensor2["Presion"] = excelSensor2["Presion"].tolist()
		datosSensor2["Fecha"] = excelSensor2["Fecha"].tolist()

	except Exception as ex:
		print("Datos del excel no cargados")

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

	# Textos dinamicos
	ultimaLecturaSensor1 = tkinter.Label(canvas, text = "00") 
	ultimaLecturaSensor1.config(font =("Courier", 40), bg="#F6F6F6")
	ultimaLecturaSensor1.place(x=120,y=160)
	ultimaLecturaSensor2 = tkinter.Label(canvas, text = "00") 
	ultimaLecturaSensor2.config(font =("Courier", 40), bg="#F6F6F6")
	ultimaLecturaSensor2.place(x=380,y=160)
	#ultimaLecturaSensor1.config(text="25")

	fechaLabel = tkinter.Label(canvas, text = "2020/01/01") 
	fechaLabel.config(font =("Courier", 25), bg="#F6F6F6")
	fechaLabel.place(x=600,y=155)

	horaLabel = tkinter.Label(canvas, text = "00:00:00") 
	horaLabel.config(font =("Courier", 25), bg="#F6F6F6")
	horaLabel.place(x=600,y=205)

	alertaSensor = tkinter.Label(canvas, text = "") 
	alertaSensor.config(font =("Courier", 14), bg="#EFCA43")
	alertaSensor.place(x=850,y=170)

	fechaInicio = tkinter.Entry(canvas)
	fechaInicio.config(font =("Courier", 14), bg="#F6F6F6", width=15)
	fechaInicio.insert(0, ObtenerFecha())
	fechaInicio.place(x=695,y=350)

	fechaFin = tkinter.Entry(canvas)
	fechaFin.config(font =("Courier", 14), bg="#F6F6F6", width=15)
	fechaFin.insert(0, ObtenerFecha())
	fechaFin.place(x=850,y=350)

	horaInicio = tkinter.Entry(canvas)
	horaInicio.config(font =("Courier", 14), bg="#F6F6F6", width=15)
	horaInicio.insert(0, "00:00:00")
	horaInicio.place(x=695,y=415)

	horaFin = tkinter.Entry(canvas)
	horaFin.config(font =("Courier", 14), bg="#F6F6F6", width=15)
	horaFin.insert(0, "23:59:59")
	horaFin.place(x=850,y=415)

	presionFiltroS1 = tkinter.Label(canvas, text = "") 
	presionFiltroS1.config(font =("Courier", 40), bg="#F6F6F6")
	presionFiltroS1.place(x=700,y=500)

	presionFiltroS2 = tkinter.Label(canvas, text = "") 
	presionFiltroS2.config(font =("Courier", 40), bg="#F6F6F6")
	presionFiltroS2.place(x=855,y=500)

	botonFiltrar = tkinter.Button(canvas, text="Filtrar", font="10", width=13, 
			command=lambda:Filtrar(fechaInicio, fechaFin, horaInicio, horaFin, presionFiltroS1, presionFiltroS2))
	botonFiltrar.place(x=695, y=450)
	
	botonReset = tkinter.Button(canvas, text="Reset", font="10", width=13, 
			command=lambda:ResetDatos(fechaInicio, fechaFin, horaInicio, horaFin, presionFiltroS1, presionFiltroS2))
	botonReset.place(x=850, y=450)

	# Datos
	hiloDatos = threading.Thread(target=MonitorDatosRealTime)
	hiloDatos.setDaemon(True)
	hiloDatos.start()

	# Monitor alerta
	hiloAlerta = threading.Thread(target=MonitorAlertas)
	hiloAlerta.setDaemon(True)
	hiloAlerta.start()

	# Monitor de guardado
	hiloGuardado = threading.Thread(target=MonitorGuardado)
	hiloGuardado.setDaemon(True)
	hiloGuardado.start()

	# Datos de las graficas
	datosGraficoSensor1 = {"Hora":[],"Sensor 1":[]}
	datosGraficoSensor2 = {"Hora":[],"Sensor 2":[]}

	# Se crea la instancia del plot
	figuraGraficaRt = plt.Figure(figsize=(5,2))
	eje = figuraGraficaRt.add_subplot(111)
	graficaRt = FigureCanvasTkAgg(figuraGraficaRt, canvas)
	graficaRt.get_tk_widget().place(x=75,y=330)

	ultimaAlerta = ""

	while ( ejecucion ):
		try:
			if ( ventana.winfo_exists() ):
				pass
			else:
				ejecucion = False
				continue

		except Exception as ex:
			ejecucion = False
			continue

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

		# Se actuliza los datos del dashboard
		if ( len(datosSensor1["Presion"]) > 0 and len(datosSensor2["Presion"]) > 0 ):
			ultimaLecturaSensor1.config(text=f'{datosSensor1["Presion"][-1]}')
			ultimaLecturaSensor2.config(text=f'{datosSensor2["Presion"][-1]}')
			fechaLabel.config(text=f'{datosSensor1["Fecha"][-1]}')
			horaLabel.config(text=f'{datosSensor1["Hora"][-1]}')

		# Se actualiza la ultima alerta
		if ( len(alertas) > 0 ):
			alertaSensor.config(text=alertas[-1])
			if ( alertas[-1] != ultimaAlerta ):
				ultimaAlerta = alertas[-1]
				titulo = "Alerta Sensor"
				if ( "Sensor 1" in ultimaAlerta ):
					titulo = "Alerta Sensor 1"

				elif ( "Sensor 2" in ultimaAlerta ):
					titulo = "Alerta Sensor 2"

				messagebox.showerror(titulo,
				 f'{ObtenerFecha()} {ObtenerHora()}: '+
				 "Alerta: La presion ha estado en el nivel minimo por 5 minutos, se sufre riesgo de devastecimiento.",
				 icon="warning")

		# Se borran los datos anteriores
		eje.clear()

		# Se actualizan los datos
		eje.axhline(y=miniValorAceptado)
		datosFrame = pandas.DataFrame(datosGraficoSensor1, columns=['Hora','Sensor 1'])
		datosFrame2 = pandas.DataFrame(datosGraficoSensor2, columns=['Hora','Sensor 2'])
		
		datosFrame = datosFrame[['Hora','Sensor 1']].groupby('Hora').sum()
		datosFrame.plot(kind='line', legend=True, ax=eje, color='c',marker='o', fontsize=6)
		datosFrame2 = datosFrame2[['Hora','Sensor 2']].groupby('Hora').sum()
		datosFrame2.plot(kind='line', legend=True, ax=eje, color='r',marker='o', fontsize=6)

		# Actualiza la grafica
		graficaRt.draw()

		# Se actualiza la ventana
		ventana.update()

	hiloGuardado.join()
	sys.exit()

def ResetDatos(fechaInicio, fechaFin, horaInicio, horaFin, presionFiltroS1, presionFiltroS2):
	fechaInicio.delete(0,"end")
	fechaInicio.insert(0, ObtenerFecha())
	fechaFin.delete(0,"end")
	fechaFin.insert(0, ObtenerFecha())
	horaInicio.delete(0,"end")
	horaInicio.insert(0, "00:00:00")
	horaFin.delete(0,"end")
	horaFin.insert(0, "23:59:59")
	presionFiltroS1.config(text="")
	presionFiltroS2.config(text="")

def Filtrar(fechaInicio, fechaFin, horaInicio, horaFin, presionFiltroS1, presionFiltroS2):
	temp = []
	if ( fechaInicio.get() == fechaFin.get() ):
		temp = BuscarPorHora(horaInicio.get(), horaFin.get(), fechaFin.get())
	
	else:
		temp = BuscarPorFecha(fechaInicio.get(), fechaFin.get())

	presionFiltroS1.config(text="")
	presionFiltroS2.config(text="")

	if ( len(temp) > 0 ):
		presionFiltroS1.config(text=temp[0])
		if ( len(temp) > 1 ):
			presionFiltroS2.config(text=temp[1])
	else:
		
		messagebox.showerror("Alerta",
				"No hay datos en los rangos establecidos, verifique sus entradas.",
				 icon="warning")

def BuscarPorFecha(fechaInicio, fechaFin):
	global datosSensor1, datosSensor2
	temp = []
	tempS1 = 0
	contador1 = 0
	contador2 = 0
	tempS2 = 0

	for i in range(0, len(datosSensor1["Fecha"])):
		if ( FechaMenorIgual(datosSensor1["Fecha"][i], fechaFin) ):
			if ( FechaMayorIgual(datosSensor1["Fecha"][i], fechaInicio) ):
				contador1 += 1
				tempS1 += datosSensor1["Presion"][i]

	for i in range(0, len(datosSensor2["Fecha"])):
		if ( FechaMenorIgual(datosSensor2["Fecha"][i], fechaFin) ):
			if ( FechaMayorIgual(datosSensor2["Fecha"][i], fechaInicio) ):
				contador2 += 1
				tempS2 += datosSensor2["Presion"][i]

	if ( contador1 != 0 ):
		temp.append(f'{round(tempS1/contador1, 2)}')

	if ( contador2 != 0 ):
		temp.append(f'{round(tempS2/contador2, 2)}')

	return temp;

def BuscarPorHora(horaInicio, horaFin, fecha):
	global datosSensor1, datosSensor2
	temp = []
	tempS1 = 0
	contador1 = 0
	contador2 = 0
	tempS2 = 0

	for i in range(0, len(datosSensor1["Hora"])):
		if ( datosSensor1["Fecha"][i] == fecha ):
			if ( HoraAInt(horaInicio) <= HoraAInt(datosSensor1["Hora"][i])  ):
				if ( HoraAInt(datosSensor1["Hora"][i]) <= HoraAInt(horaFin) ):
					contador1 += 1
					tempS1 += datosSensor1["Presion"][i]

	for i in range(0, len(datosSensor2["Hora"])):
		if ( datosSensor2["Fecha"][i] == fecha ):
			if ( HoraAInt(horaInicio) <= HoraAInt(datosSensor2["Hora"][i])  ):
				if ( HoraAInt(datosSensor2["Hora"][i]) <= HoraAInt(horaFin) ):
					contador2 += 1
					tempS2 += datosSensor2["Presion"][i]

	if ( contador1 != 0 ):
		temp.append(f'{round(tempS1/contador1, 2)}')

	if ( contador2 != 0 ):
		temp.append(f'{round(tempS2/contador2, 2)}')

	return temp;

def ObtenerLecturaSensor1():
	temp = {"Presion":random.randint(12, 16),"Hora":ObtenerHora(),"Fecha":ObtenerFecha()}
	return temp

def ObtenerLecturaSensor2():
	temp = {"Presion":random.randint(14, 20),"Hora":ObtenerHora(),"Fecha":ObtenerFecha()}
	return temp

def MonitorDatosRealTime():
	global ejecucion, datosSensor1, datosSensor2

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

		time.sleep(1)

def MonitorAlertas():
	global datosSensor1, datosSensor2, ejecucion, alertas
	while ( ejecucion ):
		if ( datosSensor1["ConteoBajas"] >= 5 ) :
			datosSensor1["ConteoBajas"] = 0
			alertas.append(f'{ObtenerFecha()} {ObtenerHora()}\nSensor 1\n({coordenadas})')

		# Resetea el conteo de lecturas bajas si se obtienen mas de 3 lecturas normales
		if ( datosSensor1["ConteoAltas"] >= 3 ):
			datosSensor1["ConteoBajas"] = 0
			datosSensor1["ConteoAltas"] = 0

		if ( datosSensor2["ConteoBajas"] >= 5 ) :
			datosSensor2["ConteoBajas"] = 0
			alertas.append(f'{ObtenerFecha()} {ObtenerHora()}\nSensor 2\n({coordenadas})')

		# Resetea el conteo de lecturas bajas si se obtienen mas de 3 lecturas normales
		if ( datosSensor2["ConteoAltas"] >= 3 ):
			datosSensor2["ConteoBajas"] = 0
			datosSensor2["ConteoAltas"] = 0

		time.sleep(1)

def MonitorGuardado():
	global datosSensor1, datosSensor2, ejecucion
	while ( ejecucion ):
		datosFrame = pandas.DataFrame(datosSensor1, columns= ["Presion", "Hora", "Fecha"])
		datosFrame.to_excel(f'{directorio}/sensor1.xlsx', index = False, header=True)

		datosFrame2 = pandas.DataFrame(datosSensor2, columns= ["Presion", "Hora", "Fecha"])
		datosFrame2.to_excel(f'{directorio}/sensor2.xlsx', index = False, header=True)
		
		# Cada 2 segundos se guardan los datos
		for i in range(0, 2):
			if ( not ejecucion ):
				break
			time.sleep(i)

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

def FechaAInt(fecha):
	year = 0
	mes = 0
	dia = 0

	try:
		temp = fecha.split('-')
		if ( len(temp) == 3 ):
			year = int(temp[0])
			mes = int(temp[1])
			dia = int(temp[2])

	except Exception as ex:
		pass

	return [year, mes, dia]

def ValidarFecha(year, mes, dia):
	if ( year > 0 ):
		if ( mes <= 12 and mes >= 1 ):
			if ( dia <= 31 and dia >= 1 ):
				return True

	return False

def FechaMayorIgual(fechaA, fechaB):
	# Si fechaA >= fechaB-> True
	yearA, mesA, diaA = FechaAInt(fechaA)
	yearB, mesB, diaB = FechaAInt(fechaB)
	temp = False
	if ( ValidarFecha(yearA, mesA, diaA) and 
		ValidarFecha(yearB, mesB, diaB)):
		if ( yearA == yearB ):
			if ( mesA == mesB ):
				if ( diaA >= diaB ):
					temp = True

				elif ( diaA < diaB ):
					temp = False

			elif ( mesA > mesB ):
				temp = True

			elif ( mesA < mesB ):
				temp = False

		elif ( yearA > yearB ):
			temp = True

		elif ( yearA < yearB ):
			temp = False

	return temp

def FechaMenorIgual(fechaA, fechaB):
	# Si fechaB >= fechaA -> True
	yearA, mesA, diaA = FechaAInt(fechaA)
	yearB, mesB, diaB = FechaAInt(fechaB)
	temp = False
	if ( ValidarFecha(yearA, mesA, diaA) and 
		ValidarFecha(yearB, mesB, diaB)):
		if ( yearA == yearB ):
			if ( mesA == mesB ):
				if ( diaA <= diaB ):
					temp = True

				elif ( diaA > diaB ):
					temp = False

			elif ( mesA < mesB ):
				temp = True

			elif ( mesA > mesB ):
				temp = False

		elif ( yearA < yearB ):
			temp = True

		elif ( yearA > yearB ):
			temp = False

	return temp

def HoraAInt(hora):
		horas = 0
		minutos = 0
		segundos = 0

		try:
			temp = hora.split(':')
			if ( len(temp) == 3 ):
				horas = int(temp[0])
				minutos = int(temp[1])
				segundos = int(temp[2])

		except Exception as ex:
			pass

		return 3600*horas+60*minutos+segundos

main()