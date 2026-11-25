const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('rate table is valid JSON for server and executable for browser',()=>{
 const source=fs.readFileSync('data/service-rates.js','utf8');
 const parsed=JSON.parse(source.split('=').slice(1).join('=').trim().replace(/;$/,''));
 const context={window:{}};vm.runInNewContext(source,context);
 assert.deepEqual(JSON.parse(JSON.stringify(context.window.ALTCAM_RATES)),parsed);
});
test('checkout adapter preserves structured installation',()=>{
 const context={window:{location:{origin:'https://example.test',pathname:'/'}}};
 context.URL=URL;context.URLSearchParams=URLSearchParams;
 vm.runInNewContext(fs.readFileSync('lead-payload.js','utf8'),context);
 const config={indoor:2,outdoor:2,nvr:true,mobile:true};
 const payload=context.window.AltcamLead.apiPayload({customer:{name:'Test',phone:'0630000000'},needs_installation:true,installation:config,items:[]},true);
 assert.equal(payload.installation,config);
 assert.equal(payload.needs_installation,true);
 assert.match(fs.readFileSync('catalog.js','utf8'),/installation:needsInstallation\?installationConfig\(\):null/);
});
