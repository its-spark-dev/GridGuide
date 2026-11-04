// Decode/seek the actual WebM and load its real captions in Chromium.
import {chromium,expect} from '@playwright/test';
import {serveMedia} from './serve-release-media.mjs';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(process.env.GG_RECORD_DIR??'../docs/media/v1.1.0-integrated');
const shots=JSON.parse(await readFile(join(root,'shots.json')));
expect(shots.application_commit).toBe('3c53d8e9429318f121c210d148f7d2b35ae52147');
const pkg=JSON.parse(await readFile(join(root,'package.json')));
expect(createHash('sha256').update(JSON.stringify(pkg.manifest,null,2)+'\n').digest('hex')).toBe(shots.package_manifest_sha256);
expect(createHash('sha256').update(await readFile(new URL('./record-release.mjs',import.meta.url))).digest('hex')).toBe(shots.capture_script_sha256);
for(const name of [...shots.shots.map(s=>s.name),'mobile-overview','mobile-preparedness','mobile-operator']){
 const png=await readFile(join(root,name+'.png'));expect(png.subarray(0,8).toString('hex')).toBe('89504e470d0a1a0a');
 expect([png.readUInt32BE(16),png.readUInt32BE(20)]).toEqual(name.startsWith('mobile-')?[390,844]:[1280,800]);
}
const server=await serveMedia(root);let browser;
try {
 await expect.poll(async()=>{try{return(await fetch('http://127.0.0.1:18192/player.html')).status;}catch{return 0;}}).toBe(200);
 browser=await chromium.launch({channel:process.env.CI?undefined:'chrome'});const page=await browser.newPage({viewport:{width:1280,height:900}});
 await page.goto('http://127.0.0.1:18192/player.html');
 await page.locator('video').evaluate(v=>{v.muted=true;});
 await expect.poll(()=>page.locator('video').evaluate(v=>Number.isFinite(v.duration)?v.duration:0)).toBeGreaterThan(240);
 await expect.poll(()=>page.locator('track').evaluate(t=>t.readyState)).toBe(2);
 const metadata=await page.locator('video').evaluate(v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight}));
 expect(metadata.width).toBe(1280);expect(metadata.height).toBe(800);expect(metadata.duration).toBeLessThan(330);
 await page.locator('video').evaluate(async v=>{v.textTracks[0].mode='showing';await v.play();});await page.waitForTimeout(1000);
 expect(await page.locator('video').evaluate(v=>v.currentTime)).toBeGreaterThan(0);
 await page.locator('video').evaluate(v=>v.pause());
 const cueResults=[];
 for(const s of shots.shots){
  expect(s.end).toBeGreaterThan(s.start);expect(s.end).toBeLessThanOrEqual(metadata.duration+1);
  await page.locator('video').evaluate((v,t)=>new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=t;}),s.start+1);
  await expect.poll(()=>page.locator('video').evaluate(v=>v.textTracks[0].activeCues?.[0]?.text??'')).toBe(s.caption);
  expect(await page.locator('video').evaluate(v=>v.error)).toBeNull();cueResults.push({scene:s.name,caption_matches:true,seek_decodes:true});
  if(process.env.GG_VERIFY_SHOTS&&['01-overview','09-offline','15-replay'].includes(s.name))await page.screenshot({path:join(process.env.GG_VERIFY_SHOTS,s.name+'.png')});
 }
 const provenancePath=join(root,'provenance.json');
 try {const p=JSON.parse(await readFile(provenancePath));for(const [file,pin] of Object.entries(p.files_sha256))expect(createHash('sha256').update(await readFile(join(root,file))).digest('hex')).toBe(pin);}catch(e){if(e.code!=='ENOENT')throw e;}
 const result={status:'PASS',...metadata,scene_count:shots.shots.length,actual_playback:true,caption_checks:cueResults,browser:await browser.version(),scope:'Chromium decode, playback, seek and cue alignment; no manual accessibility claim'};
 if(process.env.GG_VERIFY_REPORT)await writeFile(process.env.GG_VERIFY_REPORT,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{if(browser)await browser.close();server.closeAllConnections();await new Promise(r=>server.close(r));}
