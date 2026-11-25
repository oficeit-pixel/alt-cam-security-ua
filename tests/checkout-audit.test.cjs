const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('rate table is valid JSON for server and executable for browser',()=>{
 const source=fs.readFileSync('data/service-rates.js','utf8');
 const parsed=JSON.parse(source.split('=').slice(1).join('=').trim().replace(/;$/,''));
 const context={window:{}};vm.runInNewContext(source,context);
 assert.deepEqual(JSON.parse(JSON.stringify(context.window.ALTCAM_RATES)),parsed);
});
test('checkout adapter preserves structured installation',()=>{
 const context={window:{location:{origin:'https://example.test',pathname:'/'}}};
 vm.runInNewContext(fs.readFileSync('lead-payload.js','utf8'),context);
 const script=fs.readFileSync('lead-payload.js','utf8');
 assert.match(script,/installation:payload.installation/);
 assert.match(fs.readFileSync('catalog.js','utf8'),/installation:needsInstallation\?installationConfig\(\):null/);
});
