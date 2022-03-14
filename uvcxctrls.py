import logging

import uvcx

class UVCXH264Ctrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = uvcx.find_unit_id_in_sysfs(device, uvcx.H264_XU_GUID)
        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0

    def h264_muxing_supported(self):
        return self.supported() and (self.maximum_config.bStreamMuxOption & uvcx.STREAM_MUX_H264) > 0

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        self.default_config = uvcx.get_h264_default_config(self.fd, self.unit_id)
        self.minimum_config = uvcx.get_h264_minimum_config(self.fd, self.unit_id)
        self.maximum_config = uvcx.get_h264_maximum_config(self.fd, self.unit_id)
        self.current_config = uvcx.get_h264_current_config(self.fd, self.unit_id)
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
            UVCXCtrl(
                'uvcx_h264_slice_mode',
                self.minimum_config.wSliceMode,
                self.maximum_config.wSliceMode,
                self.default_config.wSliceMode,
                uvcx.UVC_H264_BMHINTS_SLICEMODE,
                'wSliceMode',
                {
                    uvcx.UVC_H264_SLICE_MODE_OFF: 'Off',
                    uvcx.UVC_H264_SLICE_MODE_BITS_PER_SLICE: 'BitsPerSlice',
                    uvcx.UVC_H264_SLICE_MODE_MBS_PER_SLICE: 'MBsPerSlice',
                    uvcx.UVC_H264_SLICE_MODE_SLICES_PER_FRAME: 'SlicesPerFrame',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_slice_units',
                self.minimum_config.wSliceUnits,
                self.maximum_config.wSliceUnits,
                self.default_config.wSliceUnits,
                uvcx.UVC_H264_BMHINTS_SLICEUNITS,
                'wSliceUnits',
            ),
            UVCXCtrl(
                'uvcx_h264_entropy',
                self.minimum_config.bEntropyCABAC,
                self.maximum_config.bEntropyCABAC,
                self.default_config.bEntropyCABAC,
                uvcx.UVC_H264_BMHINTS_ENTROPY,
                'bEntropyCABAC',
                {
                    uvcx.UVC_H264_ENTROPY_CAVLC: 'CAVLC',
                    uvcx.UVC_H264_ENTROPY_CABAC: 'CABAC',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_usage',
                self.minimum_config.bUsageType,
                self.maximum_config.bUsageType,
                self.default_config.bUsageType,
                uvcx.UVC_H264_BMHINTS_USAGE,
                'bUsageType',
                {
                    uvcx.UVC_H264_USAGE_REALTIME: 'Realtime',
                    uvcx.UVC_H264_USAGE_BROADCAST: 'Broadcast',
                    uvcx.UVC_H264_USAGE_STORAGE: 'Storage',
                }
            ),
            UVCXCtrl(
                'uvcx_h264_leaky_bucket_size',
                self.minimum_config.wLeakyBucketSize,
                self.maximum_config.wLeakyBucketSize,
                self.default_config.wLeakyBucketSize,
                uvcx.UVC_H264_BMHINTS_LEAKY_BKT_SIZE,
                'wLeakyBucketSize',
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

    def setup_ctrls(self, params):
        if not self.supported():
            return

        for k, v in params.items():
            if not k.startswith('uvcx_h264_'):
                continue
            ctrl = find_by_name(self.ctrls, k)
            if ctrl == None:
                logging.warning(f'UVCXH264Ctrls: can\'t find {k} control')
                continue
            if ctrl.menu:
                menukey  = find_by_value(ctrl.menu, v)
                if menukey == None:
                    logging.warning(f'UVCXH264Ctrls: can\'t find {v} in {list(ctrl.menu.values())}')
                    continue
                setattr(self.current_config, ctrl.sname, menukey)
            else:
                setattr(self.current_config, ctrl.sname, int(v))
            self.current_config.bmHints |= ctrl.hint

        uvcx.set_h264_config(self.fd, self.unit_id, self.current_config)
        current = uvcx.get_h264_current_config(self.fd, self.unit_id)

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
                logging.warning(f'UVCXH264Ctrls: failed to set {k} to {desired_value}, current value {current_value}\n')

    def request_h264_idr(self):
        uvcx.request_h264_frame_type(self.fd, self.unit_id, uvcx.PICTURE_TYPE_IDR)


class UVCXKiyoProCtrls:
    def __init__(self, device, fd):
        self.device = device
        self.fd = fd
        self.unit_id = uvcx.find_unit_id_in_sysfs(device, uvcx.UVC_EU1_GUID)
        self.usb_ids = uvcx.find_usb_ids_in_sysfs(device)
        self.get_device_controls()

    def supported(self):
        return self.unit_id != 0 and self.usb_ids == '1532:0e05'

    def get_device_controls(self):
        if not self.supported():
            self.ctrls = []
            return

        # getting the values doesn't work in this way, maybe later in newer firmwares
        #current = uvcx.to_buf(uvcx.UVC_KIYO_PRO_LOAD)
        #uvcx.query_xu_control(self.fd, self.unit_id, uvcx.UVCX_VIDEO_CONFIG_COMMIT, uvcx.UVC_GET_CUR, current)
        #print('current:', list(current))

        self.ctrls = [
            KIYOCtrl(
                'uvcx_kiyo_pro_af_mode',
                {
                    uvcx.UVC_KIYO_PRO_AF_PASSIVE: 'Passive',
                    uvcx.UVC_KIYO_PRO_AF_RESPONSIVE: 'Responsive',
                }
            ),
            KIYOCtrl(
                'uvcx_kiyo_pro_hdr',
                {
                    uvcx.UVC_KIYO_PRO_HDR_OFF: 'Off',
                    uvcx.UVC_KIYO_PRO_HDR_ON: 'On',
                }
            ),
            KIYOCtrl(
                'uvcx_kiyo_pro_hdr_mode',
                {
                    uvcx.UVC_KIYO_PRO_HDR_BRIGHT: 'Bright',
                    uvcx.UVC_KIYO_PRO_HDR_DARK: 'Dark',
                }
            ),
            KIYOCtrl(
                'uvcx_kiyo_pro_fov',
                {
                    uvcx.UVC_KIYO_PRO_FOV_WIDE: 'Wide',
                    uvcx.UVC_KIYO_PRO_FOV_MEDIUM: 'Medium',
                    uvcx.UVC_KIYO_PRO_FOV_NARROW: 'Narrow',
                }
            ),
        ]
        self.befores = {
            uvcx.UVC_KIYO_PRO_FOV_MEDIUM: uvcx.UVC_KIYO_PRO_FOV_MEDIUM_PRE,
            uvcx.UVC_KIYO_PRO_FOV_NARROW: uvcx.UVC_KIYO_PRO_FOV_NARROW_PRE,
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
                logging.warning(f'UVCXKiyoProCtrls: can\'t find {k} control')
                continue
            menukey = find_by_value(ctrl.menu, v)
            if menukey == None:
                logging.warning(f'UVCXKiyoProCtrls: can\'t find {v} in {list(ctrl.menu.values())}')
                continue
            ctrl.value = menukey

            before = self.befores.get(ctrl.value)
            if before:
                uvcx.query_xu_control(self.fd, self.unit_id, uvcx.UVCX_VIDEO_CONFIG_PROBE, uvcx.UVC_SET_CUR, uvcx.to_buf(before))
            
            uvcx.query_xu_control(self.fd, self.unit_id, uvcx.UVCX_VIDEO_CONFIG_PROBE, uvcx.UVC_SET_CUR, uvcx.to_buf(ctrl.value))

        # Don't need to save the state into the camera, uncomment if you want to save
        #uvcx.query_xu_control(self.fd, self.unit_id, uvcx.UVCX_VIDEO_CONFIG_PROBE, uvcx.UVC_SET_CUR, uvcx.to_buf(uvcx.UVC_KIYO_PRO_SAVE))



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



class UVCXCtrl:
    def __init__(self, name, minimum, maximum, default, hint, sname, menu = None):
        self.name = name
        self.minimum = minimum
        self.maximum = maximum
        self.default = default
        self.hint = hint
        self.sname = sname
        self.menu = menu

class KIYOCtrl:
    def __init__(self, name, menu = None):
        self.name = name
        self.value = None
        self.menu = menu
