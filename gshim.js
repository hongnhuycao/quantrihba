/* Lớp nối Google Sheets cho bản chạy trên GitHub Pages.
   App gốc gọi window.__G.use("mcp").callTool("Google Sheets","get_values"|"update_formulas",{spreadsheetId,range,...}).
   Ở đây các lệnh đó đi thẳng tới Google Sheets API bằng tài khoản Google của người đang đăng nhập:
   ai không được chia sẻ file Sheet thì không đọc/ghi được. Trang không chứa sẵn số liệu nào. */
(function(){
const CFG=window.HBA_CONFIG||{};const CLIENT_ID=CFG.googleClientId||"";
const SCOPES="https://www.googleapis.com/auth/spreadsheets openid email profile";
let token=null,tokenExp=0,tokenClient=null,waiters=[],me=null;
const gate=document.createElement("div");gate.id="g-gate";
gate.innerHTML='<div class="g-box"><div class="g-logo">HBA</div><h1>HBA Quản trị</h1><p id="g-msg">Đăng nhập bằng tài khoản Google đã được chia sẻ các file Google Sheet của HBA để xem và cập nhật số liệu.</p><button id="g-btn" type="button">Đăng nhập Google</button><p class="g-small">Trang không lưu số liệu. Mọi số liệu đọc trực tiếp từ Google Sheets theo quyền của tài khoản bạn.</p></div>';
const css=document.createElement("style");css.textContent='#g-gate{position:fixed;inset:0;z-index:100;display:grid;place-items:center;background:#f2f4f5;font-family:"Be Vietnam Pro",system-ui,sans-serif;padding:16px}#g-gate[hidden]{display:none}.g-box{max-width:420px;width:100%;background:#fff;border:1px solid #dbe2e6;border-radius:16px;padding:28px 24px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.06)}.g-logo{width:52px;height:52px;border-radius:14px;background:#0e5c63;color:#fff;font-weight:800;display:grid;place-items:center;margin:0 auto 10px}.g-box h1{font-size:22px;margin:0 0 8px;color:#13202a}.g-box p{color:#4b5b67;font-size:14px;line-height:1.5;margin:0 0 16px}#g-btn{background:#0e5c63;color:#fff;border:0;border-radius:10px;padding:12px 22px;font:inherit;font-weight:700;font-size:15px;cursor:pointer}#g-btn:disabled{opacity:.5}.g-small{font-size:12px!important;color:#7b8b96!important;margin:14px 0 0!important}@media (prefers-color-scheme:dark){#g-gate{background:#0e161c}.g-box{background:#152029;border-color:#283844}.g-box h1{color:#e7eef2}.g-box p{color:#a8b7c1}}';
document.head.appendChild(css);document.addEventListener("DOMContentLoaded",()=>document.body.appendChild(gate));
const msg=t=>{const m=document.getElementById("g-msg");if(m)m.textContent=t;};
function loadGis(){return new Promise((ok,no)=>{if(window.google&&google.accounts&&google.accounts.oauth2)return ok();const s=document.createElement("script");s.src="https://accounts.google.com/gsi/client";s.async=true;s.onload=ok;s.onerror=()=>no(new Error("Không tải được dịch vụ đăng nhập Google."));document.head.appendChild(s);});}
async function initClient(){await loadGis();tokenClient=google.accounts.oauth2.initTokenClient({client_id:CLIENT_ID,scope:SCOPES,callback:r=>{if(r.error){waiters.splice(0).forEach(w=>w.no({code:"needs_reauth",message:r.error}));msg("Chưa đăng nhập được: "+r.error+". Bấm thử lại.");return;}
 token=r.access_token;tokenExp=Date.now()+((+r.expires_in||3600)-120)*1000;try{sessionStorage.setItem("g.tok",JSON.stringify({token,tokenExp}));}catch(e){}waiters.splice(0).forEach(w=>w.ok(token));gate.hidden=true;},error_callback:e=>{waiters.splice(0).forEach(w=>w.no({code:"needs_reauth",message:e&&e.type}));msg("Cửa sổ đăng nhập bị đóng hoặc bị chặn. Bấm thử lại.");}});}
function askToken(prompt){return new Promise((ok,no)=>{waiters.push({ok,no});tokenClient.requestAccessToken({prompt});});}
try{const s=JSON.parse(sessionStorage.getItem("g.tok")||"null");if(s&&s.tokenExp>Date.now()){token=s.token;tokenExp=s.tokenExp;}}catch(e){}
let ready;const readyP=new Promise(r=>ready=r);
document.addEventListener("DOMContentLoaded",async()=>{const b=document.getElementById("g-btn");
 if(!CLIENT_ID){b.disabled=true;msg("Chưa cấu hình Google Client ID trong file config.js. Xem hướng dẫn trong README của repo.");return;}
 try{await initClient();}catch(e){msg(e.message);b.disabled=true;return;}
 if(token){gate.hidden=true;ready();}
 b.addEventListener("click",async()=>{b.disabled=true;try{await askToken("");ready();}catch(e){}b.disabled=false;});});
async function tok(){if(token&&Date.now()<tokenExp)return token;if(!tokenClient)await readyP;try{return await askToken("");}catch(e){gate.hidden=false;throw e;}}
async function api(url,opt,retry){const t=await tok();const r=await fetch(url,Object.assign({},opt,{headers:Object.assign({"Authorization":"Bearer "+t,"Content-Type":"application/json"},(opt||{}).headers)}));
 if(r.status===401&&!retry){token=null;return api(url,opt,true);}
 const j=await r.json().catch(()=>({}));if(!r.ok){const m=(j.error&&j.error.message)||("HTTP "+r.status);throw {code:r.status===401?"needs_reauth":r.status===429?"rate_limited":"tool_error",message:m,retryable:r.status===429||r.status>=500};}return j;}
const base=id=>"https://sheets.googleapis.com/v4/spreadsheets/"+encodeURIComponent(id)+"/values/";
async function call(server,tool,input){
 if(tool==="get_values"){const j=await api(base(input.spreadsheetId)+encodeURIComponent(input.range)+"?valueRenderOption=FORMATTED_VALUE&dateTimeRenderOption=FORMATTED_STRING");return {payload:{range:j.range,values:j.values||[]}};}
 if(tool==="update_formulas"||tool==="update_values"){const j=await api(base(input.spreadsheetId)+encodeURIComponent(input.range)+"?valueInputOption="+(tool==="update_formulas"?"USER_ENTERED":"RAW"),{method:"PUT",body:JSON.stringify({range:input.range,majorDimension:"ROWS",values:input.formulas||input.values})});return {payload:j};}
 throw {code:"not_in_manifest",message:tool};}
const watches=new Set();
const mcp={callTool:(s,t,i)=>call(s,t,i),
 watchTool:(s,t,i,h)=>{const w={s,t,i,h};watches.add(w);(async()=>{try{const res=await call(s,t,i);h({type:"data",result:Object.assign(res,{cache:{storedAt:Date.now()}})});}catch(e){h({type:"error",error:e});}})();return ()=>watches.delete(w);},
 invalidate:async()=>{for(const w of watches){try{const res=await call(w.s,w.t,w.i);w.h({type:"data",result:Object.assign(res,{cache:{storedAt:Date.now()}})});}catch(e){w.h({type:"error",error:e});}}}};
const user={me:async()=>{if(me)return me;try{const j=await api("https://www.googleapis.com/oauth2/v3/userinfo");me={name:j.name||j.email||"",email:j.email||""};}catch(e){me={name:"",email:""};}return me;},isOwner:()=>false,canEdit:()=>true};
const downloads={save:async({filename,data})=>{const u=URL.createObjectURL(data instanceof Blob?data:new Blob([data]));const a=document.createElement("a");a.href=u;a.download=filename;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),4000);}};
window.__G={use:async n=>{if(n==="mcp"){await readyP;return mcp;}if(n==="user")return user;if(n==="downloads")return downloads;return null;}};
})();
