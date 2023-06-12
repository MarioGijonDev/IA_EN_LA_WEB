
# IMPORTS
import modules.HandTrackingModule as htm
import cv2
import numpy as np
import math
import alsaaudio
from PIL import Image
from flask_socketio import emit
from utils.imageFormatting import readb64, encode64

#Variables de alsaaudio
m = alsaaudio.Mixer()
#Crear instancia de la clase HandDetector
detector = htm.HandDetector()

def main(dataImage):
	# Recivimos la imagen que nos manda el WebSocket
  # Convertimos la imagen base64 a matriz de numpy válida para OpenCV
	frame = readb64(dataImage)

	# Usamos el método findHands del módulo HandTrackingModule para obtener los landmarks de la imagen
	frame = detector.findHands(frame)

	# Obtenemos la información de los landmarks (posición en el eje x, y, z en la imagen)
	lmList, _ = detector.findPosition(frame)

	# Comprobamos que se han encontrado landmarks en la imagen (en caso contrario, no podríamos operar con ellos)
	if len(lmList) != 0:
		# Obtenemos la posición de los landmarks de los dedos índice y pulgar. (lmList[dedo][landmark del dedo])
		x1, y1 = lmList[4][1], lmList[4][2]
		x2, y2 = lmList[8][1], lmList[8][2]

		# Obtenemos el punto medio entre ambos (esto definirá el valor 0 del volúmen (mute))
		cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

		# Realizamos los dibujos para que nos sirva de ayuda a la hora de subir y bajar el volúmen
		# Dibujar un circulo en la punta del dedo índice
		cv2.circle(frame, (x1, y1), 15, (255, 0, 0), cv2.FILLED)
		# Dibujar un circulo en la punta del dedo pulgar
		cv2.circle(frame, (x2, y2), 15, (255, 0, 0), cv2.FILLED)
		# Dibujar la línea que une ambos puntos (la longitud de esta línea definirá el % de volúmen)
		cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
		# Dibujar un circulo en el munto medio entre ambos
		cv2.circle(frame, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

		# Distancia entre los dos puntos
		# '|' -> Cateto 1 -> Dedo 1
		# '-' -> Cateto 2 -> Dedo 2
		# '.' -> Hipotenusa -> Distancia entre la punta de los dos dedos -> % volumen
		# 
		# |*
		#	| *
		#	|  *
		# |   *
		# |    *
		# |------
		# Para calcular la hipotenusa, usamos la función hypot de math
		# Pasamospor parametro la diferencia entre las cordenadas x, y de ambos puntos
		lenght = math.hypot(x2 - x1, y2 - y1)

		# Para que sea mas intuitivo, definimos que si la dstancia es menor de 35, dibujemos el circulo intermedio en rojo para definir que está en mute
		# ¿Porque 35 y no 0?, para tener en cuenta que la precisión no siempre es perfecta, y es muy dificil que, con una cámara de baja definición, se vea
		# claramente como los dedos están unidos, por lo que especificamos un rango mínimo de 35, a partir de ahí se supondrá que los dedos están unidos
		if lenght < 35:
			cv2.circle(frame, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

		# La proporción de volumen respecto a la longitud media de la distancia entre ambos dedos
		# range -> min, max
		# Hand range -> 30 - 180
		# Volume range -> 0 - 100
		
		# Para obtener la proporción, usamos la función interp de numpy, que nos devuelve la interpolación de dos rangos conocidos
		# De manera muy básica, la interpolación implica encontrar valores intermedios entre datos existentes, en este caso, rangos
		# Nos devuelve lo que sería la proporción entre la longitud de la mano respecto al mínimo y máximo del volúmen (0-100)
		# Así, podemos aprovechar el rango máximo y mínimo de longitud entre los dedos ya que el promedio máximo de longitud total es de 180% respecto al volumen (100%
		
		# Proporción de volumen respecto a la longitud de los dedos
		vol = int(np.interp(int(lenght), [30, 170], [0, 100]))
		# Proporción de barra de volumen que se muestra en la imagen respecto a la longitud de los dedos
		volBar = int(np.interp(int(lenght), [30, 170], [400, 150]))
		# Proporción del porcentaje de volumen que queremos asignar al pc
		volPer = int(np.interp(int(lenght), [30, 170], [0, 100]))

		# Modificamos el volumen del dispositivo usando la librería de alsaaudio
		# Esta librería ofrece herramientas para acceder a los drivers de audio y poder controlar el volumen del dispositivo linux
		if vol == 0:
			m.setmute(1)
		else:
			m.setmute(0)
			m.setvolume(int(vol))
		
		# Añadimos dibujos para ver el volumen del dispositivo
		# Barra de audio que muestra el mín y máx de audio (0-100%)
		cv2.rectangle(frame, (50, 150), (85, 400), (255, 0, 0), 1)
		# Barra de audio que muestra graficamente el % de volumen actual
		cv2.rectangle(frame, (50, volBar), (85, 400), (255, 0, 0), cv2.FILLED)
		# Muestra la cantidad (número) de % de volumen actual
		cv2.putText(frame, f'{volPer} %', (40,450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
	
	# Codificamos la imagen en formato base64
	processedImage = encode64(frame)
	# Devolvemos la imagen ya procesada al WebSocket para que se muestre en el cliente
	emit('response_back', processedImage)