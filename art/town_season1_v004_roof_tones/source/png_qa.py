"""Display-code-preserving PNG QA functions copied from v003; no art edits."""
import bpy,struct,zlib,binascii,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(relative):
    image=bpy.data.images.load(str(ROOT/relative),check_existing=False);w,h=image.size;values=np.empty(w*h*4,dtype=np.float32);image.pixels.foreach_get(values);bpy.data.images.remove(image)
    values=values.reshape(h,w,4)
    # Blender exposes these byte-image pixels as normalized display-code values.
    # Prove that interpretation against the first raw PNG pixel (all predictors zero).
    raw=(ROOT/relative).read_bytes();ww,hh,depth,color,_,_,interlace=struct.unpack_from('>IIBBBBB',raw,16)
    assert (ww,hh,depth,color,interlace)==(w,h,8,6,0)
    offset=8;idats=[]
    while offset<len(raw):
        length=struct.unpack_from('>I',raw,offset)[0];kind=raw[offset+4:offset+8]
        if kind==b'IDAT':idats.append(raw[offset+8:offset+8+length])
        offset+=12+length
    first=zlib.decompressobj().decompress(b''.join(idats),5)[1:5]
    assert bytes(np.rint(values[-1,0]*255).astype(np.uint8))==first
    assert np.max(np.abs(values*255-np.rint(values*255)))<1e-4
    return values

def png(path,codes):
    # Copy normalized PNG code bytes directly. No gamma/view/color adjustment.
    encoded=np.rint(np.clip(codes,0,1)*255).astype(np.uint8)
    encoded=np.flipud(encoded);h,w=encoded.shape[:2]
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',binascii.crc32(name+data)&0xffffffff)
    data=b''.join(b'\0'+row.tobytes() for row in encoded)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(data,6))+chunk(b'IEND',b''))

def metrics(a,b):
    diff=np.abs(a[:,:,:3]-b[:,:,:3]);maximum=diff.max(axis=2);where=np.argwhere(maximum>.01)
    def decode(rgb):return np.where(rgb<=.04045,rgb/12.92,np.power((rgb+.055)/1.055,2.4))
    linear=np.abs(decode(a[:,:,:3])-decode(b[:,:,:3]))
    return {'mean_png_code_rgb_abs_error':float(diff.mean()),'mean_display_linear_rgb_abs_error':float(linear.mean()),'png_code_rgb_rmse':float(np.sqrt(np.mean(diff*diff))),
            'max_png_code_channel_difference':float(diff.max()),'p99_max_channel_difference':float(np.quantile(maximum,.99)),
            'percent_pixels_over_0_01':float(np.mean(maximum>.01)*100),'percent_pixels_over_0_003':float(np.mean(maximum>.003)*100),
            'difference_over_0_01_bbox_bottom_left':([int(where[:,1].min()),int(where[:,0].min()),int(where[:,1].max()),int(where[:,0].max())] if len(where) else None)}
