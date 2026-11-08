const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function setup(consent){
 const events=[],clicks={};
 const element=()=>({setAttribute(){},append(){},querySelector(){return {}},hidden:false});
 const document={head:element(),body:element(),referrer:'',title:'Test',createElement:element,addEventListener:(name,fn)=>clicks[name]=fn};
 const window={};
 vm.runInNewContext(fs.readFileSync('analytics.js','utf8'),{window,document,
 location:{search:'',origin:'https://example.test',pathname:'/',reload(){}},
 localStorage:{getItem:()=>consent,setItem(){}},sessionStorage:{getItem:()=>null,setItem(){}},URL,URLSearchParams});
 // Replace GA sink only after consent initialization.
 window.gtag=(...args)=>events.push(args);
 return {window,events};
}
test('no analytics without consent, including direct named events',()=>{
 for(const consent of [null,'no']){
  const {window,events}=setup(consent);
  for(const name of ['form_submit','quiz_complete','cart_submit','click_telegram'])window.altcamAnalytics(name);
  assert.equal(events.length,0);
 }
});
test('accepted consent sends requested events without customer fields',()=>{
 const {window,events}=setup('yes');
 window.altcamAnalytics('submit_lead',{phone:'secret',name:'secret'});
 window.altcamAnalytics('checkout_completed',{email:'secret'});
 assert.equal(events[0][1],'form_submit');assert.equal(events[1][1],'cart_submit');
 assert.ok(!JSON.stringify(events).includes('secret'));
});
