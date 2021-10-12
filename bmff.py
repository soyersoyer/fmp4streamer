from struct import pack

HANDLERNAME = b'TinyStreamer'
COMPATSTRING = b'isomiso2iso5avc1mp41'

# functions unrolled to minimize function calls, because they are very slow in python

# References:
# ISO/IEC 14496 Part 12
# ISO/IEC 14496 Part 15

# ISO/IEC 14496 Part 14 is not used.

COMPATSTRINGSIZE = 20
FTYPSIZE = 8 + COMPATSTRINGSIZE + 8
def write_ftyp(w):
    w.write(pack('>I 4s 4s I 20s', FTYPSIZE, b'ftyp', b'isom', 0x200, COMPATSTRING))
#    w.write((FTYPSIZE).to_bytes(4, 'big'))
#    w.write(b'ftyp')
#    w.write(b'isom')      # major brand
#    w.write((0x200).to_bytes(4, 'big')) # minor version
#    w.write(COMPATSTRING) # compatible brands

MVHDSIZE = 100 + 8

TKHDSIZE = 84 + 8

MDHDSIZE = 24 + 8
HDLRSIZE = 24 + len(HANDLERNAME) + 1 + 8

VMHDSIZE = 12 + 8

URLSIZE = 4 + 8
DREFSIZE = 8 + URLSIZE + 8
DINFSIZE = DREFSIZE + 8

AVCCSIZEWOSPSPPS = 11 + 8
AVC1SIZEWOSPSPPS = 78 + AVCCSIZEWOSPSPPS + 8
STSDSIZEWOSPSPPS = 8 + AVC1SIZEWOSPSPPS + 8
STSZSIZE = 12 + 8
STSCSIZE = 8 + 8
STTSSIZE = 8 + 8
STCOSIZE = 8 + 8
STBLSIZEWOSPSPPS = STSDSIZEWOSPSPPS + STSZSIZE + STSCSIZE + STTSSIZE + STCOSIZE + 8

MINFSIZEWOSPSPPS = VMHDSIZE + DINFSIZE + STBLSIZEWOSPSPPS + 8

MDIASIZEWOSPSPPS = MDHDSIZE + HDLRSIZE + MINFSIZEWOSPSPPS + 8

TRAKSIZEWOSPSPPS = TKHDSIZE + MDIASIZEWOSPSPPS + 8

MEHDSIZE = 8 + 8
TREXSIZE = 24 + 8
MVEXSIZE = MEHDSIZE + TREXSIZE + 8

MOOVSIZEWOSPSPPS = MVHDSIZE + TRAKSIZEWOSPSPPS + MVEXSIZE + 8

def write_moov(w, width, height, timescale, sps, pps):
    w.write(pack('>I 4s', MOOVSIZEWOSPSPPS + len(sps) + len(pps), b'moov'))
#    w.write((MOOVSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'moov')

    w.write(pack('>I 4s I I I I I I H H II III III III IIIIIII', MVHDSIZE, b'mvhd',
    0, 0, 0, timescale, 0, 0x00010000, 0x0100, 0, 0, 0, 
    0x00010000, 0, 0,
    0, 0x00010000, 0,
    0, 0, 0x40000000,
    0, 0, 0, 0, 0, 0, 0))
#    w.write(MVHDSIZE.to_bytes(4, 'big'))
#    w.write(b'mvhd')
#    w.write((0).to_bytes(4, 'big'))          # version and flags
#    w.write((0).to_bytes(4, 'big'))          # creation time
#    w.write((0).to_bytes(4, 'big'))          # modification time
#    w.write((timescale).to_bytes(4, 'big'))  # timescale
#    w.write((0).to_bytes(4, 'big'))          # duration (all 1s == unknown)
#    w.write((0x00010000).to_bytes(4, 'big')) # rate (1.0 == normal)
#    w.write((0x0100).to_bytes(2, 'big'))     # volume (1.0 == normal)
#    w.write((0).to_bytes(2, 'big'))          # reserved
#    w.write((0).to_bytes(4, 'big'))          # reserved
#    w.write((0).to_bytes(4, 'big'))          # reserved
#    w.write((0x00010000).to_bytes(4, 'big')) # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x00010000).to_bytes(4, 'big')) # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x0).to_bytes(4, 'big'))        # matrix
#    w.write((0x40000000).to_bytes(4, 'big')) # matrix
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # pre-defined
#    w.write((0).to_bytes(4, 'big'))          # next track id

    w.write(pack('>I 4s', TRAKSIZEWOSPSPPS + len(sps) + len(pps), b'trak'))
#    w.write((TRAKSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'trak')
    
    w.write(pack('>I 4s I I I I I I I I H H H H I I I I I I I I I I I', TKHDSIZE, b'tkhd',
    7, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0x00010000, 0, 0, 0, 0x00010000, 0, 0, 0, 0x40000000,
    int(width)<<16, int(height)<<16))
#    w.write(TKHDSIZE.to_bytes(4, 'big'))
#    w.write(b'tkhd')
#    w.write((7).to_bytes(4, 'big'))               # version and flags (track enabled)
#    w.write((0).to_bytes(4, 'big'))               # creation time
#    w.write((0).to_bytes(4, 'big'))               # modification time
#    w.write((1).to_bytes(4, 'big'))               # track id
#    w.write((0).to_bytes(4, 'big'))               # reserved
#    w.write((0).to_bytes(4, 'big'))               # duration
#    w.write((0).to_bytes(4, 'big'))               # reserved
#    w.write((0).to_bytes(4, 'big'))               # reserved
#    w.write((0).to_bytes(2, 'big'))               # layer
#    w.write((0).to_bytes(2, 'big'))               # alternate group
#    w.write((0).to_bytes(2, 'big'))               # volume (ignored for video tracks)
#    w.write((0).to_bytes(2, 'big'))               # reserved
#    w.write((0x00010000).to_bytes(4, 'big'))      # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x00010000).to_bytes(4, 'big'))      # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x0).to_bytes(4, 'big'))             # matrix
#    w.write((0x40000000).to_bytes(4, 'big'))      # matrix
#    w.write((int(width)<<16).to_bytes(4, 'big'))  # width (fixed-point 16.16 format)
#    w.write((int(height)<<16).to_bytes(4, 'big')) # height (fixed-point 16.16 format)

    w.write(pack('>I 4s', MDIASIZEWOSPSPPS + len(sps) + len(pps), b'mdia'))
#    w.write((MDIASIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'mdia')

    w.write(pack('>I 4s I I I I I H H', MDHDSIZE, b'mdhd', 0, 0, 0, timescale, 0, 0x55c4, 0))
#    w.write(MDHDSIZE.to_bytes(4, 'big'))
#    w.write(b'mdhd')
#    w.write((0).to_bytes(4, 'big'))          # version and flags
#    w.write((0).to_bytes(4, 'big'))          # creation time
#    w.write((0).to_bytes(4, 'big'))          # modification time
#    w.write((timescale).to_bytes(4, 'big'))  # timescale
#    w.write((0).to_bytes(4, 'big'))          # duration
#    w.write((0x55c4).to_bytes(2, 'big'))     # language ('und' == undefined)
#    w.write((0).to_bytes(2, 'big'))          # pre-defined

    w.write(pack('>I 4s I I 4s I I I %ds B' % len(HANDLERNAME), HDLRSIZE, b'hdlr',
    0, 0, b'vide', 0, 0, 0, HANDLERNAME, 0))
#    w.write(HDLRSIZE.to_bytes(4, 'big'))
#    w.write(b'hdlr')
#    w.write((0).to_bytes(4, 'big'))         # version and flags
#    w.write((0).to_bytes(4, 'big'))         # pre-defined
#    w.write(b'vide')          # handler type
#    w.write((0).to_bytes(4, 'big'))         # reserved
#    w.write((0).to_bytes(4, 'big'))         # reserved
#    w.write((0).to_bytes(4, 'big'))         # reserved
#    w.write(HANDLERNAME)       # name
#    w.write((0).to_bytes(1, 'big'))         # null-terminator

    w.write(pack('>I 4s', MINFSIZEWOSPSPPS + len(sps) + len(pps), b'minf'))
#    w.write((MINFSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'minf')

    w.write(pack('>I 4s I H H H H', VMHDSIZE, b'vmhd', 1, 0, 0, 0, 0))
#    w.write(VMHDSIZE.to_bytes(4, 'big'))
#    w.write(b'vmhd')
#    w.write((1).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(2, 'big')) # graphics mode
#    w.write((0).to_bytes(2, 'big')) # opcolor
#    w.write((0).to_bytes(2, 'big')) # opcolor
#    w.write((0).to_bytes(2, 'big')) # opcolor

    w.write(pack('>I 4s', DINFSIZE, b'dinf'))
#    w.write((DINFSIZE).to_bytes(4, 'big'))
#    w.write(b'dinf')

    w.write(pack('>I 4s I I', DREFSIZE, b'dref', 0, 1))
#    w.write((DREFSIZE).to_bytes(4, 'big'))
#    w.write(b'dref')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((1).to_bytes(4, 'big')) # entry count

    w.write(pack('>I 4s I', URLSIZE, b'url ', 1))
#    w.write((URLSIZE).to_bytes(4, 'big'))
#    w.write(b'url ')
#    w.write((1).to_bytes(4, 'big')) # version and flags

    w.write(pack('>I 4s', STBLSIZEWOSPSPPS + len(sps) + len(pps), b'stbl'))
#    w.write((STBLSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'stbl')

    # Sample Table Box
    w.write(pack('>I 4s IH H', STSDSIZEWOSPSPPS + len(sps) + len(pps), b'stsd', 0, 0, 1))
#    w.write((STSDSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'stsd')
#    w.write((0).to_bytes(6, 'big')) # reserved
#    w.write((1).to_bytes(2, 'big')) # deta reference index

    w.write(pack('>I 4s IH H H H I I I H H I I I H 32s H H',
    AVC1SIZEWOSPSPPS + len(sps) + len(pps), b'avc1',
    0, 0, 1, 0, 0, 0, 0, 0, width, height, 0x00480000, 0x00480000, 0, 1, bytes(32), 0x18, 0xffff))
#    w.write((AVC1SIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'avc1')
#    w.write((0).to_bytes(6, 'big'))           # reserved
#    w.write((1).to_bytes(2, 'big'))           # data reference index
#    w.write((0).to_bytes(2, 'big'))           # pre-defined
#    w.write((0).to_bytes(2, 'big'))           # reserved
#    w.write((0).to_bytes(4, 'big'))           # pre-defined
#    w.write((0).to_bytes(4, 'big'))           # pre-defined
#    w.write((0).to_bytes(4, 'big'))           # pre-defined
#    w.write((int(width)).to_bytes(2, 'big'))  # width
#    w.write((int(height)).to_bytes(2, 'big')) # height
#    w.write((0x00480000).to_bytes(4, 'big'))  # horizontal resolution: 72 dpi
#    w.write((0x00480000).to_bytes(4, 'big'))  # vertical resolution: 72 dpi
#    w.write((0).to_bytes(4, 'big'))           # data size: 0
#    w.write((1).to_bytes(2, 'big'))           # frame count: 1
#    w.write(bytes(32))          # compressor name
#    w.write((0x18).to_bytes(2, 'big'))        # depth
#    w.write((0xffff).to_bytes(2, 'big'))      # pre-defined

    # MPEG-4 Part 15 extension
    # See ISO/IEC 14496-15:2004 5.3.4.1.2
    w.write(pack('>I 4s B B B B B B H %ds B H %ds' % (len(sps), len(pps)),
    AVCCSIZEWOSPSPPS + len(sps) + len(pps), b'avcC',
    1, 0x64, 0x00, 0x2a, 0xff, 0xe1,
    len(sps), sps, 1, len(pps), pps))
#    w.write((AVCCSIZEWOSPSPPS + len(sps) + len(pps)).to_bytes(4, 'big'))
#    w.write(b'avcC')
#    w.write((1).to_bytes(1, 'big'))    # configuration version
#    w.write((0x64).to_bytes(1, 'big')) # H.264 profile (0x64 == high)
#    w.write((0x00).to_bytes(1, 'big')) # H.264 profile compatibility
#    w.write((0x2a).to_bytes(1, 'big')) # H.264 level (0x28 == 4.0, 0x2a == 4.2)
#    w.write((0xff).to_bytes(1, 'big')) # nal unit length - 1 (upper 6 bits == 1)
#    w.write((0xe1).to_bytes(1, 'big')) # number of sps (upper 3 bits == 1)
#    w.write((len(sps)).to_bytes(2, 'big'))
#    w.write(sps)
#    w.write((1).to_bytes(1, 'big')) # number of pps
#    w.write((len(pps)).to_bytes(2, 'big'))
#    w.write(pps)

    w.write(pack('>I 4s I I I', STSZSIZE, b'stsz', 0, 0, 0))
#    w.write(STSZSIZE.to_bytes(4, 'big'))
#    w.write(b'stsz')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(4, 'big')) # sample size
#    w.write((0).to_bytes(4, 'big')) # sample count

    w.write(pack('>I 4s I I', STSCSIZE, b'stsc', 0, 0))
#    w.write(STSCSIZE.to_bytes(4, 'big'))
#    w.write(b'stsc')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(4, 'big')) # entry count

    w.write(pack('>I 4s I I', STTSSIZE, b'stts', 0, 0))
#    w.write(STTSSIZE.to_bytes(4, 'big'))
#    w.write(b'stts')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(4, 'big')) # entry count

    w.write(pack('>I 4s I I', STCOSIZE, b'stco', 0, 0))
#    w.write(STCOSIZE.to_bytes(4, 'big'))
#    w.write(b'stco')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(4, 'big')) # entry count

    # Movie Extends Box
    w.write(pack('>I 4s', MVEXSIZE, b'mvex'))
#    w.write(MVEXSIZE.to_bytes(4, 'big'))
#    w.write(b'mvex')

    # Movie Extends Header Box
    w.write(pack('>I 4s I I', MEHDSIZE, b'mehd', 0 ,0))
#    w.write(MEHDSIZE.to_bytes(4, 'big'))
#    w.write(b'mehd')
#    w.write((0).to_bytes(4, 'big')) # version and flags
#    w.write((0).to_bytes(4, 'big')) # fragment duration


    # Track Extends Box
    w.write(pack('>I 4s I I I I I I', TREXSIZE, b'trex', 0, 1, 1, 0, 0, 0x00010000))
#    w.write(TREXSIZE.to_bytes(4, 'big'))
#    w.write(b'trex')
#    w.write((0).to_bytes(4, 'big'))          # version and flags
#    w.write((1).to_bytes(4, 'big'))          # track id
#    w.write((1).to_bytes(4, 'big'))          # default sample description index
#    w.write((0).to_bytes(4, 'big'))          # default sample duration
#    w.write((0).to_bytes(4, 'big'))          # default sample size
#    w.write((0x00010000).to_bytes(4, 'big')) # default sample flags



TFHDSIZE = 12 + 8
TFDTSIZE = 12 + 8
TRUNSIZE = 24 + 8
TRAFSIZE = TFHDSIZE + TFDTSIZE + TRUNSIZE + 8
MFHDSIZE = 8 + 8
MOOFSIZE = MFHDSIZE + TRAFSIZE + 8

# Movie Fragment Box
def write_moof(w, seq, mdatsize, is_idr, sampleduration, decodetime):
    w.write(pack('>20s I 40s Q 20s 4s I I',
b'\x00\x00\x00\x68\
moof\
\x00\x00\x00\x10\
mfhd\
\x00\x00\x00\x00',
    seq,
b'\x00\x00\x00\x50\
traf\
\x00\x00\x00\x14\
tfhd\
\x00\x02\x00\x20\
\x00\x00\x00\x01\
\x01\x01\x00\x00\
\x00\x00\x00\x14\
tfdt\
\x01\x00\x00\x00',
    decodetime,
b'\x00\x00\x00\x20\
trun\
\x00\x00\x03\x05\
\x00\x00\x00\x01\
\x00\x00\x00\x70',
    (b'\x02\x00\x00\x00' if is_idr else b'\x01\x01\x00\x00'),
    sampleduration,
    (mdatsize - 8)))

#    w.write(MOOFSIZE.to_bytes(4, 'big'))
#    w.write(b'moof')
#
#    # Movie Fragment Header Box
#    w.write(MFHDSIZE.to_bytes(4, 'big'))
#    w.write(b'mfhd')
#    w.write((0).to_bytes(4, 'big'))   # version and flags
#    w.write((seq).to_bytes(4, 'big')) # sequence number
#
#    # Track Fragment Box
#    w.write((TRAFSIZE).to_bytes(4, 'big'))
#    w.write(b'traf')
#    
#    # Track Fragment Header Box
#    w.write((TFHDSIZE).to_bytes(4, 'big'))
#    w.write(b'tfhd')
#    w.write((0x020020).to_bytes(4, 'big'))   # version and flags
#    w.write((1).to_bytes(4, 'big'))          # track ID
#    w.write((0x01010000).to_bytes(4, 'big')) # default sample flags
#
#    # Track Fragment Base Media Decode Time Box
#    w.write((TFDTSIZE).to_bytes(4, 'big'))
#    w.write(b'tfdt')
#    w.write((0x01000000).to_bytes(4, 'big')) # version and flags
#    w.write(decodetime.to_bytes(8, 'big'))    # base media decode time
#
#    # Track Run Box
#    w.write((TRUNSIZE).to_bytes(4, 'big'))
#    w.write(b'trun')
#    w.write((0x00000305).to_bytes(4, 'big')) # version and flags
#    w.write((1).to_bytes(4, 'big'))          # sample count
#    w.write((0x70).to_bytes(4, 'big'))       # data offset
#    if is_idr:
#        w.write((0x02000000).to_bytes(4, 'big')) # first sample flags (i-frame)
#    else:
#        w.write((0x01010000).to_bytes(4, 'big')) # first sample flags (not i-frame)
#    w.write((sampleduration).to_bytes(4, 'big'))      # sample duration
#    w.write((mdatsize - 8).to_bytes(4, 'big')) # sample size

# Media Data Box
def write_mdat(w, nalus):
    w.write(get_mdat_size(nalus).to_bytes(4, 'big'))
    w.write(b'mdat')
    for nalu in nalus:
        w.write((len(nalu)).to_bytes(4, 'big'))
        w.write(nalu)

def get_mdat_size(nalus):
    size = 8
    for nalu in nalus:
        size += 4+len(nalu)
    return size

def test_h264_to_fmp4(h264file, mp4file):
    fin = open(h264file, 'rb')
    h264 = fin.read()
    fin.close()

    delim = b'\00\00\00\01'
    # Raspberry Pi 3B+ SPS/PPS for H.264 high 4.2
    sps = b'\x27\x64\x00\x2a\xac\x2b\x40\x28\x02\xdd\x00\xf1\x22\x6a'
    pps = b'\x28\xee\x02\x5c\xb0\x00'

    sampletime = 333
    timescale = 24*sampletime

    nals = h264.split(delim)

    fout = open(mp4file, 'wb')

    write_ftyp(fout)
    write_moov(fout, 1280, 720, timescale, sps, pps)

    seq = 1
    for k, nal in enumerate(nals):
        if len(nal) == 0:
            continue
        nal_type = nal[0] & 0x1f
        if nal_type == 5 or nal_type == 1:
            if nal_type == 5:
                nalus = [nals[k-2], nals[k-1], nal]
                is_idr = True
            else:
                nalus = [nal]
                is_idr = False
            mdat_size = get_mdat_size(nalus)
            write_moof(fout, seq, mdat_size, is_idr, sampletime, seq*sampletime)
            write_mdat(fout, nalus)
            seq = seq + 1

    fout.close()
