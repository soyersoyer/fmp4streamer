from fcntl import ioctl
from threading import Thread
import mmap, os, struct, logging, sys

from v4l2ctrls import V4L2Ctrls
import v4l2

JPEG_APP0 = b'\xff\xe0'
JPEG_APP4 = b'\xff\xe4'
JPEG_APP4_END = b'\xe4'

class V4L2M2M(Thread):
    def __init__(self, device, pipe, params, width, height,
        input_format, capture_format, input_memory, capture_memory):
        super(V4L2M2M, self).__init__()

        self.device = device
        self.stopped = False
        self.pipe = pipe
        self.num_input_bufs = 6
        self.num_cap_bufs = 6
        self.input_bufs = []
        self.cap_bufs = []

        self.input_format = input_format

        self.fd = os.open(self.device, os.O_RDWR, 0)

        self.ctrls = V4L2Ctrls(self.device, self.fd)
        self.ctrls.setup_v4l2_ctrls(params)

        self.init_device(
            width,
            height,
            input_format,
            capture_format,
            input_memory,
            capture_memory
        )

    def init_device(self, width, height, input_format, capture_format, input_memory, capture_memory):
        fmt = v4l2.v4l2_format()

        input_pix_fmt = v4l2.get_fourcc(input_format)

        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        fmt.fmt.pix_mp.width = width
        fmt.fmt.pix_mp.height = height
        fmt.fmt.pix_mp.pixelformat = input_pix_fmt
        fmt.fmt.pix_mp.field = v4l2.V4L2_FIELD_ANY
        # libcamera currently has no means to request the right colour space, hence:
        # fmt.fmt.pix_mp.colorspace = v4l2.V4L2_COLORSPACE_JPEG
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

        if not (fmt.fmt.pix_mp.pixelformat == input_pix_fmt):
            logging.error(f'{self.device}: {input_format} input format not available')
            sys.exit(3)

        if not (fmt.fmt.pix_mp.width == width or fmt.fmt.pix_mp.width == width):
            logging.error(f'{self.device}: {width}x{height} input mode not available')
            sys.exit(3)

        capture_pix_fmt = v4l2.get_fourcc(capture_format)

        fmt = v4l2.v4l2_format()
        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        fmt.fmt.pix_mp.width = width
        fmt.fmt.pix_mp.height = height
        fmt.fmt.pix_mp.pixelformat = capture_pix_fmt
        fmt.fmt.pix_mp.field = v4l2.V4L2_FIELD_ANY
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

        if not (fmt.fmt.pix_mp.pixelformat == capture_pix_fmt):
            logging.error(f'{self.device}: {capture_format} capture format not available')
            sys.exit(3)

        if not (fmt.fmt.pix_mp.width == width or fmt.fmt.pix_mp.width == width):
            logging.error(f'{self.device}: {width}x{height} capture mode not available')
            sys.exit(3)

        # Request that the necessary buffers are allocated. The output queue
        # (input to the encoder) shares buffers from our caller, these must be
        # DMABUFs (or MMAP?). Buffers for the encoded bitstream must be allocated and
        # m-mapped.

        reqbufs = v4l2.v4l2_requestbuffers()
        reqbufs.count = self.num_input_bufs
        reqbufs.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        reqbufs.memory = v4l2.get_mem_type(input_memory)
        ioctl(self.fd, v4l2.VIDIOC_REQBUFS, reqbufs)
        self.num_input_bufs = reqbufs.count

        for i in range(self.num_input_bufs):
            planes = v4l2.v4l2_planes()
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
            buf.memory = reqbufs.memory
            buf.index = i
            buf.length = 1
            buf.m.planes = planes

            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            if buf.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.buffer = mmap.mmap(self.fd, buf.m.planes[0].length,
                    flags=mmap.MAP_SHARED,
                    prot=mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=buf.m.planes[0].m.mem_offset)

                expbuf = v4l2.v4l2_exportbuffer()
                expbuf.type = buf.type
                expbuf.index = buf.index
                expbuf.plane = 0
                expbuf.flags = os.O_CLOEXEC | os.O_RDWR
                
                ioctl(self.fd, v4l2.VIDIOC_EXPBUF, expbuf)
                buf.fd = expbuf.fd

            self.input_bufs.append(buf)


        reqbufs = v4l2.v4l2_requestbuffers()
        reqbufs.count = self.num_cap_bufs
        reqbufs.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        reqbufs.memory = v4l2.get_mem_type(capture_memory)

        ioctl(self.fd, v4l2.VIDIOC_REQBUFS, reqbufs)
        self.num_cap_bufs = reqbufs.count

        for i in range(self.num_cap_bufs):
            planes = v4l2.v4l2_planes()
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
            buf.memory = reqbufs.memory
            buf.index = i
            buf.length = 1
            buf.m.planes = planes

            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            if reqbufs.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.buffer = mmap.mmap(self.fd, buf.m.planes[0].length,
                    flags=mmap.MAP_SHARED,
                    prot=mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=buf.m.planes[0].m.mem_offset)

                expbuf = v4l2.v4l2_exportbuffer()
                expbuf.type = buf.type
                expbuf.index = buf.index
                expbuf.plane = 0
                expbuf.flags = os.O_CLOEXEC | os.O_RDWR
                
                ioctl(self.fd, v4l2.VIDIOC_EXPBUF, expbuf)
                buf.fd = expbuf.fd

            self.cap_bufs.append(buf)

    def connect_buffers(self, prev):
        for i in range(self.num_input_bufs):
            buf = self.input_bufs[i]
            bufprev = prev.cap_bufs[i]
            if buf.memory == v4l2.V4L2_MEMORY_DMABUF and bufprev.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.m.planes[0].m.fd = bufprev.fd
        
        if not hasattr(self.pipe, 'input_bufs'):
            return
        
        for i in range(self.num_cap_bufs):
            buf = self.cap_bufs[i]
            bufp = self.pipe.input_bufs[i]
            if buf.memory == v4l2.V4L2_MEMORY_DMABUF and bufp.memory == v4l2.V4L2_MEMORY_MMAP:
                buf.m.planes[0].m.fd = bufp.fd

        self.pipe.connect_buffers(self)

    def request_key_frame(self):
        try:
            ctrl = v4l2.v4l2_control(v4l2.V4L2_CID_MPEG_VIDEO_FORCE_KEY_FRAME, 0)
            ioctl(self.fd, v4l2.VIDIOC_S_CTRL, ctrl)
        except Exception as e:
            logging.warning(f'{self.device}: request_key_frame: failed: {e}')

    def print_ctrls(self):
        self.ctrls.print_ctrls()

    def capture_loop(self):
        for buf in self.cap_bufs:
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)

        seq = 0

        while not self.stopped:
            buf = self.cap_bufs[seq % self.num_cap_bufs]
            #print(f"capture {self.device} dqbuf {buf.index}")
            ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)
            #print(f'capture {self.device}: {buf.m.planes[0].bytesused}')

            # store bytesused the same place as without MPLANE
            buf.bytesused = buf.m.planes[0].bytesused

            self.pipe.write_buf(seq, buf)
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
            seq += 1

    def write_buf(self, seq, ibuf):
        buf = self.input_bufs[seq % self.num_input_bufs]
        buf.timestamp = ibuf.timestamp
        buf.timecode = ibuf.timecode
        buf.m.planes[0].bytesused = ibuf.bytesused
        #buf.m.planes[0].length = ibuf.length

        if buf.memory == v4l2.V4L2_MEMORY_MMAP and ibuf.memory == v4l2.V4L2_MEMORY_MMAP:
            buf.buffer[:ibuf.bytesused] = ibuf.buffer[:ibuf.bytesused]

        # RPI decoder failed to decode with MJPGs with APP0 JFIF so patch to APP4
        if self.input_format == "MJPG":
            mbuf = buf.buffer if buf.memory == v4l2.V4L2_MEMORY_MMAP else ibuf.buffer
            app0_start = mbuf.find(JPEG_APP0, 0, 4)
            if app0_start != -1:
                mbuf[app0_start+1:app0_start+2] = JPEG_APP4_END
            app0_start = mbuf.find(JPEG_APP0, 4, 500)
            if app0_start != -1:
                mbuf[app0_start+1:app0_start+2] = JPEG_APP4_END
        
        #print(f"{self.device} writing input buf seq {seq} bytesused {buf.m.planes[0].bytesused} length {buf.m.planes[0].length} fd {buf.m.planes[0].m.fd} buf length {buf.length}")
        try:
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
        except Exception as e:
            logging.warning(f'{self.device}: write_buf: qbuf failed: {e}')
            return

        ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)


    def start_capturing(self):
        ioctl(self.fd, v4l2.VIDIOC_STREAMON, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE))
        ioctl(self.fd, v4l2.VIDIOC_STREAMON, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE))
        self.capture_loop()
        ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE))
        ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE))

    def stop_capturing(self):
        self.stopped = True

   # Thread run
    def run(self):
        self.start_capturing()

    # Thread stop
    def stop(self):
        self.stop_capturing()
