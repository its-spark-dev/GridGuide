import {chromium,expect} from '../../../frontend/node_modules/@playwright/test/index.mjs';
import {spawn} from 'node:child_process';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const out=new URL('.',import.meta.url).pathname;
const pkg=process.env.GRIDGUIDE_PACKAGE;
const python=process.env.GRIDGUIDE_PUBLIC_PYTHON;
if(!pkg||!python)throw Error('Explicit inspected package and pinned Python environment required');
const expected=JSON.parse(await readFile(new URL('../v1.1.0-integrated/package.json',import.meta.url)));
const manifest=JSON.parse(await readFile(pkg+'/PUBLIC_MANIFEST.json'));
expect(manifest).toEqual(expected.manifest);
const server=spawn(python,['-m','uvicorn','backend.public_app:create_public_app','--factory','--host','127.0.0.1','--port','18194','--no-access-log'],{cwd:pkg,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},stdio:'ignore'});
let browser;
try {
 await expect.poll(async()=>{try{return(await fetch('http://127.0.0.1:18194/ready')).status;}catch{return 0;}},{timeout:20000}).toBe(200);
 browser=await chromium.launch({channel:'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1420},deviceScaleFactor:1,reducedMotion:'reduce'});
 await page.route('**/*',r=>r.request().url().startsWith('http://127.0.0.1:18194/')?r.continue():r.abort());
 await page.goto('http://127.0.0.1:18194/preparedness/');
 await expect(page.getByRole('combobox',{name:'Fictional scenario',exact:true})).toBeEnabled();
 await page.evaluate(()=>document.fonts.ready);
 await expect(page.getByRole('heading',{name:'Your generic preparedness kit',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Download generic kit',exact:true})).toBeInViewport();
 await page.screenshot({path:out+'/preparedness-desktop.png'});
 const image=await readFile(out+'/preparedness-desktop.png');
 await writeFile(out+'/capture.json',JSON.stringify({application_commit:'3c53d8e9429318f121c210d148f7d2b35ae52147',documentation_base:'6e50896c455f1d74663be2d7c5ed606be77d7834',package_sha256:'dbf1c3251fd5e297f223b424898f35f18ac27cbb182b24dd1656486cffc32ebf',captured_at:new Date().toISOString(),browser:await browser.version(),viewport:{width:1440,height:1420},device_scale_factor:1,reduced_motion:'reduce',route:'/preparedness/',state:'Fresh online page, default fictional scenario; no snapshot saved and offline kit not installed',runtime:'Pinned deploy/requirements.lock; uvicorn factory on loopback',external_requests:'blocked; same-origin real responses only',editing:'None: native viewport screenshot; no DOM, response or data modifications',sha256:createHash('sha256').update(image).digest('hex')},null,2)+'\n');
 console.log('Authentic preparedness screenshot captured');
}finally{await browser?.close();server.kill('SIGTERM');}
