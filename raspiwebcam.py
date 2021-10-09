import io, os, socketserver
from subprocess import Popen, PIPE
from threading import Thread, Condition
from http import server
from time import time

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
    '--nopreview',
    '--timeout', '0',
    '--output', '-'],
    stdout=PIPE, bufsize=65536)
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
    def __init__(self, w, width, height, timescale, sampleDuration, sps, pps):
        self.seq = 1
        self.sps = sps
        self.pps = pps
        self.start = None
        self.frameBuf = io.BytesIO()

        self.w = w
        self.width = width
        self.height = height
        self.timescale = timescale
        self.sampleDuration = sampleDuration

        self.writeHeader()

        if not self.sps or not self.pps:
            print("MP4Writer: sps, pps NALUs are missing!")

    def writeHeader(self):
        buf = io.BytesIO()
        bmff.writeFTYP(buf)
        bmff.writeMOOV(buf, self.width, self.height, self.timescale, self.sps, self.pps)
        self.w.write(buf.getbuffer())

    def addNALUs(self, nalus):
        for nalu in nalus:
            naluType = H264NALU.getType(nalu)

            # our first frame should have SPS, PPS, IDR NALU, so wait until we have an IDR
            if self.seq == 1 and naluType != H264NALU.IDRTYPE:
                continue

            if naluType == H264NALU.IDRTYPE:
                self.writeFrame([self.sps, self.pps, nalu], isIDR=True)
            elif naluType == H264NALU.NONIDRTYPE:
                self.writeFrame([nalu], isIDR=False)

    def writeFrame(self, nalus, isIDR):
        if self.start == None:
            self.start = time()
        mdatSize = bmff.getMDATsize(nalus)
        self.frameBuf.seek(0)
        self.frameBuf.truncate(bmff.MOOFSIZE + mdatSize)
        decodeTime = int((time() - self.start) * timescale)
        bmff.writeMOOF(self.frameBuf, self.seq, mdatSize, isIDR, self.sampleDuration, decodeTime)
        bmff.writeMDAT(self.frameBuf, nalus)
        self.seq = self.seq + 1
        self.w.write(self.frameBuf.getbuffer())


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
        self.justStarted = True
        self.sps = None
        self.pps = None
        self.nalus = []
        self.prevBuf = bytes()
        self.condition = Condition()

    def write(self, buf):
        nalus = []
        findFrom = 0
        while True:
            NALUStart = buf.find(H264NALU.DELIMITER, findFrom)
            if NALUStart == 0:
                if self.prevBuf:
                    nalus.append(self.prevBuf)
                    self.prevBuf = bytes()
                findFrom = NALUStart + 4
            elif NALUStart > 0:
                nalus.append(self.prevBuf + buf[findFrom:NALUStart])
                self.prevBuf = bytes()
                findFrom = NALUStart + 4
            else:
                self.prevBuf = self.prevBuf + buf[findFrom:]
                break

        if self.justStarted:
            if len(nalus) > 2:
                if H264NALU.getType(nalus[0]) == H264NALU.SPSTYPE:
                    self.sps = nalus[0]
                if H264NALU.getType(nalus[1]) == H264NALU.PPSTYPE:
                    self.pps = nalus[1]
            self.justStarted = False


        if len(nalus):
            with self.condition:
                self.nalus = nalus
                self.condition.notify_all()

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
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'video/mp4; codecs="avc1.640028"')
            self.end_headers()
            try:
                mp4Writer = MP4Writer(self.wfile, width, height, timescale, sampleDuration, output.sps, output.pps)
                while True:
                    with output.condition:
                        output.condition.wait()
                        nalus = output.nalus
                    mp4Writer.addNALUs(nalus)
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
