'use strict';
const q=s=>document.querySelector(s);
const btn=q('#record'),status=q('#status'),hint=q('#hint'),transcript=q('#transcript'),plan=q('#plan'),latency=q('#latency'),alias=q('#alias'),entity=q('#entity'),save=q('#save'),mappingStatus=q('#mappingStatus');
const confirmBtn=q('#confirm'),confirmStatus=q('#confirmStatus'),panelState=q('#panelState'),tokenInput=q('#haToken'),saveTokenBtn=q('#saveToken'),tokenStatus=q('#tokenStatus');
let tokenConfigured=false,pendingConfirmation=null,expiryTimer=null;
let stream=null,ctx=null,mic=null,proc=null,mute=null,timer=null,chunks=[],active=false,busy=false;
let inventory={entities:[],aliases:{},mapping:{}};
function clearConfirmation(){
  pendingConfirmation=null;
  if(expiryTimer)clearTimeout(expiryTimer);
  expiryTimer=null;confirmBtn.disabled=true;
  confirmBtn.textContent='请先说出明确的灯光指令';
}
function showConfirmation(p){
  clearConfirmation();
  if(!p.confirmation_required || !p.confirm_id){
    confirmStatus.textContent='当前指令只预览；只有明确的、已绑定的灯光开关能执行。';return;
  }
  if(!tokenConfigured){
    confirmStatus.textContent='灯光目标已确认，但请先配置 HA 访问令牌，然后重新说一次指令。';return;
  }
  pendingConfirmation=p.confirm_id;
  const word=p.action==='turn_on'?'打开':'关闭';
  confirmBtn.textContent=`确认${word}：${p.alias}（30 秒内）`;
  confirmBtn.disabled=false;
  confirmStatus.textContent='仅按下绿色按钮才会发送 HA 请求，不会自动执行。';
  expiryTimer=setTimeout(()=>{clearConfirmation();confirmStatus.textContent='确认已超时，请重新说话。';},30000);
}
async function refreshPanelState(){
  try{const r=await fetch('/panel-ceiling-state',{cache:'no-store'});if(!r.ok)throw Error();const j=await r.json();
    panelState.textContent=!j.mapped?'面板第二路尚未映射':!j.available?'面板第二路：HA 状态暂不可读取':`面板第二路（吸顶灯）：HA 显示${j.state==='on'?'已打开':'已关闭'}`;
  }catch(e){panelState.textContent='面板状态暂不可读取';}
}
async function configureToken(){
  const token=tokenInput.value.trim();if(!token){tokenStatus.textContent='请先在 HA 个人资料中创建令牌，再粘贴到这里。';return;}
  saveTokenBtn.disabled=true;tokenStatus.textContent='正在通过 ZUK 本机的 HA 验证令牌…';
  try{
    const r=await fetch('/credentials',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})});
    const j=await r.json();if(!r.ok||!j.configured)throw Error(j.error||'无效的 HA 令牌');
    tokenInput.value='';tokenConfigured=true;tokenStatus.textContent='已连接 HA：令牌已保存在 ZUK 私有目录。';
    clearConfirmation();confirmStatus.textContent='为了安全，请再说一次灯光指令，再手动确认执行。';await refreshPanelState();
  }catch(e){tokenStatus.textContent='HA 令牌验证失败，请检查令牌是否来自当前 HA 8125。';}
  finally{saveTokenBtn.disabled=false;}
}
async function confirmLight(){
  if(!pendingConfirmation || !tokenConfigured)return;
  const id=pendingConfirmation;clearConfirmation();confirmBtn.disabled=true;
  confirmStatus.textContent='正在向 HA 发送人工确认的灯光指令…';
  try{
    const r=await fetch('/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({confirm_id:id})});
    const j=await r.json();if(!r.ok||!j.submitted)throw Error(j.error||'HA 未接受请求');
    confirmStatus.textContent=`HA 已接受${j.action==='turn_on'?'打开':'关闭'}的请求，请观察面板和吸顶灯是否响应。`;await refreshPanelState();
  }catch(e){confirmStatus.textContent='操作未完成：'+(e.message||'请重试并重新识别语音');}
}
function option(value,label){const e=document.createElement('option');e.value=value;e.textContent=label;return e;}
function populateAlias(){alias.replaceChildren(option('','请选择语音名称'));for(const name of Object.keys(inventory.aliases))alias.appendChild(option(name,name));refreshEntity();}
function refreshEntity(){const a=alias.value,d=inventory.aliases[a];entity.replaceChildren(option('','请选择对应 HA 实体'));for(const e of inventory.entities.filter(x=>x.domain===d))entity.appendChild(option(e.entity_id,`${e.area?'['+e.area+'] ':''}${e.name} (${e.entity_id})`));entity.value=inventory.mapping[a]||'';mappingStatus.textContent=entity.value?'已绑定该 HA 实体':'尚未绑定';save.disabled=!a||!entity.value;}
async function loadInventory(){try{const r=await fetch('/entities',{cache:'no-store'});if(!r.ok)throw Error('entities unavailable');inventory=await r.json();populateAlias();}catch(e){mappingStatus.textContent='读取 HA 实体失败，可先测试语音';}}
function floatToPCM16(samples,sr){const ratio=sr/16000,n=Math.floor(samples.length/ratio),out=new Int16Array(n);for(let i=0;i<n;i++){let a=Math.floor(i*ratio),b=Math.min(samples.length,Math.max(a+1,Math.floor((i+1)*ratio))),sum=0;for(let j=a;j<b;j++)sum+=samples[j];out[i]=Math.round(Math.max(-1,Math.min(1,sum/(b-a)))*32767);}return new Uint8Array(out.buffer);}
function cleanup(){if(timer)clearTimeout(timer);timer=null;active=false;if(proc){proc.onaudioprocess=null;proc.disconnect();proc=null;}if(mic){mic.disconnect();mic=null;}if(mute){mute.disconnect();mute=null;}if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;}if(ctx){ctx.close().catch(()=>{});ctx=null;}btn.classList.remove('rec');btn.textContent='🎙 点击录音';}
async function start(){if(active||busy)return;clearConfirmation();try{stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});ctx=new (window.AudioContext||window.webkitAudioContext)();await ctx.resume();mic=ctx.createMediaStreamSource(stream);proc=ctx.createScriptProcessor(4096,1,1);mute=ctx.createGain();mute.gain.value=0;mic.connect(proc);proc.connect(mute);mute.connect(ctx.destination);chunks=[];proc.onaudioprocess=e=>{if(active)chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));};active=true;btn.classList.add('rec');btn.textContent='■ 点击结束录音';status.textContent='正在录音（ZUK 本机）';hint.textContent='录音中，最长 8 秒；点击结束后开始离线识别。';timer=setTimeout(()=>stop(),8000);}catch(e){status.textContent='无法录音，请允许 Chrome 使用麦克风';hint.textContent=e.name||'麦克风不可用';cleanup();}}
async function stop(){if(!active)return;const rate=ctx.sampleRate,parts=chunks.slice();cleanup();const len=parts.reduce((v,p)=>v+p.length,0);if(len<rate/10){status.textContent='录音时间太短';return;}busy=true;btn.disabled=true;status.textContent='本机 SenseVoice 推理中…';try{const all=new Float32Array(len);let i=0;for(const p of parts){all.set(p,i);i+=p.length;}const audio=floatToPCM16(all,rate);const r=await fetch('/recognize',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:audio});const j=await r.json();if(!r.ok)throw Error(j.error||'服务错误');transcript.textContent=j.text||'（没有识别到人声）';const p=j.plan||{};if(!p.understood){plan.textContent='暂不执行：'+(p.reason||'无法理解指令');}else{const a=p.action==='set_temperature'?`设置到 ${p.temperature} ℃`:p.action==='turn_on'?'打开':'关闭';plan.textContent=`模拟：${p.alias} → ${a} / `+(p.entity?`${p.entity.area?'['+p.entity.area+'] ':''}${p.entity.name} (${p.entity.entity_id})`:'尚未绑定实际设备');if(p.alias && inventory.aliases[p.alias]){alias.value=p.alias;refreshEntity();}}showConfirmation(p);latency.textContent=`本机识别耗时 ${j.elapsed_ms} ms · 本轮未自动执行家电操作`;status.textContent='识别完成，可以继续测试';}catch(e){status.textContent='识别失败';plan.textContent=String(e.message||e);}finally{busy=false;btn.disabled=false;}}
async function saveMapping(){if(!alias.value||!entity.value)return;save.disabled=true;mappingStatus.textContent='保存中…';try{const r=await fetch('/map',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({alias:alias.value,entity_id:entity.value})});const j=await r.json();if(!r.ok)throw Error(j.error||'保存失败');inventory.mapping[alias.value]=entity.value;mappingStatus.textContent='映射已保存。请重新说出指令验证映射。';clearConfirmation();}catch(e){mappingStatus.textContent='保存失败：'+e.message;}finally{save.disabled=false;}}
async function boot(){try{const r=await fetch('/health',{cache:'no-store'});const h=await r.json();if(!h.ready)throw Error();tokenConfigured=Boolean(h.token_configured);tokenStatus.textContent=tokenConfigured?'已连接 HA：令牌在 ZUK 本机安全保存。':'尚未配置 HA 令牌；只有识别与预览可用。';status.textContent='已就绪 · SenseVoice INT8 模型常驻';btn.textContent='🎙 点击录音';btn.disabled=false;}catch(e){status.textContent='本机 8127 服务尚未启动';}await loadInventory();await refreshPanelState();}
btn.addEventListener('click',()=>active?stop():start());alias.addEventListener('change',refreshEntity);entity.addEventListener('change',()=>{save.disabled=!alias.value||!entity.value;mappingStatus.textContent='待保存映射';});save.addEventListener('click',saveMapping);saveTokenBtn.addEventListener('click',configureToken);confirmBtn.addEventListener('click',confirmLight);boot();
