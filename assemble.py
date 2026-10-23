from pathlib import Path
import json, base64
p=Path(__file__).parent
page=(p/'page.html').read_text().replace('__DB__',(p/'database.json').read_text()).replace('__PINS__',(p/'pinterest-catalog.json').read_text()).replace('__DISCOVERIES__',(p/'discoveries.json').read_text()).replace('__ENGINE__',(p/'aesthetic-engine.js').read_text())
server='''
const analysisCache=new Map();
const reply=(v,status=200)=>Response.json(v,{status,headers:{'cache-control':'no-store'}});
export default {async fetch(req,env){const url=new URL(req.url);
if(url.pathname.startsWith('/assets/options/')){const file=url.pathname.split('/').pop();const bytes=ASSETS[file];if(!bytes)return new Response('Not found',{status:404});return new Response(Uint8Array.from(atob(bytes),c=>c.charCodeAt(0)),{headers:{'content-type':'image/webp','cache-control':'public, max-age=31536000, immutable','x-content-type-options':'nosniff'}});}
if(url.pathname==='/api/analyze'){
 if(req.method!=='POST')return reply({error:'Method not allowed'},405);
 if(req.headers.get('origin')&&req.headers.get('origin')!==url.origin)return reply({error:'허용되지 않은 요청입니다.'},403);
 try{const raw=await req.text();if(raw.length>10000)return reply({error:'요청이 너무 큽니다.'},413);const {answers,feedback,refresh}=JSON.parse(raw);const items=[];const scores={};
 for(let i=0;i<DB.length;i++){const ids=answers?.[i];if(!Array.isArray(ids)||ids.length<1||ids.length>3||new Set(ids).size!==ids.length)return reply({error:'모든 감각을 선택해주세요.'},400);for(const id of ids){const o=DB[i].options.find(x=>x.id===id);if(!o)return reply({error:'올바르지 않은 선택입니다.'},400);items.push({id:o.id,category:DB[i].label,name:o.name,en:o.en,tags:o.tags,color:o.color});for(const [k,v] of Object.entries(o.tags))scores[k]=(scores[k]||0)+v/ids.length;}}
 if(!env.GEMINI_API_KEY)return reply({error:'AI 연결 설정을 확인해주세요.'},503);
 const preferences={};if(feedback&&typeof feedback==='object'&&!Array.isArray(feedback))for(const d of DISCOVERIES)if(feedback[d.id]===1||feedback[d.id]===-1)preferences[d.id]=feedback[d.id];
 const cacheKey=JSON.stringify([DB.map((d,i)=>[...answers[i]].sort()),Object.entries(preferences).sort()]);const cached=analysisCache.get(cacheKey);if(!refresh&&cached&&Date.now()-cached.time<1800000)return reply(cached.result);
 const palette=buildPalette(items);const recommendations=rankCatalog(DISCOVERIES,items,preferences).filter(d=>preferences[d.id]!==-1).slice(0,3);
 const prompt='당신은 MOODID 미감 에디터입니다. 실제 선택 감각과 고정 속성만 근거로 개인 미감 프로필을 작성하세요. 고정 유형 배정, MBTI, 성격 및 심리 진단, 선택하지 않은 취향 단정 금지. 서로 다른 감각의 공통점과 대비를 구체적 선택 3~5개와 연결해 설명하세요. JSON 스키마: {name:짧고 고유한 한국어 미감 이름,english:2~5단어 영어 제목,description:한국어 종합 분석 180자 내외,keywords:감각 키워드 문자열 6개,sensorySynthesis:{title:전체 선택을 하나의 감각으로 연결한 짧은 제목,text:시간 계절 날씨 장소 색조 빛 음악 소리 향 질감 공간의 역할을 하나의 장면으로 엮은 통합 감각 설명 180자 내외. 선택을 항목별 나열하지 말고 서로 어우러져 느껴지는 감각을 구체적으로 묘사. 종합 분석문과 반복하지 말 것},senseRoles:[{category:주어진 카테고리명,role:해당 선택이 전체 미감에서 맡는 역할 30자 이내}] 12개,connection:{title:연결고리를 표현하는 제목,text:서로 다른 선택 3개 이상을 연결한 한국어 설명 100자 내외},paletteExplanation:주어진 팔레트와 빛 날씨 계절 선택의 관계를 설명한 60자 내외 문장,queries:[{title:한국어 탐색 주제,query:영어 Pinterest 검색어}] 6개,discoveries:[{id:주어진 추천 후보 id,reason:실제 선택에서 해당 미감으로 연결한 근거 55자 이내}]}. queries는 분위기,공간,풍경,디테일,빛,음악 관련 시각 레퍼런스처럼 서로 다른 관점으로 작성. URL이나 Pinterest 핀 ID를 생성하지 마세요. 추천은 가능성으로 표현하고 사용자 피드백은 추천에만 반영하세요. 핵심 점수와 팔레트는 변경 금지. JSON만 반환. 데이터:'+JSON.stringify({items:items.map(({category,name})=>({category,name})),scores,palette,recommendations:recommendations.map(({id,name,tags})=>({id,name,tags})),preferences});
 const res=await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent',{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':env.GEMINI_API_KEY},body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{thinkingConfig:{thinkingLevel:'low'},responseMimeType:'application/json',temperature:.75,maxOutputTokens:6000}}),signal:AbortSignal.timeout(45000)});
 if(!res.ok)return reply({error:res.status===429?'AI 요청 한도에 도달했어요. 잠시 후 다시 시도해주세요.':'Gemini 인증 또는 모델 연결을 확인해주세요.'},502);
 const rawResult=await res.json();const txt=rawResult.candidates?.[0]?.content?.parts?.filter(p=>p.text).map(p=>p.text).join('');const data=JSON.parse(txt);
 if(typeof data.name!=='string'||typeof data.english!=='string'||typeof data.description!=='string'||!Array.isArray(data.keywords)||!Array.isArray(data.queries))throw Error();
 const sensorySynthesis=data.sensorySynthesis&&typeof data.sensorySynthesis.title==='string'&&typeof data.sensorySynthesis.text==='string'?{title:data.sensorySynthesis.title.slice(0,150),text:data.sensorySynthesis.text.slice(0,1200)}:undefined;
 const senseRoles=Array.isArray(data.senseRoles)?data.senseRoles.filter(x=>DB.some(d=>d.label===x.category)&&typeof x.role==='string').slice(0,12).map(x=>({category:x.category,role:x.role.slice(0,200)})):[];
 const connection=data.connection&&typeof data.connection.title==='string'&&typeof data.connection.text==='string'?{title:data.connection.title.slice(0,150),text:data.connection.text.slice(0,1200)}:undefined;
 const discoveries=Array.isArray(data.discoveries)?data.discoveries.filter(x=>recommendations.some(d=>d.id===x.id)&&typeof x.reason==='string').map(x=>({id:x.id,reason:x.reason.slice(0,400)})).slice(0,3):[];
 const result={name:data.name.slice(0,70),english:data.english.slice(0,100),description:data.description.slice(0,1500),keywords:data.keywords.filter(x=>typeof x==='string').slice(0,6),queries:data.queries.filter(x=>typeof x.title==='string'&&typeof x.query==='string').slice(0,8),sensorySynthesis,senseRoles,connection,discoveries,paletteExplanation:typeof data.paletteExplanation==='string'?data.paletteExplanation.slice(0,600):undefined};if(analysisCache.size>=100)analysisCache.delete(analysisCache.keys().next().value);analysisCache.set(cacheKey,{time:Date.now(),result});return reply(result);
 }catch{return reply({error:'분석 연결이 지연되고 있어요. 다시 시도해주세요.'},503)}
}
if(url.pathname!=='/')return new Response('Not found',{status:404});return new Response(PAGE,{headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-cache','x-content-type-options':'nosniff'}});
}};
'''
assets={f.name:base64.b64encode(f.read_bytes()).decode() for f in (p/'assets/options').glob('*.webp')}
(p/'worker/index.js').write_text('const ASSETS='+json.dumps(assets)+';\n'+'const DB='+ (p/'database.json').read_text()+';\nconst PIN_CATALOG='+(p/'pinterest-catalog.json').read_text()+';\nconst DISCOVERIES='+(p/'discoveries.json').read_text()+';\n'+(p/'aesthetic-engine.js').read_text()+'\nconst PAGE='+json.dumps(page,ensure_ascii=False)+';\n'+server)
