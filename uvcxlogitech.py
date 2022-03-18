import uvcx, logging

# Logitech peripheral GUID ffe52d21-8030-4e2c-82d9-f587d00540bd
LOGITECH_PERIPHERAL_GUID = b'\x21\x2d\xe5\xff\x30\x80\x2c\x4e\x82\xd9\xf5\x87\xd0\x05\x40\xbd'

LOGITECH_PERIPHERAL_LED1_SEL = 0x09
LOGITECH_PERIPHERAL_LED1_LEN = 5

LOGITECH_PERIPHERAL_LED1_MODE_OFFSET = 1
LOGITECH_PERIPHERAL_LED1_MODE_OFF =   0x00
LOGITECH_PERIPHERAL_LED1_MODE_ON =    0x01
LOGITECH_PERIPHERAL_LED1_MODE_BLINK = 0x02
LOGITECH_PERIPHERAL_LED1_MODE_AUTO =  0x03

LOGITECH_PERIPHERAL_LED1_FREQUENCY_OFFSET = 3

class LogitechCtrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = uvcx.find_unit_id_in_sysfs(device, LOGITECH_PERIPHERAL_GUID)

        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        self.ctrls = [
            Ctrl(
                'uvcx_logitech_led1_mode',
                LOGITECH_PERIPHERAL_LED1_SEL,
                LOGITECH_PERIPHERAL_LED1_LEN,
                LOGITECH_PERIPHERAL_LED1_MODE_OFFSET,
                {
                    LOGITECH_PERIPHERAL_LED1_MODE_OFF: 'Off',
                    LOGITECH_PERIPHERAL_LED1_MODE_ON: 'On',
                    LOGITECH_PERIPHERAL_LED1_MODE_BLINK: 'Blink',
                    LOGITECH_PERIPHERAL_LED1_MODE_AUTO: 'Auto'
                }
            ),
            Ctrl(
                'uvcx_logitech_led1_frequency',
                LOGITECH_PERIPHERAL_LED1_SEL,
                LOGITECH_PERIPHERAL_LED1_LEN,
                LOGITECH_PERIPHERAL_LED1_FREQUENCY_OFFSET,
            ),
        ]

    def print_ctrls(self):
        for c in self.ctrls:

            default_config = uvcx.to_buf(bytes(c.len))
            minimum_config = uvcx.to_buf(bytes(c.len))
            maximum_config = uvcx.to_buf(bytes(c.len))
            current_config = uvcx.to_buf(bytes(c.len))

            uvcx.query_xu_control(self.fd, self.unit_id, c.selector, uvcx.UVC_GET_DEF, default_config)
            uvcx.query_xu_control(self.fd, self.unit_id, c.selector, uvcx.UVC_GET_MIN, minimum_config)
            uvcx.query_xu_control(self.fd, self.unit_id, c.selector, uvcx.UVC_GET_MAX, maximum_config)
            uvcx.query_xu_control(self.fd, self.unit_id, c.selector, uvcx.UVC_GET_CUR, current_config)
            
            default = default_config[c.offset][0]
            minimum = minimum_config[c.offset][0]
            maximum = maximum_config[c.offset][0]
            value = current_config[c.offset][0]

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
            if not k.startswith('uvcx_logitech_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                logging.warning(f'LogitechCtrls: can\'t find {k} control in {[c.name for c in self.ctrls]}')
                continue
            if ctrl.menu:
                menukey  = find_by_value(ctrl.menu, v)
                if menukey == None:
                    logging.warning(f'LogitechCtrls: can\'t find {v} in {[v for v in ctrl.menu.values()]}')
                    continue
                desired = menukey
            else:
                desired = int(v)

            current_config = uvcx.to_buf(bytes(ctrl.len))
            uvcx.query_xu_control(self.fd, self.unit_id, ctrl.selector, uvcx.UVC_GET_CUR, current_config)
            current_config[ctrl.offset] = desired
            uvcx.query_xu_control(self.fd, self.unit_id, ctrl.selector, uvcx.UVC_SET_CUR, current_config)
            uvcx.query_xu_control(self.fd, self.unit_id, ctrl.selector, uvcx.UVC_GET_CUR, current_config)
            current = current_config[ctrl.offset][0]

            if ctrl.menu:
                desired = ctrl.menu.get(desired, desired)
                current = ctrl.menu.get(current, current)
            if current != desired:
                logging.warning(f'LogitechCtrls: failed to set {k} to {desired}, current value {current}\n')



class Ctrl:
    def __init__(self, name, selector, len, offset, menu = None):
        self.name = name
        self.selector = selector
        self.len = len
        self.offset = offset
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
