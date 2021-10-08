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
        data, iframe = (bmff.nals2AVC([nals[k-2], nals[k-1], nal]), True) if nalType == 5 \
            else (bmff.nals2AVC([nal]), False)
        bmff.writeMOOF(fout, seq, len(data), iframe, 333)
        bmff.writeMDAT(fout, data)
        seq = seq + 1

fout.close()
