/** UI-only tests: no HTTP server, browser, conversion, or game process. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const code=await readFile(new URL('./app.js',import.meta.url),'utf8');
const html=await readFile(new URL('./index.html',import.meta.url),'utf8');
const css=await readFile(new URL('./styles.css',import.meta.url),'utf8');
const ui=await import('data:text/javascript;base64,'+Buffer.from(code).toString('base64'));
const recipes=[
  {id:'stock-one',title:'Stock One',kind:'vanilla',gameplay:['mp'],author:'LucasArts',status:'supported',requires_archive:false},
  {id:'custom-two',title:'Stone Sanctuary',kind:'custom',gameplay:['mp','ctf'],author:'Original Author',summary:'A fortress courtyard.',status:'verified',requires_archive:true},
  {id:'future-sp',title:'Future Story',kind:'custom',gameplay:['sp'],author:'Author',status:'unavailable',requires_archive:true},
  {id:'mod-three',title:'Custom Gameplay',kind:'mod',gameplay:['mp'],author:'Mod Author',status:'ready',requires_archive:true},
];
test('selection is empty without explicit IDs',()=>assert.deepEqual(ui.selectedRecipes(recipes,new Set()),[]));
test('unknown and unavailable status is not selectable',()=>{
  assert.equal(ui.selectable({}),false);assert.equal(ui.selectable({status:'unavailable'}),false);assert.equal(ui.selectable({status:'unreviewed'}),false);
});
test('only declared supported status tokens are selectable',()=>{
  for(const status of ['verified','supported','ready','available'])assert.equal(ui.selectable({status}),true);
});
test('category and mode filters intersect',()=>assert.deepEqual(ui.visibleRecipes(recipes,{kind:'custom',gameplay:'ctf'}).map(r=>r.id),['custom-two']));
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
