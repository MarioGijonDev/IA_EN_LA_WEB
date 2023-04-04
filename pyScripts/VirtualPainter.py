#Imports
from flask import request
import modules.HandTrackingModule as htm
import numpy as np
import time
import os
import io
import base64,cv2
from PIL import Image
from flask_socketio import emit

def readb64(base64_string):
    idx = base64_string.find('base64,')
    base64_string  = base64_string[idx+7:]

    sbuf = io.BytesIO()

    sbuf.write(base64.b64decode(base64_string, ' /'))
    
    pimg = Image.open(sbuf)    

    return cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

#Obtenemos la instancia de la clase Hand Tracking Module
detector = htm.HandDetector(detectionCon=0.85)

#Directorio donde se encuentran las imagenes de las pinturas
folderPath = "img/PainterImages"

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

header = overlayList[5]

#Esta es la imagen superpuesta donde dibujaremos
frameC2 = np.zeros((720, 1280, 3), np.uint8)

#Thickness
brushThickness = 15
cleanThickness = 50

def main(data_image, headerImageColor, lineDrawed):

    xp, yp = 0, 0

    #Color del dibujo
    drawColor = (255, 0, 255)

    color = headerImageColor

    frame = (readb64(data_image))

    #Volteamos la imagen para simular el modo espejo
    frame = cv2.flip(frame, 1)

    #Detectar manos
    frame = detector.findHands(frame)

    #Obtener datos de los dedos
    lmList = detector.findPosition(frame)


    if len(lmList) != 0 :
        
        #Localización ejes x, y para el punto 8 (índice)
        x1, y1 = lmList[8][1:]
        #Localización ejes x, y para el punto 12 (corazón)
        x2, y2 = lmList[12][1:]

        #Recibir valores 
        fingers = detector.fingersUp(mirror = True)

        #Si está el dedo índice y corazón arriba, está en selection mode
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0
            cv2.rectangle(frame, (x1, y1 - 25), (x2, y2 + 25), (255, 0, 255), cv2.FILLED)

            #Comprobar donde está seleccionando de la cabecera
            if y1 < 60:

                if 0 < x1 < 175:
                    color = 'red'
                    
                elif 175 < x1 <= 360:
                    color = 'green'
                    
                if 360 < x1 <= 510:
                    color = 'blue'
                    
                elif 512 < x1 <= 710:
                    color = 'black'
                    
                if 710 < x1 <= 910:
                    color = 'white'
                    
                elif 910 < x1:
                    color = 'clean'

                emit('headerImage', color)
        
        colorInfo = getHeaderImage(color);

        header = colorInfo['header']
        drawColor = colorInfo['drawColor']

        frame[0:55, 0:1280] = header;

        #Si solo el dedo índice está arriba, está en drawing mode
        if fingers[1] and fingers[2] == False:

            xp = int(lineDrawed[0])
            yp = int(lineDrawed[1])

            cv2.circle(frame, (x1, y1), 15, drawColor, cv2.FILLED)

            #Si los dos valores previos son 0, significa que son los valores iniciales y los igualamos a los valores actuales
            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            if(color == 'clean'):
                thickness = cleanThickness
            else:
                thickness = brushThickness


            #Dibujar la linea
            cv2.line(frame, (xp, yp), (x1, y1), drawColor, thickness)
            #Segundo canvas donde se verà el dbujo
            cv2.line(frameC2, (xp, yp), (x1, y1), drawColor, thickness)

            xp, yp = x1, y1

    emit('lineDrawed', [xp, yp])

    # Convertimos el canvas en gris
    imgGray = cv2.cvtColor(frameC2, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, imgInv)
    frame = cv2.bitwise_or(frame, frameC2)

    # Convertimos la imagen en formato jpeg
    imgencode = cv2.imencode('.jpeg', frame,[cv2.IMWRITE_JPEG_QUALITY,40])[1]
    """ imgencodeC2 = cv2.imencode('.jpeg', frameC2,[cv2.IMWRITE_JPEG_QUALITY,40])[1] """

    # base64 encode frame
    stringData = base64.b64encode(imgencode).decode('utf-8')
    b64_src = 'data:image/jpeg;base64,'
    stringData = b64_src + stringData

    # base64 encode canvas
    """ stringDataC2 = base64.b64encode(imgencodeC2).decode('utf-8')
    stringDataC2 = b64_src + stringDataC2 """

    # emit the frame back
    emit('response_back', stringData)

    # emit the frame back
    """ emit('response_back_c2', stringDataC2) """
    

def getHeaderImage(color):
    if color =='red':
        return {'header': overlayList[0], 'drawColor': (0, 0, 255)}
    if color == 'green':
        return {'header': overlayList[1], 'drawColor': (0, 128, 0)}
    if color == 'blue':
        return {'header': overlayList[2], 'drawColor': (255, 0, 0)}
    if color == 'black':
        return {'header': overlayList[3], 'drawColor': (80, 80, 80)}
    if color == 'white':
        return {'header': overlayList[4], 'drawColor': (255, 255, 255)}
    if color == 'clean':
        return {'header': overlayList[5], 'drawColor': (0, 0, 0)}