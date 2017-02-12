import os
import json
from flask import Flask, request, render_template, session, flash, redirect, \
    url_for, jsonify

from flask_socketio import SocketIO, emit, disconnect
from celery import Celery
from db import Influx

# Flask configuration
app = Flask(__name__)
#app.config['SECRET_KEY'] = ''

# SocketIO configuration
async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# InfluxDB configuration
influx = Influx()

@app.route('/')
def index():
    temp = influx.query_measurement_distinct_tag("temp", "id")
    server_array = [[1,2,3,4,5,6,7,8,9,10,11],[4,5,6,7,8,9,10,11,12,13,11],[4,5,6,7,8,9,10,11,12,13,11]]
    return render_template('index.html', async_mode=socketio.async_mode,
                            temp=temp, server_array=server_array)

def background_thread():
    while True:
        socketio.sleep(2)
        temp = influx.query_measurement_distinct_tag("temp", "id")
        temp = json.dumps(temp)
        temp_mean = influx.get_mean("temp", "id", "temperature")
        socketio.emit('background_thread', {'temp': temp, 'temp_mean': temp_mean},)

@socketio.on('connect')
def connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    app.run(debug=True)
    socketio.run(app)