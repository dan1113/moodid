function itemsFor(a){return DB.flatMap((d,i)=>d.options.filter(o=>(a?.[i]||[]).includes(o.id)).map(o=>({...o,category:d.label})));}
function mixColor(a,b,t){return '#'+a.slice(1).match(/../g).map((v,i)=>Math.round(parseInt(v,16)*(1-t)+parseInt(b.slice(1+i*2,3+i*2),16)*t).toString(16).padStart(2,'0')).join('');}
function buildPalette(items){
 const selected=items.filter(x=>x.category==='색상').map(x=>x.color);const ids=new Set(items.map(x=>x.id));
 const weather=ids.has('2_5')?'#D5E2E8':ids.has('2_1')?'#9EADB0':ids.has('2_2')||ids.has('2_3')?'#788799':ids.has('2_0')?'#B9C6D0':'#A5AFA8';
 const warm=ids.has('6_1')||ids.has('6_3');const light=warm?'#C78F62':ids.has('6_2')?'#9E61AD':ids.has('6_6')?'#8A9BB9':'#E8DCCB';
 const season=ids.has('1_6')||ids.has('1_5')?'#B49A74':ids.has('1_7')?'#C6D1DB':ids.has('1_0')||ids.has('1_1')?'#B9C6AD':'#A7C3C1';
 const base=selected[0]||'#536B78';const colors=[...selected,mixColor(base,weather,.65),mixColor(season,light,.45),light,mixColor(base,'#F3EFE5',.87)];
 const colorItems=items.filter(x=>x.category==='색상');const names=[...colorItems.map(x=>x.name),'날씨의 공기감','계절과 빛의 온도','빛의 포인트','부드러운 여백'];const candidates=colors.map((hex,i)=>({hex,name:names[i]||'부드러운 여백'}));const unique=candidates.filter((c,i)=>candidates.findIndex(x=>x.hex.toLowerCase()===c.hex.toLowerCase())===i);for(const t of [.2,.4,.6,.8]){const hex=mixColor(base,'#F3EFE5',t);if(unique.length<5&&!unique.some(x=>x.hex===hex))unique.push({hex,name:'부드러운 여백'});}
 return unique.slice(0,5);
}
const senseRoles={시간:'장면의 리듬과 빛이 머무는 시간을 정해요.',계절:'공기와 색의 바탕이 되는 계절감을 더해요.',날씨:'장면을 감싸는 대기와 대비를 만들어요.',장소:'좋아하는 감각이 머물 공간의 배경이에요.',색상:'세계의 중심이 되는 시각 언어예요.',색조:'같은 색에서도 선명함과 깊이를 조절해요.',빛:'장면의 온도와 윤곽을 드러내요.',소리:'보이는 풍경에 움직임과 공간감을 더해요.',음악:'장면에 흐를 리듬과 청각적 질감을 더해요.',향:'눈에 보이지 않는 공기의 인상을 완성해요.',질감:'손끝에 느껴질 소재의 표정을 더해요.',공간:'선택한 감각을 배치하는 방식과 여백이에요.'};
function buildDNA(items,roles=[]){return DB.map(d=>({category:d.label,en:d.en,choices:items.filter(x=>x.category===d.label),role:roles.find(x=>x.category===d.label)?.role||senseRoles[d.label]}));}
function rankCatalog(catalog,items,feedback={}){const ids=new Set(items.map(x=>x.id)),tags={};items.forEach(o=>Object.entries(o.tags).forEach(([t,v])=>tags[t]=(tags[t]||0)+v));return catalog.map(c=>({...c,score:c.tags.reduce((n,t)=>n+(tags[t]||0),0)+c.options.filter(id=>ids.has(id)).length*4+(feedback[c.id]===1?6:feedback[c.id]===-1?-20:0)})).sort((a,b)=>b.score-a.score);}
function matchPins(items){const ranked=rankCatalog(PIN_CATALOG,items);const out=[];for(const kind of ['atmosphere','space','scenery']){const pick=ranked.find(p=>p.kind===kind&&!out.some(x=>x.id===p.id));if(pick)out.push(pick)}return out.slice(0,3);}
function discoveriesFor(items){const feedback=read('moodid-discovery-feedback',{});return rankCatalog(DISCOVERIES,items,feedback).filter(x=>feedback[x.id]!==-1).slice(0,3);}
function connectionFallback(items){const light=items.filter(x=>x.category==='빛').map(x=>x.name).join(' · '),weather=items.filter(x=>x.category==='날씨').map(x=>x.name).join(' · '),material=items.filter(x=>x.category==='질감').map(x=>x.name).join(' · ');return {title:'서로 다른 감각이 하나의 장면이 될 때',text:`‘${weather}’의 공기감에 ‘${light}’의 빛을 더하고, ‘${material}’의 질감으로 손끝의 감각을 겹쳐보세요. 이처럼 선택한 요소들은 같은 분위기를 반복하기보다 서로 다른 역할로 당신만의 장면을 함께 구성합니다.`};}
function recommendationReason(d,items){const matched=items.filter(x=>d.options.includes(x.id)).map(x=>x.name);return (matched.length?matched.slice(0,3).join(' · '):d.tags.slice(0,2).join(' · '))+' 선호에서 이어진 탐색 제안이에요. 아직 확인되지 않은 취향이니, 마음에 드는지 가볍게 만나보세요.';}
function synthesizeSenses(items){
 const pick=c=>items.filter(x=>x.category===c).map(x=>x.name).slice(0,2).join(' · '),weights={};items.forEach(o=>Object.entries(o.tags).forEach(([k,v])=>weights[k]=(weights[k]||0)+v));
 const nouns={'고요한':'고요함','따뜻한':'온기','몽환적인':'몽환성','향수 어린':'시간의 깊이','자연적인':'자연의 결','도시적인':'도시의 리듬','정갈한':'정돈된 여백','선명한':'선명한 생동감'},top=Object.keys(weights).sort((a,b)=>weights[b]-weights[a]).slice(0,2);
 return {title:top.map(t=>nouns[t]||t).join(' · ')+'의 어우러짐',text:`선택한 감각 전반에는 ‘${top.map(t=>nouns[t]||t).join(' · ')}’이라는 결이 흐릅니다. ‘${pick('날씨')}’의 공기, ‘${pick('빛')}’에서 느껴지는 빛, ‘${pick('질감')}’의 표면이 하나의 장면에 겹쳐져요. ‘${pick('음악')}’의 리듬과 ‘${pick('향')}’의 잔향이 더해지면, 눈에 보이는 색과 손끝의 촉감, 공간의 분위기가 따로 떨어지지 않고 하나의 세계로 느껴집니다.`};
}
function normalizeExplorations(queries){
 const used=new Set();return (Array.isArray(queries)?queries:[]).slice(0,6).flatMap(q=>{
 if(!q||typeof q.query!=='string'||typeof q.title!=='string')return [];
 const pin=PIN_CATALOG.find(p=>p.id===q.pinId);
 if(pin){if(used.has(pin.id))return [];used.add(pin.id);return [{pinId:pin.id,title:pin.title,query:pin.query,reason:typeof q.reason==='string'?q.reason.slice(0,240):''}];}
 return [{pinId:null,title:q.title.slice(0,100),query:q.query.slice(0,200),reason:''}];
 });
}
function fallbackExplorations(items){return rankCatalog(PIN_CATALOG,items).slice(0,6).map(p=>({pinId:p.id,title:p.title,query:p.query,reason:''}));}
function matchCuriosityPins(queries){return queries.map(q=>PIN_CATALOG.find(p=>p.id===q.pinId)||null);}
