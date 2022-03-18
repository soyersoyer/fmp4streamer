import uvcx, logging

# UVC EU1 extension GUID 23e49ed0-1178-4f31-ae52-d2fb8a8d3b48
UVC_EU1_GUID = b'\xd0\x9e\xe4\x23\x78\x11\x31\x4f\xae\x52\xd2\xfb\x8a\x8d\x3b\x48'

# UVC EU2 extension GUID 2c49d16a-32b8-4485-3ea8-643a152362f2
UVC_EU2_GUID = b'\x6a\xd1\x49\x2c\xb8\x32\x85\x44\x3e\xa8\x64\x3a\x15\x23\x62\xf2'

EU1_SET_ISP = 0x01
EU1_GET_ISP_RESULT = 0x02

AF_RESPONSIVE = b'\xff\x06\x00\x00\x00\x00\x00\x00'
AF_PASSIVE =    b'\xff\x06\x01\x00\x00\x00\x00\x00'

HDR_OFF =       b'\xff\x02\x00\x00\x00\x00\x00\x00'
HDR_ON =        b'\xff\x02\x01\x00\x00\x00\x00\x00'

HDR_DARK =      b'\xff\x07\x00\x00\x00\x00\x00\x00'
HDR_BRIGHT =    b'\xff\x07\x01\x00\x00\x00\x00\x00'

FOV_WIDE =       b'\xff\x01\x00\x03\x00\x00\x00\x00'
FOV_MEDIUM_PRE = b'\xff\x01\x00\x03\x01\x00\x00\x00'
FOV_MEDIUM =     b'\xff\x01\x01\x03\x01\x00\x00\x00'
FOV_NARROW_PRE = b'\xff\x01\x00\x03\x02\x00\x00\x00'
FOV_NARROW =     b'\xff\x01\x01\x03\x02\x00\x00\x00'

GRAYSCALE_OFF =  b'\xff\x03\x00\x00\x00\x00\x00\x00'
GRAYSCALE_ON =   b'\xff\x03\x01\x00\x00\x00\x00\x00'

# Unknown yet, the synapse sends it in start
UNKNOWN =       b'\xff\x04\x00\x00\x00\x00\x00\x00'

# save previous values to the camera
SAVE =          b'\xc0\x03\xa8\x00\x00\x00\x00\x00'

LOAD =          b'\x00\x00\x00\x00\x00\x00\x00\x00'

class KiyoProCtrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = uvcx.find_unit_id_in_sysfs(device, UVC_EU1_GUID)
        self.usb_ids = uvcx.find_usb_ids_in_sysfs(device)
        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0 and self.usb_ids == '1532:0e05'

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        # getting the values doesn't work in this way, maybe later in newer firmwares
        #current = uvcx.to_buf(LOAD)
        #uvcx.query_xu_control(self.fd, self.unit_id, EU1_GET_ISP_RESULT, uvcx.UVC_GET_CUR, current)
        #print('current:', list(current))

        self.ctrls = [
            Ctrl(
                'uvcx_kiyo_pro_af_mode',
                {
                    AF_PASSIVE: 'Passive',
                    AF_RESPONSIVE: 'Responsive',
                }
            ),
            Ctrl(
                'uvcx_kiyo_pro_hdr',
                {
                    HDR_OFF: 'Off',
                    HDR_ON: 'On',
                }
            ),
            Ctrl(
                'uvcx_kiyo_pro_hdr_mode',
                {
                    HDR_BRIGHT: 'Bright',
                    HDR_DARK: 'Dark',
                }
            ),
            Ctrl(
                'uvcx_kiyo_pro_fov',
                {
                    FOV_WIDE: 'Wide',
                    FOV_MEDIUM: 'Medium',
                    FOV_NARROW: 'Narrow',
                }
            ),
            Ctrl(
                'uvcx_kiyo_pro_grayscale',
                {
                    GRAYSCALE_OFF: 'Off',
                    GRAYSCALE_ON: 'On',
                }
            ),
        ]
        self.befores = {
            FOV_MEDIUM: FOV_MEDIUM_PRE,
            FOV_NARROW: FOV_NARROW_PRE,
        }
    
    def print_ctrls(self):
        for c in self.ctrls:
            print(c.name, end = ' = ')
            valmenu = c.menu.get(c.value)
            print(f'{valmenu if valmenu else "Unset [Camera setting]"}\t(', end = ' ')
            print('values:', end = ' ')
            for k, v in c.menu.items():
                print('%a' % v, end = ' ')
            print(')')

    def setup_ctrls(self, params):
        if not self.supported():
            return

        for k, v in params.items():
            if not k.startswith('uvcx_kiyo_pro_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                logging.warning(f'KiyoProCtrls: can\'t find {k} control in {[c.name for c in self.ctrls]}')
                continue
            menukey = find_by_value(ctrl.menu, v)
            if menukey == None:
                logging.warning(f'KiyoProCtrls: can\'t find {v} in {list(ctrl.menu.values())}')
                continue
            ctrl.value = menukey

            before = self.befores.get(ctrl.value)
            if before:
                uvcx.query_xu_control(self.fd, self.unit_id, EU1_SET_ISP, uvcx.UVC_SET_CUR, uvcx.to_buf(before))
            
            uvcx.query_xu_control(self.fd, self.unit_id, EU1_SET_ISP, uvcx.UVC_SET_CUR, uvcx.to_buf(ctrl.value))

        # Don't need to save the state into the camera, uncomment if you want to save
        #uvcx.query_xu_control(self.fd, self.unit_id, EU1_SET_ISP, uvcx.UVC_SET_CUR, uvcx.to_buf(SAVE))

class Ctrl:
    def __init__(self, name, menu = None):
        self.name = name
        self.value = None
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
