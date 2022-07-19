import uvcx, logging, ctypes

# H264 extension GUID a29e7641-de04-47e3-8b2b-f4341aff003b
UVC_H264_GUID = b'\x41\x76\x9e\xa2\x04\xde\xe3\x47\x8b\x2b\xf4\x34\x1a\xff\x00\x3b'

VIDEO_CONFIG_PROBE      = 0x01
VIDEO_CONFIG_COMMIT     = 0x02
RATE_CONTROL_MODE       = 0x03
TEMPORAL_SCALE_MODE     = 0x04
SPATIAL_SCALE_MODE      = 0x05
SNR_SCALE_MODE          = 0x06
LTR_BUFFER_SIZE_CONTROL = 0x07
LTR_PICTURE_CONTROL     = 0x08
PICTURE_TYPE_CONTROL    = 0x09
VERSION                 = 0x0A
ENCODER_RESET           = 0x0B
FRAMERATE_CONFIG        = 0x0C
VIDEO_ADVANCE_CONFIG    = 0x0D
BITRATE_LAYERS          = 0x0E
QP_STEPS_LAYERS         = 0x0F

BMHINTS_NONE           = 0x0000
BMHINTS_RESOLUTION     = 0x0001
BMHINTS_PROFILE        = 0x0002
BMHINTS_RATECONTROL    = 0x0004
BMHINTS_USAGE          = 0x0008
BMHINTS_SLICEMODE      = 0x0010
BMHINTS_SLICEUNITS     = 0x0020
BMHINTS_MVCVIEW        = 0x0040
BMHINTS_TEMPORAL       = 0x0080
BMHINTS_SNR            = 0x0100
BMHINTS_SPATIAL        = 0x0200
BMHINTS_SPATIAL_RATIO  = 0x0400
BMHINTS_FRAME_INTERVAL = 0x0800
BMHINTS_LEAKY_BKT_SIZE = 0x1000
BMHINTS_BITRATE        = 0x2000
BMHINTS_ENTROPY        = 0x4000
BMHINTS_IFRAMEPERIOD   = 0x8000

PROFILE_CONSTRAINED_BASELINE = 0x4240
PROFILE_BASELINE = 0x4200
PROFILE_MAIN = 0x4D00
PROFILE_HIGH = 0x6400

RATECONTROL_CBR = 0x01
RATECONTROL_VBR = 0x02
RATECONTROL_CONST_QP = 0x03

QP_STEPS_I_FRAME_TYPE    = 0x01
QP_STEPS_P_FRAME_TYPE    = 0x02
QP_STEPS_B_FRAME_TYPE    = 0x04
QP_STEPS_ALL_FRAME_TYPES = 0x07

SLICE_MODE_OFF = 0x00
SLICE_MODE_BITS_PER_SLICE = 0x01
SLICE_MODE_MBS_PER_SLICE = 0x02
SLICE_MODE_SLICES_PER_FRAME = 0x03

ENTROPY_CAVLC = 0x00
ENTROPY_CABAC = 0x01

USAGE_REALTIME = 0x01
USAGE_BROADCAST = 0x02
USAGE_STORAGE = 0x03

STREAM_MUX_DISABLED = 0x00
STREAM_MUX_ENABLED = 0x01
STREAM_MUX_H264 = 0x02
STREAM_MUX_YUYV = 0x04
STREAM_MUX_NV12 = 0x08
STREAM_MUX_CONTAINER_MJPEG = 0x40

STREAM_MUX_H264_ENABLED = STREAM_MUX_H264 | STREAM_MUX_ENABLED
STREAM_MUX_YUYV_ENABLED = STREAM_MUX_YUYV | STREAM_MUX_ENABLED
STREAM_MUX_NV12_ENABLED = STREAM_MUX_NV12 | STREAM_MUX_ENABLED

PICTURE_TYPE_IFRAME   = 0x0000 # Generate an IFRAME
PICTURE_TYPE_IDR      = 0x0001 # Generate an IDR
PICTURE_TYPE_IDR_FULL = 0x0002 # Generate an IDR frame with new SPS and PPS

class picture_type_control_t(ctypes.Structure):
    _fields_ = [
        ('wLayerID', ctypes.c_uint16),
        ('wPicType', ctypes.c_uint16),
    ]

class version_t(ctypes.Structure):
    _fields_ = [
        ('wVersion', ctypes.c_uint16),
    ]


class qp_steps_layers_t(ctypes.Structure):
    _fields_ = [
        ('wLayerID', ctypes.c_uint16),
        ('bFrameType', ctypes.c_uint8),
        ('bMinQp', ctypes.c_uint8),
        ('bMaxQp', ctypes.c_uint8),
    ]

class video_config_probe_commit(ctypes.Structure):
    _fields_ = [
		('dwFrameInterval', ctypes.c_uint32),
		('dwBitRate', ctypes.c_uint32),
		('bmHints', ctypes.c_uint16),
		('wConfigurationIndex', ctypes.c_uint16),
		('wWidth', ctypes.c_uint16),
		('wHeight', ctypes.c_uint16),
		('wSliceUnits', ctypes.c_uint16),
		('wSliceMode', ctypes.c_uint16),
		('wProfile', ctypes.c_uint16),
		('wIFramePeriod', ctypes.c_uint16),
		('wEstimatedVideoDelay', ctypes.c_uint16),
		('wEstimatedMaxConfigDelay', ctypes.c_uint16),
		('bUsageType', ctypes.c_uint8),
		('bRateControlMode', ctypes.c_uint8),
		('bTemporalScaleMode', ctypes.c_uint8),
		('bSpatialScaleMode', ctypes.c_uint8),
		('bSNRScaleMode', ctypes.c_uint8),
		('bStreamMuxOption', ctypes.c_uint8),
		('bStreamFormat', ctypes.c_uint8),
		('bEntropyCABAC', ctypes.c_uint8),
		('bTimestamp', ctypes.c_uint8),
		('bNumOfReorderFrames', ctypes.c_uint8),
		('bPreviewFlipped', ctypes.c_uint8),
		('bView', ctypes.c_uint8),
		('bReserved1', ctypes.c_uint8),
		('bReserved2', ctypes.c_uint8),
		('bStreamID', ctypes.c_uint8),
		('bSpatialLayerRatio', ctypes.c_uint8),
		('wLeakyBucketSize', ctypes.c_uint16),
    ]

def request_h264_frame_type(fd, unit_id, type):
    picture_type_req = picture_type_control_t()
    picture_type_req.wLayerID = 0
    picture_type_req.wPicType = type

    uvcx.query_xu_control(fd, unit_id, PICTURE_TYPE_CONTROL, uvcx.UVC_SET_CUR, picture_type_req)

def request_h264_idr(fd, unit_id):
    request_h264_frame_type(fd, unit_id, PICTURE_TYPE_IDR)

def get_h264_default_config(fd, unit_id):
    config = video_config_probe_commit()
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_PROBE, uvcx.UVC_GET_DEF, config)
    return config

def get_h264_minimum_config(fd, unit_id):
    config = video_config_probe_commit()
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_PROBE, uvcx.UVC_GET_MIN, config)
    return config

def get_h264_maximum_config(fd, unit_id):
    config = video_config_probe_commit()
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_PROBE, uvcx.UVC_GET_MAX, config)
    return config

def get_h264_current_config(fd, unit_id):
    config = video_config_probe_commit()
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_PROBE, uvcx.UVC_GET_CUR, config)
    return config

def get_h264_resolution_config(fd, unit_id):
    config = video_config_probe_commit()
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_PROBE, uvcx.UVC_GET_RES, config)
    return config

def set_h264_config(fd, unit_id, config):
    uvcx.query_xu_control(fd, unit_id, VIDEO_CONFIG_COMMIT, uvcx.UVC_SET_CUR, config)

def get_h264_version(fd, unit_id):
    version = version_t()
    uvcx.query_xu_control(fd, unit_id, VERSION, uvcx.UVC_GET_CUR, version)
    return version.wVersion

class H264Ctrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = uvcx.find_unit_id_in_sysfs(device, UVC_H264_GUID)
        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0

    def h264_muxing_supported(self):
        return self.supported() and (self.maximum_config.bStreamMuxOption & STREAM_MUX_H264) > 0

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        self.default_config = get_h264_default_config(self.fd, self.unit_id)
        self.minimum_config = get_h264_minimum_config(self.fd, self.unit_id)
        self.maximum_config = get_h264_maximum_config(self.fd, self.unit_id)
        self.current_config = get_h264_current_config(self.fd, self.unit_id)
        self.ctrls = [
            Ctrl(
                'uvcx_h264_stream_mux',
                BMHINTS_NONE,
                'bStreamMuxOption',
                {
                    STREAM_MUX_DISABLED: 'None',
                    STREAM_MUX_H264_ENABLED: 'H264',
                }
            ),
            Ctrl(
                'uvcx_h264_width',
                BMHINTS_RESOLUTION,
                'wWidth',
            ),
            Ctrl(
                'uvcx_h264_height',
                BMHINTS_RESOLUTION,
                'wHeight',
            ),
            Ctrl(
                'uvcx_h264_frame_interval',
                BMHINTS_FRAME_INTERVAL,
                'dwFrameInterval',
            ),
            Ctrl(
                'uvcx_h264_bitrate',
                BMHINTS_BITRATE,
                'dwBitRate',
            ),
            Ctrl(
                'uvcx_h264_rate_control_mode',
                BMHINTS_RATECONTROL,
                'bRateControlMode',
                {
                    RATECONTROL_CBR: 'CBR',
                    RATECONTROL_VBR: 'VBR',
                    RATECONTROL_CONST_QP: 'Const QP',
                }
            ),
            Ctrl(
                'uvcx_h264_profile',
                BMHINTS_PROFILE,
                'wProfile',
                {
                    PROFILE_CONSTRAINED_BASELINE: 'Constrained',
                    PROFILE_BASELINE: 'Baseline',
                    PROFILE_MAIN: 'Main',
                    PROFILE_HIGH: 'High',
                }
            ),
            Ctrl(
                'uvcx_h264_i_frame_period',
                BMHINTS_IFRAMEPERIOD,
                'wIFramePeriod',
            ),
            Ctrl(
                'uvcx_h264_slice_mode',
                BMHINTS_SLICEMODE,
                'wSliceMode',
                {
                    SLICE_MODE_OFF: 'Off',
                    SLICE_MODE_BITS_PER_SLICE: 'BitsPerSlice',
                    SLICE_MODE_MBS_PER_SLICE: 'MBsPerSlice',
                    SLICE_MODE_SLICES_PER_FRAME: 'SlicesPerFrame',
                }
            ),
            Ctrl(
                'uvcx_h264_slice_units',
                BMHINTS_SLICEUNITS,
                'wSliceUnits',
            ),
            Ctrl(
                'uvcx_h264_entropy',
                BMHINTS_ENTROPY,
                'bEntropyCABAC',
                {
                    ENTROPY_CAVLC: 'CAVLC',
                    ENTROPY_CABAC: 'CABAC',
                }
            ),
            Ctrl(
                'uvcx_h264_usage',
                BMHINTS_USAGE,
                'bUsageType',
                {
                    USAGE_REALTIME: 'Realtime',
                    USAGE_BROADCAST: 'Broadcast',
                    USAGE_STORAGE: 'Storage',
                }
            ),
            Ctrl(
                'uvcx_h264_leaky_bucket_size',
                BMHINTS_LEAKY_BKT_SIZE,
                'wLeakyBucketSize',
            ),            
        ]

    def print_ctrls(self):
        for c in self.ctrls:
            minimum = getattr(self.minimum_config, c.sname)
            maximum = getattr(self.maximum_config, c.sname)
            default = getattr(self.default_config, c.sname)
            value = getattr(self.current_config, c.sname)
            print(c.name, end = ' = ')
            if not c.menu:
                print('%a\t(' % value, 'default:', default, 'min:', minimum, 'max:', maximum, end = ')\n')
            else:
                valmenu = c.menu.get(value)
                defmenu = c.menu.get(default)
                print(f'{valmenu if valmenu else value}\t(', end = ' ')
                if defmenu:
                    print(f'default: {defmenu}', end = ' ')
                print('values:', end = ' ')
                for k, v in c.menu.items():
                    print('%a' % v, end = ' ')
                print(')')

    def setup_ctrls(self, params):
        if not self.supported():
            return

        for k, v in params.items():
            if not k.startswith('uvcx_h264_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                logging.warning(f'H264Ctrls: can\'t find {k} control in {[c.name for c in self.ctrls]}')
                continue
            if ctrl.menu:
                menukey  = find_by_value(ctrl.menu, v)
                if menukey == None:
                    logging.warning(f'H264Ctrls: can\'t find {v} in {list(ctrl.menu.values())}')
                    continue
                setattr(self.current_config, ctrl.sname, menukey)
            else:
                setattr(self.current_config, ctrl.sname, int(v))
            self.current_config.bmHints |= ctrl.hint

        set_h264_config(self.fd, self.unit_id, self.current_config)
        current = get_h264_current_config(self.fd, self.unit_id)

        for k, v in params.items():
            if not k.startswith('uvcx_h264_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                continue
            desired_value = getattr(self.current_config, ctrl.sname)
            current_value = getattr(current, ctrl.sname)
            if ctrl.menu:
                desired_value = ctrl.menu.get(desired_value, desired_value)
                current_value = ctrl.menu.get(current_value, current_value)
            if current_value != desired_value:
                logging.warning(f'H264Ctrls: failed to set {k} to {desired_value}, current value {current_value}\n')

    def refresh_ctrls(self):
        set_h264_config(self.fd, self.unit_id, self.current_config)

    def request_h264_idr(self):
        request_h264_frame_type(self.fd, self.unit_id, PICTURE_TYPE_IDR)

class Ctrl:
    def __init__(self, name, hint, sname, menu = None):
        self.name = name
        self.hint = hint
        self.sname = sname
        self.menu = menu

def find_by_name(ctrls, name):
    for c in ctrls:
        if name == c.name:
            return c
    return None

def find_by_value(menu, value):
    for k, v in menu.items():
        if v == value:
            return k
    return None
