import {readFile,stat,readdir} from 'node:fs/promises';
import {resolve} from 'node:path';
const directory=resolve('dist/pages'),prefix='/kurzuskaosz-horgaszat';
let checked=0;
async function check(url){if(!url.startsWith(prefix+'/'))return;const path=decodeURIComponent(url.slice(prefix.length+1).split(/[?#]/)[0]);const target=resolve(directory,path);if(!target.startsWith(directory))throw Error('Escaping asset URL');if(!(await stat(target)).isFile())throw Error(`Missing asset: ${url}`);checked++;}
for(const page of ['index.html','modell/index.html']){
 const html=await readFile(resolve(directory,page),'utf8');
 if(html.includes('id="__next_error__"'))throw Error(`Render failed: ${page}`);
 for(const match of html.matchAll(/(?:src|href)="([^"]+)"/g)){if(match[1].endsWith('/'))continue;await check(match[1]);}
}
const cssPath=resolve(directory,'_next/static/css');
for(const name of await readdir(cssPath)){if(!name.endsWith('.css'))continue;const css=await readFile(resolve(cssPath,name),'utf8');for(const match of css.matchAll(/url\(["']?([^\s)'";]+)["']?\)/g))await check(match[1]);}
const manifest=JSON.parse(await readFile('generated-assets.json','utf8'));
for(const file of manifest.files){if((await stat(resolve(directory,file.path.slice(7)))).size!==file.bytes)throw Error(`Wrong asset size: ${file.path}`);}
console.log(`Pages check passed: 2 rendered routes, ${checked} linked assets, ${manifest.files.length} model/download assets.`);
