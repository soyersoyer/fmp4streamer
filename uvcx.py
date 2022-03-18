import v4l2, ctypes, logging, os.path
from fcntl import ioctl

#
# ioctl structs, codes for uvc extensions
#

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


def to_buf(b):
    return ctypes.create_string_buffer(b)

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
        return ''

    vendor = read_usb_id_from(vendorfile)
    product = read_usb_id_from(productfile)

    return vendor + ':' + product

def read_usb_id_from(file):
    id = ''
    try:
        with open(file, 'r') as f:
            id = f.read().strip()
    except Exception as e:
        logging.warning(f'uvcx: failed to read usb id from {file}: {e}')
    return id
