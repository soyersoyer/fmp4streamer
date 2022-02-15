from fcntl import ioctl
from threading import Thread
import mmap, os, struct, logging, sys

from v4l2ctrls import V4L2Ctrls
import v4l2

class V4L2M2M(Thread):
    def __init__(self, device, params, width, height, input_format, capture_format):
        super(V4L2M2M, self).__init__()

        self.device = device
        self.stopped = False
        self.pipe = None
        self.num_input_bufs = 6
        self.num_cap_bufs = 12
        self.input_bufs = []
        self.cap_bufs = []

        self.fd = os.open(self.device, os.O_RDWR, 0)

        self.ctrls = V4L2Ctrls(self.device, self.fd)
        self.ctrls.setup_v4l2_ctrls(params)

        self.init_device(
            width,
            height,
            input_format,
            capture_format
        )

    def init_device(self, width, height, input_format, capture_format):
        fmt = v4l2.v4l2_format()

        input_pix_fmt = v4l2.get_fourcc(input_format)

        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        fmt.fmt.pix.width = width
        fmt.fmt.pix.height = height
        fmt.fmt.pix.pixelformat = input_pix_fmt
        fmt.fmt.pix.field = v4l2.V4L2_FIELD_ANY
        # libcamera currently has no means to request the right colour space, hence:
        # fmt.fmt.pix.colorspace = v4l2.V4L2_COLORSPACE_JPEG
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

        if not (fmt.fmt.pix.pixelformat == input_pix_fmt):
            logging.error(f'{self.device}: {input_format} input format not available')
            sys.exit(3)

        capture_pix_fmt = v4l2.get_fourcc(capture_format)

        fmt = v4l2.v4l2_format()
        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        fmt.fmt.pix.width = width
        fmt.fmt.pix.height = height
        fmt.fmt.pix.pixelformat = capture_pix_fmt
        fmt.fmt.pix.field = v4l2.V4L2_FIELD_ANY
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

        if not (fmt.fmt.pix.pixelformat == capture_pix_fmt):
            logging.error(f'{self.device}: {capture_format} capture format not available')
            sys.exit(3)

        # Request that the necessary buffers are allocated. The output queue
        # (input to the encoder) shares buffers from our caller, these must be
        # DMABUFs (or MMAP?). Buffers for the encoded bitstream must be allocated and
        # m-mapped.

        reqbufs = v4l2.v4l2_requestbuffers()
        reqbufs.count = self.num_input_bufs
        reqbufs.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
        reqbufs.memory = v4l2.V4L2_MEMORY_MMAP
        #reqbufs.memory = v4l2.V4L2_MEMORY_DMABUF
        ioctl(self.fd, v4l2.VIDIOC_REQBUFS, reqbufs)
        self.num_input_bufs = reqbufs.count

        for i in range(self.num_input_bufs):
            planes = v4l2.v4l2_planes()
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE
            buf.memory = v4l2.V4L2_MEMORY_MMAP
            #buf.memory = v4l2.V4L2_MEMORY_DMABUF
            buf.index = i
            buf.length = 1
            buf.m.planes = planes

            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            #buf.buffer = mmap.mmap(self.fd, buf.m.planes[0].length,
            #    flags=mmap.MAP_SHARED,
            #    prot=mmap.PROT_READ | mmap.PROT_WRITE,
            #    offset=buf.m.planes[0].m.mem_offset)

            expbuf = v4l2.v4l2_exportbuffer()
            expbuf.type = buf.type
            expbuf.index = buf.index
            expbuf.flags = os.O_CLOEXEC | os.O_RDWR
            
            ioctl(self.fd, v4l2.VIDIOC_EXPBUF, expbuf)
            buf.fd = expbuf.fd

            self.input_bufs.append(buf)


        reqbufs = v4l2.v4l2_requestbuffers()
        reqbufs.count = self.num_cap_bufs
        reqbufs.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
        reqbufs.memory = v4l2.V4L2_MEMORY_MMAP

        ioctl(self.fd, v4l2.VIDIOC_REQBUFS, reqbufs)
        self.num_cap_bufs = reqbufs.count

        for i in range(self.num_cap_bufs):
            planes = v4l2.v4l2_planes()
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
            buf.memory = v4l2.V4L2_MEMORY_MMAP
            buf.index = i
            buf.length = 1
            buf.m.planes = planes

            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            buf.buffer = mmap.mmap(self.fd, buf.m.planes[0].length,
                flags=mmap.MAP_SHARED,
                prot=mmap.PROT_READ | mmap.PROT_WRITE,
                offset=buf.m.planes[0].m.mem_offset)
            self.cap_bufs.append(buf)

            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)

    def request_key_frame(self):
        try:
            ctrl = v4l2.v4l2_control(v4l2.V4L2_CID_MPEG_VIDEO_FORCE_KEY_FRAME, 0)
            ioctl(self.fd, v4l2.VIDIOC_S_CTRL, ctrl)
        except Exception as e:
            logging.warning(f'{self.device}: request_key_frame: failed: {e}')

    def print_ctrls(self):
        self.ctrls.print_ctrls()

    def capture_loop(self):
        seq = 0

        while not self.stopped:
            buf = self.cap_bufs[seq % self.num_cap_bufs]
            #planes = v4l2.v4l2_planes()
            #buf = v4l2.v4l2_buffer()
            #buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE
            #buf.memory = v4l2.V4L2_MEMORY_MMAP
            #buf.length = 1
            #buf.m.planes = planes
            #print(f"{self.device} capture dqbuf")
            ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)

            # store bytesused the same place as without MPLANE
            buf.bytesused = buf.m.planes[0].bytesused

            #buf.buffer = self.cap_bufs[buf.index].buffer
            #print(f"{self.device} frame captured seq {seq}")
            self.pipe.write_buf(seq, buf)
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
            seq += 1

    def write_buf(self, seq, ibuf):
        buf = self.input_bufs[seq % self.num_input_bufs]
        buf.timestamp = ibuf.timestamp
        buf.timecode = ibuf.timecode
        buf.m.planes[0].bytesused = ibuf.bytesused
        buf.m.planes[0].length = ibuf.length
        #buf.m.planes[0].m.fd = ibuf.fd

        #print(f"{self.device} writing input buf seq {seq} bytesused {buf.m.planes[0].bytesused} length {buf.m.planes[0].length} fd {buf.m.planes[0].m.fd} buf length {buf.length}")
        #buf.buffer[:ibuf.bytesused] = ibuf.buffer[:ibuf.bytesused]
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
