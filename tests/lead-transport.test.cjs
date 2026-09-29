const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../lead-payload.js'),'utf8');
function setup(fetch){
  let cancel,delay,cleared=false;
  const context={AbortController,fetch,ALTCAM_CONTACTS:{apiBase:'https://test.invalid/'},setTimeout(fn,ms){cancel=fn;delay=ms;return 1;},clearTimeout(){cleared=true;}};
  vm.runInNewContext(source,context);
  return {post:context.AltcamLead.post,cancel:()=>cancel(),delay:()=>delay,cleared:()=>cleared};
}
test('12 second timeout aborts and clears timer',async()=>{
  const transport=setup((url,options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new Error('aborted')))));
  const sent=transport.post('/site-lead',{});
  assert.equal(transport.delay(),12000);transport.cancel();
  await assert.rejects(sent,/aborted/);assert.equal(transport.cleared(),true);
});
test('HTTP 200 with ok:false is not success',async()=>{
  const transport=setup(async()=>({ok:true,json:async()=>({ok:false})}));
  await assert.rejects(transport.post('/site-lead',{}));
  assert.equal(transport.cleared(),true);
});
test('configured API base and JSON are used',async()=>{
  const transport=setup(async(url,options)=>{
    assert.equal(url,'https://test.invalid/site-lead');
    assert.equal(options.body,'{"name":"test"}');
    return {ok:true,json:async()=>({ok:true,id:42})};
  });
  assert.equal((await transport.post('/site-lead',{name:'test'})).id,42);
});
