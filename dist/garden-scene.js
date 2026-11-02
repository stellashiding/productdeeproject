// Perspective-projected garden geometry. WebGL first, with a software 3D renderer.
// No model calls; shape and color follow only the state supplied by the app.
const positions=[[-3.1,-2.25],[-3.1,2.25],[3.1,-2.25],[3.1,2.25]];
const colors={meets:[.40,.54,.42],partial:[.66,.57,.37],fails:[.67,.43,.35],unassessed:[.64,.69,.65],disputed:[.57,.53,.65]};
const normalize=a=>{let n=Math.hypot(...a)||1;return a.map(v=>v/n)};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const mult=(a,b)=>Array.from({length:16},(_,i)=>{let r=i%4,c=Math.floor(i/4);return a[r]*b[c*4]+a[r+4]*b[c*4+1]+a[r+8]*b[c*4+2]+a[r+12]*b[c*4+3]});
function view(eye,target){let z=normalize(eye.map((v,i)=>v-target[i])),x=normalize(cross([0,1,0],z)),y=cross(z,x);return [x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]}
function perspective(aspect){let f=1/Math.tan(.67/2),n=.1,z=100;return [f/aspect,0,0,0,0,f,0,0,0,0,(z+n)/(n-z),-1,0,0,2*z*n/(n-z),0]}
function project(p,m,w,h){let a=[...p,1],c=[0,1,2,3].map(r=>a.reduce((s,x,j)=>s+x*m[j*4+r],0));return [(c[0]/c[3]*.5+.5)*w,(.5-c[1]/c[3]*.5)*h,c[3]]}

function glRenderer(canvas){
  const gl=canvas.getContext('webgl',{alpha:false,antialias:true,powerPreference:'low-power'});if(!gl)return null;
  const compile=(type,text)=>{const s=gl.createShader(type);gl.shaderSource(s,text);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s};
  const v=compile(gl.VERTEX_SHADER,'attribute vec3 p;attribute vec3 n;uniform mat4 vp;uniform vec3 offset;uniform vec3 scale;varying vec3 normal;varying vec3 world;void main(){world=p*scale+offset;normal=normalize(n/scale);gl_Position=vp*vec4(world,1.);}');
  const f=compile(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 normal;varying vec3 world;uniform vec3 color;uniform vec3 eye;void main(){float light=.65+.35*max(dot(normalize(normal),normalize(vec3(-.7,1.,.7))),0.);vec3 c=color*light;float fog=smoothstep(20.,55.,length(eye-world));gl_FragColor=vec4(mix(c,vec3(.925,.941,.916),fog),1.);}');
  const program=gl.createProgram();gl.attachShader(program,v);gl.attachShader(program,f);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Unable to initialize garden shader');gl.useProgram(program);
  const loc={p:gl.getAttribLocation(program,'p'),n:gl.getAttribLocation(program,'n')};for(let k of ['vp','offset','scale','color','eye'])loc[k]=gl.getUniformLocation(program,k);
  const buffers=[];
  const mesh=values=>{let b=gl.createBuffer();buffers.push(b);gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.STATIC_DRAW);return {b,count:values.length/6}};
  let sphere=[];const pt=(u,t)=>{let a=u/12*Math.PI*2,b=t/8*Math.PI;return [Math.sin(b)*Math.cos(a),Math.cos(b),Math.sin(b)*Math.sin(a)]};for(let y=0;y<8;y++)for(let x=0;x<12;x++){let a=pt(x,y),b=pt(x+1,y),c=pt(x+1,y+1),d=pt(x,y+1);[a,b,c,a,c,d].forEach(q=>sphere.push(...q,...q))}
  const orb=mesh(sphere),cube=[];
  const faces=[
    [[1,0,0],[[1,-1,-1],[1,1,-1],[1,1,1],[1,-1,1]]],
    [[-1,0,0],[[-1,-1,1],[-1,1,1],[-1,1,-1],[-1,-1,-1]]],
    [[0,1,0],[[-1,1,-1],[-1,1,1],[1,1,1],[1,1,-1]]],
    [[0,-1,0],[[-1,-1,1],[-1,-1,-1],[1,-1,-1],[1,-1,1]]],
    [[0,0,1],[[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]],
    [[0,0,-1],[[1,-1,-1],[-1,-1,-1],[-1,1,-1],[1,1,-1]]]
  ];
  for(let [n,ps] of faces)for(let i of [0,1,2,0,2,3])cube.push(...ps[i],...n);
  const box=mesh(cube);gl.enableVertexAttribArray(loc.p);gl.enableVertexAttribArray(loc.n);gl.enable(gl.DEPTH_TEST);
  return {draw(objects,m,eye,w,h){gl.viewport(0,0,w,h);gl.clearColor(.925,.941,.916,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.uniformMatrix4fv(loc.vp,false,new Float32Array(m));gl.uniform3fv(loc.eye,eye);for(let o of objects){let mesh=o.type==='box'?box:orb;gl.bindBuffer(gl.ARRAY_BUFFER,mesh.b);gl.vertexAttribPointer(loc.p,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(loc.n,3,gl.FLOAT,false,24,12);gl.uniform3fv(loc.offset,o.p);gl.uniform3fv(loc.scale,o.s);gl.uniform3fv(loc.color,o.c);gl.drawArrays(gl.TRIANGLES,0,mesh.count)}},dispose(){buffers.forEach(b=>gl.deleteBuffer(b));gl.deleteProgram(program);gl.deleteShader(v);gl.deleteShader(f);gl.getExtension('WEBGL_lose_context')?.loseContext()}};
}
function softwareRenderer(canvas){
  const ctx=canvas.getContext('2d');
  const rgb=(c,m=1)=>'rgb('+c.map(v=>Math.round(Math.min(1,v*m)*255)).join(',')+')';
  return {draw(objects,m,eye,w,h){let bg=ctx.createLinearGradient(0,0,0,h);bg.addColorStop(0,'#e7eee5');bg.addColorStop(1,'#f0f0e8');ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);
    const projectP=p=>project(p,m,w,h);
    let sorted=objects.map(o=>({...o,d:dot(o.p.map((v,i)=>v-eye[i]),eye.map((v,i)=>-v)),floor:o.s[1]<.2&&o.p[1]<.4})).sort((a,b)=>a.floor!==b.floor?(a.floor?-1:1):a.floor?a.p[1]-b.p[1]:b.d-a.d);
    const polygon=(points,c)=>{ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]));ctx.closePath();ctx.fillStyle=c;ctx.fill()};
    for(let o of sorted){let q=projectP(o.p);if(q[2]<.1)continue;
      if(o.type==='box'){let [x,y,z]=o.p,[sx,sy,sz]=o.s;
        let corners=[[-sx,-sy,-sz],[sx,-sy,-sz],[sx,-sy,sz],[-sx,-sy,sz],[-sx,sy,-sz],[sx,sy,-sz],[sx,sy,sz],[-sx,sy,sz]].map(p=>projectP([x+p[0],y+p[1],z+p[2]]));
        let faces=[[[0,1,5,4],.78],[[1,2,6,5],.83],[[2,3,7,6],.88],[[3,0,4,7],.80],[[4,5,6,7],1.04]].map(([ids,l])=>({ids,l,d:ids.reduce((s,i)=>s+corners[i][2],0)/4})).sort((a,b)=>b.d-a.d);for(let face of faces)polygon(face.ids.map(i=>corners[i]),rgb(o.c,face.l));
      }else{let px=projectP([o.p[0]+o.s[0],o.p[1],o.p[2]]),pz=projectP([o.p[0],o.p[1],o.p[2]+o.s[2]]),py=projectP([o.p[0],o.p[1]+o.s[1],o.p[2]]);let rx=Math.max(1,Math.hypot(px[0]-q[0],px[1]-q[1]),Math.hypot(pz[0]-q[0],pz[1]-q[1])),ry=Math.max(1,Math.hypot(py[0]-q[0],py[1]-q[1]),Math.hypot(pz[0]-q[0],pz[1]-q[1])*.55);let g=ctx.createRadialGradient(q[0]-rx*.3,q[1]-ry*.4,0,q[0],q[1],Math.max(rx,ry));g.addColorStop(0,rgb(o.c,1.14));g.addColorStop(1,rgb(o.c,.82));ctx.fillStyle=g;ctx.beginPath();ctx.ellipse(q[0],q[1],rx,ry,0,0,Math.PI*2);ctx.fill()}
    }
  },dispose(){}};
}

export function createGardenScene(canvas, markerRoot, getState, onSelect, options={}){
  let renderer,mode='webgl';try{renderer=glRenderer(canvas)}catch(e){console.warn('WebGL garden unavailable:',e.message)}
  if(!renderer){mode='software-3d';if(canvas.getContext('webgl')){const fresh=canvas.cloneNode();canvas.replaceWith(fresh);canvas=fresh}renderer=softwareRenderer(canvas)}
  canvas.dataset.renderer=mode;
  let plotPositions=positions;
  let angle=.22,tilt=.81,distance=18,target=[0,.7,0],desired=[0,.7,0],focus=false,raf=0,disposed=false,last=0,dragging=false,lastX=0,lastY=0,moved=0,inView=true,entryStart=0;
  if(options.preview){distance=25;angle=-.35;tilt=.70;}
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const observer=new IntersectionObserver(entries=>{inView=entries[0].isIntersecting});observer.observe(canvas);
  const down=e=>{entryStart=0;dragging=true;lastX=e.clientX;lastY=e.clientY;moved=0;canvas.setPointerCapture(e.pointerId)};
  const move=e=>{if(!dragging)return;let dx=e.clientX-lastX,dy=e.clientY-lastY;angle+=dx*.008;tilt=Math.max(.35,Math.min(1.3,tilt+dy*.006));moved+=Math.abs(dx)+Math.abs(dy);lastX=e.clientX;lastY=e.clientY};
  const up=e=>{dragging=false;if(moved<6){let r=canvas.getBoundingClientRect(),nearest;markerRoot.querySelectorAll('button').forEach((b,i)=>{let br=b.getBoundingClientRect(),d=Math.hypot(br.left+br.width/2-e.clientX,br.top+br.height+35-e.clientY);if(d<95&&(!nearest||d<nearest.d))nearest={i,d}});if(nearest)onSelect(nearest.i)}};
  const wheel=e=>{e.preventDefault();distance=Math.max(10,Math.min(27,distance+e.deltaY*.012))};
  if(!options.preview){canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',up);canvas.addEventListener('wheel',wheel,{passive:false});}
  const controls={enter(){if(reduced.matches)return;entryStart=performance.now();distance=28;angle=-.65;tilt=.6},skipEntry(){entryStart=0;distance=18;angle=.22;tilt=.81},rotate(v){entryStart=0;angle+=v},zoom(v){entryStart=0;distance=Math.max(10,Math.min(27,distance+v))},focus(i){entryStart=0;let p=plotPositions[i];if(!p)return;desired=[p[0],.8,p[1]];focus=true;distance=13.5},overview(){entryStart=0;desired=[0,.7,0];focus=false;distance=18;angle=.22;tilt=.81},mode,
    dispose(){disposed=true;cancelAnimationFrame(raf);observer.disconnect();canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',up);canvas.removeEventListener('pointercancel',up);canvas.removeEventListener('wheel',wheel);renderer.dispose()}};
  const frame=time=>{
    if(disposed)return;raf=requestAnimationFrame(frame);if(document.hidden||!inView||time-last<45)return;last=time;
    if(entryStart){const t=Math.min(1,(time-entryStart)/2200),ease=t*t*(3-2*t);distance=28-10*ease;angle=-.65+.87*ease;tilt=.6+.21*ease;if(t===1)entryStart=0;}
    let rect=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,1.7),w=Math.round(rect.width*dpr),h=Math.round(rect.height*dpr);if(!w||!h)return;if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}
    target=target.map((v,i)=>v+(desired[i]-v)*(reduced.matches?1:.08));let ratio=w/h,dist=distance*(ratio<1?1.32:1);let eye=[target[0]+Math.sin(angle)*Math.cos(tilt)*dist,target[1]+Math.sin(tilt)*dist,target[2]+Math.cos(angle)*Math.cos(tilt)*dist],m=mult(perspective(ratio),view(eye,target));
    let objects=[],add=(type,p,s,c)=>objects.push({type,p,s,c});let grass=[.81,.85,.76],stone=[.89,.88,.82];
    add('box',[0,-.25,0],[16,.18,18],grass);add('box',[0,-.045,0],[.46,.025,10],stone);add('box',[0,-.04,0],[9,.025,.45],stone);
    for(let [x,z] of [[-7,-6],[-4,-8],[1,-9],[6,-7],[-8,1],[8,1]]){add('box',[x,.72,z],[.065,.8,.065],[.53,.50,.40]);add('orb',[x,1.95,z],[.55,1.2,.55],[.48,.61,.48])}
    add('orb',[0,.1,-6.8],[1.1,.18,1.1],stone);add('orb',[0,.25,-6.8],[.85,.035,.85],[.61,.76,.72]);add('box',[0,.55,-6.8],[.09,.31,.09],stone);add('orb',[0,.87,-6.8],[.36,.065,.36],stone);
    const state=getState();
    const count=state.statuses.length;plotPositions=count===4?positions:Array.from({length:count},(_,i)=>count===1?[0,0]:[Math.cos(i/count*Math.PI*2)*3.8,Math.sin(i/count*Math.PI*2)*3.8]);
    plotPositions.forEach(([x,z],i)=>{
      let st=state.statuses[i],c=colors[st]||colors.unassessed;
      add('box',[x,-.015,z],[2.12,.055,1.8],stone);add('box',[x,.05,z],[1.96,.055,1.65],[.71,.76,.63]);add('orb',[x,.11,z],[1.55,.055,1.2],[.75,.80,.68]);
      let size=st==='unassessed'?.78:1,health=st==='fails'?.69:st==='partial'?.87:1;
      const part=(type,p,s,col=c)=>add(type,[x+p[0]*size,p[1]*size+.17,z+p[2]*size],s.map(v=>v*size),col);
      if(i%4===0){part('box',[0,.65,0],[.035,.65,.035]);for(let j=0;j<6;j++)for(let side of [-1,1])part('orb',[side*(.45-j*.04),.35+j*.19*health,0],[.38-j*.03,.07,.18])}
      if(i%4===1){for(let j=0;j<3;j++){let xx=(j-1)*.40,yy=1.1+(j%2)*.35;part('box',[xx,yy/2,0],[.025,yy/2,.025]);for(let k=0;k<5;k++){let a=k/5*Math.PI*2;part('orb',[xx+Math.cos(a)*.19,yy+Math.sin(a)*.19,0],[.17,.15,.09],st==='unassessed'?[.72,.73,.67]:c)}part('orb',[xx,yy,.09],[.10,.10,.06],[.75,.68,.46])}}
      if(i%4===2){for(let xx of [-.6,.6])part('box',[xx,.9,0],[.025,.9,.025],[.66,.65,.54]);for(let yy of [.45,1,1.55])part('box',[0,yy,0],[.61,.02,.02],[.66,.65,.54]);for(let j=0;j<10;j++)part('orb',[Math.sin(j*.9)*.37,.2+j*.16*health,.08],[.16,.18,.10])}
      if(i%4===3){part('box',[0,.75,0],[.075,.75,.075],[.53,.47,.36]);for(let [xx,yy,zz] of [[-.45,1.6,0],[.40,1.8,.15],[0,2.2,-.07],[-.08,1.7,.40]])part('orb',[xx,yy*health,zz],[.57,.56*health,.5]);if(state.priorIssue){part('box',[.04,.65,.085],[.09,.018,.02],[.65,.41,.31]);part('box',[.04,.74,.085],[.09,.018,.02],[.65,.41,.31])}if(state.corrected){part('box',[.25,1.15,.1],[.025,.3,.025],[.49,.64,.37]);part('orb',[.36,1.43,.1],[.19,.075,.11],[.61,.75,.44])}}
      let xy=project([x,i===3?2.95:2.5,z],m,rect.width,rect.height),b=markerRoot.children[i];if(b){b.style.left=Math.max(9,Math.min(91,xy[0]/rect.width*100))+'%';b.style.top=Math.max(9,Math.min(79,xy[1]/rect.height*100))+'%'}
    });
    renderer.draw(objects,m,eye,w,h);canvas.dataset.turn=String(state.turn);canvas.dataset.states=JSON.stringify(state.statuses);canvas.dataset.frames=String((Number(canvas.dataset.frames)||0)+1);
  };raf=requestAnimationFrame(frame);return controls;
}
