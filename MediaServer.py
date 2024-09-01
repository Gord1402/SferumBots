import time

import cv2
import numpy as np
from flask import Flask, Response

app = Flask(__name__)

last_frame = None
audio_file_path = ""


def generate_video():
    while True:
        if last_frame is not None:
            img = cv2.imencode('.jpeg', last_frame)[1].tobytes()
            yield (b'--frame\r\n'
                   b'X-Timestamp: ' + str(time.time()).encode() + b"\r\n" +
                   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')


@app.route("/video_stream")
def video_stream_page():
    return Response(generate_video(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/audio_file")
def audio_file_page():
    with open(audio_file_path, "rb") as f:
        return Response(f.read())


class MediaServer:
    def __init__(self, port=5000, width=640, height=480):
        self.port = port
        self.width = width
        self.height = height
        self.last_frame = np.zeros((width, height, 3))
        self.update_stream()

    def add_next_frame(self, frame):
        self.last_frame = frame
        self.update_stream()

    @staticmethod
    def add_audio_path(path):
        global audio_file_path
        audio_file_path = path

    def update_stream(self):
        global last_frame
        last_frame = self.last_frame

    def run(self):
        app.run(host='0.0.0.0', port=self.port, ssl_context='adhoc')
