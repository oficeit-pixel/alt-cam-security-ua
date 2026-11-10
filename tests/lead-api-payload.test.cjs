const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
function setup(){
 const data=new Map(),calls=[];
 const root={location:{origin:'https://example.test',pathname:'/',search:'?utm_source=google&utm_term=cameras'},
 sessionStorage:{getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)},ALTCAM_CONTACTS:{apiBase:'https://api.example.test'},
 fetch:async(url,options)=>{calls.push({url,payload:JSON.parse(options.body)});return {ok:true,json:async()=>({ok:true})};}};
 vm.runInNewContext(fs.readFileSync('lead-payload.js','utf8'),{window:root,URL,URLSearchParams,AbortController,setTimeout,clearTimeout});
 return {root,calls};
}
test('first touch survives navigation and every form uses canonical API',async()=>{
 const {root,calls}=setup();
 root.location.search='?utm_source=changed';
 for(const [type,source] of [['contact_form','hero'],['quiz','quiz'],['quote_confirmation','calculator'],['catalog_consultation','consultation']]){
  await root.AltcamLead.post('/site-lead',{type,client:{name:'Тест',phone:'0630000000'},details:{walls:'бетон'}});
  const call=calls.at(-1);
  assert.equal(call.url,'https://api.example.test/api/lead');
  assert.equal(call.payload.source_form,source);
  assert.equal(call.payload.utm_source,'google');
  assert.equal(call.payload.object.walls,'бетон');
 }
});
test('cart keeps items, delivery and signed consultation context',async()=>{
 const {root,calls}=setup();
 await root.AltcamLead.post('/api/orders',{customer:{name:'Тест',phone:'0630000000'},
 items:[{id:'x',quantity:2}],delivery:{type:'pickup'},consultation:{init_data:'test-only'}});
 const p=calls[0].payload;
 assert.equal(p.source_form,'cart');assert.equal(p.cart[0].id,'x');
 assert.equal(p.delivery.type,'pickup');assert.equal(p.consultation.init_data,'test-only');
});
