import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import worker from '../worker/index.js';
const db=JSON.parse(fs.readFileSync(new URL('../database.json',import.meta.url),'utf8'));
const ids=db.flatMap(d=>d.options.map(o=>o.id));
assert.equal(ids.length,88);
for(const id of ids){
 const path=new URL('../assets/options/'+id+'.webp',import.meta.url);
 assert.ok(fs.existsSync(path),'Missing image '+id);
 const res=await worker.fetch(new Request('https://moodid.test/assets/options/'+id+'.webp'),{});
 assert.equal(res.status,200);assert.equal(res.headers.get('content-type'),'image/webp');
 const bytes=Buffer.from(await res.arrayBuffer());assert.ok(bytes.equals(fs.readFileSync(path)));
}
const html=await (await worker.fetch(new Request('https://moodid.test/'),{})).text();
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
new vm.Script(script);
assert.ok(html.includes('/assets/options/${o.id}.webp'));
console.log('All 88 unique option assets are present, served correctly, and wired to the questionnaire. Client syntax passed.');
