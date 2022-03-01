import logging, struct
from threading import Condition

class H264NALU:
    DELIMITER = b'\x00\x00\x00\x01'

    NONIDRTYPE = 1
    IDRTYPE = 5
    SPSTYPE = 7
    PPSTYPE = 8

    @staticmethod
    def get_type(nalubytes):
        return nalubytes[0] & 0x1f

JPEG_SOI = b'\xff\xd8' # JPEG Start Of Image
JPEG_APP4 = b'\xff\xe4' # JPEG APP4 marker to store metadata (H264 frame)

class H264Parser(object):
    def __init__(self):
        self.sps = None
        self.pps = None
        self.condition = Condition()
        self.nalus = []
        self.frame_secs = 0
        self.frame_usecs = 0

    def write_buf(self, seq, buf):
        nalus = []

        # find H264 inside MJPG
        if buf.buffer.find(JPEG_SOI, 0, 2) == 0:
            app4_start = buf.buffer.find(JPEG_APP4)
            if app4_start != -1:
                header_length = struct.unpack_from('<H', buf.buffer, app4_start + 6)[0]
                payload_start = app4_start + 4 + header_length
                payload_size = struct.unpack_from('<I', buf.buffer, payload_start)[0]
                # 4 byte size + 4 byte DELIMITER
                start = payload_start + 8
                # 4 byte size + payload + n x segment header (app4+len)
                end = payload_start + 4 + payload_size + (payload_size >> 16) * 4
                next_seg_start = app4_start + 65535
                while start < end:
                    next = buf.buffer.find(H264NALU.DELIMITER, start, end)
                    if next == -1:
                        next = end
                    if next > next_seg_start:
                        nalu = buf.buffer[start : next_seg_start]
                        while next > next_seg_start:
                            nalu += buf.buffer[next_seg_start + 4 : min(next, next_seg_start + 65535)]
                            next_seg_start += 65535
                        nalus.append(nalu)
                    else:
                        nalus.append(memoryview(buf.buffer)[start : next])
                    start = next + 4
        else:
            start = 4
            end = buf.bytesused
            while start < end:
                next = buf.buffer.find(H264NALU.DELIMITER, start, end)
                if next == -1:
                    next = end
                nalus.append(memoryview(buf.buffer)[start : next])
                start = next + 4

        if seq == 0:
            for nalu in nalus:
                if len(nalu) and H264NALU.get_type(nalu) == H264NALU.SPSTYPE:
                    self.sps = bytes(nalu)
                if len(nalu) and H264NALU.get_type(nalu) == H264NALU.PPSTYPE:
                    self.pps = bytes(nalu)
            if not self.sps or not self.pps:
                logging.error('H264Parser: Invalid H264 first frame. Unable to read SPS and PPS.')

        with self.condition:
            self.nalus = nalus
            self.frame_secs = buf.timestamp.secs
            self.frame_usecs = buf.timestamp.usecs
            self.condition.notify_all()

    def read_frame(self):
        with self.condition:
            self.condition.wait()
            return self.nalus, self.frame_secs, self.frame_usecs
