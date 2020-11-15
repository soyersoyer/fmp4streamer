import tornado.web, tornado.ioloop, tornado.websocket  
from picamera import PiCamera, PiVideoFrameType
from string import Template
import io, os, socket, time

# start configuration
serverPort = 8000

camera = PiCamera(sensor_mode=1, resolution='1920x1080', framerate=30)
camera.vflip = True
camera.hflip = True
camera.video_denoise = True

recordingOptions = {
    'format' : 'h264', 
    #'bitrate' : 25000000, 
    'quality' : 20, 
    'profile' : 'high', 
    'level' : '4.2', 
    'intra_period' : 15, 
    'intra_refresh' : 'both', 
    'inline_headers' : True, 
    'sps_timing' : True
}
# end configuration

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 0))
serverIp = s.getsockname()[0]

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def getFile(filePath):
    file = open(filePath,'r')
    content = file.read()
    file.close()
    return content

def templatize(content, replacements):
    tmpl = Template(content)
    return tmpl.substitute(replacements)

appHtml = templatize(getFile('index.html'), {'ip':serverIp, 'port':serverPort, 'fps':camera.framerate})
appJs = getFile('jmuxer.min.js')

class StreamBuffer(object):
    def __init__(self,camera):
        self.frameTypes = PiVideoFrameType()
        self.frame = None
        self.loop = None
        self.buffer = io.BytesIO()
        self.camera = camera

    def setLoop(self, loop):
        self.loop = loop

    def write(self, buf):
        if self.camera.frame.complete and self.camera.frame.frame_type != self.frameTypes.sps_header:
            self.buffer.write(buf)
            self.frame = self.buffer.getvalue()
            self.buffer.seek(0)
            self.buffer.truncate()

            if self.loop is not None:
                self.loop.add_callback(callback=wsHandler.broadcast, message=self.frame)
        else:
            self.buffer.write(buf)

class wsHandler(tornado.websocket.WebSocketHandler):
    connections = []

    def open(self):
        self.connections.append(self)

    def on_close(self):
        self.connections.remove(self)

    def on_message(self, message):
        pass

    @classmethod
    def broadcast(cl, message):
        for connection in cl.connections:
            connection.write_message(message, True)

class htmlHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appHtml)

class jsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(appJs)

requestHandlers = [
    (r"/ws/", wsHandler),
    (r"/", htmlHandler),
    (r"/jmuxer.min.js", jsHandler)
]

try:
    streamBuffer = StreamBuffer(camera)
    camera.start_recording(streamBuffer, **recordingOptions) 
    application = tornado.web.Application(requestHandlers)
    application.listen(serverPort)
    loop = tornado.ioloop.IOLoop.current()
    streamBuffer.setLoop(loop)
    loop.start()
except KeyboardInterrupt:
    camera.stop_recording()
    camera.close()
    loop.stop()