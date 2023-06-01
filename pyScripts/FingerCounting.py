
#Imports
import modules.HandTrackingModule as htm
import cv2
import time
import os
import io
import cv2
import numpy as np
from flask_socketio import emit
from utils.imageFormatting import readb64, encode64

#Ruta de la carpeta de imagenes
folderPath = "img/FingerImages"

#Lista con todos los elementos de la carpeta ordenados
myList = sorted(os.listdir(folderPath))

#Lista que contendrá las imagenes
overlayList = []

#Recorre la lista de los elementos de una carpeta
for imPath in myList:
    #Obtiene las imagenes de la carpeta
    image = cv2.imread(f'{folderPath}/{imPath}')
    #Añade las imagenes a una lista
    overlayList.append(image)


#Almacenará el numero de dedos levantados
totalFingers = 0

# Instancia de la clase HandDetector del módulo HandTrackingModule
detector = htm.HandDetector()

# Función que ejecuta la ruta respectiva al fichero, recive una imagen del WebSocket, la procesa, y la devuelve al WebSocket
def main(data_image):
  # Recivimos la imagen que nos manda el WebSocket
  # Convertimos la imagen base64 a matriz de numpy válida para OpenCV
  frame = readb64(data_image)

  frame = cv2.flip(frame,1)

  # Obtenemos la altura de la imagen para dibujar la línea que separará la referencia de la mano izquierda y de la derecha
  h, w, _ = frame.shape
  # Marcamos el punto que describirá el inicio de la línea
  firstPoint = (int(w/2), 0)
  # Marcamos el punto que describirá el final de la línea
  secondPoint = (int(w/2), h)
  # Dibujamos la línea
  cv2.line(frame, firstPoint, secondPoint, (255, 255, 255), 2)

  # Usamos el método findHands del módulo HandTrackingModule para obtener los landmarks de la imagen
  frame = detector.findHands(frame)

  # Hay que tener en cuenta que findPosition2hand, comprueba primero que haya 2 manos
  # Landmarks de la primera mano
  # Obtenemos la posición de cada landmark
  # Landmarks de la segunda mano
  # Obtenemos la posición de cada landmark
  lmList1, lmList2 = detector.findPositionAux(frame, handNo=[0,1], draw=False)

  # Detectamos que dedos se encuentran arriba con el método fingersUp del HandTrackingModule
  hands = detector.fingersUp(mirror=True)

  if len(hands) == 2:
    # Lista con el id de los dedos que se encuentran alzados (0 para abajo) (1 para arriba)
    hand1, fingers1 = hands[0]
    hand2, fingers2 = hands[1]

    totalFingers1 = fingers1.count(1)
    totalFingers2 = fingers2.count(1)
    totalFingers = totalFingers1 + totalFingers2

    # Si la primera mano es la derecha:
    if hand1 == 'R':
      # Mano derecha
      # Rectangulo y número de dedos a la derecha para la primera mano
      cv2.rectangle(frame, (w, 0), (w-200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers1), (w-150, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
      # Mano Izquierda
      # Rectangulo y número de dedos a la izquierda para la segunda mano
      cv2.rectangle(frame, (0, 0), (200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers2), (50, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
    # Por contrario, si la primera mano es la izquierda:
    elif hand1 == 'L':
      # Mano izquierda
      # Rectangulo y número de dedos a la izquierda para la primera mano
      cv2.rectangle(frame, (0, 0), (200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers1), (50, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
      # Mano Derecha
      # Rectangulo y número de dedos a la derecha para la segunda mano
      cv2.rectangle(frame, (w, 0), (w-200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers2), (w-150, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)

    # Dibujamos el resultado en un rectangulo centrado y abajo de la imagen
    # Si el número total de dedos supera 1 cifra, es decir, 10, debemos tener un rectangulo más grande para que entren 2 cifras
    if totalFingers > 9:
      # Dibujamos el número total de dedos en un rectangulo para 2 cifras
      cv2.rectangle(frame, (int(w/2)-150, h), (int(w/2)+150, h-200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (int(w/2)-100, h-50), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
    else:
      # Dibujamos el número total de dedos en un rectangulo para 1 cifra
      cv2.rectangle(frame, (int(w/2)-100, h), (int(w/2)+100, h-200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (int(w/2)-50, h-50), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)

  elif len(hands) == 1:
    hand, fingers = hands[0]

    # Numeros de 1 que se encuentran en la lista, es decir, números de dedos que se encuentran alzados
    totalFingers = fingers.count(1)

    # En cambio, si no existe la variable totalFingers2, implica que solo hay una mano almacenada en el valor totalFingers directamente
    # La suma se representará en el lado correspondiente a la mano (izq, der)
    # Si la mano es la derecha
    if hand == 'R':
      # Dibujamos el rectangulo con la cifra total de números alzados de la mano a la derecha
      cv2.rectangle(frame, (w, 0), (w-200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (w-150, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
    else:
      # Dibujamos el rectangulo con la cifra total de números alzados de la mano a la izquierda
      cv2.rectangle(frame, (0, 0), (200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (50, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)

  
  
  # Codificamos la imagen en formato base64
  processedImage = encode64(frame)
  # Devolvemos la imagen ya procesada al WebSocket para que se muestre en el cliente
  emit('response_back', processedImage)




















