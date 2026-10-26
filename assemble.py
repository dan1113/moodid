from pathlib import Path
import json, base64
p=Path(__file__).parent
page=(p/'page.html').read_text().replace('__DB__',(p/'database.json').read_text()).replace('__PINS__',(p/'pinterest-catalog.json').read_text()).replace('__DISCOVERIES__',(p/'discoveries.json').read_text()).replace('__RESULT_REFERENCES__',json.dumps(json.loads((p/'result-reference-db.json').read_text())['references'],ensure_ascii=False)).replace('__ENGINE__',(p/'aesthetic-engine.js').read_text())
server='''
const analysisCache=new Map(),requestWindows=new Map();let activeAnalyses=0;
const reply=(v,status=200)=>Response.json(v,{status,headers:{'cache-control':'no-store'}});
export default {async fetch(req,env){const url=new URL(req.url);
if(url.pathname.startsWith('/assets/options/')){const file=url.pathname.split('/').pop();const bytes=ASSETS[file];if(!bytes)return new Response('Not found',{status:404});return new Response(Uint8Array.from(atob(bytes),c=>c.charCodeAt(0)),{headers:{'content-type':'image/webp','cache-control':'public, max-age=31536000, immutable','x-content-type-options':'nosniff'}});}
if(url.pathname==='/api/image-search'||url.pathname==='/api/reference-image')return imageSearchRoute(req,env,url);
if(url.pathname==='/api/stats'){
 if(!['GET','POST'].includes(req.method))return reply({error:'Method not allowed'},405);
 if(!env.MOODID_COUNTER)return reply({available:false},503);
 if(req.method==='POST'){
  if(req.headers.get('origin')!==url.origin)return reply({error:'Forbidden'},403);
  try{const raw=await req.text();if(raw.length>5000)return reply({error:'Too large'},413);const body=JSON.parse(raw);
   if(!/^[a-f0-9-]{36}$/.test(body.visitorId||'')||!DB.every((d,i)=>Array.isArray(body.answers?.[i])&&body.answers[i].length>=1&&body.answers[i].length<=3&&new Set(body.answers[i]).size===body.answers[i].length&&body.answers[i].every(id=>d.options.some(o=>o.id===id))))return reply({error:'Invalid completion'},400);
   const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body.visitorId)))).map(b=>b.toString(16).padStart(2,'0')).join('');
   return await env.MOODID_COUNTER.get(env.MOODID_COUNTER.idFromName('completed-browsers-v1')).fetch('https://counter/complete',{method:'POST',body:JSON.stringify({hash})});
  }catch{return reply({available:false},503)}
 }
 try{return await env.MOODID_COUNTER.get(env.MOODID_COUNTER.idFromName('completed-browsers-v1')).fetch('https://counter/count')}catch{return reply({available:false},503)}
}
if(url.pathname==='/api/analyze'){
 if(req.method!=='POST')return reply({error:'Method not allowed'},405);
 if(req.headers.get('origin')&&req.headers.get('origin')!==url.origin)return reply({error:'허용되지 않은 요청입니다.'},403);
 try{const raw=await req.text();if(raw.length>10000)return reply({error:'요청이 너무 큽니다.'},413);let parsed;try{parsed=JSON.parse(raw)}catch{return reply({error:'요청 형식이 올바르지 않아요.'},400)}if(!parsed||typeof parsed!=='object'||Array.isArray(parsed))return reply({error:'요청 형식이 올바르지 않아요.'},400);const {answers,feedback,refresh}=parsed;const items=[];const scores={};
 for(let i=0;i<DB.length;i++){const ids=answers?.[i];if(!Array.isArray(ids)||ids.length<1||ids.length>3||new Set(ids).size!==ids.length)return reply({error:'모든 감각을 선택해주세요.'},400);for(const id of ids){const o=DB[i].options.find(x=>x.id===id);if(!o)return reply({error:'올바르지 않은 선택입니다.'},400);items.push({id:o.id,category:DB[i].label,name:o.name,en:o.en,tags:o.tags,color:o.color});for(const [k,v] of Object.entries(o.tags))scores[k]=(scores[k]||0)+v/ids.length;}}
 if(!env.GEMINI_API_KEY)return reply({error:'AI 연결 설정을 확인해주세요.'},503);
 const preferences={};if(feedback&&typeof feedback==='object'&&!Array.isArray(feedback))for(const d of DISCOVERIES)if(feedback[d.id]===1||feedback[d.id]===-1)preferences[d.id]=feedback[d.id];
 const cacheKey=JSON.stringify(['no-music-v5',DB.map((d,i)=>[...answers[i]].sort()),Object.entries(preferences).sort()]);const cached=analysisCache.get(cacheKey);if(!refresh&&cached&&Date.now()-cached.time<1800000)return reply(cached.result);
 const client=req.headers.get('cf-connecting-ip')||'local',now=Date.now(),window=requestWindows.get(client);if(window&&now-window.start<60000&&window.count>=6)return reply({error:'분석 요청이 많아요. 1분 뒤 다시 시도해주세요. 기본 결과는 그대로 볼 수 있어요.'},429);if(activeAnalyses>=4)return reply({error:'분석이 몰리고 있어요. 잠시 뒤 다시 시도해주세요.'},429);if(requestWindows.size>=1000)requestWindows.delete(requestWindows.keys().next().value);requestWindows.set(client,window&&now-window.start<60000?{...window,count:window.count+1}:{start:now,count:1});activeAnalyses++;try{
 const palette=buildPalette(items);const recommendations=rankCatalog(DISCOVERIES,items,preferences).filter(d=>preferences[d.id]!==-1).slice(0,3);
 const prompt='당신은 MOODID 미감 에디터입니다. 실제 선택 감각과 고정 속성만 근거로 개인 미감 프로필을 작성하세요. 고정 유형 배정, MBTI, 성격 및 심리 진단, 선택하지 않은 취향 단정 금지. 서로 다른 감각의 공통점과 대비를 구체적 선택 3~5개와 연결해 설명하세요. JSON 스키마: {name:짧고 고유한 한국어 미감 이름,english:2~5단어 영어 제목,description:한국어 종합 분석 180자 내외,keywords:감각 키워드 문자열 6개,sensorySynthesis:{title:전체 선택을 하나의 감각으로 연결한 짧은 제목,text:시간 계절 날씨 장소 색조 빛 소리 향 질감 공간의 역할을 하나의 장면으로 엮은 통합 감각 설명 180자 내외. 선택을 항목별 나열하지 말고 서로 어우러져 느껴지는 감각을 구체적으로 묘사. 종합 분석문과 반복하지 말 것},senseRoles:[{category:주어진 카테고리명,role:해당 선택이 전체 미감에서 맡는 역할 30자 이내}] 11개,connection:{title:연결고리를 표현하는 제목,text:서로 다른 선택 3개 이상을 연결한 한국어 설명 100자 내외},paletteExplanation:주어진 팔레트와 빛 날씨 계절 선택의 관계를 설명한 60자 내외 문장,queries:[{referenceId:제공된 referenceCandidates의 id 또는 null,title:한국어 탐색 제목,query:영어 Pinterest 검색어,reason:실제 선택과 해당 사진의 연결을 설명한 70자 이내 문장}] 6개,discoveries:[{id:주어진 추천 후보 id,reason:실제 선택에서 해당 미감으로 연결한 근거 55자 이내}]}. queries는 분위기,공간,풍경,디테일,빛,감각 관련 시각 레퍼런스처럼 서로 다른 관점으로 작성. referenceCandidates는 선택한 감각과 일치하는 결과 DB 후보입니다. imageType=generated는 실제 Pinterest 사진이 아닌 감각 예시 이미지입니다. 제목과 query는 고정 DB를 그대로 쓰고 referenceId로만 연결하세요. imageType=pinterest는 확인된 핀 사진의 제목과 검색어입니다. 사진을 직접 보고 있다고 주장하지 마세요. 사진을 먼저 고른 뒤 제목과 검색어는 해당 후보와 정확히 동일하게 사용하세요. 사진에 없는 계절 날씨 시간 바다 등은 묘사하지 마세요. reason은 사용자 실제 선택과 사진의 확인된 특징 사이 연결만 설명하세요. 소리와 향은 선택된 감각으로만 설명하세요. 음악, 장르, 곡, 가수, 플레이리스트를 새로 제안하거나 해석에 넣지 마세요. 사진을 연결할 근거가 없으면 referenceId:null로 검색 주제만 제안하세요. id를 새로 만들지 말고 같은 핀을 중복 사용하지 마세요. URL을 생성하지 마세요. 추천은 가능성으로 표현하고 사용자 피드백은 추천에만 반영하세요. 핵심 점수와 팔레트는 변경 금지. JSON만 반환. 데이터:'+JSON.stringify({items:items.map(({category,name})=>({category,name})),scores,palette,referenceCandidates:referenceCandidates(items).map(({id,title,query,description,imageType,options})=>({id,title,query,description,imageType,matchedChoices:items.filter(o=>options.includes(o.id)).map(o=>o.name)})),recommendations:recommendations.map(({id,name,tags})=>({id,name,tags})),preferences});
 const configured=(env.GEMINI_MODEL||'').trim().replace('models/','');
 if(configured&&!/^[a-zA-Z0-9.-]+$/.test(configured))return reply({error:'GEMINI_MODEL 형식이 올바르지 않아요. 모델 ID만 입력해주세요.',code:'MODEL_CONFIG_INVALID'},503);
 let model=configured||'gemini-3.8-flash',res,upstreamError;
 const apiKey=String(env.GEMINI_API_KEY).trim();
 if(!apiKey)return reply({error:'Cloudflare 프로덕션의 GEMINI_API_KEY 값을 확인해주세요.',code:'API_KEY_MISSING'},503);
 const callModel=async(name,withThinking=false)=>{
  const generationConfig={responseMimeType:'application/json',temperature:.75,maxOutputTokens:6000};
  if(withThinking)generationConfig.thinkingConfig={thinkingLevel:'low'};
  const response=await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+name+':generateContent',{method:'POST',headers:{'content-type':'application/json','x-goog-api-key':apiKey},body:JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig}),signal:AbortSignal.timeout(25000)});
  let error={};if(!response.ok){try{error=(await response.json()).error||{}}catch{}}
  return {response,error};
 };
 let attempt=await callModel(model);
 // Only recover model availability or unsupported thinking parameters, never authentication/quota.
 if(attempt.response.status===404){model=model==='gemini-3.6-flash'?'gemini-3.8-flash':'gemini-3.6-flash';attempt=await callModel(model);}
 if(attempt.response.status===400&&/thinking|thinkingLevel|thinking_level/i.test(String(attempt.error.message||'')))attempt=await callModel(model,false);
 res=attempt.response;upstreamError=attempt.error;
 if(!res.ok){
  const status=res.status,message=String(upstreamError.message||''),reasons=(Array.isArray(upstreamError.details)?upstreamError.details:[]).map(d=>d?.reason||'').join(' ');
  let code='GEMINI_UPSTREAM_ERROR',error='Gemini 서버에서 분석 요청을 처리하지 못했어요. 잠시 뒤 다시 시도해주세요.';
  if(/User location is not supported/i.test(message)){code='GEMINI_LOCATION_UNSUPPORTED';error='AI 서버의 지역을 Google이 지원하지 않는 것으로 판단했어요. 기본 결과는 사용할 수 있으며, 운영자의 서버 지역 확인이 필요합니다.';}
  else if(/leaked|API key (?:was |is )?(?:reported as )?blocked/i.test(message)){code='API_KEY_BLOCKED';error='Gemini API 키가 유출 또는 차단된 키로 감지됐어요. AI Studio에서 새 키를 발급해 Cloudflare 비밀값을 교체해주세요.';}
  else if(/API_KEY_INVALID|API_KEY_EXPIRED/.test(reasons)||status===401||/API key not valid|invalid api key/i.test(message)){code='API_KEY_INVALID';error='Gemini API 키가 유효하지 않아요. Cloudflare 프로덕션 비밀값을 확인해주세요.';}
  else if(/BILLING|billing|payment|credit/i.test(reasons+' '+message)||status===402){code='BILLING_REQUIRED';error='Gemini 프로젝트의 결제 또는 크레딧 상태를 AI Studio에서 확인해주세요.';}
  else if(status===403){code='GEMINI_PERMISSION_DENIED';error='Gemini 접근 권한이 거부됐어요. API 키의 API 제한·웹사이트 제한과 프로젝트 이용 권한을 확인해주세요. 이 서비스는 브라우저가 아닌 Worker 서버에서 Gemini를 호출합니다.';}
  else if(status===404){code='MODEL_NOT_FOUND';error='이 프로젝트에서 사용할 Gemini 모델을 찾지 못했어요. AI Studio에서 사용 가능한 모델 ID를 GEMINI_MODEL에 설정해주세요.';}
  else if(status===429){code='GEMINI_RATE_LIMIT';error='Gemini 사용량 한도에 도달했어요. 잠시 기다리거나 AI Studio에서 프로젝트 한도를 확인해주세요.';}
  else if(status===400){code='GEMINI_INVALID_REQUEST';const safe=message.split(apiKey).join('[redacted]').replace(/(?:AIza|AQ[.])[A-Za-z0-9_.-]{12,}/g,'[redacted]').replace(/https?:[^ ]+/g,'[url]').slice(0,240);error='Gemini 요청 설정 오류: '+(safe||'모델과 API 설정을 확인해주세요.');}
  const upstreamStatus=typeof upstreamError.status==='string'&&/^[A-Z_]+$/.test(upstreamError.status)?upstreamError.status:null;
  console.error(JSON.stringify({event:'gemini_analysis_failed',code,upstreamStatus,upstreamHttpStatus:status,model}));
  return reply({error,code,upstreamStatus,upstreamHttpStatus:status,model},status===429?429:502);
 }
 const rawResult=await res.json();const txt=rawResult.candidates?.[0]?.content?.parts?.filter(p=>p.text&&!p.thought).map(p=>p.text).join('');const data=JSON.parse(txt);
 if(!validInterpretation(data))throw Error();
 if(typeof data.name!=='string'||typeof data.english!=='string'||typeof data.description!=='string'||!Array.isArray(data.keywords)||!Array.isArray(data.queries))throw Error();
 const sensorySynthesis=data.sensorySynthesis&&typeof data.sensorySynthesis.title==='string'&&typeof data.sensorySynthesis.text==='string'?{title:data.sensorySynthesis.title.slice(0,150),text:data.sensorySynthesis.text.slice(0,1200)}:undefined;
 const senseRoles=Array.isArray(data.senseRoles)?data.senseRoles.filter(x=>x&&DB.some(d=>d.label===x.category)&&typeof x.role==='string').slice(0,12).map(x=>({category:x.category,role:x.role.slice(0,200)})):[];
 const connection=data.connection&&typeof data.connection.title==='string'&&typeof data.connection.text==='string'?{title:data.connection.title.slice(0,150),text:data.connection.text.slice(0,1200)}:undefined;
 const discoveries=Array.isArray(data.discoveries)?data.discoveries.filter(x=>x&&recommendations.some(d=>d.id===x.id)&&typeof x.reason==='string').map(x=>({id:x.id,reason:x.reason.slice(0,400)})).slice(0,3):[];
 const result={name:data.name.slice(0,70),english:data.english.slice(0,100),description:data.description.slice(0,1500),keywords:data.keywords.filter(x=>typeof x==='string').slice(0,6),queries:normalizeExplorations(data.queries,items),sensorySynthesis,senseRoles,connection,discoveries,paletteExplanation:typeof data.paletteExplanation==='string'?data.paletteExplanation.slice(0,600):undefined};if(analysisCache.size>=100)analysisCache.delete(analysisCache.keys().next().value);analysisCache.set(cacheKey,{time:Date.now(),result});return reply(result);
 }finally{activeAnalyses--}
 }catch(err){const timeout=err?.name==='TimeoutError'||err?.name==='AbortError';const code=timeout?'GEMINI_TIMEOUT':err instanceof SyntaxError?'GEMINI_INVALID_RESPONSE':'GEMINI_ANALYSIS_FAILED';console.error(JSON.stringify({event:'gemini_analysis_failed',code}));return reply({error:timeout?'Gemini 응답 시간이 초과됐어요. 기본 결과는 그대로 볼 수 있어요.':code==='GEMINI_INVALID_RESPONSE'?'Gemini 응답 형식을 읽지 못했어요. 다시 시도해주세요.':'AI 분석을 완료하지 못했어요. 기본 결과는 유지됩니다. 다시 시도해주세요.',code},503)}
}
if(url.pathname!=='/')return new Response('Not found',{status:404});return new Response(PAGE,{headers:{'content-type':'text/html; charset=utf-8','cache-control':'no-store, no-cache, max-age=0, must-revalidate','cloudflare-cdn-cache-control':'no-store','cdn-cache-control':'no-store','pragma':'no-cache','expires':'0','x-content-type-options':'nosniff'}});
}};

export class MoodidCounter {
 constructor(ctx){this.ctx=ctx;this.sql=ctx.storage.sql;this.sql.exec('CREATE TABLE IF NOT EXISTS completed (id TEXT PRIMARY KEY)');this.sql.exec('CREATE TABLE IF NOT EXISTS totals (id INTEGER PRIMARY KEY, count INTEGER NOT NULL)');this.sql.exec('INSERT OR IGNORE INTO totals (id,count) VALUES (1,0)');}
 async fetch(req){
  if(req.method==='POST'){
   const {hash}=await req.json();if(!/^[a-f0-9]{64}$/.test(hash||''))return Response.json({error:'Invalid id'},{status:400});
   this.ctx.storage.transactionSync(()=>{const added=this.sql.exec('INSERT OR IGNORE INTO completed (id) VALUES (?) RETURNING id',hash).toArray();if(added.length)this.sql.exec('UPDATE totals SET count=count+1 WHERE id=1');});
  }
  const count=this.sql.exec('SELECT count FROM totals WHERE id=1').one().count;
  return Response.json({available:true,count,unit:'unique_browser',since:'deployment'},{headers:{'cache-control':'no-store'}});
 }
}

'''
assets={f.name:base64.b64encode(f.read_bytes()).decode() for f in (p/'assets/options').glob('*.webp')}
(p/'worker/index.js').write_text('const ASSETS='+json.dumps(assets)+';\n'+'const RESULT_REFERENCES='+json.dumps(json.loads((p/'result-reference-db.json').read_text())['references'],ensure_ascii=False)+';\n'+'const DB='+ (p/'database.json').read_text()+';\nconst PIN_CATALOG='+(p/'pinterest-catalog.json').read_text()+';\nconst DISCOVERIES='+(p/'discoveries.json').read_text()+';\n'+(p/'aesthetic-engine.js').read_text()+'\n'+(p/'image-search-worker.js').read_text()+'\nconst PAGE='+json.dumps(page,ensure_ascii=False)+';\n'+server)
