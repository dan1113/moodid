from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
import json
p=Path(__file__).parent
entries=json.loads((p/'image-sources.json').read_text())
for e in entries:
 out=p/'assets/options'/f"{e['id']}.webp"
 if not out.exists():
  im=Image.open(e['path']).convert('RGB'); im=ImageOps.fit(im,(480,320),method=Image.Resampling.LANCZOS);im.save(out,'WEBP',quality=76,method=6)
print('Optimized',len(entries),'images')
