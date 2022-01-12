import logging
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


class H264Parser(object):
    def __init__(self):
        self.sps = None
        self.pps = None
        self.condition = Condition()
        self.frame_data = None
        self.frame_secs = 0
        self.frame_usecs = 0
    
    def write_buf(self, seq, buf):
        if seq == 0:
            self.read_header(buf)
        else:
            self.process_image(buf)

    def read_header(self, buf):
        data = buf.buffer.read(buf.bytesused)
        nalus = data.split(H264NALU.DELIMITER)

        if len(nalus) > 1 and len(nalus[0]) == 0:
            nalus.pop(0)

        for nalu in nalus:
            if len(nalu) and H264NALU.get_type(nalu) == H264NALU.SPSTYPE:
                self.sps = nalu
            if len(nalu) and H264NALU.get_type(nalu) == H264NALU.PPSTYPE:
                self.pps = nalu
        if not self.sps or not self.pps:
            logging.error('V4L2H264Parser: can\'t read SPS and PPS from the first frame')
    
    def process_image(self, buf):
        data = memoryview(buf.buffer)[4 : buf.bytesused]

        with self.condition:
            self.frame_data = data
            self.frame_secs = buf.timestamp.secs
            self.frame_usecs = buf.timestamp.usecs
            self.condition.notify_all()

    def read_frame(self):
        with self.condition:
            self.condition.wait()
            return self.frame_data, self.frame_secs, self.frame_usecs
