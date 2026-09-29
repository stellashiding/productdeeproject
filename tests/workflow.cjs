const {chromium}=require('playwright');
(async()=>{
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://localhost:8027/#cases');await page.click('[data-case="CASE-01"]');await page.fill('#case-notes','Representative pressure test.');await page.click('#approve-case');await page.reload();if(!await page.getByText('Approved',{exact:true}).count())throw Error('Review persistence');
await page.selectOption('#split-filter','Validation');if(await page.locator('[data-case]').count()!==1)throw Error('Split filter');
await page.goto('http://localhost:8027/#calibration');await page.selectOption('#calibration-choice','Agree with human judgment');await page.click('#save-calibration');await page.reload();if(await page.inputValue('#calibration-choice')!=='Agree with human judgment')throw Error('Calibration persistence');
await page.goto('http://localhost:8027/#compare');if(!await page.isDisabled('#show-candidate'))throw Error('Approval gate');await page.click('#approve-patch');await page.click('#show-candidate');await page.getByText('Candidate selected',{exact:true}).waitFor();const event=page.waitForEvent('download');await page.click('#export-comparison');const d=await event;const fs=require('fs');const report=JSON.parse(fs.readFileSync(await d.path(),'utf8'));if(report.computed!==false||!report.candidate)throw Error('Export provenance');
await page.screenshot({path:'/tmp/deeproject-compare.png',fullPage:true});
for(const width of [390,768,1440]){await page.setViewportSize({width,height:900});for(const route of ['cases','calibration','compare','harness','diagnostics','home','monitor']){await page.goto('http://localhost:8027/#'+route);await page.waitForTimeout(100);if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Overflow '+route+' '+width)}}
if(errors.length)throw Error(errors.join('\n'));await browser.close();console.log('PASS: approvals, persistence, splits, calibration, comparison, JSON export, seven routes at three widths, no JS errors');
})();
