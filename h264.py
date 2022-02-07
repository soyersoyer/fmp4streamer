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
        self.nalus = []
        self.frame_secs = 0
        self.frame_usecs = 0
    
    def write_buf(self, seq, buf):
        nalus = []
        last = 0
        while last != -1:
            next = buf.buffer.find(H264NALU.DELIMITER, last + 4, buf.bytesused)
            nalus.append(memoryview(buf.buffer)[last + 4 : next if next != -1 else buf.bytesused])
            last = next

        if seq == 0:
            for nalu in nalus:
                if len(nalu) and H264NALU.get_type(nalu) == H264NALU.SPSTYPE:
                    self.sps = bytes(nalu)
                if len(nalu) and H264NALU.get_type(nalu) == H264NALU.PPSTYPE:
                    self.pps = bytes(nalu)
            if not self.sps or not self.pps:
                logging.error('H264Parser: can\'t read SPS and PPS from the first frame')

        with self.condition:
            self.nalus = nalus
            self.frame_secs = buf.timestamp.secs
            self.frame_usecs = buf.timestamp.usecs
            self.condition.notify_all()

    def read_frame(self):
        with self.condition:
            self.condition.wait()
            return self.nalus, self.frame_secs, self.frame_usecs
