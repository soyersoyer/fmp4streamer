import io

# References:
# ISO/IEC 14496 Part 12
# ISO/IEC 14496 Part 15

# ISO/IEC 14496 Part 14 is not used.

def writeInt(w, value, n):
    w.write(value.to_bytes(n, 'big'))

def writeTag(w, tag, b):
    writeInt(w, b.tell()+8, 4) # box size
    w.write(tag)               # box type
    w.write(b.getvalue())      # box content

def writeFTYP(w):
    b = io.BytesIO()
    b.write(b'isom')                 # major brand
    writeInt(b, 0x200, 4)            # minor version
    b.write(b'isomiso2iso5avc1mp41') # compatible brands
    writeTag(w, b'ftyp', b)

def writeMOOV(w, width, height, timescale, sps, pps):
    b = io.BytesIO()
    writeMVHD(b, timescale)
    writeTRAK(b, width, height, timescale, sps, pps)
    writeMVEX(b)
    writeTag(w, b'moov', b)

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
    writeInt(b, 0, 4)          # next track id
    writeTag(w, b'mvhd', b)

def writeTRAK(w, width, height, timescale, sps, pps):
    b = io.BytesIO()
    writeTKHD(b, width, height)
    writeMDIA(b, width, height, timescale, sps, pps)
    writeTag(w, b'trak', b)

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
    writeTag(w, b'tkhd', b)

def writeMDIA(w, width, height, timescale, sps, pps):
    b = io.BytesIO()
    writeMDHD(b, timescale)
    writeHDLR(b)
    writeMINF(b, width, height, sps, pps)
    writeTag(w, b'mdia', b)

def writeMDHD(w, timescale):
    b = io.BytesIO()
    writeInt(b, 0, 4)          # version and flags
    writeInt(b, 0, 4)          # creation time
    writeInt(b, 0, 4)          # modification time
    writeInt(b, timescale, 4)  # timescale
    writeInt(b, 0, 4)          # duration
    writeInt(b, 0x55c4, 2)     # language ('und' == undefined)
    writeInt(b, 0, 2)          # pre-defined
    writeTag(w, b'mdhd', b)

def writeHDLR(w):
    b = io.BytesIO()
    writeInt(b, 0, 4)         # version and flags
    writeInt(b, 0, 4)         # pre-defined
    b.write(b'vide')          # handler type
    writeInt(b, 0, 4)         # reserved
    writeInt(b, 0, 4)         # reserved
    writeInt(b, 0, 4)         # reserved
    b.write(b'TinyStreamer')  # name
    writeInt(b, 0, 1)         # null-terminator
    writeTag(w, b'hdlr', b)

def writeMINF(w, width, height, sps, pps):
    b = io.BytesIO()
    writeVMHD(b)
    writeDINF(b)
    writeSTBL(b, width, height, sps, pps)
    writeTag(w, b'minf', b)

def writeVMHD(w):
    b = io.BytesIO()
    writeInt(b, 1, 4) # version and flags
    writeInt(b, 0, 2) # graphics mode
    writeInt(b, 0, 2) # opcolor
    writeInt(b, 0, 2) # opcolor
    writeInt(b, 0, 2) # opcolor
    writeTag(w, b'vmhd', b)

def writeDINF(w):
    b = io.BytesIO()
    writeDREF(b)
    writeTag(w, b'dinf', b)

def writeDREF(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 1, 4) # entry count
    writeURL(b)
    writeTag(w, b'dref', b)

def writeURL(w):
    b = io.BytesIO()
    writeInt(b, 1, 4) # version and flags
    writeTag(w, b'url ', b)

def writeSTBL(w, width, height, sps, pps):
    b = io.BytesIO()
    writeSTSD(b, width, height, sps, pps)
    writeSTSZ(b)
    writeSTSC(b)
    writeSTTS(b)
    writeSTCO(b)
    writeTag(w, b'stbl', b)

# Sample Table Box
def writeSTSD(w, width, height, sps, pps):
    b = io.BytesIO()
    writeInt(b, 0, 6) # reserved
    writeInt(b, 1, 2) # deta reference index
    writeAVC1(b, width, height, sps, pps)
    writeTag(w, b'stsd', b)

def writeAVC1(w, width, height, sps, pps):
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
    writeAVCC(b, sps, pps)
    writeTag(w, b'avc1', b)

# MPEG-4 Part 15 extension
# See ISO/IEC 14496-15:2004 5.3.4.1.2
def writeAVCC(w, sps, pps):
    b = io.BytesIO()
    writeInt(b, 1, 1)    # configuration version
    writeInt(b, 0x64, 1) # H.264 profile (0x64 == high)
    writeInt(b, 0x00, 1) # H.264 profile compatibility
    writeInt(b, 0x2a, 1) # H.264 level (0x28 == 4.0, 0x2a == 4.2)
    writeInt(b, 0xff, 1) # nal unit length - 1 (upper 6 bits == 1)
    writeInt(b, 0xe1, 1) # number of sps (upper 3 bits == 1)

    writeInt(b, len(sps), 2)
    b.write(sps)
    writeInt(b, 1, 1) # number of pps
    writeInt(b, len(pps), 2)
    b.write(pps)
    writeTag(w, b'avcC', b)

def writeSTTS(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b'stts', b)

def writeSTSC(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b'stsc', b)

def writeSTSZ(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # sample size
    writeInt(b, 0, 4) # sample count
    writeTag(w, b'stsz', b)

def writeSTCO(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # entry count
    writeTag(w, b'stco', b)

# Movie Extends Box
def writeMVEX(w):
    b = io.BytesIO()
    writeMEHD(b)
    writeTREX(b)
    writeTag(w, b'mvex', b)


# Movie Extends Header Box
def writeMEHD(w):
    b = io.BytesIO()
    writeInt(b, 0, 4) # version and flags
    writeInt(b, 0, 4) # fragment duration
    writeTag(w, b'mehd', b)


# Track Extends Box
def writeTREX(w):
    b = io.BytesIO()
    writeInt(b, 0, 4)          # version and flags
    writeInt(b, 1, 4)          # track id
    writeInt(b, 1, 4)          # default sample description index
    writeInt(b, 0, 4)          # default sample duration
    writeInt(b, 0, 4)          # default sample size
    writeInt(b, 0x00010000, 4) # default sample flags
    writeTag(w, b'trex', b)


TFHDSIZE = 12 + 8
TFDTSIZE = 12 + 8
TRUNSIZE = 24 + 8
TRAFSIZE = TFHDSIZE + TFDTSIZE + TRUNSIZE + 8
MFHDSIZE = 8 + 8
MOOFSIZE = MFHDSIZE + TRAFSIZE + 8

# Movie Fragment Box
def writeMOOF(w, seq, mdatSize, isIDR, sampleDuration, decodeTime):
    w.write(MOOFSIZE.to_bytes(4, 'big'))
    w.write(b'moof')

    # Movie Fragment Header Box
    w.write(MFHDSIZE.to_bytes(4, 'big'))
    w.write(b'mfhd')
    w.write((0).to_bytes(4, 'big'))   # version and flags
    w.write((seq).to_bytes(4, 'big')) # sequence number

    # Track Fragment Box
    w.write((TRAFSIZE).to_bytes(4, 'big'))
    w.write(b'traf')
    
    # Track Fragment Header Box
    w.write((TFHDSIZE).to_bytes(4, 'big'))
    w.write(b'tfhd')
    w.write((0x020020).to_bytes(4, 'big'))   # version and flags
    w.write((1).to_bytes(4, 'big'))          # track ID
    w.write((0x01010000).to_bytes(4, 'big')) # default sample flags

    # Track Fragment Base Media Decode Time Box
    w.write((TFDTSIZE).to_bytes(4, 'big'))
    w.write(b'tfdt')
    w.write((0x01000000).to_bytes(4, 'big')) # version and flags
    w.write(decodeTime.to_bytes(8, 'big'))    # base media decode time

    # Track Run Box
    w.write((TRUNSIZE).to_bytes(4, 'big'))
    w.write(b'trun')
    w.write((0x00000305).to_bytes(4, 'big')) # version and flags
    w.write((1).to_bytes(4, 'big'))          # sample count
    w.write((0x70).to_bytes(4, 'big'))       # data offset
    if isIDR:
        w.write((0x02000000).to_bytes(4, 'big')) # first sample flags (i-frame)
    else:
        w.write((0x01010000).to_bytes(4, 'big')) # first sample flags (not i-frame)
    w.write((sampleDuration).to_bytes(4, 'big'))      # sample duration
    w.write((mdatSize - 8).to_bytes(4, 'big')) # sample size

# Media Data Box
def writeMDAT(w, nalus):
    w.write(getMDATsize(nalus).to_bytes(4, 'big'))
    w.write(b'mdat')
    for nalu in nalus:
        w.write((len(nalu)).to_bytes(4, 'big'))
        w.write(nalu)

def getMDATsize(nalus):
    size = 8
    for nalu in nalus:
        size += 4+len(nalu)
    return size
