// Cloudflare Worker: semantic searches per palette color; credentials remain server-side.
const imageSearchWindows=new Map();
const imageJson=(data,status=200)=>Response.json(data,{status,headers:{'cache-control':'no-store'}});
const imageColorNames=[['#243b55','deep navy blue'],['#657b91','slate blue'],['#a9bfca','pale blue gray'],['#9c252c','deep warm red'],['#c75942','terracotta red'],['#c58d62','warm amber'],['#ddb766','golden beige'],['#e8dccb','warm ivory'],['#b5ac96','muted stone beige'],['#6c7150','muted olive green'],['#486345','forest green'],['#b4c3ac','sage green'],['#9c8ead','dusty lavender'],['#292d2c','charcoal'],['#eeeeea','soft white']];
function colorRgb(c){return c.slice(1).match(/../g).map(x=>parseInt(x,16));}
function imageColorName(c){const rgb=colorRgb(c);return [...imageColorNames].sort((a,b)=>{const dist=x=>colorRgb(x[0]).reduce((s,v,i)=>s+(v-rgb[i])**2,0);return dist(a)-dist(b)})[0][1];}
function imageSearchPlan(items,palette){
 const picks=c=>items.filter(o=>o.category===c),pick=c=>picks(c)[0];
 return palette.slice(0,3).map((targetColor,index)=>{const [r,g,b]=colorRgb(targetColor),warm=r>b*1.12&&r>g*1.04,cool=b>r*1.08;let role,focus,secondary;
 if(cool){role='날씨와 공기';focus=pick('날씨');secondary=pick('장소');}
 else if(warm){role='빛과 온기';focus=pick('빛');secondary=pick('질감');}
 else if(g>r*1.02||g>b*1.1){role='공간과 자연';focus=pick('장소');secondary=pick('공간');}
 else{role=index===1?'빛과 온기':'소재와 공간';focus=pick(index===1?'빛':'질감');secondary=pick(index===1?'공간':'장소');}
 const color=imageColorName(targetColor),tone=pick('색조');
 // Each photo has one visual role, rather than forcing every chosen sense into one query.
 const terms=[color,focus?.en,secondary?.en,tone?.en,'editorial photography'];
 return {targetColor,role,choices:[focus?.name,secondary?.name].filter(Boolean),query:[...new Set(terms.filter(Boolean))].join(' ')};
 });
}
function publicImageUrl(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&u.hostname.includes('.')&&!/^(?:\d|\[)/.test(u.hostname)&&!/(?:^|\.)(?:localhost|local|internal|test|invalid|example|onion)$/.test(u.hostname)&&u.href.length<2200}catch{return false}}
async function imageSignature(value,key){const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);return [...new Uint8Array(await crypto.subtle.sign('HMAC',k,new TextEncoder().encode(value)))].map(v=>v.toString(16).padStart(2,'0')).join('');}
async function imageSearchRoute(req,env,url){
 const key=String(env.SERPAPI_API_KEY||'').trim();if(!key)return imageJson({code:'SEARCH_KEY_MISSING',error:'이미지 검색 연결을 준비 중이에요.'},503);
 if(url.pathname==='/api/reference-image'){
  if(req.method!=='GET')return imageJson({error:'Method not allowed'},405);
  const u=url.searchParams.get('url')||'',expiry=url.searchParams.get('expires')||'',sig=url.searchParams.get('sig')||'';
  if(!publicImageUrl(u)||!/^\d{13}$/.test(expiry)||Number(expiry)<Date.now()||Number(expiry)>Date.now()+90000000||sig!==await imageSignature(u+'|'+expiry,key))return imageJson({error:'Invalid image request'},403);
  try{const r=await fetch(u,{redirect:'manual',signal:AbortSignal.timeout(12000),headers:{Accept:'image/*'}});if(!r.ok||!/^image\/(jpeg|png|webp|avif)(?:;|$)/i.test(r.headers.get('content-type')||''))return imageJson({error:'Image unavailable'},502);if(Number(r.headers.get('content-length'))>7000000)return imageJson({error:'Image too large'},413);const bytes=await r.arrayBuffer();if(bytes.byteLength>7000000)return imageJson({error:'Image too large'},413);return new Response(bytes,{headers:{'content-type':r.headers.get('content-type'),'cache-control':'public,max-age=3600','x-content-type-options':'nosniff'}})}catch{return imageJson({error:'Image unavailable'},502)}
 }
 if(req.method!=='POST')return imageJson({error:'Method not allowed'},405);
 if(req.headers.get('origin')!==url.origin)return imageJson({error:'Forbidden'},403);
 try{
  const raw=await req.text();if(raw.length>7000)return imageJson({error:'Too large'},413);let body;try{body=JSON.parse(raw)}catch{return imageJson({error:'Invalid JSON'},400)}
  const items=[];for(let i=0;i<DB.length;i++){const ids=body.answers?.[i];if(!Array.isArray(ids)||ids.length<1||ids.length>3||new Set(ids).size!==ids.length)return imageJson({error:'모든 감각을 선택해주세요.'},400);for(const id of ids){const o=DB[i].options.find(o=>o.id===id);if(!o)return imageJson({error:'Invalid choice'},400);items.push({...o,category:DB[i].label});}}
  const palette=buildPalette(items).map(c=>c.hex),plan=imageSearchPlan(items,palette);
  const cacheId=await imageSignature(JSON.stringify(plan),key),cacheUrl=new Request(url.origin+'/__image-cache/'+cacheId),cached=await caches.default.match(cacheUrl);
  if(cached)return cached;
  const ip=req.headers.get('cf-connecting-ip')||'local',now=Date.now(),window=imageSearchWindows.get(ip);
  if(window&&now-window.time<60000&&window.count>=3)return imageJson({error:'이미지 검색 요청이 많아요. 1분 뒤 다시 시도해주세요.',code:'SEARCH_RATE_LIMIT'},429);
  if(imageSearchWindows.size>1000)imageSearchWindows.delete(imageSearchWindows.keys().next().value);
  imageSearchWindows.set(ip,window&&now-window.time<60000?{time:window.time,count:window.count+1}:{time:now,count:1});
  const groups=await Promise.all(plan.map(async slot=>{
   const endpoint=new URL('https://serpapi.com/search.json');Object.entries({engine:'google_images',q:slot.query+' -collage -palette -quote -wallpaper',api_key:key,safe:'active',hl:'en'}).forEach(([k,v])=>endpoint.searchParams.set(k,v));
   const r=await fetch(endpoint,{signal:AbortSignal.timeout(25000)});if(!r.ok)throw Object.assign(new Error('provider'),{providerStatus:r.status});const data=await r.json();if(data.error)throw new Error('provider');
   const seen=new Set(),candidates=[];const expires=String(Date.now()+86400000);
   for(const item of data.images_results||[]){const original=item.original,source=item.link,w=Number(item.original_width),h=Number(item.original_height);
    if(!publicImageUrl(original)||!publicImageUrl(source)||seen.has(original)||Math.min(w,h)<600||w/h<.65||w/h>1.9||/istock|shutterstock|dreamstime|alamy|gettyimages|depositphotos/i.test(original+' '+source)||/color palette|colour palette|wallpaper|quotes|collage/i.test(item.title||''))continue;
    seen.add(original);const sig=await imageSignature(original+'|'+expires,key);candidates.push({id:await imageSignature(original,key),image:'/api/reference-image?'+new URLSearchParams({url:original,expires,sig}),source,title:String(item.title||'Image reference').slice(0,180),width:w,height:h});if(candidates.length>=6)break;
   }
   return {...slot,candidates};
  }));
  const response=Response.json({groups,provider:'Google Images via SerpApi'},{headers:{'cache-control':'public,max-age=21600'}});await caches.default.put(cacheUrl,response.clone());return response;
 }catch(e){return imageJson({code:e.providerStatus===401?'SEARCH_AUTH_FAILED':'SEARCH_UNAVAILABLE',error:e.providerStatus===401?'이미지 검색 키를 확인해주세요.':'이미지 검색이 지연되고 있어요. 잠시 후 다시 시도해주세요.'},502)}
}
