
# IMPORTS
import modules.HandTrackingModule as htm
import cv2
import time
import os
import io
import cv2
import numpy as np
from flask_socketio import emit
from utils.imageFormatting import readb64, encode64

"""
COMENTAMOS ESTO, POR SI SE QUIERE USAR IMÁGENES EN VEZ DE NÚMEROS
#Ruta de la carpeta de imagenes
folderPath = "img/FingerImages"

# Lista con todas las imagenes en la carpeta
myList = sorted(os.listdir(folderPath))

# Lista que contendrá las imagenes
overlayList = []

#Recorre la lista de los elementos de una carpeta
for imPath in myList:
  #Obtiene las imagenes de la carpeta
  image = cv2.imread(f'{folderPath}/{imPath}')
  #Añade las imagenes a la lista creada anteriormente
  overlayList.append(image)
"""


#Almacenará el numero de dedos levantados
totalFingers = 0

# Instancia de la clase HandDetector del módulo HandTrackingModule
detector = htm.HandDetector()

# Función que ejecuta la ruta respectiva al fichero, recive una imagen del WebSocket, la procesa, y la devuelve al WebSocket
def main(dataImage):
  # Recivimos la imagen que nos manda el WebSocket
  # Convertimos la imagen base64 a matriz de numpy válida para OpenCV
  frame = readb64(dataImage)
  # Ponemos la imagen en modo espejo para que sea más intuitivo a la hora de posicionar la mano en la imagen
  frame = cv2.flip(frame,1)

  # Obtenemos la altura de la imagen para dibujar la línea que separará la referencia de la mano izquierda y de la derecha
  h, w, _ = frame.shape
  # Marcamos el punto que describirá el inicio de la línea
  firstPoint = (int(w/2), 0)
  # Marcamos el punto que describirá el final de la línea
  secondPoint = (int(w/2), h)
  # Dibujamos la línea
  cv2.line(frame, firstPoint, secondPoint, (255, 255, 255), 2)

  # Usamos el método findHands del módulo HandTrackingModule para generar los landmarks de la imagen
  frame = detector.findHands(frame)
  # Obtenemos la posición de cada landmark de ambas manos
  # El método findPosition comprueba que haya una segunda mano, en caso contrario se devolverá un array vacío para la segunda mano
  detector.findPosition(frame, handNo=[0,1], draw=False)
  # Detectamos que dedos se encuentran arriba con el método fingersUp del HandTrackingModule
  # Este método devuelve una lista con dos listas en su interior, de esta manera
  #   [[izq/derecha, nºDedos levantados de la primera mano][izq/derecha, nºDedos levantados de la segunda mano]]
  hands = detector.fingersUp(mirror=True)

  # Si el tamaño de la lista es es 2, implica que se han detectado 2 manos, esto hay que tenerlo en cuenta a la hora de contar y mostrar el resultado
  # Esta comprobación será necesaria para no sufrir una excepción "Index out of bounds" al querer acceder a una segunda mano inexistente
  if len(hands) == 2:
    # Obtenemos la orientación de la mano mano (hand) y la cantidad de dedos hacia arriba (fingers)
    #   hand nos indica si es la derecha (R) i la izquierda (L) nos aydará a saber donde dibujar el número en la imagen
    #   fingers es una lista de 0 y 1, donde el 0 indica que el dedo está abajo y el 1, que el dedo está hacia arriba
    # 1º mano
    hand1, fingers1 = hands[0]
    # 2º mano
    hand2, fingers2 = hands[1]

    # Obtenemos la cantidad de números que se encuentran hacia arriba (1)
    # 1º mano
    totalFingers1 = fingers1.count(1)
    # 2º mano
    totalFingers2 = fingers2.count(1)

    # Cantidad total de los dedos que se encuentran hacia arriba
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

  # Si el tamaño de la lista es 1, implica que se han detectado solamente 1 mano
  elif len(hands) == 1:
    # Obtenemos la orientación de la mano (hand) y la cantidad de dedos hacia arriba (fingers)
    hand, fingers = hands[0]

    # Obtenemos la cantidad de números que se encuentran hacia arriba (1)
    totalFingers = fingers.count(1)

    # La suma se representará en el lado correspondiente a la mano (izq, der)
    # Si la mano es la derecha
    if hand == 'R':
      # Dibujamos el rectangulo con la cifra total de números alzados de la mano a la derecha
      cv2.rectangle(frame, (w, 0), (w-200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (w-150, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)
    # Si la mano es la izquierda
    elif hand == 'L':
      # Dibujamos el rectangulo con la cifra total de números alzados de la mano a la izquierda
      cv2.rectangle(frame, (0, 0), (200, 200), (204, 155, 81), cv2.FILLED)
      cv2.putText(frame, str(totalFingers), (50, 155), cv2.FONT_HERSHEY_PLAIN, 10, (255, 255, 255), 15)

  
  
  # Codificamos la imagen en formato base64
  processedImage = encode64(frame)
  # Devolvemos la imagen ya procesada al WebSocket para que se muestre en el cliente
  emit('response_back', processedImage)




















