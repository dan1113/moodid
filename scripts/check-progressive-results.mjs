import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import worker from '../worker/index.js';
const html=await(await worker.fetch(new Request('https://moodid.test/'),{})).text(),script=html.match(/<script>([\s\S]*)<\/script>/)[1];
const element={innerHTML:'',style:{}};const storage=new Map();let finish,calls=0;
const ctx=vm.createContext({document:{querySelector:()=>element},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},window:{scrollTo(){}},setTimeout,clearTimeout,AbortController,AbortSignal,console,fetch:()=>{calls++;return new Promise(resolve=>finish=resolve)}});
vm.runInContext(script,ctx);vm.runInContext(`let rendered=[],patched=0;result=()=>rendered.push({pending:current.pending,dna:itemsFor(current.answers).length,palette:current.palette.length});refreshInterpretation=()=>patched++;DB.forEach((d,i)=>answers[i]=[d.options[0].id]);let request=analyze();`,ctx);
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(rendered)',ctx)),[{pending:true,dna:11,palette:5}]);assert.equal(calls,1);
finish(Response.json({name:'완성',english:'COMPLETE',description:'분석',keywords:[],queries:[]}));await vm.runInContext('request',ctx);assert.equal(vm.runInContext('current.ai',ctx),true);assert.equal(vm.runInContext('patched',ctx),1);
await vm.runInContext('analyze()',ctx);assert.equal(calls,1,'Identical answers should reuse browser cache');assert.equal(vm.runInContext('current.pending',ctx),false);
console.log('Results render before the network resolves; AI updates in place; identical answers use cache.');
