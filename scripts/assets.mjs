import {readFile,writeFile,mkdir,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const manifest=JSON.parse(await readFile(resolve(root,'generated-assets.json'),'utf8'));
const verify=process.argv.includes('--verify');
for(const asset of manifest.files){
 if(!/^public\/(models|images|downloads)\/[\w.-]+$/.test(asset.path))throw Error('Invalid generated asset path');
 const destination=resolve(root,asset.path);let valid=false;
 try{if((await stat(destination)).size===asset.bytes)valid=createHash('sha256').update(await readFile(destination)).digest('hex')===asset.sha256;}catch{}
 if(valid)continue;
 if(verify)throw Error(`Missing or changed build asset: ${asset.path}. Run pnpm assets first.`);
 const filename=asset.path.split('/').at(-1);
 const response=await fetch(`https://github.com/MKristof64/kurzuskaosz-horgaszat/releases/download/model-v1/${filename}`);
 if(!response.ok)throw Error(`Download failed (${response.status}): ${filename}`);
 const data=Buffer.from(await response.arrayBuffer());
 if(data.length!==asset.bytes||createHash('sha256').update(data).digest('hex')!==asset.sha256)throw Error(`Integrity check failed: ${filename}`);
 await mkdir(dirname(destination),{recursive:true});await writeFile(destination,data);console.log(`Ready: ${filename}`);
}
console.log(`Verified ${manifest.files.length} generated assets.`);
