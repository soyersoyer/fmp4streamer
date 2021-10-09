import bmff, io

fin = open("test.h264", "rb")
h264 = fin.read()
fin.close()

nals = h264.split(b'\00\00\00\01')

fout = open("test.mp4", "wb")

bmff.writeFTYP(fout)
bmff.writeMOOV(fout, 1280, 720)

seq = 1
for k, nal in enumerate(nals):
    if len(nal) == 0:
        continue
    nalType = nal[0] & 0x1f
    if nalType == 5 or nalType == 1:
        if (nalType == 5):
            nalus = [nals[k-2], nals[k-1], nal]
            isIDR = True
        else:
            nalus = [nal]
            isIDR = False
        mdatSize = bmff.getMDATsize(nalus)
        bmff.writeMOOF(fout, seq, mdatSize, isIDR, 333)
        bmff.writeMDAT(fout, nalus)
        seq = seq + 1

fout.close()
