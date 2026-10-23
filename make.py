import json
from pathlib import Path
p=Path('/workspace/sites/moodid')
rows=[
('TIME','어떤 시간에 마음이 머무나요?','시간','새벽 4시|동트는 아침|오전 10시|한낮|오후 3시|해 질 녘|블루 아워|자정','dawn|morning|sunlit morning|midday|afternoon|sunset|blue hour|midnight'),
('SEASON','당신이 기다리는 계절은?','계절','초봄|늦봄|초여름|한여름|장마철|초가을|늦가을|한겨울','early spring|late spring|early summer|summer|rainy season|early autumn|late autumn|winter'),
('WEATHER','어떤 공기가 당신을 감싸면 좋을까요?','날씨','맑은 하늘|옅은 안개|보슬비|장대비|흐린 하늘|소복한 눈|바람 부는 날|비 갠 직후','clear sky|mist|drizzle|heavy rain|overcast|snow|windy|after rain'),
('PLACE','오래 머물고 싶은 장소는?','장소','깊은 숲|잔잔한 바다|오래된 골목|도시의 옥상|작은 도서관|들판|호숫가|지하철역','forest|ocean|old alley|city rooftop|library|meadow|lake|train station'),
('COLOR','눈길이 오래 닿는 색을 골라주세요.','색상','네이비|버건디|아이보리|올리브|코발트|테라코타|라벤더|차콜','navy|burgundy|ivory|olive|cobalt|terracotta|lavender|charcoal'),
('TONE','색의 어떤 표정이 좋은가요?','색조','파스텔|먼지 낀 뮤트|선명한 비비드|깊은 딥톤|모노톤|빛바랜 색|흙빛|투명한 색','pastel|muted|vivid|deep tones|monochrome|faded|earthy|translucent'),
('LIGHT','당신의 장면을 비추는 빛은?','빛','아침 자연광|따뜻한 간접조명|네온사인|촛불|창문 사이 햇살|차가운 형광등|달빛|흐린 날 확산광','morning light|warm ambient light|neon|candlelight|window sunlight|fluorescent|moonlight|diffused light'),
('SOUND','가만히 듣고 싶은 소리는?','소리','창가의 빗소리|나뭇잎 바람|달리는 열차|잔잔한 파도|장작 타는 소리|카페의 웅성거림|도시의 밤|고요한 정적','rain sounds|rustling leaves|train sounds|ocean waves|crackling fire|cafe ambience|city night|silence'),
('MUSIC','장면에 음악을 더한다면?','음악','느긋한 재즈|담백한 인디|공간을 채우는 앰비언트|피아노 클래식|로파이|몽환적인 드림팝|일렉트로닉|어쿠스틱','jazz|indie|ambient|classical piano|lofi|dream pop|electronic|acoustic'),
('SCENT','공기에 남았으면 하는 향은?','향','마른 나무 우디|포근한 머스크|상큼한 시트러스|은은한 플로럴|젖은 흙|깨끗한 비누|달콤한 바닐라|바다의 소금기','woody|musk|citrus|floral|petrichor|clean soap|vanilla|sea salt'),
('TEXTURE','손끝에 닿으면 좋은 질감은?','질감','바스락한 린넨|거친 콘크리트|투명한 유리|오래된 종이|부드러운 벨벳|결이 있는 나무|차가운 금속|따뜻한 니트','linen|concrete|glass|aged paper|velvet|wood grain|metal|knit'),
('SPACE','당신의 공간은 어떤 모습인가요?','공간','여백 있는 미니멀|시간이 쌓인 빈티지|묵직한 브루탈리즘|편안한 내추럴|자유로운 보헤미안|반짝이는 퓨처리즘|정갈한 일본식|풍성한 맥시멀','minimal interior|vintage interior|brutalist interior|natural interior|bohemian interior|futuristic interior|japanese interior|maximalist interior')]
tags=['고요한','따뜻한','선명한','몽환적인','자연적인','도시적인','향수 어린','정갈한']
# Explicit category-specific semantic mappings; each option carries two independent attributes.
maps=[[0,4,7,2,1,6,3,5],[3,1,4,2,0,4,6,7],[2,3,0,5,7,0,4,1],[4,0,6,5,7,4,3,5],[0,6,7,4,2,1,3,5],[3,0,2,6,7,6,4,7],[4,1,5,1,2,7,3,0],[0,4,6,0,1,5,5,7],[1,6,3,7,0,3,2,4],[4,1,2,3,4,7,1,0],[4,5,7,6,3,4,5,1],[7,6,5,4,3,2,0,2]]
colors=['#293C50','#723D48','#E7DFCC','#6C7150','#315BC4','#BB7455','#A49AAF','#373936']
db=[]
for ci,(en,q,label,ko,eng) in enumerate(rows):
 opts=[]
 for j,(name,search) in enumerate(zip(ko.split('|'),eng.split('|'))):
  a=maps[ci][j]; b={0:3,1:6,2:5,3:0,4:7,5:2,6:1,7:0}[a]
  opts.append(dict(id=f'{ci}_{j}',name=name,en=search,tags={tags[a]:1,tags[b]:.35},color=colors[j]))
 db.append(dict(en=en,q=q,label=label,options=opts))
(p/'database.json').write_text(json.dumps(db,ensure_ascii=False))
