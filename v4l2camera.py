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
        self.decoder = None
        self.num_cap_bufs = 6
        self.cap_bufs = []

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

        sizeimage = self.get_sizeimage()
        
        self.ctrls = V4L2Ctrls(self.device, self.fd)
        self.ctrls.setup_v4l2_ctrls(params)

        self.uvcx_ctrls = UVCXCtrls(self.device, self.fd)
        self.uvcx_ctrls.setup_uvcx_ctrls(params)

        decoder = params.get('decoder')
        decoder_input_format = params.get('decoder_input_format', capture_format)
        decoder_memory = params.get('decoder_memory', 'MMAP-DMABUF')

        encoder = params.get('encoder')
        encoder_input_format = params.get('encoder_input_format', 'YU12' if decoder else capture_format)
        encoder_memory = params.get('encoder_memory', 'MMAP-MMAP')


        capture_memory = params.get('capture_memory', 'DMABUF' if encoder or decoder else 'MMAP')



        if encoder:
            encoderparams = dict(config.items(encoder) if encoder in config else {})
            self.encoder = V4L2M2M(encoder, self.pipe, encoderparams, width, height, encoder_input_format, 'H264', encoder_memory)
            self.pipe = self.encoder

        if decoder:
            decoderparams = dict(config.items(decoder) if decoder in config else {})
            self.decoder = V4L2M2M(decoder, self.encoder, decoderparams, width, height, decoder_input_format, encoder_input_format, decoder_memory, sizeimage)
            self.pipe = self.decoder

        if capture_format not in ['H264', 'MJPGH264'] and not self.encoder:
            logging.error(f'{self.device}: capture format is not H264 or MJPGH264, please add the V4L2 M2M encoder (or decoder) devices to the config')
            sys.exit(3)

        if capture_format == 'MJPGH264':
            if not self.uvcx_ctrls.supported():
                logging.error(f'{self.device}: capture format is MJPGH264, but the H264 UVC extension is not supported by the device. Muxing the H264 into the MJPG is impossible.')
                sys.exit(3)
            if not self.uvcx_ctrls.h264_muxing_supported():
                logging.error(f'{self.device}: capture format is MJPGH264, but muxing the H264 into the MJPG is not supported by the device.')
                sys.exit(3)

        self.init_buffers(capture_memory)
        self.connect_buffers()



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

    def get_sizeimage(self):
        fmt = v4l2.v4l2_format()
        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        ioctl(self.fd, v4l2.VIDIOC_G_FMT, fmt)
        return fmt.fmt.pix.sizeimage

    def init_buffers(self, capture_memory):
        req = v4l2.v4l2_requestbuffers()
        
        req.count = self.num_cap_bufs
        req.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        req.memory = v4l2.get_mem_type(capture_memory)


        try:
            ioctl(self.fd, v4l2.VIDIOC_REQBUFS, req)
        except Exception:
            logging.error(f'video buffer request failed on {self.device}')
            sys.exit(3)
        
        if req.count != self.num_cap_bufs:
            logging.error(f'Insufficient buffer memory on {self.device}')
            sys.exit(3)

        for i in range(req.count):
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
            buf.memory = req.memory
            buf.index = i
            
            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            #print(buf.m.offset, buf.length)

            if req.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.buffer = mmap.mmap(self.fd, buf.length,
                    flags=mmap.MAP_SHARED | 0x08000, #MAP_POPULATE
                    prot=mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=buf.m.offset)

                expbuf = v4l2.v4l2_exportbuffer()
                expbuf.type = buf.type
                expbuf.index = buf.index
                expbuf.flags = os.O_CLOEXEC | os.O_RDWR
                
                ioctl(self.fd, v4l2.VIDIOC_EXPBUF, expbuf)
                buf.fd = expbuf.fd
  

            self.cap_bufs.append(buf)


    def connect_buffers(self):
        if not hasattr(self.pipe, 'input_bufs'):
            return

        for i in range(self.num_cap_bufs):
            buf = self.cap_bufs[i]
            bufp = self.pipe.input_bufs[i]
            if buf.memory == v4l2.V4L2_MEMORY_DMABUF and bufp.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.m.fd = bufp.fd
        self.pipe.connect_buffers(self)

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
        if self.decoder:
            self.decoder.print_ctrls()
            print()
        if self.encoder:
            self.encoder.print_ctrls()
            print()

    def main_loop(self):
        for buf in self.cap_bufs:
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)

        seq = 0
        while not self.stopped:
            buf = self.cap_bufs[seq % self.num_cap_bufs]
            #print(f'{self.device} dqbuf {buf.index}')
            ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)
            #print(f'{self.device} {buf.bytesused}')
            self.pipe.write_buf(seq, buf)
            #print(f'{self.device} qbuf {buf.index}')
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
            seq += 1


    def start_capturing(self):
        ioctl(self.fd, v4l2.VIDIOC_STREAMON, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))
        self.main_loop()
        ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))

    def stop_capturing(self):
        self.stopped = True

    # Thread run
    def run(self):
        if self.encoder:
            self.encoder.start()
        if self.decoder:
            self.decoder.start()
        self.start_capturing()

    # Thread stop
    def stop(self):
        self.stop_capturing()
        if self.decoder:
            self.decoder.stop()
            self.decoder.join()
        if self.encoder:
            self.encoder.stop()
            self.encoder.join()
        
