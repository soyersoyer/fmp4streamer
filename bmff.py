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


def writeTag(w, tag, b):
    writeInt(w, b.tell()+8, 4) # box size
    writeString(w, tag)        # box type
    w.write(b.getvalue())      # box content

def writeFTYP(w):
    b = io.BytesIO()
    writeString(b, b"isom")                 # major brand
    writeInt(b, 0x200, 4)                   # minor version
    writeString(b, b"isomiso2iso5avc1mp41") # compatible brands
    writeTag(w, b"ftyp", b)

def writeMOOV(w, width, height, timescale):
    b = io.BytesIO()
    writeMVHD(b, timescale)
    writeTRAK(b, width, height, timescale)
    writeMVEX(b)
    writeTag(w, b"moov", b)

def writeMVHD(w, timescale):
    b = io.BytesIO()
    writeInt(b, 0, 4)          # version and flags
    writeInt(b, 0, 4)          # creation time
    writeInt(b, 0, 4)          # modification time
    writeInt(b, timescale, 4)  # timescale
    writeInt(b, 0, 4)          # duration (all 1s == unknown)
    writeInt(b, 0x00010000, 4) # rate (1.0 == normal)
    writeInt(b, 0x0100, 2)     # volume (1.0 == normal)
    writeInt(b, 0, 2)          # reserved
    writeInt(b, 0, 4)          # reserved
    writeInt(b, 0, 4)          # reserved
    writeInt(b, 0x00010000, 4) # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x00010000, 4) # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x0, 4)        # matrix
    writeInt(b, 0x40000000, 4) # matrix
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, 0, 4)          # pre-defined
    writeInt(b, -1, 4)         # next track id
    writeTag(w, b"mvhd", b)

def writeTRAK(w, width, height, timescale):
    b = io.BytesIO()
    writeTKHD(b, width, height)
    writeMDIA(b, width, height, timescale)
    writeTag(w, b"trak", b)

def writeTKHD(w, width, height):
    b = io.BytesIO()
    writeInt(b, 7, 4)               # version and flags (track enabled)
    writeInt(b, 0, 4)               # creation time
    writeInt(b, 0, 4)               # modification time
    writeInt(b, 1, 4)               # track id
    writeInt(b, 0, 4)               # reserved
    writeInt(b, 0, 4)               # duration
    writeInt(b, 0, 4)               # reserved
    writeInt(b, 0, 4)               # reserved
    writeInt(b, 0, 2)               # layer
    writeInt(b, 0, 2)               # alternate group
    writeInt(b, 0, 2)               # volume (ignored for video tracks)
    writeInt(b, 0, 2)               # reserved
    writeInt(b, 0x00010000, 4)      # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x00010000, 4)      # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x0, 4)             # matrix
    writeInt(b, 0x40000000, 4)      # matrix
    writeInt(b, int(width)<<16, 4)  # width (fixed-point 16.16 format)
    writeInt(b, int(height)<<16, 4) # height (fixed-point 16.16 format)
    writeTag(w, b"tkhd", b)

def writeMDIA(w, width, height, timescale):
    b = io.BytesIO()
    writeMDHD(b, timescale)
    writeHDLR(b)
    writeMINF(b, width, height)
    writeTag(w, b"mdia", b)

def writeMDHD(w, timescale):
    b = io.BytesIO()
    writeInt(b, 0, 4)          # version and flags
    writeInt(b, 0, 4)          # creation time
    writeInt(b, 0, 4)          # modification time
    writeInt(b, timescale, 4)  # timescale
    writeInt(b, 0, 4)          # duration
    writeInt(b, 0x55c4, 2)     # language ('und' == undefined)
    writeInt(b, 0, 2)          # pre-defined
    writeTag(w, b"mdhd", b)

def writeHDLR(w):
    b = io.BytesIO()
    writeInt(b, 0, 4)              # version and flags
    writeInt(b, 0, 4)              # pre-defined
    writeString(b, b"vide")         # handler type
    writeInt(b, 0, 4)              # reserved
    writeInt(b, 0, 4)              # reserved
    writeInt(b, 0, 4)              # reserved
    writeString(b, b"TinyStreamer") # name
    writeInt(b, 0, 1)              # null-terminator
    writeTag(w, b"hdlr", b)

def writeMINF(w, width, height):
    b = io.BytesIO()
    writeVMHD(b)
    writeDINF(b)
    writeSTBL(b, width, height)
    writeTag(w, b"minf", b)

def writeVMHD(w):
    b = io.BytesIO()
    writeInt(b, 1, 4) # version and flags
    writeInt(b, 0, 2) # graphics mode
    writeInt(b, 0, 2) # opcolor
    writeInt(b, 0, 2) # opcolor
    writeInt(b, 0, 2) # opcolor
    writeTag(w, b"vmhd", b)

def writeDINF(w):
    b = io.BytesIO()
    writeDREF(b)
    writeTag(w, b"dinf", b)

def writeDREF(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 1, 4) # entry count
    writeURL(b)
    writeTag(w, b"dref", b)

def writeURL(w):
    b = io.BytesIO()
    writeInt(b, 1, 4) # version and flags
    writeTag(w, b"url ", b)

def writeSTBL(w, width, height):
    b = io.BytesIO()
    writeSTSD(b, width, height)
    writeSTSZ(b)
    writeSTSC(b)
    writeSTTS(b)
    writeSTCO(b)
    writeTag(w, b"stbl", b)

# Sample Table Box
def writeSTSD(w, width, height):
    b = io.BytesIO()
    writeInt(b, 0, 6) # reserved
    writeInt(b, 1, 2) # deta reference index
    writeAVC1(b, width, height)
    writeTag(w, b"stsd", b)

def writeAVC1(w, width, height):
    b = io.BytesIO()
    writeInt(b, 0, 6)           # reserved
    writeInt(b, 1, 2)           # data reference index
    writeInt(b, 0, 2)           # pre-defined
    writeInt(b, 0, 2)           # reserved
    writeInt(b, 0, 4)           # pre-defined
    writeInt(b, 0, 4)           # pre-defined
    writeInt(b, 0, 4)           # pre-defined
    writeInt(b, int(width), 2)  # width
    writeInt(b, int(height), 2) # height
    writeInt(b, 0x00480000, 4)  # horizontal resolution: 72 dpi
    writeInt(b, 0x00480000, 4)  # vertical resolution: 72 dpi
    writeInt(b, 0, 4)           # data size: 0
    writeInt(b, 1, 2)           # frame count: 1
    b.write(bytes(32))          # compressor name
    writeInt(b, 0x18, 2)        # depth
    writeInt(b, 0xffff, 2)      # pre-defined
    writeAVCC(b)
    writeTag(w, b"avc1", b)

# MPEG-4 Part 15 extension
# See ISO/IEC 14496-15:2004 5.3.4.1.2
def writeAVCC(w):
    b = io.BytesIO()
    writeInt(b, 1, 1)    # configuration version
    writeInt(b, 0x64, 1) # H.264 profile (0x64 == high)
    writeInt(b, 0x00, 1) # H.264 profile compatibility
    writeInt(b, 0x2a, 1) # H.264 level (0x28 == 4.0, 0x2a == 4.2)
    writeInt(b, 0xff, 1) # nal unit length - 1 (upper 6 bits == 1)
    writeInt(b, 0xe1, 1) # number of sps (upper 3 bits == 1)

    # Raspberry Pi 3B+ SPS/PPS for H.264 high 4.2
    sps = b"\x27\x64\x00\x2a\xac\x2b\x40\x28\x02\xdd\x00\xf1\x22\x6a"
    pps = b"\x28\xee\x02\x5c\xb0\x00"

    writeInt(b, len(sps), 2)
    b.write(sps)
    writeInt(b, 1, 1) # number of pps
    writeInt(b, len(pps), 2)
    b.write(pps)
    writeTag(w, b"avcC", b)

def writeSTTS(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b"stts", b)

def writeSTSC(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b"stsc", b)

def writeSTSZ(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # sample size
    writeInt(b, 0, 4) # sample count
    writeTag(w, b"stsz", b)

def writeSTCO(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b"stco", b)

# Movie Extends Box
def writeMVEX(w):
    b = io.BytesIO()
    writeMEHD(b)
    writeTREX(b)
    writeTag(w, b"mvex", b)


# Movie Extends Header Box
def writeMEHD(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # fragment duration
    writeTag(w, b"mehd", b)


# Track Extends Box
def writeTREX(w):
    b = io.BytesIO()
    writeInt(b, 0, 4)          # version and flags
    writeInt(b, 1, 4)          # track id
    writeInt(b, 1, 4)          # default sample description index
    writeInt(b, 0, 4)          # default sample duration
    writeInt(b, 0, 4)          # default sample size
    writeInt(b, 0x00010000, 4) # default sample flags
    writeTag(w, b"trex", b)

# Movie Fragment Box
def writeMOOF(w, seq, dataSize, isIDR, sampleDuration):
    b = io.BytesIO()
    writeMFHD(b, seq)
    writeTRAF(b, seq, dataSize, isIDR, sampleDuration)
    writeTag(w, b"moof", b)

# Movie Fragment Header Box
def writeMFHD(w, seq):
    b = io.BytesIO()
    writeInt(b, 0, 4)   # version and flags
    writeInt(b, seq, 4) # sequence number
    writeTag(w, b"mfhd", b)


# Track Fragment Box
def writeTRAF(w, seq, dataSize, isIDR, sampleDuration):
    b = io.BytesIO()
    writeTFHD(b)
    writeTFDT(b, seq, sampleDuration)
    writeTRUN(b, dataSize, isIDR, sampleDuration)
    writeTag(w, b"traf", b)

# Track Fragment Header Box
def writeTFHD(w):
    b = io.BytesIO()
    writeInt(b, 0x020020, 4)   # version and flags
    writeInt(b, 1, 4)          # track ID
    writeInt(b, 0x01010000, 4) # default sample flags
    writeTag(w, b"tfhd", b)


# Track Fragment Base Media Decode Time Box
def writeTFDT(w, seq, sampleDuration):
    b = io.BytesIO()
    writeInt(b, 0x01000000, 4) # version and flags
    writeInt(b, seq*sampleDuration, 8)    # base media decode time
    writeTag(w, b"tfdt", b)


# Track Run Box
def writeTRUN(w, dataSize, isIDR, sampleDuration):
    b = io.BytesIO()
    writeInt(b, 0x00000305, 4) # version and flags
    writeInt(b, 1, 4)          # sample count
    writeInt(b, 0x70, 4)       # data offset
    if isIDR:
        writeInt(b, 0x02000000, 4) # first sample flags (i-frame)
    else:
        writeInt(b, 0x01010000, 4) # first sample flags (not i-frame)
    writeInt(b, sampleDuration, 4)      # sample duration
    writeInt(b, dataSize, 4) # sample size
    writeTag(w, b"trun", b)


# Media Data Box
def writeMDAT(w, b):
    writeTag(w, b"mdat", b)


def nalus2AVC(nalus):
    b = io.BytesIO()
    for nalu in nalus:
        writeInt(b, len(nalu), 4)
        b.write(nalu)
    return b

