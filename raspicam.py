import tornado.web, tornado.ioloop, tornado.websocket
from subprocess import Popen, PIPE
from threading import Thread
import io, os

# start configuration
serverPort = 8000

raspivid = Popen([
    'raspivid',
    '--width', '800',
    '--height', '600',
    '--framerate', '30',
    '--intra', '15',
    '--qp', '20',
    '--level', '4.2',
    '--profile', 'high',
    '--spstimings',
    '--inline',
    '--irefresh', 'both',
    '--nopreview',
    '--timeout', '0',
    '--output', '-'],
    stdin=None, stdout=PIPE)
# end configuration

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def getFile(filePath):
    file = open(filePath,'r')
    content = file.read()
    file.close()
    return content


indexHtml = getFile('index.html')
jmuxerJs = getFile('jmuxer.min.js')

class CameraThread(Thread):
    def __init__(self, raspivid, streamBuffer):
        super(CameraThread, self).__init__()
        self.raspivid = raspivid
        self.streamBuffer = streamBuffer

    def run(self):
        while self.raspivid.poll() is None:
            buf = self.raspivid.stdout.read1()
            self.streamBuffer.write(buf)

class StreamBuffer(object):
    def __init__(self):
        self.loop = None
        self.buffer = io.BytesIO()

    def setLoop(self, loop):
        self.loop = loop

    def write(self, buf):
        lastFrameStart = buf.rfind(b'\x00\x00\x00\x01')
        if lastFrameStart == -1:
            self.buffer.write(buf)
        else:
            self.buffer.write(buf[0:lastFrameStart])
            if self.loop is not None and wsHandler.hasConnections():
                self.loop.add_callback(callback=wsHandler.broadcast, message=self.buffer.getvalue())
            self.buffer.seek(0)
            self.buffer.truncate()
            self.buffer.write(buf[lastFrameStart:])

class wsHandler(tornado.websocket.WebSocketHandler):
    connections = []

    def open(self):
        self.connections.append(self)

    def on_close(self):
        self.connections.remove(self)

    def on_message(self, message):
        pass

    @classmethod
    def hasConnections(cl):
        if len(cl.connections) == 0:
            return False
        return True

    @classmethod
    async def broadcast(cl, message):
        for connection in cl.connections:
            try:
                await connection.write_message(message, True)
            except tornado.websocket.WebSocketClosedError:
                pass
            except tornado.iostream.StreamClosedError:
                pass

class indexHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(indexHtml)

class jmuxerHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/javascript')
        self.write(jmuxerJs)

requestHandlers = [
    (r"/", indexHandler),
    (r"/jmuxer.min.js", jmuxerHandler),
    (r"/ws/", wsHandler),
]

try:
    streamBuffer = StreamBuffer()
    cameraThread = CameraThread(raspivid, streamBuffer)
    cameraThread.start()
    application = tornado.web.Application(requestHandlers)
    application.listen(serverPort)
    loop = tornado.ioloop.IOLoop.current()
    streamBuffer.setLoop(loop)
    loop.start()
except KeyboardInterrupt:
    loop.stop()
