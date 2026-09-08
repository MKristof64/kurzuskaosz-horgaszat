import * as T from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
import {DRACOLoader} from 'three/examples/jsm/loaders/DRACOLoader.js';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';

export const ease=(a:number,b:number,x:number)=>{const t=T.MathUtils.clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};
export function createFishingScene(host:HTMLElement,onLoad:(percent:number)=>void,onError:()=>void){
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const renderer=new T.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'});
 renderer.setPixelRatio(Math.min(devicePixelRatio,1.4));renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;renderer.setClearColor(0xece9d7,0);
 host.appendChild(renderer.domElement);renderer.domElement.setAttribute('aria-label','3D horgászat és térbeli Ishikawa-diagram');renderer.domElement.tabIndex=-1;
 const scene=new T.Scene();scene.fog=new T.FogExp2(0xdce4cd,.024);
 const camera=new T.PerspectiveCamera(38,1,.05,150);camera.position.set(0,2,10);
 const controls=new OrbitControls(camera,renderer.domElement);controls.enabled=false;controls.enableDamping=true;controls.minDistance=4;controls.maxDistance=24;controls.maxPolarAngle=Math.PI*.8;
 const pmrem=new T.PMREMGenerator(renderer),room=new RoomEnvironment(),env=pmrem.fromScene(room,.04);scene.environment=env.texture;scene.environmentIntensity=.55;room.dispose();
 scene.add(new T.HemisphereLight(0xfff2ce,0x35564e,2.4));
 const sun=new T.DirectionalLight(0xffe6ba,3.2);sun.position.set(-5,8,6);scene.add(sun);
 const rim=new T.DirectionalLight(0xe0f3e7,2.3);rim.position.set(4,4,-3);scene.add(rim);
 const fill=new T.DirectionalLight(0xfff6de,1.2);fill.position.set(0,-2,5);scene.add(fill);
 const nature=new T.Group();scene.add(nature);
 const mat=(color:T.ColorRepresentation,roughness=.7)=>new T.MeshStandardMaterial({color,roughness});
 const add=(geometry:T.BufferGeometry,material:T.Material,parent:T.Object3D=nature)=>{const m=new T.Mesh(geometry,material);parent.add(m);return m;};
 const hillMat=mat('#789281');
 for(let i=0;i<11;i++){const hill=add(new T.SphereGeometry(1,28,16),hillMat);hill.position.set(-27+i*5.5,-1.1+Math.sin(i*2)*.4,-20-Math.cos(i)*4);hill.scale.set(5.5,2.8+Math.sin(i)*1.5,3);}
 const sunDisc=add(new T.CircleGeometry(2,64),new T.MeshBasicMaterial({color:0xffe9b4,transparent:true,opacity:.75,fog:false,depthWrite:false}));sunDisc.position.set(-8,7,-30);
 const waterUniforms={uTime:{value:0},uLift:{value:0},uCamera:{value:camera.position},uRipple:{value:new T.Vector2(2.6,0)}};
 const waterMat=new T.ShaderMaterial({transparent:true,side:T.DoubleSide,depthWrite:false,uniforms:waterUniforms,vertexShader:`
  uniform float uTime; varying vec3 vWorld; varying vec3 vNormal;
  void main(){vec3 p=position;float x=p.x,z=p.y;float a=x*.8+z*.42+uTime*.62;float b=x*1.8-z*1.6-uTime*.45;
   p.z+=sin(a)*.07+sin(b)*.022;vec4 w=modelMatrix*vec4(p,1.);vWorld=w.xyz;vNormal=normalize(vec3(-cos(a)*.06,1.,-cos(b)*.06));gl_Position=projectionMatrix*viewMatrix*w;}
 `,fragmentShader:`
  uniform float uTime;uniform float uLift;uniform vec3 uCamera;uniform vec2 uRipple;varying vec3 vWorld;varying vec3 vNormal;
  void main(){vec3 viewDir=normalize(uCamera-vWorld);float fresnel=pow(1.-max(dot(vNormal,viewDir),0.),3.);
   float waves=sin(vWorld.x*2.8+sin(vWorld.z*1.7+uTime*.2)+uTime*.7)*sin(vWorld.z*3.2-uTime*.3);
   float glint=pow(max(dot(reflect(normalize(vec3(5.,-8.,-6.)),vNormal),viewDir),0.),85.);
   float d=length(vWorld.xz-uRipple);float ring=pow(max(0.,sin(d*22.-uTime*2.)),22.)*exp(-d*1.8);
   vec3 c=mix(vec3(.15,.32,.29),vec3(.65,.77,.65),fresnel);c+=waves*.025+glint*vec3(.85,.66,.35)+ring*.055;
   float mist=smoothstep(7.,35.,length(vWorld.xz));c=mix(c,vec3(.69,.77,.67),mist);gl_FragColor=vec4(c,(.86+fresnel*.12)*(1.-uLift));}
 `});
 const water=add(new T.PlaneGeometry(120,100,180,140),waterMat);water.rotation.x=-Math.PI/2;water.position.set(0,-.85,-25);
 const reeds:T.Group[]=[];const green=mat('#526b3e'),seed=mat('#715135'),leafMat=mat('#59734a');
 for(let i=0;i<36;i++){const reed=new T.Group();nature.add(reed);const side=i%2===0?-1:1;reed.position.set(side*(4.3+(i%7)*.16),-.94,1.1+(i%5)*.22);const h=.65+(i%9)*.19;const path=new T.QuadraticBezierCurve3(new T.Vector3(),new T.Vector3(side*.06,h*.65,0),new T.Vector3(side*.25,h,.04));add(new T.TubeGeometry(path,10,.008,5,false),green,reed);const head=add(new T.CapsuleGeometry(.035,.23,4,7),seed,reed);head.position.copy(path.getPoint(.9));head.rotation.z=-side*.18;const leaf=add(new T.SphereGeometry(1,6,5),leafMat,reed);leaf.position.set(-side*.12,h*.35,0);leaf.scale.set(.035,h*.3,.014);leaf.rotation.z=side*.4;reeds.push(reed);}
 for(let i=0;i<7;i++){const lily=add(new T.CircleGeometry(.24+(i%3)*.055,32,.2,Math.PI*2-.35),mat(i%2?'#526d3e':'#718252'));lily.rotation.x=-Math.PI/2;lily.rotation.z=i*1.7;lily.position.set(-3.1+(i%3)*.45,-.825,-.2+Math.floor(i/3)*.58);}
 const rodGroup=new T.Group();scene.add(rodGroup);
 const rodCurve=new T.CatmullRomCurve3([new T.Vector3(-4.8,-1.5,2),new T.Vector3(-4.2,.5,1.6),new T.Vector3(-2.7,2.8,.9),new T.Vector3(-.1,3.35,.3),new T.Vector3(2.4,2.65,0)]);
 add(new T.TubeGeometry(rodCurve,72,.023,8,false),mat('#574d35',.35),rodGroup);
 const grip=add(new T.CylinderGeometry(.071,.08,.72,16),mat('#b99a66'),rodGroup);grip.position.copy(rodCurve.getPoint(.075));grip.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),rodCurve.getTangent(.075));
 const reel=add(new T.TorusGeometry(.15,.048,10,30),mat('#ab8655',.32),rodGroup);reel.position.copy(rodCurve.getPoint(.14)).add(new T.Vector3(-.15,0,.05));
 const lineArray=new Float32Array(43*3),lineGeo=new T.BufferGeometry();lineGeo.setAttribute('position',new T.BufferAttribute(lineArray,3));const lineMat=new T.LineBasicMaterial({color:0x877e5e,transparent:true,opacity:.65});const line=new T.Line(lineGeo,lineMat);scene.add(line);
 const floatGroup=new T.Group();scene.add(floatGroup);const red=add(new T.SphereGeometry(.085,16,12,0,Math.PI*2,0,Math.PI/2),mat('#bb613f'),floatGroup);red.position.y=.005;const cream=add(new T.SphereGeometry(.085,16,12,0,Math.PI*2,Math.PI/2,Math.PI/2),mat('#f5e8c7'),floatGroup);cream.scale.y=1.3;const antenna=add(new T.CylinderGeometry(.009,.009,.21,6),mat('#bd4c31'),floatGroup);antenna.position.y=.13;
 const hook=add(new T.TorusGeometry(.066,.006,7,24,Math.PI*1.5),new T.MeshStandardMaterial({color:0xaba892,metalness:.8,roughness:.24}),floatGroup);floatGroup.remove(hook);scene.add(hook);
 const droplets=add(new T.IcosahedronGeometry(.022,0),mat('#b6d8c5'));
 nature.remove(droplets);droplets.geometry.dispose();(droplets.material as T.Material).dispose();
 const splash=new T.InstancedMesh(new T.SphereGeometry(.023,5,4),new T.MeshStandardMaterial({color:0xc7dfcc,transparent:true,opacity:.68,roughness:.12}),54);scene.add(splash);const dummy=new T.Object3D();
 const catchGroup=new T.Group();scene.add(catchGroup);const fishGroup=new T.Group();catchGroup.add(fishGroup);const labels=Array.from({length:7},()=>new T.Group());labels.forEach(g=>catchGroup.add(g));
  const branches:T.Line[]=[];const branchPoints=[[-1.15,1.45,-.32,1.0],[.9,1.45,.32,.75],[-1.15,-.2,-.4,.1],[.9,-.2,.4,-.4],[-1.15,-1.8,-.3,-1.35]];
 for(const [x,y,fx,fy] of branchPoints){const path=new T.QuadraticBezierCurve3(new T.Vector3(x,y,.18),new T.Vector3((x+fx)*.5,fy+.1,.32),new T.Vector3(fx,fy,.37));const geometry=new T.BufferGeometry().setFromPoints(path.getPoints(30));const branch=new T.Line(geometry,new T.LineBasicMaterial({color:0x65764b,transparent:true,opacity:0}));catchGroup.add(branch);branches.push(branch);}
 let alive=true,loaded=false,target=0,current=0,free=false,raf=0,last=0,lastRender=0,paused=false;const pointer=new T.Vector2();const aim=new T.Vector3(),cam=new T.Vector3(),mouth=new T.Vector3(),tip=rodCurve.getPoint(1);
 const decoder=new DRACOLoader();decoder.setDecoderPath('/draco/');decoder.setWorkerLimit(2);const loader=new GLTFLoader();loader.setDRACOLoader(decoder);
 loader.load('/models/Hal_story_bare.glb',g=>{if(!alive)return;const meshes:T.Mesh[]=[];g.scene.traverse(o=>{if(o instanceof T.Mesh)meshes.push(o);});g.scene.updateMatrixWorld(true);
  for(const m of meshes){const family=String(m.userData.story_group||m.name);const label=family.match(/^LABEL_(\d)/);if(label)m.material=Array.isArray(m.material)?m.material.map(material=>material.clone()):m.material.clone();const authoredMatrix=m.matrixWorld.clone();m.removeFromParent();authoredMatrix.decompose(m.position,m.quaternion,m.scale);m.updateMatrix();if(label)labels[Number(label[1])].add(m);else fishGroup.add(m);for(const material of Array.isArray(m.material)?m.material:[m.material]){if(material instanceof T.MeshStandardMaterial){material.envMapIntensity=.6;if(label){material.roughness=.5;material.transparent=true;} }} }
  labels.forEach(group=>{const bounds=new T.Box3();group.traverse(o=>{if(o instanceof T.Mesh){o.geometry.computeBoundingBox();o.updateMatrix();if(o.geometry.boundingBox)bounds.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrix));}});group.userData.corner=new T.Vector3(bounds.min.x,bounds.max.y,0);group.visible=false;});loaded=true;onLoad(100);
 },e=>{if(e.total)onLoad(Math.min(99,Math.round(e.loaded/e.total*100)));},()=>{if(alive)onError();});
 const resize=()=>{const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h);camera.aspect=w/Math.max(h,1);camera.updateProjectionMatrix();};const observer=new ResizeObserver(resize);observer.observe(host);resize();
 const mouse=(e:PointerEvent)=>{pointer.set((e.clientX/innerWidth-.5)*2,(e.clientY/innerHeight-.5)*2);};window.addEventListener('pointermove',mouse,{passive:true});
 const visibility=()=>{paused=document.hidden;};document.addEventListener('visibilitychange',visibility);
 function frame(ms:number){if(!alive)return;raf=requestAnimationFrame(frame);if(paused||ms-lastRender<1000/40)return;const dt=Math.min((ms-last)/1000,.06)||.016;last=ms;lastRender=ms;const time=reduced?0:ms/1000;current=T.MathUtils.damp(current,target,5,dt);const p=reduced?target:current;const lift=ease(.3,1.9,p),diagram=ease(6.45,7.2,p),mobile=camera.aspect<.9;
  waterUniforms.uTime.value=time;waterUniforms.uLift.value=ease(1.3,2.5,p)*.97;water.position.y=-.85;nature.position.y=0;rodGroup.position.y=lift*1.8;rodGroup.visible=p<7.4;
  reeds.forEach((reed,i)=>{reed.rotation.z=Math.sin(time*.55+i*.9)*.033;});
  if(!free){const distance=mobile?Math.max(11,7/(2*Math.tan(T.MathUtils.degToRad(19))*camera.aspect)):T.MathUtils.lerp(10.4,12,diagram);cam.set((reduced?0:pointer.x*.1),T.MathUtils.lerp(2.45,2.7,lift)+(reduced?0:pointer.y*.05),distance);camera.position.lerp(cam,.11);aim.set(0,T.MathUtils.lerp(0,2.2,lift),0);camera.lookAt(aim);controls.target.copy(aim);}
  const centerX=mobile?0:T.MathUtils.lerp(1.65,0,diagram);catchGroup.position.set(centerX,T.MathUtils.lerp(-1.7,2.2,lift),0);rodGroup.position.x=lift*(centerX-.052-tip.x);catchGroup.scale.setScalar(mobile?.84:.92);
  const pullAngle=lift*Math.PI/2;const sway=Math.sin(time*1.15)*(.027+.028*lift);fishGroup.rotation.set(0,.10+Math.sin(time*.45)*.085,pullAngle+sway);const lip=new T.Vector3(1.859,.056,0);const pivot=lip.clone().applyEuler(new T.Euler(0,.1,pullAngle));fishGroup.position.copy(pivot).sub(lip.clone().applyEuler(fishGroup.rotation));
  labels.forEach((group,i)=>{const show=i>=5?ease(6.6,7.15,p):ease(1.05+i*.97,1.65+i*.97,p);group.visible=loaded&&show>.005;const positions=[[-3.35,2.25],[1.05,2.25],[-3.35,.55],[1.05,.55],[-3.35,-1.15],[-.68,2.75],[1.05,-1.2]];const sizes=[1.15,1.10,1.15,1.07,1.07,1.15,.72];const scale=sizes[i]*(.96+.04*show);group.scale.setScalar(scale);const corner=group.userData.corner as T.Vector3|undefined;if(corner)group.position.set(positions[i][0]-corner.x*scale,positions[i][1]-corner.y*scale,(1-show)*-.2);group.traverse(o=>{if(o instanceof T.Mesh)for(const m of Array.isArray(o.material)?o.material:[o.material])m.opacity=show;});});
  branches.forEach((branch,i)=>{const show=ease(1.05+i*.97,1.65+i*.97,p);branch.visible=loaded&&show>.005;(branch.material as T.LineBasicMaterial).opacity=show*.8;branch.geometry.setDrawRange(0,Math.ceil(show*31));});catchGroup.updateMatrixWorld(true);fishGroup.updateMatrixWorld(true);mouth.set(1.859,.056,0).applyMatrix4(fishGroup.matrixWorld);const lineEnd=loaded?mouth:new T.Vector3(2.5,-.85,0);const lineTip=tip.clone().add(rodGroup.position);for(let i=0;i<43;i++){const f=i/42;const q=lineTip.clone().lerp(lineEnd,f);q.x+=Math.sin(f*Math.PI)*.12*(1-lift);q.y-=Math.sin(f*Math.PI)*.18*(1-lift);lineArray[i*3]=q.x;lineArray[i*3+1]=q.y;lineArray[i*3+2]=q.z;}lineGeo.attributes.position.needsUpdate=true;lineGeo.computeBoundingSphere();line.visible=p<7.4;floatGroup.visible=p<7.4;const floatY=Math.max(-.76,lineEnd.y+.31);const floatT=T.MathUtils.clamp((lineTip.y-floatY)/Math.max(.01,lineTip.y-lineEnd.y),0,1);floatGroup.position.copy(lineTip).lerp(lineEnd,floatT);hook.position.copy(lineEnd).add(new T.Vector3(0,.04,0));hook.visible=p<7.4;floatGroup.rotation.z=Math.sin(time*1.7)*.06*(1-lift);waterUniforms.uRipple.value.set(lineEnd.x,lineEnd.z);
  const sp=T.MathUtils.clamp((p-.55)/.85,0,1);splash.visible=sp>0&&sp<1;for(let i=0;i<54;i++){const angle=i*2.39996;const r=sp*(.25+(i%7)*.13);dummy.position.set(centerX+Math.cos(angle)*r,-.8+Math.sin(sp*Math.PI)*(1+(i%5)*.14),Math.sin(angle)*r);dummy.scale.setScalar(Math.max(.01,1-sp));dummy.updateMatrix();splash.setMatrixAt(i,dummy.matrix);}splash.instanceMatrix.needsUpdate=true;
  if(free)controls.update();renderer.render(scene,camera);
 }
 raf=requestAnimationFrame(frame);
 return {update(p:number,instant=false){target=T.MathUtils.clamp(p,0,8);if(instant)current=target;},interact(v:boolean){free=v;controls.enabled=v;renderer.domElement.style.touchAction=v?'none':'pan-y';renderer.domElement.tabIndex=v?0:-1;if(v){controls.target.set(0,2.2,0);controls.update();}},reset(){free=false;controls.enabled=false;},snapshot(){return{loaded,progress:Number(current.toFixed(2)),free,visibleGroups:labels.map((g,i)=>g.visible?i:null).filter(i=>i!==null),triangles:renderer.info.render.triangles};},dispose(){alive=false;cancelAnimationFrame(raf);observer.disconnect();window.removeEventListener('pointermove',mouse);document.removeEventListener('visibilitychange',visibility);controls.dispose();decoder.dispose();const geometries=new Set<T.BufferGeometry>(),materials=new Set<T.Material>(),textures=new Set<T.Texture>();scene.traverse(o=>{if(o instanceof T.Mesh||o instanceof T.Line){geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material]){materials.add(m);for(const value of Object.values(m))if(value instanceof T.Texture)textures.add(value);}}});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());env.dispose();pmrem.dispose();renderer.dispose();renderer.domElement.remove();}};
}
