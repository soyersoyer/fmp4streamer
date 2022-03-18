import v4l2, ctypes, logging, os.path
from fcntl import ioctl

#
# ioctl structs, codes for uvc extensions
#

class uvcx_picture_type_control_t(ctypes.Structure):
    _fields_ = [
        ('wLayerID', ctypes.c_uint16),
        ('wPicType', ctypes.c_uint16),
    ]

class uvcx_version_t(ctypes.Structure):
    _fields_ = [
        ('wVersion', ctypes.c_uint16),
    ]

class uvcx_qp_steps_layers_t(ctypes.Structure):
    _fields_ = [
        ('wLayerID', ctypes.c_uint16),
        ('bFrameType', ctypes.c_uint8),
        ('bMinQp', ctypes.c_uint8),
        ('bMaxQp', ctypes.c_uint8),
    ]


class uvc_xu_control_query(ctypes.Structure):
    _fields_ = [
        ('unit', ctypes.c_uint8),
        ('selector', ctypes.c_uint8),
        ('query', ctypes.c_uint8),		# Video Class-Specific Request Code,
                                        # defined in linux/usb/video.h A.8. 
        ('size', ctypes.c_uint16),
        ('data', ctypes.c_void_p),
    ]

UVCIOC_CTRL_QUERY = v4l2._IOWR('u', 0x21, uvc_xu_control_query)

PICTURE_TYPE_IFRAME = 0x0000 # Generate an IFRAME
PICTURE_TYPE_IDR = 0x0001 # Generate an IDR
PICTURE_TYPE_IDR_FULL = 0x0002 # Generate an IDR frame with new SPS and PPS

UVCX_PICTURE_TYPE_CONTROL = 0x09

# A.8. Video Class-Specific Request Codes
UVC_RC_UNDEFINED = 0x00
UVC_SET_CUR      = 0x01
UVC_GET_CUR      = 0x81
UVC_GET_MIN      = 0x82
UVC_GET_MAX      = 0x83
UVC_GET_RES      = 0x84
UVC_GET_LEN      = 0x85
UVC_GET_INFO     = 0x86
UVC_GET_DEF      = 0x87

# H264 extension GUID a29e7641-de04-47e3-8b2b-f4341aff003b
H264_XU_GUID = b'\x41\x76\x9e\xa2\x04\xde\xe3\x47\x8b\x2b\xf4\x34\x1a\xff\x00\x3b'


UVCX_VIDEO_CONFIG_PROBE		 = 0x01
UVCX_VIDEO_CONFIG_COMMIT	 = 0x02
UVCX_RATE_CONTROL_MODE		 = 0x03
UVCX_TEMPORAL_SCALE_MODE	 = 0x04
UVCX_SPATIAL_SCALE_MODE		 = 0x05
UVCX_SNR_SCALE_MODE			 = 0x06
UVCX_LTR_BUFFER_SIZE_CONTROL = 0x07
UVCX_LTR_PICTURE_CONTROL	 = 0x08
UVCX_PICTURE_TYPE_CONTROL	 = 0x09
UVCX_VERSION				 = 0x0A
UVCX_ENCODER_RESET			 = 0x0B
UVCX_FRAMERATE_CONFIG		 = 0x0C
UVCX_VIDEO_ADVANCE_CONFIG	 = 0x0D
UVCX_BITRATE_LAYERS			 = 0x0E
UVCX_QP_STEPS_LAYERS		 = 0x0F

UVC_H264_BMHINTS_NONE           = 0x0000
UVC_H264_BMHINTS_RESOLUTION     = 0x0001
UVC_H264_BMHINTS_PROFILE        = 0x0002
UVC_H264_BMHINTS_RATECONTROL    = 0x0004
UVC_H264_BMHINTS_USAGE          = 0x0008
UVC_H264_BMHINTS_SLICEMODE      = 0x0010
UVC_H264_BMHINTS_SLICEUNITS     = 0x0020
UVC_H264_BMHINTS_MVCVIEW        = 0x0040
UVC_H264_BMHINTS_TEMPORAL       = 0x0080
UVC_H264_BMHINTS_SNR            = 0x0100
UVC_H264_BMHINTS_SPATIAL        = 0x0200
UVC_H264_BMHINTS_SPATIAL_RATIO  = 0x0400
UVC_H264_BMHINTS_FRAME_INTERVAL = 0x0800
UVC_H264_BMHINTS_LEAKY_BKT_SIZE = 0x1000
UVC_H264_BMHINTS_BITRATE        = 0x2000
UVC_H264_BMHINTS_ENTROPY        = 0x4000
UVC_H264_BMHINTS_IFRAMEPERIOD   = 0x8000

UVC_H264_PROFILE_CONSTRAINED_BASELINE = 0x4240
UVC_H264_PROFILE_BASELINE = 0x4200
UVC_H264_PROFILE_MAIN = 0x4D00
UVC_H264_PROFILE_HIGH = 0x6400

UVC_H264_RATECONTROL_CBR = 0x01
UVC_H264_RATECONTROL_VBR = 0x02
UVC_H264_RATECONTROL_CONST_QP = 0x03

UVC_H264_QP_STEPS_I_FRAME_TYPE    = 0x01
UVC_H264_QP_STEPS_P_FRAME_TYPE    = 0x02
UVC_H264_QP_STEPS_B_FRAME_TYPE    = 0x04
UVC_H264_QP_STEPS_ALL_FRAME_TYPES = 0x07

UVC_H264_SLICE_MODE_OFF = 0x00
UVC_H264_SLICE_MODE_BITS_PER_SLICE = 0x01
UVC_H264_SLICE_MODE_MBS_PER_SLICE = 0x02
UVC_H264_SLICE_MODE_SLICES_PER_FRAME = 0x03

UVC_H264_ENTROPY_CAVLC = 0x00
UVC_H264_ENTROPY_CABAC = 0x01

UVC_H264_USAGE_REALTIME = 0x01
UVC_H264_USAGE_BROADCAST = 0x02
UVC_H264_USAGE_STORAGE = 0x03

STREAM_MUX_DISABLED = 0x00
STREAM_MUX_ENABLED = 0x01
STREAM_MUX_H264 = 0x02
STREAM_MUX_YUYV = 0x04
STREAM_MUX_NV12 = 0x08
STREAM_MUX_CONTAINER_MJPEG = 0x40

STREAM_MUX_H264_ENABLED = STREAM_MUX_H264 | STREAM_MUX_ENABLED
STREAM_MUX_YUYV_ENABLED = STREAM_MUX_YUYV | STREAM_MUX_ENABLED
STREAM_MUX_NV12_ENABLED = STREAM_MUX_NV12 | STREAM_MUX_ENABLED

def to_buf(b):
    return ctypes.create_string_buffer(b)

class uvcx_video_config_probe_commit(ctypes.Structure):
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


def get_length_xu_control(fd, unit_id, selector):
    length = ctypes.c_uint16(0)

    xu_ctrl_query = uvc_xu_control_query()
    xu_ctrl_query.unit = unit_id
    xu_ctrl_query.selector = selector
    xu_ctrl_query.query = UVC_GET_LEN
    xu_ctrl_query.size = 2 # sizeof(length)
    xu_ctrl_query.data = ctypes.cast(ctypes.pointer(length), ctypes.c_void_p)

    try:
       ioctl(fd, UVCIOC_CTRL_QUERY, xu_ctrl_query)
    except Exception as e:
        logging.warning(f'uvcx: UVCIOC_CTRL_QUERY (GET_LEN) - Fd: {fd} - Error: {e}')

    return length

def query_xu_control(fd, unit_id, selector, query, data):
    len = get_length_xu_control(fd, unit_id, selector)

    xu_ctrl_query = uvc_xu_control_query()
    xu_ctrl_query.unit = unit_id
    xu_ctrl_query.selector = selector
    xu_ctrl_query.query = query
    xu_ctrl_query.size = len
    xu_ctrl_query.data = ctypes.cast(ctypes.pointer(data), ctypes.c_void_p)

    try:
        ioctl(fd, UVCIOC_CTRL_QUERY, xu_ctrl_query)
    except Exception as e:
        logging.warning(f'uvcx: UVCIOC_CTRL_QUERY ({query}) - Fd: {fd} - Error: {e}')


def request_h264_frame_type(fd, unit_id, type):
    picture_type_req = uvcx_picture_type_control_t()
    picture_type_req.wLayerID = 0
    picture_type_req.wPicType = type

    query_xu_control(fd, unit_id, UVCX_PICTURE_TYPE_CONTROL, UVC_SET_CUR, picture_type_req)

def request_h264_idr(fd, unit_id):
    request_h264_frame_type(fd, unit_id, PICTURE_TYPE_IDR)

def get_h264_default_config(fd, unit_id):
    config = uvcx_video_config_probe_commit()
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_PROBE, UVC_GET_DEF, config)
    return config

def get_h264_minimum_config(fd, unit_id):
    config = uvcx_video_config_probe_commit()
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_PROBE, UVC_GET_MIN, config)
    return config

def get_h264_maximum_config(fd, unit_id):
    config = uvcx_video_config_probe_commit()
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_PROBE, UVC_GET_MAX, config)
    return config

def get_h264_current_config(fd, unit_id):
    config = uvcx_video_config_probe_commit()
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_PROBE, UVC_GET_CUR, config)
    return config

def get_h264_resolution_config(fd, unit_id):
    config = uvcx_video_config_probe_commit()
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_PROBE, UVC_GET_RES, config)
    return config

def set_h264_config(fd, unit_id, config):
    query_xu_control(fd, unit_id, UVCX_VIDEO_CONFIG_COMMIT, UVC_SET_CUR, config)

def get_h264_version(fd, unit_id):
    uvcx_version = uvcx_version_t()
    query_xu_control(fd, unit_id, UVCX_VERSION, UVC_GET_CUR, uvcx_version)
    return uvcx_version.wVersion

# the usb device descriptors file contains the descriptors in a binary format
# the byte before the extension guid is the extension unit id
def find_unit_id_in_sysfs(device, guid):
    if os.path.islink(device):
        device = os.readlink(device)
    device = os.path.basename(device)
    descfile = f'/sys/class/video4linux/{device}/../../../descriptors'
    if not os.path.isfile(descfile):
        return 0

    try:
        with open(descfile, 'rb') as f:
            descriptors = f.read()
            guid_start = descriptors.find(guid)
            if guid_start > 0:
                return descriptors[guid_start - 1]
    except Exception as e:
        logging.warning(f'uvcx: failed to read uvc xu unit id from {descfile}: {e}')

    return 0

def find_usb_ids_in_sysfs(device):
    if os.path.islink(device):
        device = os.readlink(device)
    device = os.path.basename(device)
    vendorfile = f'/sys/class/video4linux/{device}/../../../idVendor'
    productfile = f'/sys/class/video4linux/{device}/../../../idProduct'
    if not os.path.isfile(vendorfile) or not os.path.isfile(productfile):
        return 0

    vendor = ''
    try:
        with open(vendorfile, 'r') as f:
            vendor = f.read().strip()
    except Exception as e:
        logging.warning(f'uvcx: failed to read usb vendor id from {vendorfile}: {e}')

    product = ''
    try:
        with open(productfile, 'r') as f:
            product = f.read().strip()
    except Exception as e:
        logging.warning(f'uvcx: failed to read usb product id from {productfile}: {e}')

    return vendor+':'+product
