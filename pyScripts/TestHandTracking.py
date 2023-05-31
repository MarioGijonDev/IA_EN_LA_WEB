
# IMPORTS
from flask_socketio import emit
import cv2
import numpy as np
import modules.HandTrackingModule as htm
from utils.imageFormatting import readb64, encode64

# Instancia de la clase HandDetector del módulo HandTrackingModule
detector = htm.HandDetector()

# Función que ejecuta la ruta respectiva al fichero, recive una imagen del WebSocket, la procesa, y la devuelve al WebSocket
def main(data_image):
  # Recivimos la imagen que nos manda el WebSocket
  # Convertimos la imagen base64 a matriz de numpy válida para OpenCV
  frame = readb64(data_image)

  # Usamos el método findHands del módulo HandTrackingModule para obtener los landmarks de la imagen
  frame = detector.findHands(frame)

  # Codificamos la imagen en formato base64
  processedImage = encode64(frame)

  # Devolvemos la imagen ya procesada al WebSocket para que se muestre en el cliente
  emit('response_back', processedImage)
  
  