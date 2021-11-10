import io, socketserver, logging, configparser, getopt, sys
from threading import Thread
from http import server
from time import time

import bmff
from v4l2camera import V4L2Camera, H264NALU

def get_index_html(codec):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>fmp4streamer</title>
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
'''.encode('utf-8')

def get_stream_m3u8(width, height, codec):
    return f'''#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=150000,RESOLUTION={width}x{height},CODECS="{codec}"
streaminf.m3u8
'''.encode('utf-8')

def get_streaminf_m3u8():
    return f'''#EXTM3U
#EXT-X-TARGETDURATION:49057
#EXT-X-VERSION:4
#EXTINF:49057.00,
stream.mp4?{int(time())}
#EXT-X-ENDLIST
'''.encode('utf-8')


class MP4Writer:
    def __init__(self, w, width, height, timescale, sps, pps):
        if not sps or not pps:
            raise ValueError('MP4Writer: sps, pps NALUs are missing!')

        self.seq = 0
        self.sps = sps
        self.pps = pps
        self.start_secs = 0
        self.start_usecs = 0

        self.framebuf = io.BytesIO()

        self.w = w
        self.width = width
        self.height = height
        self.timescale = timescale
        self.timescaleusec = timescale / 1000000
        self.decodetime = 0
        self.prevtime = 0

        self.write_header()


    def write_header(self):
        buf = io.BytesIO()
        bmff.write_ftyp(buf)
        bmff.write_moov(buf, self.width, self.height, self.timescale, self.sps, self.pps)
        self.w.write(buf.getbuffer())

    def add_nalu(self, frame_data, frame_secs, frame_usecs):
        nalutype = H264NALU.get_type(frame_data)

        # our first frame should have SPS, PPS, IDR NALU, so wait until we have an IDR
        if self.seq == 0 and nalutype != H264NALU.IDRTYPE:
            return

        if nalutype == H264NALU.IDRTYPE:
            self.write_frame([self.sps, self.pps, frame_data], frame_secs, frame_usecs, is_idr=True)
        elif nalutype == H264NALU.NONIDRTYPE:
            self.write_frame([frame_data], frame_secs, frame_usecs, is_idr=False)

    def write_frame(self, nalus, frame_secs, frame_usecs, is_idr):
        if self.seq == 0:
            self.start_secs = frame_secs
            self.start_usecs = frame_usecs
            sampleduration = 1
        else:
            sampleduration = round(
                (frame_secs - self.start_secs) * self.timescale +
                (frame_usecs - self.start_usecs) * self.timescaleusec -
                self.decodetime)

        mdatsize = bmff.get_mdat_size(nalus)
        self.framebuf.seek(0)
        bmff.write_moof(self.framebuf, self.seq, mdatsize, is_idr, sampleduration, self.decodetime)
        bmff.write_mdat(self.framebuf, nalus)
        self.w.write(self.framebuf.getbuffer()[:bmff.MOOFSIZE + mdatsize])

        self.seq += 1
        self.decodetime += sampleduration


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
            indexhtml = get_index_html(config.codec())
            self.send_header('Content-Length', len(indexhtml))
            self.end_headers()
            self.wfile.write(indexhtml)
        elif self.path == '/stream.m3u8':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Type', 'application/x-mpegURL')
            streamm3u8 = get_stream_m3u8(config.width(), config.height(), config.codec())
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
            self.send_header('Content-Type', f'video/mp4; codecs="{config.codec()}"')
            self.end_headers()
            try:
                mp4_writer = MP4Writer(self.wfile, config.width(), config.height(), config.timescale(), camera.sps, camera.pps)
                camera.request_key_frame()
                while True:
                    with camera.condition:
                        camera.condition.wait()
                        frame_data = camera.frame_data
                        frame_secs = camera.frame_secs
                        frame_usecs = camera.frame_usecs
                    mp4_writer.add_nalu(frame_data, frame_secs, frame_usecs)
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


class V4L2CameraThread(Thread):
    def __init__(self, camera):
        super(V4L2CameraThread, self).__init__()
        self.camera = camera

    def run(self):
        self.camera.start_capturing()

    def stop(self):
        self.camera.stop_capturing()

class Config(configparser.ConfigParser):
    def __init__(self, configfile):
        super(Config, self).__init__({
            'width': 800,
            'height': 600,
            'fps': 30,
        })
        self.read_dict({'server': {'listen': '', 'port': 8000}})

        if len(self.read(configfile)) == 0:
            logging.warning(f'Couldn\'t read {configfile}, using default config')

        if len(self.sections()) == 1:
            self.add_section('/dev/video0')

        self.device = self.get_devices()[0]

    def get_devices(self):
        return [s for s in self.sections() if s != 'server']

    def get_device(self):
        return self.device

    def width(self):
        return int(self[self.device]['width'])

    def height(self):
        return int(self[self.device]['height'])

    def fps(self):
        return int(self[self.device]['fps'])

    def sampleduration(self):
        return 500

    def timescale(self):
        return self.fps() * self.sampleduration()

    def h264_profile(self):
        return self[self.device].get('h264_profile', 'High')

    def h264_level(self):
        return self[self.device].get('h264_level', '4')

    def codec(self):
        profiles = {'High' : '6400', 'Main': '4d00', 'Baseline': '4200'}
        levels = {'4': '28', '4.1': '29', '4.2': '2a'}
        codec = 'avc1.' + profiles.get(self.h264_profile(), '6400') + levels.get(self.h264_level(), '28')
        return codec

def usage():
    print(f'usage: python3 {sys.argv[0]} [--help] [--list-controls] [--config CONFIG]\n')
    print(f'optional arguments:')
    print(f'  -h, --help                  show this help message and exit')
    print(f'  -l, --list-controls         list the v4l2 controls and values for the camera')
    print(f'  -c CONFIG, --config CONFIG  use CONFIG as a config file, default: fmp4streamer.conf')


try:
    arguments, values = getopt.getopt(sys.argv[1:], "hlc:", ["help", "list-controls","config="])
except getopt.error as err:
    print(err)
    usage()
    sys.exit(2)

list_controls = False
configfile = "fmp4streamer.conf"

for current_argument, current_value in arguments:
    if current_argument in ('-h', '--help'):
        usage()
        sys.exit(0)
    elif current_argument in ("-l", "--list-controls"):
        list_controls = True
    elif current_argument in ("-c", "--config"):
        configfile = current_value

config = Config(configfile)
device = config.get_device()

camera = V4L2Camera(device, dict(config.items(device)))
if list_controls:
    camera.print_ctrls()
    sys.exit(0)
cameraThread = V4L2CameraThread(camera)
cameraThread.start()

server = StreamingServer((config.get('server', 'listen'), config.getint('server', 'port')), StreamingHandler)
server.start()
cameraThread.stop()
cameraThread.join()
