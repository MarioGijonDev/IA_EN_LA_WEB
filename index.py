
from functools import wraps
from flask import Flask, render_template, Response, make_response, request, session
import requests
from flask_socketio import SocketIO
import pyScripts.TestHandTracking as tht
import pyScripts.FingerCounting as fc
import pyScripts.VolumeHandControl as vhc
import pyScripts.VirtualPainter as vp

# Creamos la app de Flask
app = Flask(__name__)
app.secret_key = 'asdcvbert324$$asd'
# Creamos la instancia del Socket.IO para la conexión concurrente entre cliente y servidor
# Aceptamos todos los dominios
socketio = SocketIO(app,cors_allowed_origins='*')

# Decorador para verificar si el usuario está autenticado
def loginRequired(f):
	# Función interna para obtener la respuesta de autentificación del usuario
	def checkAuth():
		try:
			# Realizamos la solicitud para refrescar y obtener el token de acceso a partir del refresh token del navegador
			# La cookie se encuentra en HTTPOnly y no podemos acceder a ella directamente
			res_token = requests.get('http://localhost:3000/api/v1/auth/refresh', cookies=request.cookies)
			# Pasamos la respuesta a json para poder acceder a la información como si fuese un diccionario python
			token_data = res_token.json()
			# Obtenemos el token que recivimos de la respuesta
			token = token_data.get('token')
			# Comprobamos que finalmente hemos obtenido el token de acceso
			if not token:
				return False
			# Creamos los headers para realizar la solicitud
			headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
			# Realizamos la solicitud para verificar la autenticación enviando el token de acceso
			res = requests.get('http://localhost:3000/api/v1/auth/protected', headers=headers)
			# Pasamos la respuesta a json
			response = res.json()
			# Verificar el estado de la respuesta para determinar si el usuario está autenticado
			if response.get('status') == 'bad':
				return False
			# En caso de que se encontrase autenticado, devolvemos la respuesta que contiene el nombre del usuario
			return response
		except Exception as e:
			# Manejamos cualquier excepción y devolvemos False en caso de error
			print(e)
			return False
	# Utilizamos wraps enviando la función que irá tras usar el decorador
	# Con esto, preservamos el nombre y los metadatos de la función original
	@wraps(f)
	# Esta función es la que se ejecutará "antes" de la función que se define tras usar el decorador
	# Con esto, Conseguimos que se reemplace momentaneamente la función original, por el contenido de la función decorada
	# Si la ejecución del decorador llega hasta el final, devolvemos la función original, esto implica ejecutar el código que fué reemplazado
	# Sencillamente, hacemos un reemplazo momentaneo del código, y si todo va bien, volvemos a reemplazarlo por el original
	# *args permite pasar un número variable de argumentos posicionales como array a una función. 
	# **kwargs permite pasar un número variable de argumentos clave-valor como diccionario
	def decoratedFunction(*args, **kwargs):
		# Obtenemos el resultado de la verificación de autenticación
		response = checkAuth()
		# Si no está autenticado, Mostramos el html informando que no está autenticado y dando la opción de autenticarse
		if not response:
			return render_template('notLoggedIn.html')
		# Almacenamos el nombre de usuario en la sesión para mostrarlo en el index
		session['name'] = response.get('name')
		# Ejecutamos la función original con los argumentos y palabras clave que preservamos anteriormente
		return f(*args, **kwargs)
	
	# Devolvemos la función decorada para que pueda ser ejecutada en las demñás funciones, de lo contrario, solo se ejecutará una vez
	return decoratedFunction



# Índice ##############################################
# Definimos la ruta raiz
@app.route('/', methods=['POST', 'GET'])
# Utilizamos el decorados loginRequired para comprobar que se encuentra autenticado
@loginRequired
# Esta ruta ejecutará el método index
def index():
  # Devolvemos el html index.html del directorio templeates y le enviamos el nombre del usuario almacenado en la sesión
  return render_template('index.html', name=session.get('name'))



# Test Hand Tracking ##############################################
@app.route('/test', methods=['POST', 'GET'])
# Utilizamos el decorador loginRequired para comprobar que se encuentra autenticado
@loginRequired
def test():
  return render_template('test.html')

# Definimos un canal websocket de escucha
# Esta ruta ejecutará el método image_test cada vez que se use el canal image-test
@socketio.on('image-test')
# La función asociada al canal recivirá el parámetro enviado al ejecutar el método emti() desde el cliente
def image_test(dataImage):
  # La función responderá ejecutando el método main de la herramienta correspondiente, en este caso, el main del TestHandTracking
  # Este método será el encargado de procesar la imagen y hacer el emit() para que el cliente reciva el resultado
  Response(tht.main(dataImage))



# Finger Counting ##############################################
@app.route('/finger', methods=['POST', 'GET'])
# Utilizamos el decorador loginRequired para comprobar que se encuentra autenticado
@loginRequired
def fingerCounting():
  return render_template('finger.html')

@socketio.on('image-finger-counting')
def image_fingerCounting(dataImage):
  Response(fc.main(dataImage))



# Volume Control ##############################################
@app.route('/volume', methods=['POST', 'GET'])
# Utilizamos el decorador loginRequired para comprobar que se encuentra autenticado
@loginRequired
def volume():
  return render_template('volume.html')

@socketio.on('image-volume')
def image_volume(dataImage):
  Response(vhc.main(dataImage))



# Virtual Painter ##############################################
@app.route('/painter', methods=['POST', 'GET'])
# Utilizamos el decorador loginRequired para comprobar que se encuentra autenticado
@loginRequired
def painter():
  # Creamos la respuesta
  resp = make_response(render_template('painter.html'))
  # Inicializamos los valores de las cookies necesarias
  # El header por defecto es el de borrar
  resp.set_cookie('headerImage', 'clean')
  # Inicializamos las posiciones activas a 0
  resp.set_cookie('xp', '0')
  resp.set_cookie('yp', '0')
  # Devolvemos la respuesta, que contiene el html y las cookies que se agregaran al navegador del cliente
  return resp

@socketio.on('image-painter')
def image_painter(dataImage):
  # La única diferencia en este caso es que el dataImage es un array con la imagen, el header, y la pocisición activate del usuario
  Response(vp.main(dataImage['image'], dataImage['headerImage'], dataImage['lineDrawed']))


# Ejecutar main ##############################################
if __name__ == '__main__':
  app.run(debug=True, host='localhost', port='5000')


