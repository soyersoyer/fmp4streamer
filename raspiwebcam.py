import io, socketserver, logging
from subprocess import Popen, PIPE
from threading import Thread, Condition
from http import server
from time import time

import bmff

# start configuration
server_port = 8000

raspivid = Popen([
    'raspivid',
    '--width', '800',
    '--height', '600',
    '--framerate', '30',
    '--intra', '15',
    '--qp', '20',
    '--irefresh', 'both',
    '--profile', 'high',
    '--level', '4.2',
    '--nopreview',
    '--timeout', '0',
    '--output', '-'],
    stdout=PIPE, bufsize=65536)
# end configuration

def get_arg(args, arg, default):
    try:
        pos = args.index("--" + arg)
        return type(default)(args[pos + 1])
    except ValueError:
        return default

width = get_arg(raspivid.args, 'width', 1920)
height = get_arg(raspivid.args, 'height', 1080)
framerate = get_arg(raspivid.args, 'framerate', 30)
profile = get_arg(raspivid.args, 'profile', 'high')
level = get_arg(raspivid.args, 'level', '4')

sampleduration = 500
timescale = framerate*sampleduration

profiles = {'high' : '6400', 'main': '4d00', 'baseline': '4200'}
levels = {'4': '28', '4.1': '29', '4.2': '2a'}
codec = 'avc1.' + profiles.get(profile, '6400') + levels.get(level, '28')


def get_index_html():
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>RaspiWebCam</title>
<link rel="icon" href="data:;base64,iVBORw0KGgo=">
<style>
body {{ margin:0; padding:0; background-color:#303030; }}
#stream {{
  max-height: 100%; max-width: 100%; margin: auto; position: absolute;
  top: 0; left: 0; bottom: 0; right: 0;
}}
</style>
</head>
<body>
  <video controls autoplay muted playsinline id="stream">
    <source src="stream.mp4?{int(time())}" type='video/mp4; codecs="{codec}"'>
    <source src="stream.m3u8" type="application/x-mpegURL">
  </video>
</body>
</html>
""".encode('utf-8')

def get_stream_m3u8():
    return f"""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=150000,RESOLUTION={width}x{height},CODECS="{codec}"
streaminf.m3u8
""".encode('utf-8')

def get_streaminf_m3u8():
    return f"""#EXTM3U
#EXT-X-TARGETDURATION:49057
#EXT-X-VERSION:4
#EXTINF:49057.00,
stream.mp4?{int(time())}
#EXT-X-ENDLIST
""".encode('utf-8')


class H264NALU:
    DELIMITER = b'\x00\x00\x00\x01'

    NONIDRTYPE = 1
    IDRTYPE = 5
    SPSTYPE = 7
    PPSTYPE = 8

    @staticmethod
    def get_type(nalubytes):
        return nalubytes[0] & 0x1f

class MP4Writer:
    def __init__(self, w, width, height, timescale, sampleduration, sps, pps):
        self.seq = 1
        self.sps = sps
        self.pps = pps
        self.start = None
        self.framebuf = io.BytesIO()

        self.w = w
        self.width = width
        self.height = height
        self.timescale = timescale
        self.sampleduration = sampleduration

        self.write_header()

        if not self.sps or not self.pps:
            raise ValueError("MP4Writer: sps, pps NALUs are missing!")

    def write_header(self):
        buf = io.BytesIO()
        bmff.write_ftyp(buf)
        bmff.write_moov(buf, self.width, self.height, self.timescale, self.sps, self.pps)
        self.w.write(buf.getbuffer())

    def add_nalus(self, nalus):
        for nalu in nalus:
            nalutype = H264NALU.get_type(nalu)

            # our first frame should have SPS, PPS, IDR NALU, so wait until we have an IDR
            if self.seq == 1 and nalutype != H264NALU.IDRTYPE:
                continue

            if nalutype == H264NALU.IDRTYPE:
                self.write_frame([self.sps, self.pps, nalu], is_idr=True)
            elif nalutype == H264NALU.NONIDRTYPE:
                self.write_frame([nalu], is_idr=False)

    def write_frame(self, nalus, is_idr):
        if self.start == None:
            self.start = time()
        mdatsize = bmff.get_mdat_size(nalus)
        self.framebuf.seek(0)
        decodetime = int((time() - self.start) * timescale)
        bmff.write_moof(self.framebuf, self.seq, mdatsize, is_idr, self.sampleduration, decodetime)
        bmff.write_mdat(self.framebuf, nalus)
        self.seq = self.seq + 1
        self.w.write(self.framebuf.getbuffer()[:bmff.MOOFSIZE + mdatsize])



class CameraThread(Thread):
    def __init__(self, raspivid, streambuffer):
        super(CameraThread, self).__init__()
        self.raspivid = raspivid
        self.streambuffer = streambuffer

    def run(self):
        while self.raspivid.poll() is None:
            buf = self.raspivid.stdout.read1()
            self.streambuffer.write(buf)

class StreamBuffer(object):
    def __init__(self):
        self.juststarted = True
        self.sps = None
        self.pps = None
        self.nalus = []
        self.prevbuf = bytes()
        self.condition = Condition()

    def write(self, buf):
        nalus = buf.split(H264NALU.DELIMITER)
        nalus[0] = self.prevbuf + nalus[0]
        self.prevbuf = nalus.pop()

        if self.juststarted:
            if len(nalus) > 2:
                if len(nalus[0]) == 0:
                    nalus.pop(0)
                if H264NALU.get_type(nalus[0]) == H264NALU.SPSTYPE:
                    self.sps = nalus[0]
                if H264NALU.get_type(nalus[1]) == H264NALU.PPSTYPE:
                    self.pps = nalus[1]
            if not self.sps or not self.pps:
                logging.warning("StreamBuffer: can't read SPS and PPS from the first NALUs")
            self.juststarted = False


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
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'text/html')
            indexhtml = get_index_html()
            self.send_header('Content-Length', len(indexhtml))
            self.end_headers()
            self.wfile.write(indexhtml)
        elif self.path == '/stream.m3u8':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'application/x-mpegURL')
            streamm3u8 = get_stream_m3u8()
            self.send_header('Content-Length', len(streamm3u8))
            self.end_headers()
            self.wfile.write(streamm3u8)
        elif self.path == '/streaminf.m3u8':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'application/x-mpegURL')
            streaminfm3u8 = get_streaminf_m3u8()
            self.send_header('Content-Length', len(streaminfm3u8))
            self.end_headers()
            self.wfile.write(streaminfm3u8)
        elif self.path.startswith('/stream.mp4'):
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', f'video/mp4; codecs="{codec}"')
            self.end_headers()
            try:
                mp4_writer = MP4Writer(self.wfile, width, height, timescale, sampleduration, output.sps, output.pps)
                while True:
                    with output.condition:
                        output.condition.wait()
                        nalus = output.nalus
                    mp4_writer.add_nalus(nalus)
            except Exception as e:
                self.log_message(f'Removed streaming client {self.client_address} {str(e)}')
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
server = StreamingServer(('', server_port), StreamingHandler)
server.start()
