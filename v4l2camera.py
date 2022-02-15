from fcntl import ioctl
from threading import Thread
import mmap, os, struct, logging, sys

import v4l2
from v4l2ctrls import V4L2Ctrls
from v4l2m2m import V4L2M2M
from uvcxctrls import UVCXCtrls

class V4L2Camera(Thread):
    def __init__(self, device, pipe, config):
        super(V4L2Camera, self).__init__()

        self.device = device
        self.stopped = False
        self.pipe = pipe
        self.encoder = None
        self.num_buffers = 6
        self.buffers = []

        self.fd = os.open(self.device, os.O_RDWR, 0)

        params = dict(config.items(device))
        width = int(params.get('width'))
        height = int(params.get('height'))
        fps = int(params.get('fps'))
        capture_format = params.get('capture_format', 'H264')

        if capture_format == 'MJPGH264':
            params['uvcx_h264_stream_mux'] = 'H264'
            params['uvcx_h264_width'] = width
            params['uvcx_h264_height'] = height

        # use the native capture format without the extension
        capture_format_real = capture_format[0:4]
        self.init_device(width, height, capture_format_real)
        self.init_fps(fps)
        
        self.ctrls = V4L2Ctrls(self.device, self.fd)
        self.ctrls.setup_v4l2_ctrls(params)

        self.uvcx_ctrls = UVCXCtrls(self.device, self.fd)
        self.uvcx_ctrls.setup_uvcx_ctrls(params)

        encoder = params.get('encoder')
        
        if encoder:
            encoderparams = dict(config.items(encoder) if encoder in config else {})
            self.encoder = V4L2M2M(encoder, encoderparams, width, height, capture_format, 'H264')
            self.encoder.pipe = self.pipe


        if capture_format not in ['H264', 'MJPGH264'] and not self.encoder:
            logging.error(f'{self.device}: capture format is not H264 or MJPGH264, please set the V4L2 M2M encoder device with the encoder config parameter')
            sys.exit(3)

        if capture_format == 'MJPGH264':
            if not self.uvcx_ctrls.supported():
                logging.error(f'{self.device}: capture format is MJPGH264, but the H264 UVC extension is not supported by the device. Muxing the H264 into the MJPG is impossible.')
                sys.exit(3)
            if not self.uvcx_ctrls.h264_muxing_supported():
                logging.error(f'{self.device}: capture format is MJPGH264, but muxing the H264 into the MJPG is not supported by the device.')
                sys.exit(3)


    def init_device(self, width, height, capture_format):
        cap = v4l2.v4l2_capability()
        fmt = v4l2.v4l2_format()
        
        ioctl(self.fd, v4l2.VIDIOC_QUERYCAP, cap)
        
        if not (cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE):
            logging.error(f'{self.device} is not a video capture device')
            sys.exit(3)
        
        if not (cap.capabilities & v4l2.V4L2_CAP_STREAMING):
            logging.error(f'{self.device} does not support streaming i/o')
            sys.exit(3)

        pix_fmt = v4l2.get_fourcc(capture_format)

        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        fmt.fmt.pix.width = width
        fmt.fmt.pix.height = height
        fmt.fmt.pix.pixelformat = pix_fmt
        fmt.fmt.pix.field = v4l2.V4L2_FIELD_ANY
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

        if not (fmt.fmt.pix.pixelformat == pix_fmt):
            logging.error(f'{self.device} {capture_format} format not available')
            sys.exit(3)

        if not (fmt.fmt.pix.width == width or fmt.fmt.pix.width == width):
            logging.error(f'{self.device} {width}x{height} mode not available')
            sys.exit(3)
        

    def init_fps(self, fps):
        parm = v4l2.v4l2_streamparm()
        parm.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        parm.parm.capture.timeperframe.numerator = 1000
        parm.parm.capture.timeperframe.denominator = fps * parm.parm.capture.timeperframe.numerator
        
        try:
            ioctl(self.fd, v4l2.VIDIOC_S_PARM, parm)
        except Exception as e:
            logging.warning(f'{self.device} Can\'t set fps to {fps}: {e}')

        tf = parm.parm.capture.timeperframe
        if tf.denominator == 0 or tf.numerator == 0:
            logging.error(f'VIDIOC_S_PARM: Invalid frame rate {fps}')
            sys.exit(3)
        if fps != (tf.denominator / tf.numerator):
            logging.warning(f'{self.device} Can\'t set fps to {fps} using {tf.denominator / tf.numerator}')


    def init_mmap(self):
        req = v4l2.v4l2_requestbuffers()
        
        req.count = self.num_buffers
        req.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        req.memory = v4l2.V4L2_MEMORY_MMAP if not self.encoder else v4l2.V4L2_MEMORY_DMABUF


        try:
            ioctl(self.fd, v4l2.VIDIOC_REQBUFS, req)
        except Exception:
            logging.error(f'video buffer request failed on {self.device}')
            sys.exit(3)
        
        if req.count < 2:
            logging.error(f'Insufficient buffer memory on {self.device}')
            sys.exit(3)

        self.num_buffers = req.count
        
        for i in range(req.count):
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
            buf.memory = v4l2.V4L2_MEMORY_MMAP if not self.encoder else v4l2.V4L2_MEMORY_DMABUF
            buf.index = i
            
            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            #print(buf.m.offset, buf.length)

            if not self.encoder:
                buf.buffer = mmap.mmap(self.fd, buf.length,
                    flags=mmap.MAP_SHARED | 0x08000, #MAP_POPULATE
                    prot=mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=buf.m.offset)
            else:
                buf.m.fd = self.encoder.input_bufs[i].fd



            #expbuf = v4l2.v4l2_exportbuffer()
            #expbuf.type = buf.type
            #expbuf.index = buf.index
            #expbuf.flags = os.O_CLOEXEC | os.O_RDWR
            
            #ioctl(self.fd, v4l2.VIDIOC_EXPBUF, expbuf)
            #print(f'{self.device} expbuf idx {buf.index} dma fd {expbuf.fd}')
            #buf.fd = expbuf.fd


            self.buffers.append(buf)

            #print(f'{self.device} qbuf {buf.index}')
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)

    def request_key_frame(self):
        if self.encoder:
            self.encoder.request_key_frame()
        elif self.uvcx_ctrls.supported():
            self.uvcx_ctrls.request_h264_idr()
        else:
            self.ctrls.request_key_frame()

    def print_ctrls(self):
        self.ctrls.print_ctrls()
        self.uvcx_ctrls.print_ctrls()
        print()
        if self.encoder:
            self.encoder.print_ctrls()
            print()

    def main_loop(self):
        seq = 0
        while not self.stopped:
            buf = self.buffers[seq % self.num_buffers]
            #print(f'{self.device} dqbuf {buf.index}')
            ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)
            if not self.encoder:
                self.pipe.write_buf(seq, buf)
            else:
                self.encoder.write_buf(seq, buf)
            #print(f'{self.device} qbuf {buf.index}')
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
            seq += 1


    def start_capturing(self):
        self.init_mmap()
        ioctl(self.fd, v4l2.VIDIOC_STREAMON, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))
        self.main_loop()
        ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))

    def stop_capturing(self):
        self.stopped = True

    # Thread run
    def run(self):
        if self.encoder:
            self.encoder.start()
        self.start_capturing()

    # Thread stop
    def stop(self):
        self.stop_capturing()
        if self.encoder:
            self.encoder.stop()
            self.encoder.join()
        
