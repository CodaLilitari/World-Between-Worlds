/** UI-only tests: no HTTP server, browser, conversion, or game process. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {runInNewContext} from 'node:vm';
const code=await readFile(new URL('./app.js',import.meta.url),'utf8');
const html=await readFile(new URL('./index.html',import.meta.url),'utf8');
const css=await readFile(new URL('./styles.css',import.meta.url),'utf8');
const ui=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const recipes=[
  {id:'stock-one',title:'Stock One',kind:'vanilla',gameplay:['mp'],author:'LucasArts',status:'supported',requires_archive:false},
  {id:'custom-two',title:'Stone Sanctuary',kind:'custom',gameplay:['mp','ctf'],author:'Original Author',summary:'A fortress courtyard.',status:'verified',requires_archive:true,source_url:'https://example.org/reviewed-level',archive_hint:'stone.zip or stone.gob'},
  {id:'future-sp',title:'Future Story',kind:'custom',gameplay:['sp'],author:'Author',status:'unavailable',requires_archive:true},
  {id:'mod-three',title:'Custom Gameplay',kind:'mod',gameplay:['mp'],author:'Mod Author',status:'ready',requires_archive:true},
];
test('selection is empty without explicit IDs',()=>assert.deepEqual(ui.selectedRecipes(recipes,new Set()),[]));
test('unknown and unavailable status is not selectable',()=>{
  assert.equal(ui.selectable({}),false);assert.equal(ui.selectable({status:'unavailable'}),false);assert.equal(ui.selectable({status:'unreviewed'}),false);
});
test('only declared supported status tokens are selectable',()=>{
  for(const status of ['verified','supported','ready','available','prototype'])assert.equal(ui.selectable({status}),true);
});
test('prototype mod is selected only by explicit ID and stays separate from maps',()=>{
  const prototype={id:'ninja-kage',title:'Ninja Kage',kind:'mod',gameplay:['mp'],status:'prototype',requires_archive:true};
  const catalog=[...recipes,prototype];
  assert.deepEqual(ui.selectedRecipes(catalog,new Set()),[]);
  assert.deepEqual(ui.selectionPayload(catalog,new Set(['stock-one']),{},{}).ids,['stock-one']);
  const result=ui.selectionPayload(catalog,new Set(['stock-one','ninja-kage']),{},{'ninja-kage':'original.zip'});
  assert.deepEqual(result.ids,['stock-one','ninja-kage']);
  assert.deepEqual(result.archives,{'ninja-kage':'original.zip'});
});
test('category and mode filters intersect',()=>assert.deepEqual(ui.visibleRecipes(recipes,{kind:'custom',gameplay:'ctf'}).map(r=>r.id),['custom-two']));
test('Levels includes stock and custom maps but excludes gameplay mods',()=>{
  assert.deepEqual(ui.visibleRecipes(recipes,{kind:'levels'}).map(r=>r.id),['stock-one','custom-two','future-sp']);
  assert.deepEqual(ui.visibleRecipes(recipes,{kind:'levels',gameplay:'ctf'}).map(r=>r.id),['custom-two']);
});
test('multiword search matches title and author case-insensitively',()=>assert.deepEqual(ui.visibleRecipes(recipes,{search:'STONE author'}).map(r=>r.id),['custom-two']));
test('gameplay names are searchable',()=>assert.deepEqual(ui.visibleRecipes(recipes,{search:'capture flag'}).map(r=>r.id),['custom-two']));
test('empty mod or SP category remains empty, without fabricated recipes',()=>{
  const noSP=recipes.filter(r=>r.id!=='future-sp');assert.deepEqual(ui.visibleRecipes(noSP,{gameplay:'sp'}),[]);
  assert.deepEqual(ui.visibleRecipes(recipes.filter(r=>r.kind!=='mod'),{kind:'mod'}),[]);
});
test('filtering does not mutate selection or input recipes',()=>{
  const ids=new Set(['custom-two']);const before=JSON.stringify(recipes);ui.visibleRecipes(recipes,{kind:'vanilla'});
  assert.deepEqual([...ids],['custom-two']);assert.equal(JSON.stringify(recipes),before);
});
test('payload contains selected supported IDs only, in catalog order',()=>{
  const payload=ui.selectionPayload(recipes,new Set(['mod-three','unknown','stock-one','future-sp']),{},{});
  assert.deepEqual(payload.ids,['stock-one','mod-three']);
});
test('payload excludes unselected and unneeded archive overrides',()=>{
  const payload=ui.selectionPayload(recipes,new Set(['stock-one','custom-two']),{jk_root:' C:\\JK ',mots_root:' C:\\MotS ',archive_dir:' E:\\ZIP ',output_dir:' E:\\Out '},{'stock-one':'wrong.zip','custom-two':' E:\\stone.zip ','mod-three':'unselected.zip'});
  assert.deepEqual(payload.archives,{'custom-two':'E:\\stone.zip'});assert.equal(payload.jk_root,'C:\\JK');assert.equal(payload.output_dir,'E:\\Out');
});
test('conversion success does not imply runtime testing',()=>{
  assert.equal(ui.runtimeLabel({status:'success'}),'Runtime test: not run on this output');
  assert.equal(ui.runtimeLabel({status:'verified',runtime_test:{status:'not-run-on-this-output'}}),'Runtime test: not run on this output');
});
test('explicit runtime evidence is displayed distinctly',()=>{
  assert.equal(ui.runtimeLabel({runtime_test:{status:'passed'}}),'Runtime test: passed');
  assert.equal(ui.runtimeLabel({runtime_test:{status:'failed'}}),'Runtime test: failed');
});
test('progress is completed count with finite bounds',()=>{
  assert.deepEqual(ui.jobProgress({progress:2,total:4}),{done:2,total:4});
  assert.deepEqual(ui.jobProgress({progress:100,total:4}),{done:4,total:4});
  assert.deepEqual(ui.jobProgress({progress:-1,total:4}),{done:0,total:4});
  assert.deepEqual(ui.jobProgress({progress:'invalid',total:'invalid'}),{done:0,total:0});
});
test('original source links reject executable and local-file protocols',()=>{
  for(const value of ['javascript:alert(1)','data:text/html,test','file:///C:/private','not a url'])assert.equal(ui.safeSourceUrl(value),null);
  assert.equal(ui.safeSourceUrl('https://example.org/level'), 'https://example.org/level');
});
test('catalog rejects duplicate IDs and malformed kinds',()=>{
  assert.throws(()=>ui.validateCatalog({recipes:[recipes[0],recipes[0]]}),/duplicate/);
  assert.throws(()=>ui.validateCatalog({recipes:[{...recipes[0],kind:'fictional'}]}),/invalid/);
  assert.throws(()=>ui.validateCatalog({}),/invalid/);
  assert.equal(ui.validateCatalog({recipes}).recipes,recipes);
});
test('all literal DOM IDs used by the application exist once',()=>{
  const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length);
  for(const [,id] of code.matchAll(/\$\('([^']+)'\)/g))assert.ok(ids.includes(id),`Missing DOM ID ${id}`);
});
test('initial document has no preselected checkbox or enabled conversion action',()=>{
  assert.doesNotMatch(html,/\bchecked(?:\s|=|>)/i);assert.match(html,/id="convert" disabled/);assert.match(code,/selected:new Set\(\)/);
});
test('every API request uses the same token-bearing helper',()=>{
  assert.equal((code.match(/\bfetch\(/g)||[]).length,1);assert.match(code,/const headers=\{Accept:'application\/json','X-Blackwing-Token':token\}/);
  assert.match(html,/<meta name="blackwing-token" content="\{\{TOKEN\}\}">/);
});
test('no untrusted HTML injection or external dependencies',()=>{
  assert.doesNotMatch(code,/innerHTML|outerHTML|insertAdjacentHTML|\beval\s*\(/);
  assert.doesNotMatch(html,/<(?:script|link)[^>]+(?:src|href)="https?:/i);
  assert.doesNotMatch(css,/@import|url\(\s*['"]?https?:/i);
});
test('selection export posts only IDs and uses an explicit local download',()=>{
  assert.match(code,/api\('\/api\/export',\{method:'POST',body:\{ids\}\}\)/);
  assert.match(code,/link\.download='wbw-recipes\.json'/);
});
test('keyboard and motion affordances are present',()=>{
  assert.match(html,/class="skip-link"/);assert.match(html,/<dialog[^>]+aria-labelledby="detail-title"/);
  assert.match(code,/focusedRecipe/);assert.match(css,/prefers-reduced-motion/);
});

const installed=(overrides={})=>({path:'C:\\MotS\\Episode\\old.goo',filename:'old.goo',id:'stock-one',title:'Stock One',kind:'vanilla',role:'level',installed_revision:1,current_revision:2,status:'update_available',message:'A reviewed revision is available.',can_update:true,...overrides});
const scanResponse=(results=[],overrides={})=>({root:'C:\\MotS',results,counts:{},warnings:[],truncated:false,...overrides});
test('revision labels use positive integer provenance, without inventing a version',()=>{
  assert.equal(ui.revisionLabel(1),'wbw_v1');assert.equal(ui.revisionLabel(12),'wbw_v12');
  for(const value of [null,undefined,0,-1,1.5,'2',Infinity])assert.equal(ui.revisionLabel(value),'Not recorded');
  assert.throws(()=>ui.validateCatalog({recipes:[{...recipes[0],revision:'2'}]}),/invalid/);
});
test('scan statuses remain distinct and missing revisions are allowed',()=>{
  const rows=['current','update_available','newer','unversioned','modified','unrecognized','error'].map(status=>installed({status,can_update:false,installed_revision:null,current_revision:null}));
  assert.equal(new Set(rows.map(row=>ui.scanStatusLabel(row.status))).size,7);
  assert.equal(ui.validateScan(scanResponse(rows)).results,rows);
  assert.equal(ui.scanStatusLabel('constructor'),'Unrecognized');
});
test('malformed scan responses cannot enable actions',()=>{
  for(const row of [{can_update:'true'},{installed_revision:-1},{current_revision:'2'},{status:'complete'},{id:4}])assert.throws(()=>ui.validateScan(scanResponse([installed(row)])),/invalid/);
  assert.throws(()=>ui.validateScan({results:[]}),/invalid/);
});
test('queue eligibility requires explicit service approval and a selectable catalog recipe',()=>{
  for(const status of ['current','update_available','newer','unversioned','modified','unrecognized','error']){
    for(const can_update of [false,undefined,'true'])assert.deepEqual(ui.scanUpdateIds(recipes,[installed({status,can_update})]),[]);
  }
  assert.deepEqual(ui.scanUpdateIds(recipes,[installed({id:null}),installed({id:'unknown'}),installed({id:'future-sp'})]),[]);
  assert.deepEqual(ui.scanUpdateIds(recipes,[installed({status:'unversioned'})]),['stock-one']);
});
test('explicit bulk updates deduplicate recipe IDs and exclude non-outdated rows',()=>{
  const rows=[installed(),installed({path:'C:\\MotS\\copy.goo'}),installed({id:'custom-two',status:'modified'}),installed({id:'mod-three'})];
  assert.deepEqual(ui.scanUpdateIds(recipes,rows,{outdatedOnly:true}),['stock-one','mod-three']);
  assert.deepEqual(ui.scanUpdateIds(recipes,rows,{locked:true}),[]);
});
test('truncation and inspection failures never claim a complete scan',()=>{
  assert.match(ui.scanSummary(scanResponse()),/^Scan complete · 0 files/);
  for(const scan of [scanResponse([],{truncated:true}),scanResponse([installed({status:'error'})])])assert.match(ui.scanSummary(scan),/^Scan incomplete/);
});
test('duplicate warnings do not mislabel a complete inventory as partial',()=>{
  const result=scanResponse([installed({duplicate:true}),installed({duplicate:true,path:'C:\\MotS\\copy.goo'})],{warnings:['Multiple archives identify this recipe.']});
  assert.equal(ui.scanSummary(result),'Scan complete with warnings · 2 files listed.');
});

// A small DOM adapter runs the actual application and its event handlers. It does
// not emulate layout or replace browser QA; all requests are intercepted locally.
async function localUI({scan=async()=>scanResponse(),convert=async()=>({job_id:'test-job'}),pick=async()=>({path:null}),settings={jk_root:'C:\\JK',mots_root:'C:\\MotS',archive_dir:'C:\\Originals',output_dir:'C:\\Output'}}={}) {
  const nodes=new Map(),requests=[],timeouts=[];
  let doc;
  class Element {
    constructor(tag='div') {this.tagName=tag.toUpperCase();this.children=[];this.dataset={};this.events={};this.attributes={};this.className='';this.value='';this.disabled=false;this._text='';this.open=false;}
    get textContent(){return this._text+this.children.map(child=>child.textContent).join('');}
    set textContent(value){this._text=String(value);this.children=[];}
    get classList(){return {add:name=>this.classList.toggle(name,true),remove:name=>this.classList.toggle(name,false),contains:name=>this.className.split(/\s+/).includes(name),toggle:(name,force)=>{const set=new Set(this.className.split(/\s+/).filter(Boolean));const include=force??!set.has(name);include?set.add(name):set.delete(name);this.className=[...set].join(' ');return include;}};}
    append(...children){for(const child of children){child.parent=this;this.children.push(child);}}
    replaceChildren(...children){this._text='';this.children=[];this.append(...children);}
    setAttribute(name,value){this.attributes[name]=value;}
    addEventListener(type,callback){(this.events[type]??=[]).push(callback);}
    async fire(type,event={}){await Promise.all((this.events[type]||[]).map(callback=>callback({target:this,preventDefault(){},...event})));}
    querySelectorAll(selector){const result=[];for(const child of this.children){if(child.tagName===selector.toUpperCase())result.push(child);result.push(...child.querySelectorAll(selector));}return result;}
    querySelector(selector){return this.querySelectorAll(selector)[0] || null;}
    get options(){return this.querySelectorAll('option');}
    focus(){doc.activeElement=this;}
    showModal(){this.open=true;}
    close(){this.open=false;}
    scrollIntoView(){}
    remove(){if(this.parent)this.parent.children=this.parent.children.filter(child=>child!==this);}
  }
  for(const match of html.matchAll(/<([a-z][\w-]*)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
    const node=new Element(match[1]);node.id=match[3];node.className=/\bclass="([^"]*)"/.exec(match[2])?.[1] || '';node.name=/\bname="([^"]*)"/.exec(match[2])?.[1];node.disabled=/\bdisabled\b/.test(match[2]);nodes.set(node.id,node);
  }
  doc={activeElement:null,body:new Element('body'),getElementById:id=>nodes.get(id),createElement:tag=>new Element(tag),createTextNode:text=>{const node=new Element('text');node.textContent=text;return node;},querySelector:selector=>selector==='meta[name="blackwing-token"]'?{content:'test-local-token'}:null,querySelectorAll:()=>[],addEventListener(){}};
  const response=data=>({ok:true,json:async()=>data});
  runInNewContext(code.replace(/^export /gm,''),{document:doc,Option:class extends Element{constructor(text,value){super('option');this.textContent=text;this.value=value;}},FormData:class {entries(){return ['jk_root','mots_root','archive_dir','output_dir'].map(name=>[name,[...nodes.values()].find(node=>node.name===name)?.value || '']);}},URL,AbortController,Error,console,setTimeout:(_callback,delay)=>{timeouts.push(delay);return 0;},clearTimeout(){},matchMedia:()=>({matches:true}),fetch:async(path,options)=>{
    requests.push({path,options});
    if(path==='/api/health')return response({});
    if(path==='/api/catalog')return response({recipes:recipes.map(recipe=>({...recipe,revision:2,revision_label:'wbw_v2'}))});
    if(path==='/api/settings')return response(settings);
    if(path==='/api/scan')return response(await scan());
    if(path==='/api/pick-path')return response(await pick(JSON.parse(options.body)));
    if(path==='/api/convert')return response(await convert());
    if(path==='/api/jobs/test-job')return response({id:'test-job',status:'complete',progress:1,total:1,results:[],logs:[]});
    throw new Error('Unexpected request: '+path);
  }});
  await new Promise(resolve=>setImmediate(resolve));
  return {nodes,requests,timeouts,click:id=>nodes.get(id).fire('click'),async editMots(value){const input=nodes.get('mots-root');input.value=value;await nodes.get('settings-form').fire('input',{target:input});}};
}
test('application initialization and path changes never scan or select automatically',async()=>{
  const page=await localUI();assert.equal(page.requests.length,3);assert.equal(page.nodes.get('queue-count').textContent,'0');
  assert.equal(page.nodes.get('scan-mots').disabled,false);
  await page.editMots('D:\\MotS');assert.equal(page.requests.length,3);
  assert.match(page.nodes.get('recipe-list').textContent,/wbw_v2/);
});
test('Levels and Mods have separate pickers and visible selection never adds hidden mods',async()=>{
  const page=await localUI();
  const options=()=>page.nodes.get('recipe-picker').options.map(option=>option.value).filter(Boolean);
  assert.deepEqual(options(),['stock-one','custom-two']);
  await page.click('select-visible');
  assert.equal(page.nodes.get('queue-count').textContent,'2');
  await page.nodes.get('kind-navigation').fire('click',{target:{closest:()=>({dataset:{kind:'mod'}})}});
  assert.deepEqual(options(),['mod-three']);
  assert.equal(page.nodes.get('library-title').textContent,'Choose a mod');
  assert.match(page.nodes.get('selection-help').textContent,/never loads it automatically/);
  await page.click('reset-filters');
  assert.deepEqual(options(),['mod-three']);
  assert.equal(page.nodes.get('queue-count').textContent,'2');
  await page.click('select-visible');
  assert.equal(page.nodes.get('queue-count').textContent,'3');
  assert.equal(page.requests.filter(request=>request.path==='/api/convert').length,0);
});
test('explicit scan uses the token API and renders every status without selecting content',async()=>{
  const rows=['current','update_available','newer','unversioned','modified','unrecognized','error'].map((status,index)=>installed({status,path:`C:\\MotS\\${index}.goo`,can_update:status==='update_available',duplicate:status==='update_available'}));
  const page=await localUI({scan:async()=>scanResponse(rows)});await page.click('scan-mots');
  const request=page.requests.find(request=>request.path==='/api/scan');assert.equal(request.options.method,'POST');assert.deepEqual(JSON.parse(request.options.body),{mots_root:'C:\\MotS'});assert.equal(request.options.headers['X-Blackwing-Token'],'test-local-token');
  assert.deepEqual(page.timeouts,[15000,15000,15000,120000]);
  const list=page.nodes.get('scan-results');assert.equal(list.children.length,7);assert.equal(list.querySelectorAll('button').length,1);
  assert.match(list.textContent,/Installed: wbw_v1Catalog: wbw_v2/);assert.match(list.textContent,/Multiple installed files/);
  for(const row of rows)assert.ok(list.textContent.includes(ui.scanStatusLabel(row.status)));
  assert.equal(page.nodes.get('queue-count').textContent,'0');assert.match(page.nodes.get('scan-status').textContent,/Scan incomplete/);
});
test('a row update queues one recipe, preserves earlier selections, and never converts',async()=>{
  const page=await localUI({scan:async()=>scanResponse([installed({id:'custom-two'})])});
  const checkbox=page.nodes.get('recipe-list').querySelectorAll('input')[0];checkbox.checked=true;await checkbox.fire('change');
  await page.click('scan-mots');await page.nodes.get('scan-results').querySelectorAll('button')[0].fire('click');
  assert.equal(page.nodes.get('queue-count').textContent,'2');assert.match(page.nodes.get('queue-list').textContent,/wbw_v2/);
  assert.equal(page.nodes.get('scan-results').querySelectorAll('button')[0].disabled,true);
  assert.equal(page.requests.filter(request=>request.path==='/api/convert').length,0);
});
test('explicit queue-all deduplicates copies and cannot act on a stale folder scan',async()=>{
  const page=await localUI({scan:async()=>scanResponse([installed(),installed({path:'C:\\MotS\\copy.goo'})])});
  await page.click('scan-mots');await page.editMots('D:\\MotS');assert.equal(page.nodes.get('queue-outdated').disabled,true);
  await page.click('queue-outdated');assert.equal(page.nodes.get('queue-count').textContent,'0');
  await page.click('scan-mots');await page.click('queue-outdated');assert.equal(page.nodes.get('queue-count').textContent,'1');
  assert.equal(page.requests.filter(request=>request.path==='/api/convert').length,0);
});
test('folder changes discard a pending scan result and expose a rescan instruction',async()=>{
  let resolveScan;const page=await localUI({scan:()=>new Promise(resolve=>{resolveScan=resolve;})});const pending=page.click('scan-mots');
  assert.equal(page.nodes.get('scan-mots').disabled,true);assert.equal(page.nodes.get('scan-results').attributes['aria-busy'],'true');
  await page.editMots('D:\\MotS');resolveScan(scanResponse([installed()]));await pending;
  assert.equal(page.nodes.get('scan-results').children.length,0);assert.match(page.nodes.get('scan-status').textContent,/folder changed/);assert.equal(page.nodes.get('scan-mots').disabled,false);
});
test('scan errors, empty folders, and truncated scans are visible and retryable',async()=>{
  let mode='error';const page=await localUI({scan:async()=>{if(mode==='error')throw new Error('Permission denied');return scanResponse([],{truncated:mode==='truncated',warnings:mode==='truncated'?['One folder was unreadable.']:[]});}});
  await page.click('scan-mots');assert.match(page.nodes.get('scan-status').textContent,/Scan failed: Permission denied/);assert.equal(page.nodes.get('scan-mots').disabled,false);
  mode='empty';await page.click('scan-mots');assert.equal(page.nodes.get('scan-empty').classList.contains('hidden'),false);assert.match(page.nodes.get('scan-empty').textContent,/No installed/);
  mode='truncated';await page.click('scan-mots');assert.match(page.nodes.get('scan-status').textContent,/incomplete/);assert.match(page.nodes.get('scan-warnings').textContent,/reached its limit/);assert.match(page.nodes.get('scan-warnings').textContent,/unreadable/);assert.match(page.nodes.get('scan-empty').textContent,/incomplete/);
});
test('running conversion disables scan and every installed-update action',async()=>{
  let resolveConvert;const page=await localUI({scan:async()=>scanResponse([installed(),installed({id:'custom-two'})]),convert:()=>new Promise(resolve=>{resolveConvert=resolve;})});
  await page.click('scan-mots');await page.nodes.get('scan-results').querySelectorAll('button')[0].fire('click');
  const pending=page.click('convert');assert.equal(page.nodes.get('scan-mots').disabled,true);assert.equal(page.nodes.get('queue-outdated').disabled,true);
  for(const button of page.nodes.get('scan-results').querySelectorAll('button'))assert.equal(button.disabled,true);
  await page.click('scan-mots');await page.click('queue-outdated');await page.nodes.get('scan-results').querySelectorAll('button')[1].fire('click');
  assert.equal(page.nodes.get('queue-count').textContent,'1');assert.equal(page.requests.filter(request=>request.path==='/api/scan').length,1);
  resolveConvert({job_id:'test-job'});await pending;assert.equal(page.nodes.get('scan-mots').disabled,false);
});

async function addRecipe(page,id) {
  const picker=page.nodes.get('recipe-picker');picker.value=id;await picker.fire('change');await page.click('add-recipe');
}
test('folder Browse buttons request only their explicit kind and never scan or convert',async()=>{
  const page=await localUI({pick:async({kind})=>({path:'D:\\Chosen\\'+kind})});
  for(const [kind,id] of Object.entries({jk_root:'jk-root',mots_root:'mots-root',output_dir:'output-dir',archive_dir:'archive-dir'})){
    await page.click('browse-'+id);assert.equal(page.nodes.get(id).value,'D:\\Chosen\\'+kind);
    assert.deepEqual(JSON.parse(page.requests.at(-1).options.body),{kind});
  }
  assert.equal(page.requests.filter(request=>request.path==='/api/pick-path').length,4);
  assert.equal(page.requests.filter(request=>request.path==='/api/scan' || request.path==='/api/convert').length,0);
  assert.deepEqual(page.timeouts,[15000,15000,15000]);
});
test('cancelled or failed Browse preserves earlier choices and allows manual path entry',async()=>{
  let fail=false;const page=await localUI({pick:async()=>{if(fail)throw new Error('Desktop dialog unavailable');return {path:null};}});
  await page.click('browse-jk-root');assert.equal(page.nodes.get('jk-root').value,'C:\\JK');assert.match(page.nodes.get('picker-status').textContent,/cancelled/);
  fail=true;await page.click('browse-jk-root');assert.equal(page.nodes.get('jk-root').value,'C:\\JK');assert.equal(page.nodes.get('jk-root').disabled,false);assert.match(page.nodes.get('picker-status').textContent,/paste the path/);assert.match(page.nodes.get('notice-text').textContent,/Desktop dialog unavailable/);
});
test('pending native chooser blocks duplicate pickers, scans, and conversion submission',async()=>{
  let resolvePick;const page=await localUI({pick:()=>new Promise(resolve=>{resolvePick=resolve;})});await addRecipe(page,'stock-one');
  const pending=page.click('browse-jk-root');assert.equal(page.nodes.get('browse-mots-root').disabled,true);assert.equal(page.nodes.get('convert').disabled,true);assert.equal(page.nodes.get('scan-mots').disabled,true);
  await page.click('browse-mots-root');await page.click('scan-mots');await page.click('convert');
  assert.equal(page.requests.filter(request=>request.path==='/api/pick-path').length,1);assert.equal(page.requests.filter(request=>request.path==='/api/convert' || request.path==='/api/scan').length,0);
  resolvePick({path:null});await pending;assert.equal(page.nodes.get('browse-mots-root').disabled,false);assert.equal(page.nodes.get('convert').disabled,false);
});
test('choosing a different MotS folder invalidates the existing read-only scan',async()=>{
  const page=await localUI({scan:async()=>scanResponse([installed()]),pick:async()=>({path:'D:\\Other MotS'})});await page.click('scan-mots');await page.click('browse-mots-root');
  assert.match(page.nodes.get('scan-status').textContent,/folder changed/);assert.equal(page.nodes.get('queue-outdated').disabled,true);
  assert.equal(page.requests.filter(request=>request.path==='/api/scan').length,1);
});
test('a selected custom recipe exposes its original-file chooser and reviewed download page',async()=>{
  const page=await localUI({pick:async()=>({path:'D:\\Downloads\\stone.zip'})});
  assert.equal(page.nodes.get('archive-overrides').children.length,0);await addRecipe(page,'custom-two');
  const sources=page.nodes.get('archive-overrides'),link=sources.querySelectorAll('a')[0];
  assert.equal(link.href,'https://example.org/reviewed-level');assert.equal(link.target,'_blank');assert.equal(link.rel,'noopener noreferrer');assert.match(link.textContent,/Download original/);
  assert.match(sources.textContent,/Download there, then Browse to the saved file/);
  await sources.querySelectorAll('button')[0].fire('click');
  assert.deepEqual(JSON.parse(page.requests.at(-1).options.body),{kind:'original_archive',recipe_id:'custom-two'});
  assert.equal(sources.querySelectorAll('input')[0].value,'D:\\Downloads\\stone.zip');
  assert.equal(page.requests.filter(request=>request.path==='/api/convert').length,0);
});
test('original-file cancellation preserves the previous per-recipe file',async()=>{
  let selected='D:\\Downloads\\stone.zip';const page=await localUI({pick:async()=>({path:selected})});await addRecipe(page,'custom-two');
  await page.nodes.get('archive-overrides').querySelectorAll('button')[0].fire('click');selected=null;
  await page.nodes.get('archive-overrides').querySelectorAll('button')[0].fire('click');
  assert.equal(page.nodes.get('archive-overrides').querySelectorAll('input')[0].value,'D:\\Downloads\\stone.zip');
});
test('a file-picker response cannot attach an archive to a recipe removed from the queue',async()=>{
  let resolvePick;const page=await localUI({pick:()=>new Promise(resolve=>{resolvePick=resolve;})});await addRecipe(page,'custom-two');
  const pending=page.nodes.get('archive-overrides').querySelectorAll('button')[0].fire('click');
  await page.nodes.get('queue-list').querySelectorAll('button')[0].fire('click');resolvePick({path:'D:\\stone.zip'});await pending;
  assert.equal(page.nodes.get('queue-count').textContent,'0');await addRecipe(page,'custom-two');assert.equal(page.nodes.get('archive-overrides').querySelectorAll('input')[0].value,'');
  assert.match(page.nodes.get('picker-status').textContent,/not applied/);
});
test('explicit conversion can use the server default output and the chosen original archive',async()=>{
  const page=await localUI({settings:{jk_root:'C:\\JK',mots_root:'C:\\MotS',archive_dir:'',output_dir:''},pick:async()=>({path:'D:\\Downloads\\stone.zip'})});await addRecipe(page,'custom-two');
  await page.nodes.get('archive-overrides').querySelectorAll('button')[0].fire('click');await page.click('convert');
  const request=page.requests.find(request=>request.path==='/api/convert');assert.ok(request);const payload=JSON.parse(request.options.body);
  assert.equal(payload.output_dir,'');assert.deepEqual(payload.ids,['custom-two']);assert.deepEqual(payload.archives,{'custom-two':'D:\\Downloads\\stone.zip'});
});
test('missing custom original points to its queue chooser before any conversion request',async()=>{
  const page=await localUI({settings:{jk_root:'C:\\JK',mots_root:'C:\\MotS',archive_dir:'',output_dir:''}});await addRecipe(page,'custom-two');await page.click('convert');
  assert.match(page.nodes.get('notice-text').textContent,/Choose the original archive for Stone Sanctuary in your queue/);
  assert.equal(page.requests.filter(request=>request.path==='/api/convert' || request.path==='/api/pick-path').length,0);
});
test('simplified layout keeps optional folders and full card library collapsed initially',()=>{
  assert.match(html,/<details class="advanced-folders" id="advanced-folders">/);assert.match(html,/<details class="catalog-details" id="catalog-details">/);
  assert.ok(html.indexOf('id="recipe-picker"')<html.indexOf('id="installed-panel"'));
  for(const id of ['browse-jk-root','browse-mots-root','browse-output-dir','browse-archive-dir'])assert.match(html,new RegExp('id="'+id+'"'));
});
test('original illustration stays local and the workbench has no audio playback',()=>{
  assert.match(html,/<script defer src="\/ui\/coda-wbw\.js"><\/script>/);assert.match(html,/<img id="coda-art" alt="Original illustration/);
  assert.doesNotMatch(html,/<audio|\bautoplay\b|<embed|<object/i);assert.doesNotMatch(code,/new\s+Audio\b|AudioContext|speechSynthesis/);
});
