"""Offline complete-scene batches, closed by observed display-page flips.

The first batch after attachment and last unfinished batch are excluded.
Camera equality is validation, never the batch identifier.
"""
import struct
def records(path):
    data=path.read_bytes();position=0
    while position<len(data):
        if position+84>len(data):raise ValueError('Truncated record header')
        header=struct.unpack_from('<21I',data,position);position+=84
        if header[0]!=0x3157464e or header[4]>64:raise ValueError('Invalid capture record')
        blocks={}
        for _ in range(header[4]):
            if position+12>len(data):raise ValueError('Truncated block header')
            tag,address,size=struct.unpack_from('<3I',data,position);position+=12
            if position+size>len(data) or tag in blocks:raise ValueError('Invalid block')
            blocks[tag]=(address,data[position:position+size]);position+=size
        yield {'pc':header[1],'frame':header[2],'id':header[3],'regs':header[5:],'blocks':blocks}
def batches(path):
    pending=[];previous=None;serial=0
    for e in records(path):
        if e['pc']!=0x04000000:
            pending.append(e);continue
        if previous is not None:
            yield {'serial':serial,'begin_refresh':previous['frame'],'end_refresh':e['frame'],
                   'display_page':1 if e['regs'][1]&16 else 0,'events':pending}
            serial+=1
        pending=[];previous=e
