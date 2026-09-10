import {spawnSync} from 'node:child_process';
import {cp,mkdir,readFile,writeFile,stat} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const basePath='/kurzuskaosz-horgaszat';
const env={...process.env,GITHUB_PAGES_BUILD:'1',NEXT_PUBLIC_BASE_PATH:basePath};
function run(args){const result=spawnSync(process.execPath,args,{cwd:root,env,stdio:'inherit'});if(result.status!==0)process.exit(result.status||1);}
run(['scripts/assets.mjs','--verify']);
run(['node_modules/vinext/dist/cli.js','build']);
const source=resolve(root,'dist/client'),destination=resolve(root,'dist/pages');
await mkdir(destination,{recursive:true});
await cp(source,destination,{recursive:true});
await mkdir(resolve(destination,'modell'),{recursive:true});
await cp(resolve(source,'modell.html'),resolve(destination,'modell/index.html'));
// Vinext prefixes the physical static-asset directory; Pages already mounts
// the artifact at the project base path, so stage that directory at its root.
try{if((await stat(resolve(source,basePath.slice(1)))).isDirectory())await cp(resolve(source,basePath.slice(1)),destination,{recursive:true});}catch{}
await writeFile(resolve(destination,'.nojekyll'),'');
for(const route of ['index.html','modell/index.html']){
 const html=await readFile(resolve(destination,route),'utf8');
 if(!html.includes('KurzusKáosz'))throw Error(`Missing rendered content: ${route}`);
 if(/(?:src|href)="\/(?:_next|models|images|draco)\//.test(html))throw Error(`Unprefixed URL in ${route}`);
}
console.log('GitHub Pages artifact ready: dist/pages');

run(['scripts/check-pages.mjs']);
