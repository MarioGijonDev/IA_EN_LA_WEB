#Imports
import cv2
import mediapipe as mp

#########################
# HANDS TRACKING MODULE #
#########################

#Clase HandDetector
class HandDetector():
    #Inicializamos los atributos de la clase
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5,modelComplexity=1,trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.modelComplex = modelComplexity
        self.trackCon = trackCon
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands,self.modelComplex,
                                        self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    #Muestra los datos de las manos
    def findHands(self, img, draw = True):
        #Cambia de BGR a RGB
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #Procesa las imagenes
        self.results = self.hands.process(imgRGB)

        #Muestra las imagenes
        #Si existe resultado
        if self.results.multi_hand_landmarks:
            #Itera el resultado
            for handLms in self.results.multi_hand_landmarks:
                #Si draw es True, mostrar los landmarks de la mano
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)

        return img
    
    #Información de un punto
    def findPosition(self, img, handNo = 0, draw = True):
        #Creamos una lista
        self.lmList = []
        #Miramos que existe el resultado
        if self.results.multi_hand_landmarks:
            #Obtener el resultado de un punto definido
            myHand = self.results.multi_hand_landmarks[handNo]
            #Recorremos el resultado de ese punto
            for id, lm in enumerate(myHand.landmark):
                #Obtenemos el shape (información del punto)
                h, w, c = img.shape
                #Obtenemos las coordenadas en px
                cx, cy = int(lm.x*w), int(lm.y*h)
                #Añadimos el id, cx y cy en la lista
                self.lmList.append([id, cx, cy])
                #Si no queremos dibujarlo, draw será False
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        
        return self.lmList
    
    #Que dedos estan arriba (1) y cuales abajo (0)
    def fingersUp(self, mirror = False):
        #Guardar si el dedo esta subido o no
        fingers = []
        
        #Dedo gordo
        #El dedo gordo funciona respecto a la coordenada del dedo indice, por lo que si está en modo espejo deberá cambiar de > a <
        if mirror :    
            if self.lmList[self.tipIds[0]][1] < self.lmList[self.tipIds[1]-3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[1]-3][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        #Bucle 4 vueltas, porque la posicion 1 es el dedo gordo y se pliega diferente
        for id in range(1, 5):
            #Si el punto 8 en el ejeY es menos que el punto 6 en el ejey de la misma mano
            #Significa que está levantado, ya que openCV usa números negativos máx 0
            #El menos 2 es porque hacemos la comparación con el segundo punto de debajo
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

