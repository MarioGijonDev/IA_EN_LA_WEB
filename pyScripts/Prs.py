
from flask_socketio import emit
import io
from PIL import Image
import base64,cv2
import numpy as np
import modules.HandTrackingModule as htm

detector = htm.HandDetector()

def readb64(base64_string):
    idx = base64_string.find('base64,')
    base64_string  = base64_string[idx+7:]

    sbuf = io.BytesIO()

    sbuf.write(base64.b64decode(base64_string, ' /'))
    
    pimg = Image.open(sbuf)    

    return cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

def main(data_image):
  frame = (readb64(data_image))

  """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

  #Detecta las manos de las imagenes
  frame = detector.findHands(frame)

  """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  imgencode = cv2.imencode('.jpeg', frame,[cv2.IMWRITE_JPEG_QUALITY,40])[1]

  # base64 encode
  stringData = base64.b64encode(imgencode).decode('utf-8')
  b64_src = 'data:image/jpeg;base64,'
  stringData = b64_src + stringData

  # emit the frame back
  emit('response_back', stringData)