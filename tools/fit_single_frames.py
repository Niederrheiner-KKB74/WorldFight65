import sys; sys.path.insert(0,'tools'); import import_fighter as imf, numpy as np
from PIL import Image
KEY=(255,0,255)
ref=imf.cells('/tmp/walk3/sheet16.png')
def upper(mask, top, n=95):
    reg=mask[top:top+n]
    ys,xs=np.nonzero(reg); cx=xs.mean()
    return reg, cx
def place_single(raw_path, refcell):
    rgb=np.array(Image.open(raw_path).convert('RGB')); bg=imf.split_key(rgb)[0]; fg=~bg
    ys,xs=np.nonzero(fg); top0=ys.min(); bot0=ys.max()
    rm=imf.figure_mask(refcell); rys,rxs=np.nonzero(rm); rtop=rys.min()
    rreg,rcx=upper(rm,rtop)
    best=None
    for s in np.arange(0.16,0.24,0.002):
        m=np.array(Image.fromarray((fg*255).astype(np.uint8)).resize((round(fg.shape[1]*s),round(fg.shape[0]*s)),Image.BOX))>=128
        mys,mxs=np.nonzero(m); mt=mys.min()
        reg,cx=upper(m,mt)
        if reg.shape[0]<95: continue
        dx=int(round(rcx-cx))
        # compare on a common window
        W=256
        a=np.zeros((95,W),bool); b=np.zeros((95,W),bool)
        a[:, :]=rreg[:, :W]
        sh=np.zeros((95,W+400),bool); 
        x0=200+dx
        sub=reg[:, :]
        w=min(sub.shape[1], W+400-x0)
        sh[:, x0:x0+w]=sub[:, :w]
        b=sh[:,200:200+W]
        iou=(a&b).sum()/(a|b).sum()
        if best is None or iou>best[0]: best=(iou,s,dx,mt)
    iou,s,dx,mt=best
    # build the cell: scale colour (bg->outline) and mask, place so that the lowest pixel is at 239 and dx aligned
    col=rgb.copy(); col[bg]=imf.OUTLINE_RGB
    W2,H2=round(rgb.shape[1]*s),round(rgb.shape[0]*s)
    c=np.array(Image.fromarray(col).resize((W2,H2),Image.LANCZOS))
    m=np.array(Image.fromarray((fg*255).astype(np.uint8)).resize((W2,H2),Image.BOX))>=128
    mys,mxs=np.nonzero(m); oy=239-mys.max(); ox=dx
    cell=np.zeros((256,256,3),np.uint8); cell[:]=KEY
    for y in range(H2):
        ty=y+oy
        if not 0<=ty<256: continue
        for_x=np.arange(W2)+ox
        ok=(for_x>=0)&(for_x<256)&m[y]
        cell[ty,for_x[ok]]=c[y,ok]
    return cell, iou, s
out=Image.new('RGB',(256*6,256),KEY)
for k in range(3): out.paste(Image.fromarray(ref[k]),(k*256,0))
for k,f in enumerate(['f4','f5','f6']):
    cell,iou,s=place_single(f'/tmp/walk3/{f}_raw.png', ref[0])
    print(f,'scale %.3f iou %.2f'%(s,iou))
    out.paste(Image.fromarray(cell),((k+3)*256,0))
out.save('/tmp/walk3/konrad_walk.png')
