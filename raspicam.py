import io, os, socketserver
from subprocess import Popen, PIPE
from threading import Thread, Condition
from http import server

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
    stdout=PIPE)
# end configuration

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def getFile(filePath):
    file = open(filePath,'r')
    content = file.read()
    file.close()
    return content.encode('utf-8')


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
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        lastFrameStart = buf.rfind(b'\x00\x00\x00\x01')
        if lastFrameStart == -1 or lastFrameStart == 0:
            self.buffer.write(buf)
        else:
            self.buffer.write(buf[0:lastFrameStart])
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
            self.buffer.truncate()
            self.buffer.write(buf[lastFrameStart:])

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(indexHtml))
            self.end_headers()
            self.wfile.write(indexHtml)
        elif self.path == '/jmuxer.min.js':
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript')
            self.send_header('Content-Length', len(jmuxerJs))
            self.end_headers()
            self.wfile.write(jmuxerJs)
        elif self.path == '/stream.h264':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'video/h264')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(frame)
            except Exception as e:
                print('Removed streaming client', self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    def start(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

output = StreamBuffer()
cameraThread = CameraThread(raspivid, output)
cameraThread.start()
server = StreamingServer(('', serverPort), StreamingHandler)
server.start()
