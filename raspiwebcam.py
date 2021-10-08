import io, os, socketserver
from subprocess import Popen, PIPE
from threading import Thread, Condition
from http import server

import bmff

# start configuration
serverPort = 8000

raspivid = Popen([
    'raspivid',
    '--width', '800',
    '--height', '600',
    '--framerate', '30',
    '--intra', '15',
    '--qp', '20',
    '--irefresh', 'both',
    '--level', '4.2',
    '--profile', 'high',
    '--spstimings',
    '--inline',
    '--nopreview',
    '--timeout', '0',
    '--output', '-'],
    stdout=PIPE)
# end configuration

def getArg(args, arg, defaultValue):
    try:
        pos = args.index("--" + arg)
        return int(args[pos + 1])
    except ValueError:
        return defaultValue


width = getArg(raspivid.args, 'width', 1920)
height = getArg(raspivid.args, 'height', 1080)
framerate = getArg(raspivid.args, 'framerate', 30)

sampleDuration = 500
timescale = framerate*sampleDuration



abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def getFile(filePath):
    file = open(filePath,'r')
    content = file.read()
    file.close()
    return content.encode('utf-8')


indexHtml = getFile('index.html')

class H264NALU:
    DELIMITER = b'\x00\x00\x00\x01'

    NONIDRTYPE = 1
    IDRTYPE = 5
    SPSTYPE = 7
    PPSTYPE = 8

    @staticmethod
    def getType(nalubytes):
        return nalubytes[0] & 0x1f

class MP4Writer:
    seq = 1
    hasIDR = False
    spsNALU = None
    ppsNALU = None

    def __init__(self, w, width, height, timescale, sampleDuration):
        self.w = w
        self.width = width
        self.height = height
        self.timescale = timescale
        self.sampleDuration = sampleDuration

        self.writeHeader()

    def writeHeader(self):
        buf = io.BytesIO()
        bmff.writeFTYP(buf)
        bmff.writeMOOV(buf, self.width, self.height, self.timescale)
        self.w.write(buf.getvalue())

    def addH264NALUs(self, h264nalus):
        # skip the first delimiter, then split to nal units
        nalus = h264nalus[4:].split(H264NALU.DELIMITER)
        self.addNALUs(nalus)

    def addNALUs(self, nalus):
        for nalu in nalus:
            naluType = H264NALU.getType(nalu)
            if naluType == H264NALU.SPSTYPE:
                self.spsNALU = nalu
            elif naluType == H264NALU.PPSTYPE:
                self.ppsNALU = nalu
            elif naluType == H264NALU.IDRTYPE:
                self.hasIDR = True

            # our first frame should have SPS, PPS, IDR NALU, so wait until we have those
            if not (self.hasIDR and self.spsNALU and self.ppsNALU):
                continue

            if naluType == H264NALU.IDRTYPE:
                self.writeFrame([self.spsNALU, self.ppsNALU, nalu], isIDR=True)
            elif naluType == H264NALU.NONIDRTYPE:
                self.writeFrame([nalu], isIDR=False)

    def writeFrame(self, nalus, isIDR):
        buf = io.BytesIO()
        avcNALUs = bmff.nalus2AVC(nalus)
        bmff.writeMOOF(buf, self.seq, avcNALUs.tell(), isIDR, self.sampleDuration)
        bmff.writeMDAT(buf, avcNALUs)
        self.seq = self.seq + 1
        self.w.write(buf.getvalue())


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
        self.nalus = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        lastNALUStart = buf.rfind(H264NALU.DELIMITER)
        if lastNALUStart == -1 or lastNALUStart == 0:
            self.buffer.write(buf)
        else:
            self.buffer.write(buf[0:lastNALUStart])
            with self.condition:
                self.nalus = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
            self.buffer.truncate()
            self.buffer.write(buf[lastNALUStart:])

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
        elif self.path.startswith('/stream.mp4'):
            self.send_response(206)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'video/mp4')
            self.end_headers()
            try:
                mp4Writer = MP4Writer(self.wfile, width, height, timescale, sampleDuration)
                while True:
                    with output.condition:
                        output.condition.wait()
                        nalus = output.nalus
                    mp4Writer.addH264NALUs(nalus)
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
