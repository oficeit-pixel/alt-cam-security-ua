const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../lead-payload.js'),'utf8');
function setup(fetch,extra={}){
  let cancel,delay,cleared=false;
  const context={AbortController,fetch,ALTCAM_CONTACTS:{apiBase:'https://test.invalid/'},setTimeout(fn,ms){cancel=fn;delay=ms;return 1;},clearTimeout(){cleared=true;}};
  Object.assign(context,extra);
  vm.runInNewContext(source,context);
  return {post:context.AltcamLead.post,warmup:context.AltcamLead.warmup,cancel:()=>cancel(),delay:()=>delay,cleared:()=>cleared};
}

test('failed warmup can retry and allows a cold server to start',async()=>{
  let calls=0;
  const transport=setup(async()=>{calls++;return {ok:false};});
  transport.warmup();
  assert.equal(transport.delay(),65000);
  await new Promise(resolve=>setImmediate(resolve));
  transport.warmup();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(calls,2);
});

test('successful warmup is not repeated',async()=>{
  let calls=0;
  const transport=setup(async()=>{calls++;return {ok:true};});
  transport.warmup();
  await new Promise(resolve=>setImmediate(resolve));
  transport.warmup();
  assert.equal(calls,1);
});
test('lead timeout allows server delivery and aborts cleanly',async()=>{
  const transport=setup((url,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted')))));
  const sent=transport.post('/site-lead',{});
  await Promise.resolve();
  assert.equal(transport.delay(),65000);transport.cancel();
  await assert.rejects(sent,/aborted/);assert.equal(transport.cleared(),true);
});

test('concurrent identical submissions share one request and result',async()=>{
  let calls=0, finish;
  const transport=setup(()=>{calls++;return new Promise(resolve=>{finish=resolve;});});
  const first=transport.post('/site-lead',{name:'test'});
  const second=transport.post('/site-lead',{name:'test'});
  assert.equal(first,second);
  await Promise.resolve();
  assert.equal(calls,1);
  finish({ok:true,json:async()=>({ok:true,id:42})});
  assert.equal((await first).id,42);
  assert.equal((await second).id,42);
});

test('different payloads are not merged and failures can retry',async()=>{
  let calls=0;
  const transport=setup(async()=>{calls++;throw new Error('offline');});
  const results=await Promise.allSettled([
    transport.post('/site-lead',{name:'first'}),
    transport.post('/site-lead',{name:'second'}),
  ]);
  assert.equal(calls,2);
  assert.ok(results.every(result=>result.status==='rejected'));
  await assert.rejects(transport.post('/site-lead',{name:'first'}),/offline/);
  assert.equal(calls,3);
});

test('duplicate submissions send only one backup and omit consultation credentials',async()=>{
  let backups=0;
  const transport=setup(async()=>({ok:true,json:async()=>({ok:true,id:1})}),{
    ALTCAM_CONTACTS:{apiBase:'https://test.invalid',backupWebhook:'https://backup.invalid'},
    navigator:{sendBeacon(url,body){
      backups++;
      assert.equal(url,'https://backup.invalid');
      assert.equal(JSON.parse(body).consultation,undefined);
    }},
  });
  const payload={name:'test',consultation:{token:'TEST_ONLY'}};
  await Promise.all([transport.post('/api/lead',payload),transport.post('/api/lead',payload)]);
  assert.equal(backups,1);
});

test('successful submission does not prevent a subsequent intentional order',async()=>{
  let calls=0;
  const transport=setup(async()=>({ok:true,json:async()=>({ok:true,id:++calls})}));
  assert.equal((await transport.post('/site-lead',{name:'test'})).id,1);
  assert.equal((await transport.post('/site-lead',{name:'test'})).id,2);
});
test('HTTP 200 with ok:false is not success',async()=>{
  const transport=setup(async()=>({ok:true,json:async()=>({ok:false})}));
  await assert.rejects(transport.post('/site-lead',{}));
  assert.equal(transport.cleared(),true);
});
test('configured API base and JSON are used',async()=>{
  const transport=setup(async(url,options)=>{
    assert.equal(url,'https://test.invalid/api/lead');
    const payload=JSON.parse(options.body);
    assert.equal(payload.name,'test');
    assert.equal(payload.source_form,'consultation');
    return {ok:true,json:async()=>({ok:true,id:42})};
  });
  assert.equal((await transport.post('/site-lead',{name:'test'})).id,42);
});

test('uncertain delivery keeps identity across reload, success clears it',async()=>{
  const store=new Map(), sent=[];
  const extra={crypto:require('node:crypto').webcrypto,TextEncoder,
    sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)}};
  const payload={name:'Test',phone:'+380630000000'};
  const first=setup(async(url,options)=>{sent.push(JSON.parse(options.body));throw new Error('lost response');},extra);
  await assert.rejects(first.post('/site-lead',payload),/lost response/);
  assert.match(sent[0].request_id,/^[a-f0-9]{32}$/);
  assert.ok([...store.values()].every(value=>!value.includes(payload.phone)));
  const reloaded=setup(async(url,options)=>{sent.push(JSON.parse(options.body));return {ok:true,json:async()=>({ok:true,id:42})};},extra);
  await reloaded.post('/site-lead',payload);
  assert.equal(sent[1].request_id,sent[0].request_id);
  await reloaded.post('/site-lead',payload);
  assert.notEqual(sent[2].request_id,sent[0].request_id);
});

test('different uncertain submissions keep independent retry identities',async()=>{
  const store=new Map(),sent=[];
  const extra={crypto:require('node:crypto').webcrypto,TextEncoder,
    sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)}};
  const transport=setup(async(url,options)=>{sent.push(JSON.parse(options.body));throw new Error('offline');},extra);
  for(const name of ['First','Second','First'])await assert.rejects(transport.post('/site-lead',{name}),/offline/);
  assert.equal(sent[0].request_id,sent[2].request_id);
  assert.notEqual(sent[0].request_id,sent[1].request_id);
});
