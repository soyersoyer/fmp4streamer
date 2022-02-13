import logging, os.path

import uvcx

class UVCXCtrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = find_unit_id_in_sysfs(device, uvcx.H264_XU_GUID)
        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0

    def h264_muxing_supported(self):
        return self.supported() and (self.maximum_config.bStreamMuxOption & uvcx.STREAM_MUX_H264) > 0

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        self.default_config = uvcx.get_default_config(self.fd, self.unit_id)
        self.minimum_config = uvcx.get_minimum_config(self.fd, self.unit_id)
        self.maximum_config = uvcx.get_maximum_config(self.fd, self.unit_id)
        self.current_config = uvcx.get_current_config(self.fd, self.unit_id)
        self.ctrls = [
            UVCXCtrl(
                'uvcx_h264_stream_mux',
                self.minimum_config.bStreamMuxOption,
                self.maximum_config.bStreamMuxOption,
                self.default_config.bStreamMuxOption,
                uvcx.UVC_H264_BMHINTS_NONE,
                'bStreamMuxOption',
                {
                    uvcx.STREAM_MUX_DISABLED: 'None',
                    uvcx.STREAM_MUX_H264_ENABLED: 'H264',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_width',
                self.minimum_config.wWidth,
                self.maximum_config.wWidth,
                self.default_config.wWidth,
                uvcx.UVC_H264_BMHINTS_RESOLUTION,
                'wWidth',
            ),
            UVCXCtrl(
                'uvcx_h264_height',
                self.minimum_config.wHeight,
                self.maximum_config.wHeight,
                self.default_config.wHeight,
                uvcx.UVC_H264_BMHINTS_RESOLUTION,
                'wHeight',
            ),
            UVCXCtrl(
                'uvcx_h264_frame_interval',
                self.minimum_config.dwFrameInterval,
                self.maximum_config.dwFrameInterval,
                self.default_config.dwFrameInterval,
                uvcx.UVC_H264_BMHINTS_FRAME_INTERVAL,
                'dwFrameInterval',
            ),
            UVCXCtrl(
                'uvcx_h264_bitrate',
                self.minimum_config.dwBitRate,
                self.maximum_config.dwBitRate,
                self.default_config.dwBitRate,
                uvcx.UVC_H264_BMHINTS_BITRATE,
                'dwBitRate',
            ),
            UVCXCtrl(
                'uvcx_h264_rate_control_mode',
                self.minimum_config.bRateControlMode,
                self.maximum_config.bRateControlMode,
                self.default_config.bRateControlMode,
                uvcx.UVC_H264_BMHINTS_RATECONTROL,
                'bRateControlMode',
                {
                    uvcx.UVC_H264_RATECONTROL_CBR: 'CBR',
                    uvcx.UVC_H264_RATECONTROL_VBR: 'VBR',
                    uvcx.UVC_H264_RATECONTROL_CONST_QP: 'Const QP',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_profile',
                self.minimum_config.wProfile,
                self.maximum_config.wProfile,
                self.default_config.wProfile,
                uvcx.UVC_H264_BMHINTS_PROFILE,
                'wProfile',
                {
                    uvcx.UVC_H264_PROFILE_CONSTRAINED_BASELINE: 'Constrained',
                    uvcx.UVC_H264_PROFILE_BASELINE: 'Baseline',
                    uvcx.UVC_H264_PROFILE_MAIN: 'Main',
                    uvcx.UVC_H264_PROFILE_HIGH: 'High',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_i_frame_period',
                self.minimum_config.wIFramePeriod,
                self.maximum_config.wIFramePeriod,
                self.default_config.wIFramePeriod,
                uvcx.UVC_H264_BMHINTS_IFRAMEPERIOD,
                'wIFramePeriod',
            ),
        ]

    def print_ctrls(self):
        for c in self.ctrls:
            value = getattr(self.current_config, c.sname)
            print(c.name, end = ' = ')
            if not c.menu:
                print('%a\t(' % value, 'default:', c.default, 'min:', c.minimum, 'max:', c.maximum, end = ')\n')
            else:
                valmenu = c.menu.get(value)
                defmenu = c.menu.get(c.default)
                print(f'{valmenu if valmenu else value}\t(', end = ' ')
                if defmenu:
                    print(f'default: {defmenu}', end = ' ')
                print('values:', end = ' ')
                for k, v in c.menu.items():
                    print('%a' % v, end = ' ')
                print(')')

    def setup_uvcx_ctrls(self, params):
        if not self.supported():
            return

        for k, v in params.items():
            if not k.startswith('uvcx_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                logging.warning(f'uvcxctrls: can\'t find {k} uvcx control')
                continue
            if ctrl.menu:
                menukey  = find_by_value(ctrl.menu, v)
                if menukey == None:
                    logging.warning(f'uvcxctrls: can\'t find {v} in {ctrl.menu}')
                    continue
                setattr(self.current_config, ctrl.sname, menukey)
            else:
                setattr(self.current_config, ctrl.sname, int(v))
            self.current_config.bmHints |= ctrl.hint

        uvcx.video_commit(self.fd, self.unit_id, self.current_config)
        current = uvcx.get_current_config(self.fd, self.unit_id)

        for k, v in params.items():
            if not k.startswith('uvcx_'):
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
                logging.warning(f'uvcxctrls: failed to set {k} to {desired_value}, current value {current_value}\n')

    def request_h264_idr(self):
        uvcx.request_h264_frame_type(self.fd, self.unit_id, uvcx.PICTURE_TYPE_IDR)

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

def find_unit_id_in_sysfs(device, guid):
    device = device.replace('/dev/', '')
    descfile = f'/sys/class/video4linux/{device}/../../../descriptors'
    if not os.path.isfile(descfile):
        descfile = f'/sys/class/video4linux/{device}/../../descriptors'
        if not os.path.isfile(descfile):
            return 0

    try:
        with open(descfile, 'rb') as f:
            descriptors = f.read()
            guid_start = descriptors.find(guid)
            if guid_start:
                return descriptors[guid_start - 1]
    except Exception as e:
        logging.warning(f'uvcxctrls: failed to read uvc xu unit id from {descfile}')

    return 0



class UVCXCtrl:
    def __init__(self, name, minimum, maximum, default, hint, sname, menu = None):
        self.name = name
        self.minimum = minimum
        self.maximum = maximum
        self.default = default
        self.hint = hint
        self.sname = sname
        self.menu = menu
