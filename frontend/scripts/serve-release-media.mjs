// Loopback-only review player. Explicit three-file scope; never a product host.
import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
export async function serveMedia(root){
 const files=new Map();
 for(const [name,type] of [['player.html','text/html; charset=utf-8'],['captions.vtt','text/vtt; charset=utf-8'],['gridguide-1.1.0-integrated.webm','video/webm']])files.set('/'+name,{data:await readFile(join(root,name)),type});
 const server=createServer((req,res)=>{
  const file=files.get(req.url==='/'?'/player.html':req.url);
  if(!file||!['GET','HEAD'].includes(req.method)){res.writeHead(404);res.end();return;}
  const {data,type}=file;let start=0,end=data.length-1;
  if(req.headers.range){const match=/^bytes=(\d+)-(\d*)$/.exec(req.headers.range);if(!match){res.writeHead(416);res.end();return;}start=Number(match[1]);end=match[2]?Math.min(Number(match[2]),end):end;if(start>end){res.writeHead(416,{'Content-Range':`bytes */${data.length}`});res.end();return;}}
  const headers={'Content-Type':type,'Content-Length':end-start+1,'Accept-Ranges':'bytes','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
  if(req.headers.range)headers['Content-Range']=`bytes ${start}-${end}/${data.length}`;
  res.writeHead(req.headers.range?206:200,headers);res.end(req.method==='HEAD'?undefined:data.subarray(start,end+1));
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(18192,'127.0.0.1',resolve);});return server;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){if(!process.env.GG_RECORD_DIR)throw Error('GG_RECORD_DIR required');await serveMedia(resolve(process.env.GG_RECORD_DIR));console.log('Local captioned player: http://127.0.0.1:18192/');}
