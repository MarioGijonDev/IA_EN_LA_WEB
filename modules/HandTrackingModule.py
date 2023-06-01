
# IMPORTS
import cv2
import mediapipe as mp

#########################
# HANDS TRACKING MODULE #
#########################
#Clase HandDetector
class HandDetector():
	#Inicializamos los atributos de la clase
	def __init__(self, mode=False, maxHands=2, detectionCon=0.5,modelComplexity=1,trackCon=0.5):
		# Indica si se debe utilizar el modo de detección simple (false) o complejo (true) de detección.
		self.mode = mode
		# Número máximo de manos que se deben detectar en una imagen.
		self.maxHands = maxHands
		# Similitud mínima requerida para considerar que la detección de una mano es válida (precisión)
		self.detectionCon = detectionCon
		# Complejidad del modelo utilizado para la detección y seguimiento de las manos (0-1)
		self.modelComplex = modelComplexity
		# Similitud mínima requerida para seguir los landmarks
		self.trackCon = trackCon
		# Acceso a los recursos y clases de mediapipe para las manos
		self.mpHands = mp.solutions.hands
		# Instancia de la clase Hands para la detección y seguimiento de manos en tiempo real
		self.hands = self.mpHands.Hands(self.mode, self.maxHands,self.modelComplex, self.detectionCon, self.trackCon)
		# Referencia al modulo draw_utils genérico para dibujar landmarks en una imagen
		self.mpDraw = mp.solutions.drawing_utils
		# Índices de los landmarks que representan las puntas de los dedos (pulgar, índice, medio, anular y meñique) respectivamente
		# Aunque no pertenezca a la clase Hands, son útiles para la realización de herramientas
		self.tipIds = [4, 8, 12, 16, 20]

	# Obtiene los landmarks de las manos, y si quisieramos, los dibujaría en la imagen
	# Solo obtiene los landmarks, no los devuelve, ya que estos landmarks quedarán registrados en la instancia de la clase
	def findHands(self, img, draw = True):
		# Procesa las imagenes y devuelve los landmarks
		# El resultado es una instancia de la clase SolutionOutputs, para acceder a los landmarks debemos acceder al atributo "multi_hand_landmarks"
		# Hay que tener en cuenta que process() no muestra los landmarks, unicamente obtenemos la localización de los landmarks
		# La localización se describe en una array de diccionaros donde cada uno define la posición normalizada (0-1) de un landmark en pixeles:
		#   - Eje x
		#   - Eje y
		#   - Eje z
		self.results = self.hands.process(img)

		# Si existe el atributo "multi_hand_landmarks", es decir, se encuentran landmarks en la imagen
		if self.results.multi_hand_landmarks:
			# Itera el resultado obteniendo accediendo al atributo para obtener los landmarks 
			for handLms in self.results.multi_hand_landmarks:
				# Si draw es True, muesta en la imagen los landmarks de la mano
				if draw:
					# El atributo mpDraw accede al método drawing_utls que dibuja en la imagen sin procesar, los landmarks
					# Este método recibe la imagen sin procesar, los landmarks y el atributo HAND_CONNECTIONS en caso de que queramos que los landmarks estén conectados por una fila linea
					self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
		# Devolvemos la imagen ya procesada, el resultado será la misma imagen pero con los landmarks dibujados 
		return img

	# Nos devuelve una matriz con el id de cada landmark y su posición x,y respectivamente, de la primera mano
	def findPositionAux(self, img, handNo = [0], draw = True):
		# Creamos una lista (acabará siendo una matriz) que almacenará todos los landmarks de la imagen
		self.lmList = [[],[]]
		# Comprobamos que se han detectados landmarks en la imagen
		if self.results.multi_hand_landmarks:
			# Obtenemos los landmarks de una mano (handNo = mano a definir (0 -> Primera en ser detectada))
			for hand in handNo:
				if hand < len(self.results.multi_hand_landmarks):
					myHand = self.results.multi_hand_landmarks[hand]
					# Iteramos sobre los landmarks de la mano
					for id, lm in enumerate(myHand.landmark):
						# Los landmarks están normalizados (>0 y <1), por lo que debemos multiplicarlos por el ancho y alto de la imagen respectivamente
						# Obtenemos el tamaño de la imagen (el valor de c es el número de canales de la imagen, no nos interesa)
						h, w, c = img.shape
						# Obtenemos las coordenadas en pixeles no normalizados del landmark
						cx, cy = int(lm.x*w), int(lm.y*h)
						# Agrupamos en un array el id, cx y cy  del landmark y lo añadimos a la lista
						#   - id: id del landmark
						#   - cx: coordenada x del landmark
						#   - cy: coordenada y del landmark
						self.lmList[hand].append([id, cx, cy])
						# Si no queremos dibujarlo, draw será False
						# El dibujo se genera definiendo en la imagen, las cordenadas del landmark, el tamaño del circulo, y la manera en la que se dibujará (relleno, sin rellenar...)
						if draw:
							cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
						

		# Devolvemos la matriz con la posición de cada landmark de la mano
		return self.lmList
	
	# Devuelve una lista con los dedos que estan hacia arriba (1) y los que estan hacia abajo (0)
	def fingersUp(self, mirror = False):
		# Lista que almacenará la cantidad de dedos que estan arriba y la cantidad de dedos que estan abajo
		hands = []
		fingers = []

		for landmarks in self.lmList:
			fingers = []
			if len(landmarks) == 0: break
			# Comprobamos primero si la mano se encuentra a la derecha o a la izquierda respecto a la mitad de la imagen
			# Con esto, podemos suponer que la que se encuentra a la derecha es la mano derecha y la que se encuentra a la izquierda es la izquierda
			# Si se encuentra a la derecha (mayor al valor intermedio en px de la imagen)
			# Este método tiene por defecto, que la mano detectada sea la derecha
			# Para saber la posición de la mano en la imagen, usamos el punto de referencia de la articuluación de la muñeca
			# lmList[dedo]
			if landmarks[0][1] > 650:
				# Activamos el efecto espejo (sin modo espejo, suponemos que el dedo gordo se encuentra a la izquierda y la mano sería la derecha)
				mirror = True
				# Definimos la mano como la derecha
				hand = 'R'
			else:
				# Desactivamos el efecto espejo (con modo espejo, suponemos que el dedo gordo se encuentra a la derecha y la mano sería la izquierda)
				mirror = False
				# Definimos la mano como la izquierda
				hand = 'L'
			
			#Dedo gordo
			#El dedo gordo funciona respecto a la coordenada del dedo indice, por lo que si está en modo espejo deberá cambiar de > a <
			if mirror :    
				if landmarks[self.tipIds[0]][1] < landmarks[self.tipIds[0]-1][1]:
						fingers.append(1)
				else:
						fingers.append(0)
			else:
				if landmarks[self.tipIds[0]][1] > landmarks[self.tipIds[0]-1][1]:
						fingers.append(1)
				else:
						fingers.append(0)
			
			#Bucle 4 vueltas, porque la posicion 1 es el dedo gordo y se pliega diferente
			for id in range(1, 5):
				#Si el punto 8 en el ejeY es menos que el punto 6 en el ejey de la misma mano
				#Significa que está levantado, ya que openCV usa números negativos máx 0
				#El menos 2 es porque hacemos la comparación con el segundo punto de debajo
				if landmarks[self.tipIds[id]][2] < landmarks[self.tipIds[id]-2][2]:
						fingers.append(1)
				else:
						fingers.append(0)
				
			hands.append([hand, fingers])

		return hands
