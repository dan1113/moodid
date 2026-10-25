import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import worker from '../worker/index.js';
const db=JSON.parse(await readFile(new URL('../database.json',import.meta.url)));
const answers=Object.fromEntries(db.map((d,i)=>[i,[d.options[0].id]]));
let seq=0;
const req=()=>new Request('https://moodid.test/api/analyze',{method:'POST',headers:{'cf-connecting-ip':'diagnostic-'+seq++},body:JSON.stringify({answers,refresh:true})});
const original=globalThis.fetch;
const ok=()=>Response.json({candidates:[{content:{parts:[{text:JSON.stringify({name:'TEST',english:'TEST',description:'설명',keywords:[],queries:[]})}]}}]});
try{
 for(const [status,message,code] of [[400,'API key not valid','API_KEY_INVALID'],[403,'Your API key was reported as leaked. secret-test','API_KEY_BLOCKED'],[403,'Requests from referer are blocked','GEMINI_PERMISSION_DENIED'],[429,'Quota exceeded','GEMINI_RATE_LIMIT'],[402,'payment required','BILLING_REQUIRED']]){
  let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({error:{message,status:'DENIED'}},{status})};
  const r=await worker.fetch(req(),{GEMINI_API_KEY:'secret-test'}),v=await r.json();assert.equal(v.code,code);assert.equal(calls,1);assert.equal(JSON.stringify(v).includes('secret-test'),false);
 }
 let calls=[];globalThis.fetch=async(u,o)=>{calls.push(u);return calls.length===1?Response.json({error:{message:'model not found'}},{status:404}):ok()};
 assert.equal((await worker.fetch(req(),{GEMINI_API_KEY:'test'})).status,200);assert.equal(calls.length,2);assert.ok(calls[1].includes('gemini-3.6-flash'));
 calls=[];globalThis.fetch=async(u,o)=>{calls.push(JSON.parse(o.body));return calls.length===1?Response.json({error:{message:'thinkingLevel not supported'}},{status:400}):ok()};
 assert.equal((await worker.fetch(req(),{GEMINI_API_KEY:'test'})).status,200);assert.equal(calls.length,2);assert.equal(calls[1].generationConfig.thinkingConfig,undefined);
 globalThis.fetch=async()=>{throw Object.assign(Error(),{name:'TimeoutError'})};assert.equal((await (await worker.fetch(req(),{GEMINI_API_KEY:'test'})).json()).code,'GEMINI_TIMEOUT');
 console.log('Gemini error classification, secret redaction, no auth/quota retries, model fallback, thinking compatibility and timeout handling passed.');
}finally{globalThis.fetch=original}
