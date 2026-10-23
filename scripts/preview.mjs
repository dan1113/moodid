import http from 'node:http';
import { readFile } from 'node:fs/promises';
const port = Number(process.env.PORT || 4173);
http.createServer(async (req, res) => {
 try {
  const url = new URL(req.url, 'http://localhost:' + port);
  if (/^\/assets\/options\/\d+_\d+\.webp$/.test(url.pathname)) {
   const bytes = await readFile(new URL('../assets/options/' + url.pathname.split('/').pop(), import.meta.url));
   res.writeHead(200, {'content-type':'image/webp'}); return res.end(bytes);
  }
  if (url.pathname !== '/') {res.writeHead(404); return res.end('Not found');}
  const [html, db] = await Promise.all([readFile(new URL('../page.html',import.meta.url),'utf8'),readFile(new URL('../database.json',import.meta.url),'utf8')]);
  res.writeHead(200, {'content-type':'text/html; charset=utf-8'}); res.end(html.replace('__DB__',db).replace('__PINS__',await readFile(new URL('../pinterest-catalog.json',import.meta.url),'utf8')).replace('__DISCOVERIES__',await readFile(new URL('../discoveries.json',import.meta.url),'utf8')).replace('__ENGINE__',await readFile(new URL('../aesthetic-engine.js',import.meta.url),'utf8')));
 } catch {res.writeHead(404);res.end('Not found');}
}).listen(port,'0.0.0.0',()=>console.log('MOODID preview on '+port));
