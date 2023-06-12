
# IMPORTS
from flask import request
import modules.HandTrackingModule as htm
import numpy as np
import time
import os
import io
import base64,cv2
from PIL import Image
from flask_socketio import emit
from utils.imageFormatting import readb64, encode64

# Directorio donde se encuentran las imagenes de las pinturas
# Estás imagenes muestran el color activo que se está pintando o la acción de borrar
folderPath = "img/PainterImages"

# Lista que contendrá todos los nombres de las imagenes de la carpeta ordenados
# 1 -> Rojo
# 2 -> Verde
# 3 -> Azul
# 4 -> Gris
# 5 -> Blanco
# 6 -> Borrar (negro)
myList = sorted(os.listdir(folderPath))

# Lista que contendrá las imagenes renderizadas con cv2
overlayList = []

#Recorre la lista de los elementos del directorio
for imPath in myList:
    # Renderiza las imagenes
    image = cv2.imread(f'{folderPath}/{imPath}')
    # Añade las imagenes a la lista
    overlayList.append(image)

# Seleccionamos la sección de borrar como predeterminada
header = overlayList[5]

# Esta es la imagen superpuesta donde dibujaremos
frameC2 = np.zeros((720, 1280, 3), np.uint8)

# Definimos el grosor del circulo según la acción
# Acción de dibujar
brushThickness = 15
# Acción de borrar
cleanThickness = 110

# Obtenemos la instancia de la clase HandDetector
detector = htm.HandDetector(detectionCon=0.35)

def main(dataImage, headerImageColor, lineDrawed):

	# Color del dibujo predeterminado (negro para borrar)
	drawColor = (255, 0, 255)

	# Obtenemos el color activo que se está usando, se encuentra almacenado en una cookie
	color = headerImageColor

	# Inicializamos las variables que nos servirán para definir donde dibujar en cada frame
	xp, yp = 0,0

	# Recivimos la imagen que nos manda el WebSocket
	# Convertimos la imagen base64 a matriz de numpy válida para OpenCV
	frame = readb64(dataImage)

	# Volteamos la imagen para simular el modo espejo y que sea más intuitivo a la hora de posicionar la mano
	frame = cv2.flip(frame, 1)

	# Usamos el método findHands del módulo HandTrackingModule para generar los landmarks de la imagen
	frame = detector.findHands(frame)

	# Obtenemos la posición de cada landmark de ambas manos
	# Despreciamos el valor de una segunda mano, ya que esta herramienta se aplica solamente a una
	lmList, _ = detector.findPosition(frame, draw=False)

	# En caso de que se haya detectado los landmarks de la mano
	if len(lmList) != 0 :
		# Obtenemos los ejes x, y para el punto 8 (dedo índice)
		x1, y1 = lmList[8][1:]
		# Obtenemos los ejes x, y para el punto 12 (dedo medio)
		x2, y2 = lmList[12][1:]

		# Obtenemos que dedos se encuentran arriba (1) y cuales abajo (0)
		hands = detector.fingersUp(mirror = True)
		# Despreciamos si la mano es la izquierda o la derecha, porque solo nos interesa saber si los dedos índice y medio se encuentran levantados
		_, fingers = hands[0]

		# Si está el dedo índice y medio arriba, está en el modo selección, por lo que no pintaremos
		if fingers[1] and fingers[2]:
			# Reiniciamos las coordenadas activas donde se está pintando
			# Estas coordenadas indican donde se está pintando
			# Si no las reiniciasemos cada vez que entramos en modo selección, cuando volvamos al modo dibujo, continuará desde la coordenada anterior
			# Esto implica que el dibujo sería continuo y no abria separación entre los dibujos
			xp, yp = 0, 0
			# Dibujamos el rectangulo en las coordenadas actuales de los dedos, este rectangulo únirá un dedo con el otro

			cv2.rectangle(frame, (x1, y1 - 25), (x2, y2 + 25), getHeaderImage(color)['drawColor'], cv2.FILLED)

			# Comprobamos si las coordenadas activas del usuario se encuentran en la cabecera
			# la cabecera acaba en el punto 60 del eje y, por lo que si el punto del usuario se encuentra por debajo de 60, es que se encuentra señalando la cabecera
			# De ser así, se comprueba a partir del eje x, que color está seleccionando
			# Cada color comprende un rango según su posición
			if y1 < 60:
				# Rango de selección del color rojo
				if 0 < x1 < 175:
					color = 'red'
				# Rango de selección del color verde
				elif 175 < x1 <= 360:
					color = 'green'
				# Rango de selección del color azul
				elif 360 < x1 <= 510:
					color = 'blue'
				# Rango de selección del color negro (en realidad es gris, el negro es para borrar, pero es un gris oscuro por lo que se entiende que nos referimos al negro)
				elif 512 < x1 <= 710:
					color = 'black'
				# # Rango de selección del color blanco
				elif 710 < x1 <= 910:
					color = 'white'
				# Rango de selección del borrador (es el negro)
				elif 910 < x1:
					color = 'clean'
				# Una vez seleccionado el color, enviamos la información al cliente para que se guarde en una cookie y así no perder la información
				# IMPORTANTE: Recordamos que una conexión HTTP/HTTPS se encuentra aislada de cualquier otra conexión anterior o posterior, por lo que los datos se "olvidan"
				# Es por ello que lo almacenamos en una cookie mediante WebSocket, para evitar la recarga continua para actualizar la cookie
				emit('headerImage', color)
				
		# A esta función le enviamos el nombre del color y nos devuelve la imagen asociada al color y el color en formato BGR para su pintarlo en la imagen
		colorInfo = getHeaderImage(color);

		# Obtenemos la cabecera con el color actual
		header = colorInfo['header']
		# Obtenemos el color actual
		drawColor = colorInfo['drawColor']
		
		# Actualizamos la cabecera en la imagen con el color seleccionado en las coordenadas donde se encuentra la cabecera
		frame[0:55, 0:1280] = header;

		#Si solo el dedo índice está arriba, está en modo dibujo
		if fingers[1] and not fingers[2]:
			# Obtenemos las coordenadas x,y del usuario que recivimos desde el WebSocket y que se encontraba almacenada en la cookie
			# Eje x
			xp = int(lineDrawed[0])
			# Eje y
			yp = int(lineDrawed[1])

			# Dibujamos un circulo en el dedo índice indicando que se está dibujando, el color será el mismo que el seleccionado para dibujar
			cv2.circle(frame, (x1, y1), 15, drawColor, cv2.FILLED)

			# Si los dos valores previos son 0, significa que son los valores iniciales y los igualamos a los valores actuales
			if xp == 0 and yp == 0:
					xp, yp = x1, y1

			# Ajustamos el radio del circulo según si es para borrar o para dibujar
			if(color == 'clean'):
				# Borrar
				thickness = cleanThickness
			else:
				# DIbujar
				thickness = brushThickness


			# Dibujamos una línea entre el punto anterior, que es el que recivimos por el web socket, y el punto actualizado que es la ubicación actual en tiempo real del dedo índice
			# Aunque parezca que el dibujo será todo lineas rectas, al haber tantas líneas como fps, si se ve las imagenes de manera fluida, se verán como se afinan más las curvas
			# En cambio, cuanto menores sean los frames por segundo, mayor se notará que se dibujan lineas rectas de un punto anterior al actual
			cv2.line(frame, (xp, yp), (x1, y1), drawColor, thickness)

			# A consecuencia de que por cada frame, se eliminará la línea anterior por otra nueva, necesitaremos un nuevo canvas donde dibujar
			# Si no actualizasemos la imagen y solo la superpusieramos, obtendriamos copias una de otra sucesivas, y no un dibujo fluido, si no una linea por frame
			# Este nuevo canvas, será donde se guardará cada línea, es decir, no se actualizará el canvas por cada frame, si no que se añadirá una línea por cada frame
			cv2.line(frameC2, (xp, yp), (x1, y1), drawColor, thickness)

			# Guardamos los valores actuales, para repetir este "bucle", donde se guarda la cordenada actual para que sirve de coordenada anterior a la coordenada siguiente (si, es lioso pero es así)
			xp, yp = x1, y1

	# Enviamos los nuevos valores al cliente mediante websocket, estos valores se guardaán en la cookie y serán recividos en la siguiente interacción
	emit('lineDrawed', [xp, yp])

	# Convertimos el canvas del dibujo en escala de grises donde cada color tendrá un nivel de intensidad de brillo
	imgGray = cv2.cvtColor(frameC2, cv2.COLOR_BGR2GRAY)
	# Generamos la imagen binaria inversa del canvas, para ello:
	# Asignamos un umbral de 50: todos los píxeles con un valor de brillo menor a 50 se convierten en 0 (negro) y con el valor mayor o igual a 50 se convierten en 255 (blanco). 
	# Invertimos los colores, por lo que el blanco pasará a negro y el negro a blanco
	# Con esto obtenemos una imagen donde el dibujo en sí será de color negro y el fondo de color blanco
	_, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
	# Convertimos la imagen binaria inversa del canvas a BGR para poder realizar las operaciones bitwise junto con la imagen
	imgInvBrg = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
	# Realizamos la operación bitwise AND entre el frame y la imagen binaria inversa del canvas.
	# 	Para cada píxel de ambas imágenes, se comparan los valores de los bits correspondientes. Si ambos son 1, el resultado será 1 (blanco), de lo contrario, será 0 (negro).
	# Con esto conseguimos mostrar solo los píxeles donde ambas imágenes tengan un valor de 255 (blanco).
	# Esto creará una imagen en la que solo se dibuja (de color negro) en los lugares donde ha pasado el dedo en modo dibujo.
	# Explicación sencilla: Es como si recortasemos con tijeras el dibujo, quedando un hueco de color negro donde debería de estar el dibujo 
	frame = cv2.bitwise_and(frame, imgInvBrg)
	# Realizamos la operación bitwise OR entre el frame obtenido  y el canvas (El canvas no ha sido modificado en ningún momento, sigue siendo fondo negro con el dibujo en color)
	# 	Para cada píxel de ambas imágenes, se comparan los valores de los bits correspondientes. Si al menos uno es 1, el resultado será 1 (blanco), de lo contrario, será 0 (negro).
	# Con esto combinamos los trazos dibujados en el frame con la capa en el canvas.
	# Explicación sencilla: Ponemos el canvas donde se ha dibujado, detrás de la imagen anterior, de manera que donde esté el hueco (negro) se verá el canvas del dibujo con el color real
	# Por esta razón no podemos dibujar el color negro y porqué funciona de borrador
	frame = cv2.bitwise_or(frame, frameC2)

	# Codificamos la imagen en formato base64
	processedImage = encode64(frame)
	# Devolvemos la imagen ya procesada al WebSocket para que se muestre en el cliente
	emit('response_back', processedImage)

	# frameC2 es el canvas con el fondo negro y el dibujo de color, lo comento porque a veces viene bien verlo para entender el proceso
	# processedImageC2 = encode64(frameC2)
	# emit('response_back_c2', processedImageC2)
    

# Le pasamos el nombre del color seleccionado y nos devuelve:
# 	header -> Imagen donde se señalan los colores o el borrador, cada imagen representa un color o el borrador
# 	drawColor -> Color en formato BGR
def getHeaderImage(color):
	if color =='red':
		return {'header': overlayList[0], 'drawColor': (0, 0, 255)}
	if color == 'green':
		return {'header': overlayList[1], 'drawColor': (0, 255, 0)}
	if color == 'blue':
		return {'header': overlayList[2], 'drawColor': (255, 100, 100)}
	if color == 'black':
		return {'header': overlayList[3], 'drawColor': (80, 80, 80)}
	if color == 'white':
		return {'header': overlayList[4], 'drawColor': (255, 255, 255)}
	if color == 'clean':
		return {'header': overlayList[5], 'drawColor': (0, 0, 0)}