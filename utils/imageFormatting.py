
import io
from PIL import Image
import base64,cv2
import numpy as np

# Función para leer una imagen codificada en base64 y convertirla en una imagen válida para OpenCV
def readb64(base64_string):
	# Encontramos el índice donde comienza la cadena "base64,..."
	idx = base64_string.find('base64,')
	# Obtenemos la subcadena después de "base64,"
	base64_string  = base64_string[idx+7:]
	# Crear un objeto BytesIO para escribir los datos decodificados de base64
	sbuf = io.BytesIO()
	# Decodificar la cadena base64 y escribir los datos en el objeto BytesIO
	sbuf.write(base64.b64decode(base64_string, ' /'))
	# Abrir la imagen desde el objeto BytesIO
	img = Image.open(sbuf)
	# Convertir la imagen PIL a un arreglo numpy y cambiar el espacio de color a RGB
	# Este espacio de color es el necesario para el tratamiento de imagenes con cv2
	# Usamos el metodo array de numpy para convertir la instancia de la clase Image, en una imagen en forma de matriz (para poder manipularla con cv2)
	# Devolvemos la imagen ya codificada en una imagen válida para OpenCV
	return cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)

def encode64(frame):
  # Codificamos la imagen a jpeg (de esta manera nos será más sencillo codificarlo a base64) usando el mñetodo b64encode
  imgencode = cv2.imencode('.jpeg', frame,[cv2.IMWRITE_JPEG_QUALITY,40])[1]
  # Codificamos a base64
  # Usamos el método decode() para asegurarnos que es una cadena (str UTF-8)
  stringData = base64.b64encode(imgencode).decode('utf-8')
  # Añadimos la parte inicial de una URL de datos de imagen en base64
  # En este caso, la imagen se trata como un archivo JPEG, por lo que se utiliza 'data:image/jpeg;base64,'
  processedImage = 'data:image/jpeg;base64,' + stringData
  return processedImage