(function(root){
 'use strict';
 const key='altcam-cart';let memory=[];
 const count=n=>Number.isFinite(Number(n))?Math.min(100,Math.max(0,Math.floor(Number(n)))):0;
 function read(){try{const value=JSON.parse(root.localStorage.getItem(key)||'[]');memory=Array.isArray(value)?value.filter(x=>x&&typeof x.id==='string').map(x=>({...x,quantity:Math.max(1,count(x.quantity||1))})):[];}catch{}return memory;}
 function write(value){memory=value;let saved=true;try{root.localStorage.setItem(key,JSON.stringify(value));}catch{saved=false;}refresh();return saved;}
 function install(config,rates){const v=rates.video,i=count(config.indoor),o=count(config.outdoor);
  const rate=(n,r)=>n===1?r.one:n===2?r.two:n<=8?r.threeToEight:r.overEight;
  return i*rate(i,v.indoorCamera)+o*rate(o,v.outdoorCamera)+(i+o?((config.nvr?v.recorderSetup:0)+(config.mobile?v.mobileAppSetup:0)):0);
 }
 function refresh(){const n=memory.reduce((sum,x)=>sum+Math.max(1,count(x.quantity||1)),0);for(const node of root.document?.querySelectorAll?.('[data-cart-count]')||[])node.textContent=n;}
 function init(){read();const doc=root.document;if(!doc)return;
  if(!doc.getElementById('cart-open')&&!doc.querySelector('[data-shared-cart]')){
   const nav=doc.querySelector('main nav,header nav,nav');if(nav){const a=doc.createElement('a');a.href='/catalog.html#cart';a.dataset.sharedCart='';a.innerHTML='Кошик (<span data-cart-count>0</span>)';nav.append(a);}
  }refresh();
 }
 root.AltcamCart={read,write,install,count,refresh};
 root.addEventListener?.('storage',event=>{if(event.key===key){read();refresh();}});
 if(root.document?.readyState==='loading')root.document.addEventListener('DOMContentLoaded',init);else init();
 if(typeof module!=='undefined')module.exports=root.AltcamCart;
})(typeof window==='undefined'?globalThis:window);
