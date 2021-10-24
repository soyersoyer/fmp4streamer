from fcntl import ioctl
from threading import Condition
import mmap, os, struct, logging

import v4l2


class H264NALU:
    DELIMITER = b'\x00\x00\x00\x01'

    NONIDRTYPE = 1
    IDRTYPE = 5
    SPSTYPE = 7
    PPSTYPE = 8

    @staticmethod
    def get_type(nalubytes):
        return nalubytes[0] & 0x1f

class V4L2Camera(object):
    def __init__(self, device, params):
        self.device = device
        self.stopped = False
        self.num_buffers = 10
        self.buffers = []
        self.sps = None
        self.pps = None
        self.condition = Condition()
        self.frame_data = None
        self.frame_secs = 0
        self.frame_usecs = 0
        self.fd = os.open(self.device, os.O_RDWR, 0)
        
        self.init_device(int(params.get('width')), int(params.get('height')))
        self.init_fps(int(params.get('fps')))
        
        self.ctrls = self.get_device_controls()
        self.init_v4l2_ctrls(self.ctrls, params)


    def init_device(self, width, height):
        cap = v4l2.v4l2_capability()
        fmt = v4l2.v4l2_format()
        
        ioctl(self.fd, v4l2.VIDIOC_QUERYCAP, cap)
        
        if not (cap.capabilities & v4l2.V4L2_CAP_VIDEO_CAPTURE):
            raise Exception(f'{self.device} is not a video capture device')
        
        if not (cap.capabilities & v4l2.V4L2_CAP_STREAMING):
            raise Exception(f'{self.device} does not support streaming i/o')

        fmt.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        fmt.fmt.pix.width = width
        fmt.fmt.pix.height = height
        fmt.fmt.pix.pixelformat = v4l2.V4L2_PIX_FMT_H264
        fmt.fmt.pix.field = v4l2.V4L2_FIELD_ANY
        ioctl(self.fd, v4l2.VIDIOC_S_FMT, fmt)

    def init_fps(self, fps):
        parm = v4l2.v4l2_streamparm()
        parm.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        parm.parm.capture.timeperframe.numerator = 1000
        parm.parm.capture.timeperframe.denominator = fps * parm.parm.capture.timeperframe.numerator
        
        ioctl(self.fd, v4l2.VIDIOC_S_PARM, parm)

        tf = parm.parm.capture.timeperframe
        if tf.denominator == 0 or tf.numerator == 0:
            raise Exception(f'VIDIOC_S_PARM: Invalid frame rate {fps}')
        if fps != (tf.denominator / tf.numerator):
            logging.warning(f'Can\'t set fps to {fps} using {tf.denominator / tf.numerator}')

    def init_v4l2_ctrls(self, ctrls, params):
        for k, v in params.items():
            if k == 'width' or k == 'height' or k == 'fps':
                continue
            ctrl = self.find_ctrl(ctrls, k)
            if ctrl == None:
                logging.warning(f'Can\'t find {k} v4l2 control')
                continue
            intvalue = 0
            if ctrl.type == v4l2.V4L2_CTRL_TYPE_INTEGER:
                intvalue = int(v)
            elif ctrl.type == v4l2.V4L2_CTRL_TYPE_BOOLEAN:
                intvalue = int(bool(v))
            elif ctrl.type == v4l2.V4L2_CTRL_TYPE_MENU:
                menu = self.find_menu_by_name(ctrl.menus, v)
                if menu == None:
                    logging.warning(f'Can\'t find {v} in {[str(c.name, "utf-8") for c in ctrl.menus]}')
                    continue
                intvalue = menu.index
            elif ctrl.type == v4l2.V4L2_CTRL_TYPE_INTEGER_MENU:
                menu = self.find_menu_by_value(ctrl.menus, int(v))
                if menu == None:
                    logging.warning(f'Can\'t find {v} in {[c.value for c in ctrl.menus]}')
                    continue
                intvalue = menu.index
            else:
                logging.warning(f'Can\'t set {k} to {v} (Unsupported control type {ctrl.type})')
                continue
            try:
                new_ctrl = v4l2.v4l2_control(ctrl.id, intvalue)
                ioctl(self.fd, v4l2.VIDIOC_S_CTRL, new_ctrl)
                if new_ctrl.value != intvalue:
                    logging.warning(f'Can\'t set {k} to {v} using {new_ctrl.value} instead of {intvalue}')
                    continue
                ctrl.value = intvalue
            except Exception as e:
                logging.warning(f'Can\'t set {k} to {v} ({e})')

            

    def find_ctrl(self, ctrls, name):
        for c in ctrls:
            if name == str(c.name, 'utf-8'):
                return c
        return None
    def find_menu_by_name(self, menus, name):
        for m in menus:
            if name == str(m.name, 'utf-8'):
                return m
        return None
    def find_menu_by_value(self, menus, value):
        for m in menus:
            if value == m.value:
                return m
        return None

    def get_device_controls(self):
        ctrls = []
        strtrans = bytes.maketrans(b' -', b'__')
        next_fl = v4l2.V4L2_CTRL_FLAG_NEXT_CTRL | v4l2.V4L2_CTRL_FLAG_NEXT_COMPOUND
        qctrl = v4l2.v4l2_queryctrl(next_fl)
        while True:
            try:
                ioctl(self.fd, v4l2.VIDIOC_QUERYCTRL, qctrl)
            except:
                break
            if qctrl.type in [v4l2.V4L2_CTRL_TYPE_INTEGER, v4l2.V4L2_CTRL_TYPE_BOOLEAN,
                v4l2.V4L2_CTRL_TYPE_MENU,v4l2.V4L2_CTRL_TYPE_INTEGER_MENU]:

                try:
                    ctrl = v4l2.v4l2_control(qctrl.id)
                    ioctl(self.fd, v4l2.VIDIOC_G_CTRL, ctrl)
                    qctrl.value = ctrl.value
                except:
                    logging.warning(f'Can\'t get ctrl {qctrl.name} value')

                qctrl.name = qctrl.name.lower().translate(strtrans, delete = b',&(.)').replace(b'__', b'_')
                if qctrl.type in [v4l2.V4L2_CTRL_TYPE_MENU, v4l2.V4L2_CTRL_TYPE_INTEGER_MENU]:
                    qctrl.menus = []
                    for i in range(qctrl.minimum, qctrl.maximum + 1):
                        try:
                            qmenu = v4l2.v4l2_querymenu(qctrl.id, i)
                            ioctl(self.fd, v4l2.VIDIOC_QUERYMENU, qmenu)
                        except:
                            continue
                        qctrl.menus.append(qmenu)
                        
            ctrls.append(qctrl)
            qctrl = v4l2.v4l2_queryctrl(qctrl.id | next_fl)

        return ctrls

    def print_ctrls(self):
        print(f'V4L2 controls for {self.device}\n')
        print(f'If you want to set one, just put as ctrl_name = Value into the configfile under the [{self.device}]')
        for c in self.ctrls:
            if c.type == v4l2.V4L2_CTRL_TYPE_CTRL_CLASS:
                print('\n\n' + str(c.name, 'utf-8')+'\n')
            else:
                print(str(c.name, 'utf-8'), end = ' = ')
                if c.type in [v4l2.V4L2_CTRL_TYPE_MENU, v4l2.V4L2_CTRL_TYPE_INTEGER_MENU]:
                    defmenu = None
                    valmenu = None
                    for m in c.menus:
                        if m.index == c.value:
                            valmenu = m
                        if m.index == c.default:
                            defmenu = m
                    if valmenu:
                        print(f'{str(valmenu.name, "utf-8") if c.type == v4l2.V4L2_CTRL_TYPE_MENU else valmenu.value}\t(', end = ' ')
                    if defmenu:
                        print(f'default: {str(defmenu.name, "utf-8") if c.type == v4l2.V4L2_CTRL_TYPE_MENU else defmenu.value}', end = ' ')
                    print('values:', end = ' ')
                    for m in c.menus:
                        print('%a' % (str(m.name, 'utf-8') if c.type == v4l2.V4L2_CTRL_TYPE_MENU else m.value),
                            end = ' ')
                    print(')')
                elif c.type in [v4l2.V4L2_CTRL_TYPE_INTEGER, v4l2.V4L2_CTRL_TYPE_BOOLEAN]:
                    print('%a\t(' % c.value, 'default:', c.default, 'min:', c.minimum, 'max:', c.maximum, end = '')
                    if c.step != 1:
                        print(' step:', c.step, end = '')
                    print(')')
                else:
                    print()

    def init_mmap(self):
        req = v4l2.v4l2_requestbuffers()
        
        req.count = self.num_buffers
        req.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
        req.memory = v4l2.V4L2_MEMORY_MMAP
        
        try:
            ioctl(self.fd, v4l2.VIDIOC_REQBUFS, req)
        except Exception:
            raise Exception('video buffer request failed')
        
        if req.count < 2:
            raise Exception(f'Insufficient buffer memory on {self.device}')

        self.num_buffers = req.count
        
        for i in range(req.count):
            buf = v4l2.v4l2_buffer()
            buf.type = v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE
            buf.memory = v4l2.V4L2_MEMORY_MMAP
            buf.index = i
            
            ioctl(self.fd, v4l2.VIDIOC_QUERYBUF, buf)

            buf.buffer = mmap.mmap(self.fd, buf.length, mmap.PROT_READ, mmap.MAP_SHARED, offset=buf.m.offset)
            self.buffers.append(buf)

    def request_key_frame(self):
        try:
            ctrl = v4l2.v4l2_control(v4l2.V4L2_CID_MPEG_VIDEO_FORCE_KEY_FRAME, 0)
            ioctl(self.fd, v4l2.VIDIOC_S_CTRL, ctrl)
        except:
            logging.warning(f'Can\'t request keyframe')

    def read_header(self, buf):
        data = buf.buffer.read(buf.bytesused)
        nalus = data.split(H264NALU.DELIMITER)

        if len(nalus) > 1 and len(nalus[0]) == 0:
            nalus.pop(0)

        for nalu in nalus:
            if H264NALU.get_type(nalu) == H264NALU.SPSTYPE:
                self.sps = nalu
            if H264NALU.get_type(nalu) == H264NALU.PPSTYPE:
                self.pps = nalu
        if not self.sps or not self.pps:
            logging.error('V4L2Camera: can\'t read SPS and PPS from the first frame')
    
    def process_image(self, buf):
        data = memoryview(buf.buffer)[4 : buf.bytesused]

        with self.condition:
            self.frame_data = data
            self.frame_secs = buf.timestamp.secs
            self.frame_usecs = buf.timestamp.usecs
            self.condition.notify_all()

    def main_loop(self):
        seq = 0
        while not self.stopped:
            buf = self.buffers[seq % self.num_buffers]
            ioctl(self.fd, v4l2.VIDIOC_DQBUF, buf)
            if seq == 0:
                self.read_header(self.buffers[buf.index])
            else:
                self.process_image(self.buffers[buf.index])
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
            seq += 1

    def start_capturing(self):
        self.init_mmap()
        for buf in self.buffers:
            ioctl(self.fd, v4l2.VIDIOC_QBUF, buf)
        ioctl(self.fd, v4l2.VIDIOC_STREAMON, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))
        self.main_loop()
        ioctl(self.fd, v4l2.VIDIOC_STREAMOFF, struct.pack('I', v4l2.V4L2_BUF_TYPE_VIDEO_CAPTURE))

    def stop_capturing(self):
        self.stopped = True

