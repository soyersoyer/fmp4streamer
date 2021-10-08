import io

# References:
# ISO/IEC 14496 Part 12
# ISO/IEC 14496 Part 15

# ISO/IEC 14496 Part 14 is not used.

def writeInt(w, value, n):
    b = bytearray(n)
    for i in range(n):
        b[n-i-1] = value & 0xff
        value >>= 8
    w.write(b)


def writeString(w, s):
    w.write(s)


def writeTag(w, tag, cb):
    b = io.BytesIO()
    cb(b)                     # callback
    writeInt(w, len(b.getvalue())+8, 4) # box size
    writeString(w, tag)       # box type
    w.write(b.getvalue())     # box content


def writeFTYP(w):
    writeTag(w, b"ftyp", lambda w: (
        writeString(w, b"isom"),                 # major brand
        writeInt(w, 0x200, 4),                  # minor version
        writeString(w, b"isomiso2iso5avc1mp41")  # compatible brands
    ))

def writeMOOV(w, width, height):
    writeTag(w, b"moov", lambda w: (
        writeMVHD(w),
        writeTRAK(w, width, height),
        writeMVEX(w),
    ))

def writeMVHD(w):
    writeTag(w, b"mvhd", lambda w: (
        writeInt(w, 0, 4),          # version and flags
        writeInt(w, 0, 4),          # creation time
        writeInt(w, 0, 4),          # modification time
        writeInt(w, 1000, 4),       # timescale
        writeInt(w, 0, 4),          # duration (all 1s == unknown)
        writeInt(w, 0x00010000, 4), # rate (1.0 == normal)
        writeInt(w, 0x0100, 2),     # volume (1.0 == normal)
        writeInt(w, 0, 2),          # reserved
        writeInt(w, 0, 4),          # reserved
        writeInt(w, 0, 4),          # reserved
        writeInt(w, 0x00010000, 4), # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x00010000, 4), # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x0, 4),        # matrix
        writeInt(w, 0x40000000, 4), # matrix
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, 0, 4),          # pre-defined
        writeInt(w, -1, 4),         # next track id
    ))

def writeTRAK(w, width, height):
    writeTag(w, b"trak", lambda w: (
        writeTKHD(w, width, height),
        writeMDIA(w, width, height),
    ))

def writeTKHD(w, width, height):
    writeTag(w, b"tkhd", lambda w: (
        writeInt(w, 7, 4),               # version and flags (track enabled)
        writeInt(w, 0, 4),               # creation time
        writeInt(w, 0, 4),               # modification time
        writeInt(w, 1, 4),               # track id
        writeInt(w, 0, 4),               # reserved
        writeInt(w, 0, 4),               # duration
        writeInt(w, 0, 4),               # reserved
        writeInt(w, 0, 4),               # reserved
        writeInt(w, 0, 2),               # layer
        writeInt(w, 0, 2),               # alternate group
        writeInt(w, 0, 2),               # volume (ignored for video tracks)
        writeInt(w, 0, 2),               # reserved
        writeInt(w, 0x00010000, 4),      # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x00010000, 4),      # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x0, 4),             # matrix
        writeInt(w, 0x40000000, 4),      # matrix
        writeInt(w, int(width)<<16, 4),  # width (fixed-point 16.16 format)
        writeInt(w, int(height)<<16, 4), # height (fixed-point 16.16 format)
    ))

def writeMDIA(w, width, height):
    writeTag(w, b"mdia", lambda w: (
        writeMDHD(w),
        writeHDLR(w),
        writeMINF(w, width, height),
    ))

def writeMDHD(w):
    writeTag(w, b"mdhd", lambda w: (
        writeInt(w, 0, 4),      # version and flags
        writeInt(w, 0, 4),      # creation time
        writeInt(w, 0, 4),      # modification time
        writeInt(w, 10000, 4),  # timescale
        writeInt(w, 0, 4),      # duration
        writeInt(w, 0x55c4, 2), # language ('und' == undefined)
        writeInt(w, 0, 2),      # pre-defined
    ))

def writeHDLR(w):
    writeTag(w, b"hdlr", lambda w: (
        writeInt(w, 0, 4),              # version and flags
        writeInt(w, 0, 4),              # pre-defined
        writeString(w, b"vide"),         # handler type
        writeInt(w, 0, 4),              # reserved
        writeInt(w, 0, 4),              # reserved
        writeInt(w, 0, 4),              # reserved
        writeString(w, b"TinyStreamer"), # name
        writeInt(w, 0, 1),              # null-terminator
    ))

def writeMINF(w, width, height):
    writeTag(w, b"minf", lambda w: (
        writeVMHD(w),
        writeDINF(w),
        writeSTBL(w, width, height),
    ))

def writeVMHD(w):
    writeTag(w, b"vmhd", lambda w: (
        writeInt(w, 1, 4), # version and flags
        writeInt(w, 0, 2), # graphics mode
        writeInt(w, 0, 2), # opcolor
        writeInt(w, 0, 2), # opcolor
        writeInt(w, 0, 2), # opcolor
    ))

def writeDINF(w):
    writeTag(w, b"dinf", lambda w: (
        writeDREF(w),
    ))

def writeDREF(w):
    writeTag(w, b"dref", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 1, 4), # entry count
        writeTag(w, b"url ", lambda w: (
            writeInt(w, 1, 4), # version and flags
        ))
    ))

def writeSTBL(w, width, height):
    writeTag(w, b"stbl", lambda w: (
        writeSTSD(w, width, height),
        writeSTSZ(w),
        writeSTSC(w),
        writeSTTS(w),
        writeSTCO(w),
    ))

# Sample Table Box
def writeSTSD(w, width, height):
    # Raspberry Pi 3B+ SPS/PPS for H.264 high 4.2
    sps = b"\x27\x64\x00\x2a\xac\x2b\x40\x28\x02\xdd\x00\xf1\x22\x6a"
    pps = b"\x28\xee\x02\x5c\xb0\x00"

    writeTag(w, b"stsd", lambda w: (
        writeInt(w, 0, 6), # reserved
        writeInt(w, 1, 2), # deta reference index
        writeTag(w, b"avc1", lambda w: (
            writeInt(w, 0, 6),           # reserved
            writeInt(w, 1, 2),           # data reference index
            writeInt(w, 0, 2),           # pre-defined
            writeInt(w, 0, 2),           # reserved
            writeInt(w, 0, 4),           # pre-defined
            writeInt(w, 0, 4),           # pre-defined
            writeInt(w, 0, 4),           # pre-defined
            writeInt(w, int(width), 2),  # width
            writeInt(w, int(height), 2), # height
            writeInt(w, 0x00480000, 4),  # horizontal resolution: 72 dpi
            writeInt(w, 0x00480000, 4),  # vertical resolution: 72 dpi
            writeInt(w, 0, 4),           # data size: 0
            writeInt(w, 1, 2),           # frame count: 1
            w.write(bytes(32)),          # compressor name
            writeInt(w, 0x18, 2),        # depth
            writeInt(w, 0xffff, 2),      # pre-defined

            # MPEG-4 Part 15 extension
            # See ISO/IEC 14496-15:2004 5.3.4.1.2
            writeTag(w, b"avcC", lambda w: (
                writeInt(w, 1, 1),    # configuration version
                writeInt(w, 0x64, 1), # H.264 profile (0x64 == high)
                writeInt(w, 0x00, 1), # H.264 profile compatibility
                writeInt(w, 0x2a, 1), # H.264 level (0x28 == 4.0, 0x2a == 4.2)
                writeInt(w, 0xff, 1), # nal unit length - 1 (upper 6 bits == 1)
                writeInt(w, 0xe1, 1), # number of sps (upper 3 bits == 1)
                writeInt(w, len(sps), 2),
                w.write(sps),
                writeInt(w, 1, 1), # number of pps
                writeInt(w, len(pps), 2),
                w.write(pps),
            ))
        ))
    ))


def writeSTTS(w):
    writeTag(w, b"stts", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 0, 4), # entry count
    ))

def writeSTSC(w):
    writeTag(w, b"stsc", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 0, 4), # entry count
    ))

def writeSTSZ(w):
    writeTag(w, b"stsz", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 0, 4), # sample size
        writeInt(w, 0, 4), # sample count
    ))

def writeSTCO(w):
    writeTag(w, b"stco", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 0, 4), # entry count
    ))

# Movie Extends Box
def writeMVEX(w):
    writeTag(w, b"mvex", lambda w: (
        writeMEHD(w),
        writeTREX(w),
    ))


# Movie Extends Header Box
def writeMEHD(w):
    writeTag(w, b"mehd", lambda w: (
        writeInt(w, 0, 4), # version and flags
        writeInt(w, 0, 4), # fragment duration
    ))


# Track Extends Box
def writeTREX(w):
    writeTag(w, b"trex", lambda w: (
        writeInt(w, 0, 4),          # version and flags
        writeInt(w, 1, 4),          # track id
        writeInt(w, 1, 4),          # default sample description index
        writeInt(w, 0, 4),          # default sample duration
        writeInt(w, 0, 4),          # default sample size
        writeInt(w, 0x00010000, 4), # default sample flags
    ))

# Movie Fragment Box
def writeMOOF(w, seq, dataSize, isIDR, sampleDuration):
    writeTag(w, b"moof", lambda w: (
        writeMFHD(w, seq),
        writeTRAF(w, seq, dataSize, isIDR, sampleDuration),
    ))

# Movie Fragment Header Box
def writeMFHD(w, seq):
    writeTag(w, b"mfhd", lambda w: (
        writeInt(w, 0, 4),   # version and flags
        writeInt(w, seq, 4), # sequence number
    ))


# Track Fragment Box
def writeTRAF(w, seq, dataSize, isIDR, sampleDuration):
    writeTag(w, b"traf", lambda w: (
        writeTFHD(w),
        writeTFDT(w, seq, sampleDuration),
        writeTRUN(w, dataSize, isIDR, sampleDuration),
    ))

# Track Fragment Header Box
def writeTFHD(w):
    writeTag(w, b"tfhd", lambda w: (
        writeInt(w, 0x020020, 4),   # version and flags
        writeInt(w, 1, 4),          # track ID
        writeInt(w, 0x01010000, 4), # default sample flags
    ))


# Track Fragment Base Media Decode Time Box
def writeTFDT(w, seq, sampleDuration):
    writeTag(w, b"tfdt", lambda w: (
        writeInt(w, 0x01000000, 4), # version and flags
        writeInt(w, sampleDuration*seq, 8),    # base media decode time
    ))


# Track Run Box
def writeTRUN(w, dataSize, isIDR, sampleDuration):
    writeTag(w, b"trun", lambda w: (
        writeInt(w, 0x00000305, 4), # version and flags
        writeInt(w, 1, 4),          # sample count
        writeInt(w, 0x70, 4),       # data offset
        isIDR and writeInt(w, 0x02000000, 4), # first sample flags (i-frame)
        not isIDR and writeInt(w, 0x01010000, 4), # first sample flags (not i-frame)
        writeInt(w, sampleDuration, 4),      # sample duration
        writeInt(w, dataSize, 4), # sample size
    ))


# Media Data Box
def writeMDAT(w, data):
    writeTag(w, b"mdat", lambda w: (
        w.write(data),
    ))


def nalus2AVC(nalus):
    b = io.BytesIO()
    for nalu in nalus:
        writeInt(b, len(nalu), 4)
        b.write(nalu)
    return b.getvalue()
