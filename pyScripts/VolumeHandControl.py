#Imports
import modules.HandTrackingModule as htm
import base64, cv2
import time
import numpy as np
import math
import alsaaudio
import io
from PIL import Image
from flask_socketio import emit

def readb64(base64_string):
    idx = base64_string.find('base64,')
    base64_string  = base64_string[idx+7:]

    sbuf = io.BytesIO()

    sbuf.write(base64.b64decode(base64_string, ' /'))
    
    pimg = Image.open(sbuf)    

    return cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

#Variables de alsaaudio
m = alsaaudio.Mixer()

#Crear instancia de la clase HandDetector
detector = htm.HandDetector()

def main(data_image):
    frame = (readb64(data_image))
    cTime = 0
    pTime = 0

    #Detectar manos
    frame = detector.findHands(frame)

    #Obtener datos de los dedos
    lmList = detector.findPosition(frame)

    #Obtener datos de la lista
    if len(lmList) != 0:
        #Mostrar datos de los puntos definidos por consola
        #print(lmList[4], lmList[8])

        #Sacar ejex de cada punto
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]

        #Obtener punto medio entre ambos
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        #Configurar puntos definidos
        cv2.circle(frame, (x1, y1), 15, (255, 0, 0), cv2.FILLED)
        cv2.circle(frame, (x2, y2), 15, (255, 0, 0), cv2.FILLED)
        cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)
        cv2.circle(frame, (cx, cy), 10, (255, 0, 255), cv2.FILLED)

        #Distancia entre los dos puntos
        lenght = math.hypot(x2 - x1, y2 - y1)

        #Mostrar el punto de intermedio entre los dos puntos
        if lenght < 30:
            cv2.circle(frame, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

        #Hand range 30 - 180
        #Volume range 0 - 100
        
        #Proporción de volumen
        vol = int(np.interp(int(lenght), [30, 170], [0, 100]))
        #Proporción de barra de volumen
        volBar = int(np.interp(int(lenght), [30, 170], [400, 150]))
        #Proporción porcentaje de volumen
        volPer = int(np.interp(int(lenght), [30, 170], [0, 100]))

        #Modificamos el volumen del dispositivo
        if vol == 0:
            m.setmute(1)
        else:
            m.setmute(0)
            m.setvolume(int(vol))
        
        #Añadimos dibujos para ver el volumen del dispositivo
        cv2.rectangle(frame, (50, 150), (85, 400), (255, 0, 0), 1)
        cv2.rectangle(frame, (50, volBar), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(frame, f'{volPer} %', (40,450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)


    #Calcular FPS
    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime

    #Mostrar FPS
    cv2.putText(frame, f'FPS: {str(int(fps))}', (15,38), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 1)

    imgencode = cv2.imencode('.jpeg', frame,[cv2.IMWRITE_JPEG_QUALITY,40])[1]

    # base64 encode
    stringData = base64.b64encode(imgencode).decode('utf-8')
    b64_src = 'data:image/jpeg;base64,'
    stringData = b64_src + stringData

    # emit the frame back
    emit('response_back', stringData)