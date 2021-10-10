import bmff, io

fin = open("test.h264", "rb")
h264 = fin.read()
fin.close()

delim = b'\00\00\00\01'
sampletime = 333
timescale = 24*sampletime

nals = h264.split(delim)

fout = open("test.mp4", "wb")

bmff.write_ftyp(fout)
bmff.write_moov(fout, 1280, 720, timescale, delim, delim)

seq = 1
for k, nal in enumerate(nals):
    if len(nal) == 0:
        continue
    nal_type = nal[0] & 0x1f
    if nal_type == 5 or nal_type == 1:
        if (nal_type == 5):
            nalus = [nals[k-2], nals[k-1], nal]
            is_idr = True
        else:
            nalus = [nal]
            is_idr = False
        mdat_size = bmff.get_mdat_size(nalus)
        bmff.write_moof(fout, seq, mdat_size, is_idr, sampletime, seq*sampletime)
        bmff.write_mdat(fout, nalus)
        seq = seq + 1

fout.close()
