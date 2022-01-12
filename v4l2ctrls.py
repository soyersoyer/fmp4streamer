import logging
from fcntl import ioctl

import v4l2

class V4L2Ctrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.get_device_controls()


    def setup_v4l2_ctrls(self, params):
        for k, v in params.items():
            if k in ['width', 'height', 'fps', 'capture_format', 'encoder']:
                continue
            ctrl = self.find_ctrl(self.ctrls, k)
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

        self.ctrls = ctrls

    def print_ctrls(self):
        print(f'\nV4L2 controls for {self.device}\n')
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
