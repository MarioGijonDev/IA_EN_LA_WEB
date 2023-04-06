from flask import Flask, render_template, Response, make_response
from flask_socketio import SocketIO
import pyScripts.TestHandTracking as tht
import pyScripts.FingerCounting as fc
import pyScripts.VolumeHandControl as vhc
import pyScripts.VirtualPainter as vp
import pyScripts.Prs as prs
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app,cors_allowed_origins='*')

# Índice ##############################################
@app.route('/', methods=['POST', 'GET'])
@cross_origin(supports_credentials=True)
def index():
    return render_template('index.html')

# Test Hand Tracking ##############################################
@app.route('/test', methods=['POST', 'GET'])
def test():
    return render_template('test.html')

@socketio.on('image-test')
def image_test(data_image):
    Response(tht.main(data_image))

# Finger Counting ##############################################
@app.route('/finger', methods=['POST', 'GET'])
def fingerCounting():
    return render_template('finger.html')

@socketio.on('image-finger-counting')
def image_fingerCounting(data_image):
    Response(fc.main(data_image))

# Volume Control ##############################################
@app.route('/volume', methods=['POST', 'GET'])
def volume():
    return render_template('volume.html')

@socketio.on('image-volume')
def image_volume(data_image):
    Response(vhc.main(data_image))

# Virtual Painter ##############################################
@app.route('/painter', methods=['POST', 'GET'])
def painter():
    resp = make_response(render_template('painter.html'))
    resp.delete_cookie('headerImage')
    resp.delete_cookie('xp')
    resp.delete_cookie('yp')
    resp.set_cookie('headerImage', 'clean')
    resp.set_cookie('xp', '0')
    resp.set_cookie('yp', '0')
    return resp

@socketio.on('image-painter')
def image_painter(data_image):
    Response(vp.main(data_image['image'], data_image['headerImage'], data_image['lineDrawed']))


# Paper Rock Scissors ##############################################
@app.route('/prs', methods=['POST', 'GET'])
def Prs():
    return render_template('prs.html')

@socketio.on('image-prs')
def image_prs(data_image):
    Response(prs.main(data_image))

# EXEC MAIN ##############################################
if __name__ == '__main__':
    app.run(debug=True)


