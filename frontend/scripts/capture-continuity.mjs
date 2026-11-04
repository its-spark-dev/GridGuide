// Authentic matched viewport comparison. Start each named build separately.
// Original API must be from the detached v1.0.0 checkout, with authorized sources.
import { chromium } from 'playwright';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
const { ORIGINAL_ORIGIN, ORIGINAL_API, BEFORE_ORIGIN, AFTER_ORIGIN, CAPTURE_DIR }=process.env;
if(!ORIGINAL_ORIGIN||!ORIGINAL_API||!BEFORE_ORIGIN||!AFTER_ORIGIN||!CAPTURE_DIR)throw new Error('All three explicit origins, original API and output directory required');
const dir=resolve(CAPTURE_DIR);await mkdir(dir,{recursive:true});
const browser=await chromium.launch({channel:'chrome'});
const records=[];
try {
 for(const [name,base] of [['v1',ORIGINAL_ORIGIN],['before',BEFORE_ORIGIN],['after',AFTER_ORIGIN]]){
  for(const [size,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
   const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce'});
   // Keep captures independent of third-party maps/providers.
   await page.route('**/*',route=>new URL(route.request().url()).origin===base?route.continue():route.abort());
   if(name==='v1')await page.route('**/api/**',async route=>{const u=new URL(route.request().url());await route.fulfill({response:await route.fetch({url:ORIGINAL_API+u.pathname+u.search})});});
   const capture=async(label)=>{
    await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>window.scrollTo(0,0));
    const file=`${name}${label?'-'+label:''}-${size}.png`;await page.screenshot({path:resolve(dir,file)});
    records.push({file,width,height,url:page.url(),sha256:createHash('sha256').update(await readFile(resolve(dir,file))).digest('hex')});
   };
   await page.goto(base);
   if(name==='v1')await page.getByTestId('risk-band').filter({hasText:'HIGH'}).waitFor();
   else if(name==='after')await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-simple');
   else await page.getByRole('button',{name:'Save this demo snapshot'}).isEnabled();
   await capture('');
   if(name==='v1'){
    await page.getByRole('navigation').getByRole('link',{name:'Prepare & alerts',exact:true}).click();
    await page.getByRole('heading',{name:'Prepare & stay informed'}).waitFor();await capture('preparedness');
    await page.getByRole('navigation').getByRole('link',{name:'Grid insights',exact:true}).click();
    await page.getByRole('heading',{name:'Same repairs. Different priorities.'}).waitFor();await capture('operator');
   }else{
    for(const [entry,path] of [['preparedness','/preparedness/'],['operator','/operator/']]){
     await page.goto(base+path);
     if(entry==='operator')await page.getByRole('heading',{name:'2. Compare identical assumptions'}).waitFor();
     else await page.getByRole('combobox',{name:'Fictional scenario',exact:true}).selectOption('syn-simple');
     await capture(entry);
    }
   }
   await page.close();
  }
 }
 await writeFile(resolve(dir,'capture.json'),JSON.stringify({captured_at:new Date().toISOString(),browser:await browser.version(),original_commit:'b324c1b355cda60035fb11fa32bcddf10931f649',before_commit:'ae6d9c482c4e55d5db483338bad34d1415b99ec5',after:'Corrective branch; see package manifest and PR head',records},null,2)+'\n');
} finally {await browser.close();}
