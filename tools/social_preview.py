#!/usr/bin/env python3
"""Render the site's 1200x630 social card. Requires Pillow; uses local system fonts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
S = 2
im = Image.new('RGB', (1200*S, 630*S), '#fdfaf3')
d = ImageDraw.Draw(im)
fonts = Path('/System/Library/Fonts/Supplemental')
def font(name, size): return ImageFont.truetype(str(fonts / name), size*S)
def text(x,y,s,size=22,color='#1c1a17',face='Arial.ttf'):
    d.text((x*S,y*S),s,font=font(face,size),fill=color)
def line(points,fill='#d6cdb9',width=1): d.line([(x*S,y*S) for x,y in points],fill=fill,width=width*S)
mark=Image.open(ROOT/'assets/mark.png').convert('RGBA'); mark.thumbnail((40*S,40*S)); im.paste(mark,(60*S,48*S),mark)
text(112,56,'RENAISSANCE LABS',17,face='Arial Bold.ttf')
line([(60,115),(1140,115)])
text(60,158,'Open Environments',65,face='Georgia.ttf')
text(60,231,'Index',65,face='Georgia.ttf')
text(62,339,'A place for models',32,face='Georgia.ttf')
text(62,382,'to practice human work.',32,'#9a7a48','Georgia Italic.ttf')
text(62,462,'Open RL environments, mapped across',20,'#625b52')
text(62,493,'every field of education and training.',20,'#625b52')
# An editorial field map: occupied plots and open space, echoing the index taxonomy.
colors=['#b0763c','#a35c47','#8a5a83','#5a6f9a','#4f7a6a','#c08f2f','#74813a','#3f8587','#b5544f','#7d6a9a']
for row in range(8):
 for col in range(6):
  x,y=790+col*55,162+row*43
  occupied=(row*7+col*3)%11<6
  fill=colors[(row+col)%10] if occupied else '#f6f0e2'
  d.rounded_rectangle((x*S,y*S,(x+40)*S,(y+28)*S),radius=3*S,fill=fill,outline=None if occupied else '#d6cdb9',width=S)
text(790,526,'FIND A FIELD. BUILD A SKILL.',12,'#625b52',face='Arial Bold.ttf')
line([(60,566),(1140,566)])
text(62,586,'practice.renaissancelabs.eu',17,'#625b52')
text(880,586,'OPEN BY DESIGN',13,'#9a7a48',face='Arial Bold.ttf')
im.resize((1200,630),Image.Resampling.LANCZOS).save(ROOT/'assets/social-preview.png',optimize=True)
print(ROOT/'assets/social-preview.png')
