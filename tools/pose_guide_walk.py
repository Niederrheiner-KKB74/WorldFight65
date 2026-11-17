#!/usr/bin/env python3
"""Pose guide for walk cycles: a simple mannequin in the 6 walk phases, near leg orange, far leg blue,
256 px cells with the floor line at y = 239 (assets/art/guides/). Attach it to the generator prompt so that
the near and far legs alternate correctly (generators tend to keep the near leg in front in all frames)."""
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'art' / 'guides'
OUT.mkdir(parents=True, exist_ok=True)
import math
from PIL import Image, ImageDraw
S=4                     # supersampling
CELL=256; GROUND=239
THIGH, SHIN, FOOT = 53, 50, 22
HIP_X = 120
# (near thigh, near knee flex, far thigh, far knee flex) in degrees; thigh + = forward
PH=[(24,4,-24,6),(8,26,-16,48),(-8,10,22,78),(-24,6,24,4),(-16,48,8,26),(22,78,-8,10)]
def leg(hx,hy,th,kn):
    t=math.radians(th); s=math.radians(th-kn)
    kx,ky=hx+THIGH*math.sin(t),hy+THIGH*math.cos(t)
    ax,ay=kx+SHIN*math.sin(s),ky+SHIN*math.cos(s)
    return (kx,ky),(ax,ay)
def stance_drop(th,kn):
    t=math.radians(th); s=math.radians(th-kn)
    return THIGH*math.cos(t)+SHIN*math.cos(s)
sheet=Image.new('RGB',(CELL*6*S,CELL*S),'white'); d=ImageDraw.Draw(sheet)
def P(x,y,k): return ((k*CELL+x)*S,y*S)
for k,(nt,nk,ft,fk) in enumerate(PH):
    # hip height: the lower of the two ankles stands on the ground (ankle 8 px above ground)
    hy=GROUND-8-max(stance_drop(nt,nk),stance_drop(ft,fk))
    bob = hy
    W=lambda pts,col,w: d.line([P(x,y,k) for x,y in pts],fill=col,width=w*S,joint='curve')
    def draw_leg(th,kn,col,dark):
        (kx,ky),(ax,ay)=leg(HIP_X,hy,th,kn)
        W([(HIP_X,hy),(kx,ky),(ax,ay)],col,16)
        # foot: on the ground flat, lifted: toes pointing down a little
        lift=GROUND-8-ay
        if th < -10 and lift < 14:          # rear foot: heel up, toes on the floor
            W([(ax-4,ay+2),(ax+FOOT*0.8,GROUND-3)],dark,10)
        else:
            ang=math.radians(min(lift*1.2,35)) if lift>2 else 0
            W([(ax-6,ay+4),(ax-6+FOOT*math.cos(ang),ay+4+FOOT*math.sin(ang))],dark,12)
    draw_leg(ft,fk,(40,80,200),(20,40,140))        # far leg: blue
    # torso, head, arms (guard) - fixed
    top=hy-104
    d.polygon([P(HIP_X-22,hy+4,k),P(HIP_X+22,hy+4,k),P(HIP_X+38,top+44,k),P(HIP_X-36,top+44,k)],fill=(150,150,150))
    d.ellipse([P(HIP_X-16,top-16,k),P(HIP_X+30,top+38,k)],fill=(170,170,170))
    d.ellipse([P(HIP_X+20,top+2,k),P(HIP_X+32,top+14,k)],fill=(90,90,90))   # face side marker
    W([(HIP_X-30,top+50),(HIP_X-10,top+84),(HIP_X+20,top+62)],(110,110,110),14)
    W([(HIP_X+30,top+50),(HIP_X+50,top+80),(HIP_X+66,top+54)],(130,130,130),14)
    draw_leg(nt,nk,(240,150,40),(200,100,20))      # near leg: orange
    d.line([P(0,GROUND,k),P(CELL-1,GROUND,k)],fill=(0,0,0),width=S)
    d.text(P(6,6,k),str(k+1),fill=(0,0,0))
img=sheet.resize((CELL*6,CELL),Image.LANCZOS)
img.save(OUT / 'walk_pose_guide.png')
for k in range(6): img.crop((k*CELL,0,(k+1)*CELL,CELL)).resize((512,512),Image.LANCZOS).save(OUT / f'walk_guide_{k+1}.png')
