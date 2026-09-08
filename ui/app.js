/* World Between Worlds: local browser UI. No external dependencies or automatic selection. */
const KINDS = {all:'All supported content',vanilla:'Vanilla JK',custom:'Custom levels',mod:'Gameplay mods'};
const MODES = {mp:'Multiplayer',ctf:'Capture the flag',sp:'Singleplayer'};
const ELIGIBLE = new Set(['verified','supported','ready','available','prototype']);
const TERMINAL = new Set(['complete','completed','done','success','succeeded','failed','error','cancelled','canceled','partial']);

export function selectable(recipe) { return ELIGIBLE.has(String(recipe.status || '').toLowerCase()); }
export function visibleRecipes(recipes, {kind='all',gameplay='all',search=''}={}) {
  const words = search.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return recipes.filter(recipe => (kind==='all' || recipe.kind===kind) &&
    (gameplay==='all' || (recipe.gameplay || []).includes(gameplay)) &&
    words.every(word => [recipe.title,recipe.author,recipe.summary,...(recipe.gameplay || []).map(mode=>MODES[mode] || mode)].join(' ').toLocaleLowerCase().includes(word)));
}
export function selectedRecipes(recipes, ids) { return recipes.filter(recipe=>ids.has(recipe.id) && selectable(recipe)); }
export function selectionPayload(recipes, ids, paths, archives) {
  const selected = selectedRecipes(recipes, ids);
  return {ids:selected.map(recipe=>recipe.id),...Object.fromEntries(['jk_root','mots_root','archive_dir','output_dir'].map(key=>[key,String(paths[key] || '').trim()])),
    archives:Object.fromEntries(selected.filter(recipe=>recipe.requires_archive && String(archives[recipe.id] || '').trim()).map(recipe=>[recipe.id,String(archives[recipe.id]).trim()]))};
}
export function runtimeLabel(result) {
  const test = result.runtime_test ?? result.runtime;
  const status = String(typeof test==='string' ? test : test?.status || '').toLowerCase();
  if (['passed','pass','success','succeeded'].includes(status)) return 'Runtime test: passed';
  if (['failed','fail','error'].includes(status)) return 'Runtime test: failed';
  if (['running','queued','pending'].includes(status)) return 'Runtime test: '+status;
  if (status && !['not_run','not-run','not-run-on-this-output','not_run_on_this_output','none','unavailable'].includes(status)) return 'Runtime test: '+status.replaceAll('_',' ');
  return 'Runtime test: not run on this output';
}
export function jobProgress(job) {
  const total = Math.max(0,Number.isFinite(Number(job.total)) ? Number(job.total) : 0);
  const count = Number.isFinite(Number(job.progress)) ? Number(job.progress) : 0;
  return {total,done:Math.max(0,Math.min(total,count))};
}
export function safeSourceUrl(value) {
  try { const url = new URL(value); return ['https:','http:'].includes(url.protocol) ? url.href : null; } catch { return null; }
}
export function validateCatalog(data) {
  if (!Array.isArray(data.recipes)) throw new Error('The local service returned an invalid recipe catalog.');
  const ids = new Set();
  for (const recipe of data.recipes) {
    if (!recipe || typeof recipe.id!=='string' || !recipe.id || ids.has(recipe.id) || typeof recipe.title!=='string' || !['vanilla','custom','mod'].includes(recipe.kind) || !Array.isArray(recipe.gameplay)) {
      throw new Error('The local service returned an invalid or duplicate recipe.');
    }
    ids.add(recipe.id);
  }
  return data;
}

function start() {
  const $ = id=>document.getElementById(id);
  const state = {recipes:[],selected:new Set(),archives:Object.create(null),dirtyPaths:new Set(),kind:'all',gameplay:'all',search:'',job:null,jobId:null,jobRunning:false,pollTimer:null,detailRequest:0};
  const el = (tag,className='',text='')=>{const node=document.createElement(tag);if(className)node.className=className;node.textContent=text;return node;};
  const announce = text=>{$('announcements').textContent=text;};
  function notice(message) { $('notice-text').textContent=message;$('notice').classList.remove('hidden'); }
  function errorText(error) { return error instanceof Error ? error.message : String(error); }
  async function api(path, {method='GET',body}={}) {
    const token=document.querySelector('meta[name="blackwing-token"]')?.content;
    if (!token || token.includes('{{')) throw new Error('The local security token is missing. Reload this page through the World Between Worlds server.');
    const headers={Accept:'application/json','X-Blackwing-Token':token};
    if (method==='POST') {
      headers['Content-Type']='application/json';
    }
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),15000);
    try {
      const response=await fetch(path,{method,headers,credentials:'same-origin',signal:controller.signal,...(body===undefined?{}:{body:JSON.stringify(body)})});
      let data;
      try { data=await response.json(); } catch { if(response.ok)throw new Error('The local service returned an unreadable response.');data={}; }
      if (!response.ok) {const error=new Error(typeof data.error==='string'?data.error:typeof data.message==='string'?data.message:`Local request failed (${response.status}).`);error.rejected=true;throw error;}
      return data;
    } catch(error) {
      if (error.name==='AbortError') throw new Error('The local service did not respond in time.');
      throw error;
    } finally { clearTimeout(timeout); }
  }
  function formPaths() { return Object.fromEntries(new FormData($('settings-form')).entries()); }
  function matching() { return visibleRecipes(state.recipes,state); }
  function renderPicker() {
    const previous=$('recipe-picker').value;
    $('recipe-picker').replaceChildren(new Option('Add a map or mod…',''));
    for (const kind of ['vanilla','custom','mod']) {
      const rows=matching().filter(recipe=>recipe.kind===kind && selectable(recipe));
      if (!rows.length) continue;
      const group=document.createElement('optgroup');group.label=KINDS[kind];
      for (const recipe of rows) {const option=new Option(recipe.title+(recipe.status==='prototype'?' (prototype)':''),recipe.id);option.disabled=state.selected.has(recipe.id) || state.jobRunning;group.append(option);}
      $('recipe-picker').append(group);
    }
    if ([...$('recipe-picker').options].some(option=>option.value===previous && !option.disabled)) $('recipe-picker').value=previous;
    $('add-recipe').disabled=!$('recipe-picker').value || state.jobRunning;
  }
  function setSelection(id,selected) {
    const recipe=state.recipes.find(row=>row.id===id);
    if (!recipe || !selectable(recipe) || state.jobRunning) return;
    selected?state.selected.add(id):state.selected.delete(id);
    renderLibrary();renderQueue();announce(`${recipe.title} ${selected?'added to':'removed from'} the queue. ${state.selected.size} selected.`);
  }
  function renderLibrary() {
    const focusedRecipe=document.activeElement?.dataset?.recipeId;
    const rows=matching();const eligible=rows.filter(selectable);
    $('recipe-list').replaceChildren();$('recipe-list').setAttribute('aria-busy','false');
    $('result-count').textContent=`${rows.length} ${rows.length===1?'recipe':'recipes'} · ${eligible.length} available`;
    $('category-caption').textContent=KINDS[state.kind]+(state.gameplay!=='all'?` · ${MODES[state.gameplay]}`:'');
    $('select-visible').textContent=`Select visible (${eligible.length})`;
    $('select-visible').disabled=!eligible.length || state.jobRunning;
    document.querySelectorAll('[data-kind]').forEach(button=>{const active=button.dataset.kind===state.kind;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
    document.querySelectorAll('[data-count]').forEach(node=>{node.textContent=String(state.recipes.filter(recipe=>selectable(recipe) && (node.dataset.count==='all' || recipe.kind===node.dataset.count)).length);});
    $('gameplay-note').textContent=state.gameplay==='sp' && !state.recipes.some(recipe=>selectable(recipe) && recipe.gameplay.includes('sp')) ? 'No singleplayer conversion recipes are supported in this catalog.' : 'Availability follows the reviewed recipes in this workbench.';
    for (const recipe of rows) {
      const active=state.selected.has(recipe.id),available=selectable(recipe);
      const card=el('article','recipe-card'+(active?' selected':'')+(!available?' unavailable':''));
      const label=el('label','card-title');const check=document.createElement('input');check.type='checkbox';check.checked=active;check.disabled=!available || state.jobRunning;check.dataset.recipeId=recipe.id;check.setAttribute('aria-label',`Select ${recipe.title}`);
      check.addEventListener('change',()=>setSelection(recipe.id,check.checked));
      const heading=el('div');heading.append(el('h3','',recipe.title),el('p','card-author',recipe.author || KINDS[recipe.kind]));label.append(check,heading);card.append(label);
      if (recipe.summary) card.append(el('p','card-copy',recipe.summary));
      const bottom=el('div','card-bottom');
      const prototype=recipe.status==='prototype';
      bottom.append(el('span','badge'+(available && !prototype?' supported':' warning'),prototype?'Prototype · limited compatibility':available?(recipe.status==='verified'?'Verified recipe':'Supported recipe'):'Unavailable'));
      for (const mode of recipe.gameplay) bottom.append(el('span','badge',MODES[mode] || mode));
      const details=el('button','card-details','Details');details.type='button';details.setAttribute('aria-label',`Details for ${recipe.title}`);details.addEventListener('click',()=>showDetails(recipe));bottom.append(details);card.append(bottom);
      if (recipe.startup_overlay) card.append(el('p','overlay-note',recipe.kind==='mod'?'Creates a separate mod folder; load it only when you choose.':'Includes a required startup overlay for this map.'));
      $('recipe-list').append(card);
    }
    $('empty-state').classList.toggle('hidden',rows.length>0);
    if (!rows.length) {
      const unavailableMode=state.gameplay!=='all' && !state.recipes.some(recipe=>selectable(recipe) && recipe.gameplay.includes(state.gameplay));
      const unavailableKind=state.kind!=='all' && !state.recipes.some(recipe=>selectable(recipe) && recipe.kind===state.kind);
      $('empty-title').textContent=unavailableMode?`${MODES[state.gameplay]} is not available yet`:unavailableKind?`No supported ${KINDS[state.kind].toLowerCase()} yet`:'No matching recipes';
      $('empty-copy').textContent=unavailableMode || unavailableKind?'This category has no supported conversion recipes in the current catalog. Nothing can be queued from it.':'Try a different title or author, or reset your category and gameplay filters.';
    }
    renderPicker();
    if(focusedRecipe && !state.jobRunning)[...$('recipe-list').querySelectorAll('input')].find(input=>input.dataset.recipeId===focusedRecipe)?.focus({preventScroll:true});
  }
  function renderQueue() {
    const rows=selectedRecipes(state.recipes,state.selected);
    $('queue-count').textContent=String(rows.length);
    $('queue-summary').textContent=rows.length?`${rows.length} ${rows.length===1?'recipe':'recipes'} selected. Your queue follows catalog order.`:'Nothing selected. Choose content from the library.';
    $('queue-empty').classList.toggle('hidden',rows.length>0);
    $('queue-list').replaceChildren();
    rows.forEach((recipe,index)=>{
      const item=el('li','queue-item');item.append(el('span','queue-item-index',String(index+1).padStart(2,'0')));
      const content=el('div','queue-item-content');content.append(el('div','queue-item-title',recipe.title),el('span','queue-item-kind',`${KINDS[recipe.kind]} · ${recipe.gameplay.map(mode=>MODES[mode] || mode).join(', ')}`));
      const remove=el('button','remove-item','×');remove.type='button';remove.disabled=state.jobRunning;remove.setAttribute('aria-label',`Remove ${recipe.title} from queue`);remove.addEventListener('click',()=>setSelection(recipe.id,false));item.append(content,remove);$('queue-list').append(item);
    });
    $('clear-selection').disabled=!rows.length || state.jobRunning;
    $('export-selection').disabled=!rows.length;
    $('convert').disabled=!rows.length || state.jobRunning;
    $('convert').textContent=state.jobRunning?'Conversion in progress…':`Convert selected (${rows.length}) →`;
    $('conversion-hint').textContent=state.jobRunning?'This queue is locked while its job runs.':rows.some(recipe=>recipe.status==='prototype')?'Includes a prototype with the compatibility limits shown in Details. Conversion creates files; it does not launch the game or load a mod.':rows.length?'Uses your original archives. Conversion creates files; it does not launch the game or load a mod.':'Select at least one available recipe.';
    const overridesOpen=$('archive-overrides').querySelector('details')?.open || false;
    $('archive-overrides').replaceChildren();
    const custom=rows.filter(recipe=>recipe.requires_archive);
    if (custom.length) {
      const details=el('details','archive-details');details.open=overridesOpen;details.append(el('summary','','Archive overrides (optional)'),el('p','','Leave these blank to use the original archive folder. Enter a full path when an archive is stored elsewhere.'));
      for (const recipe of custom) {
        const label=el('label','',recipe.title),input=document.createElement('input');input.type='text';input.autocomplete='off';input.spellcheck=false;input.value=state.archives[recipe.id] || '';input.placeholder=recipe.archive_hint || 'Full path to the original ZIP';input.disabled=state.jobRunning;input.addEventListener('input',()=>{state.archives[recipe.id]=input.value;});label.append(input);details.append(label);
      }
      $('archive-overrides').append(details);
    }
  }
  async function showDetails(recipe) {
    const request=++state.detailRequest;
    $('detail-title').textContent=recipe.title;$('detail-content').replaceChildren(el('p','',recipe.summary || 'Recipe provenance and conversion details.'));
    if (recipe.author) $('detail-content').append(el('p','',`Original author: ${recipe.author}`));
    const source=safeSourceUrl(recipe.source_url);
    if (source) { const link=el('a','quiet-link','Open original source ↗');link.href=source;link.target='_blank';link.rel='noopener noreferrer';$('detail-content').append(link); }
    const loading=el('p','','Loading recipe provenance…');$('detail-content').append(loading);
    if (!$('recipe-dialog').open) $('recipe-dialog').showModal();
    try {
      const data=await api('/api/recipes/'+encodeURIComponent(recipe.id));
      if (request!==state.detailRequest) return;
      loading.remove();$('detail-content').append(el('h3','','Provenance & transformations'),el('pre','',JSON.stringify(data,null,2)));
    } catch(error) { if(request===state.detailRequest)loading.textContent='Details could not be loaded: '+errorText(error); }
  }
  function renderJob() {
    const job=state.job;if(!job)return;
    $('job-panel').classList.remove('hidden');
    const status=String(job.status || 'queued').toLowerCase();$('job-status').textContent=status.replaceAll('_',' ');$('job-status').className='badge'+(['failed','error'].includes(status)?' error':'');
    const progress=jobProgress(job);$('job-progress').max=progress.total || 1;$('job-progress').value=progress.done;$('job-count').textContent=`${progress.done} / ${progress.total}`;
    const current=state.recipes.find(recipe=>recipe.id===job.current)?.title || job.current;
    $('job-current').textContent=current?String(current):state.jobRunning?'Preparing the queue…':'Job finished. Review the results below.';
    $('job-results').replaceChildren();
    for (const result of Array.isArray(job.results)?job.results:[]) {
      const row=el('div','job-result'),heading=el('div','job-result-heading');
      heading.append(el('strong','',state.recipes.find(recipe=>recipe.id===result.id)?.title || result.id || 'Recipe'),el('span','badge'+(result.error?' error':''),String(result.status || 'pending').replaceAll('_',' ')));row.append(heading);
      row.append(el('p','',runtimeLabel(result)));
      if (result.output) row.append(el('span','result-path','Output: '+result.output));
      if (result.manifest) row.append(el('span','result-path','Manifest: '+result.manifest));
      if (result.error) row.append(el('p','result-error',String(result.error)));
      $('job-results').append(row);
    }
    const log=$('job-log'),atEnd=log.scrollHeight-log.scrollTop-log.clientHeight<30;
    log.textContent=(Array.isArray(job.logs)?job.logs:[]).map(line=>typeof line==='string'?line:JSON.stringify(line)).join('\n');
    if(atEnd)log.scrollTop=log.scrollHeight;
    $('export-report').disabled=false;
  }
  async function pollJob() {
    clearTimeout(state.pollTimer);$('refresh-job').classList.add('hidden');
    try {
      const job=await api('/api/jobs/'+encodeURIComponent(state.jobId));
      if (job.id && job.id!==state.jobId) throw new Error('The local service returned a different job.');
      state.job=job;state.jobRunning=!TERMINAL.has(String(job.status || '').toLowerCase());renderJob();
      if(state.jobRunning)state.pollTimer=setTimeout(pollJob,1200);
      else {renderLibrary();renderQueue();announce('Conversion job finished. Review its results and runtime-test status.');}
    } catch(error) {
      notice('Could not refresh job status. The job may still be running. Use Retry status before starting another conversion. '+errorText(error));
      $('refresh-job').classList.remove('hidden');
    }
  }
  async function convert() {
    if(state.jobRunning)return;
    const payload=selectionPayload(state.recipes,state.selected,formPaths(),state.archives);
    if(!payload.ids.length)return;
    if(!payload.jk_root || !payload.mots_root || !payload.output_dir) {notice('Enter your Jedi Knight, Mysteries of the Sith, and output folders before converting.');$('setup-panel').open=true;$(!payload.jk_root?'jk-root':!payload.mots_root?'mots-root':'output-dir').focus();return;}
    const missing=selectedRecipes(state.recipes,state.selected).find(recipe=>recipe.requires_archive && !payload.archive_dir && !payload.archives[recipe.id]);
    if(missing) {notice(`Provide an original archive folder or an archive override for ${missing.title}.`);$('setup-panel').open=true;$('archive-dir').focus();return;}
    state.jobRunning=true;renderLibrary();renderQueue();$('notice').classList.add('hidden');
    try {
      const response=await api('/api/convert',{method:'POST',body:payload});
      if(typeof response.job_id!=='string' || !response.job_id)throw new Error('The local service did not return a job identifier.');
      state.jobId=response.job_id;state.job={id:response.job_id,status:'queued',progress:0,total:payload.ids.length,results:[],logs:[]};renderJob();
      $('job-heading').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});
      await pollJob();
    } catch(error) {
      if(error.rejected) {state.jobRunning=false;renderLibrary();renderQueue();notice('Conversion request was rejected: '+errorText(error));}
      else {notice('The conversion request could not be confirmed. It may have reached the local service; check its activity before reloading or submitting another queue. '+errorText(error));$('conversion-hint').textContent='Request status is uncertain. This queue stays locked to avoid submitting it twice.';}
    }
  }
  $('dismiss-notice').addEventListener('click',()=>$('notice').classList.add('hidden'));
  $('search').addEventListener('input',event=>{state.search=event.target.value;renderLibrary();});
  $('gameplay-filter').addEventListener('change',event=>{state.gameplay=event.target.value;renderLibrary();});
  $('kind-navigation').addEventListener('click',event=>{const button=event.target.closest('[data-kind]');if(button){state.kind=button.dataset.kind;renderLibrary();}});
  $('recipe-picker').addEventListener('change',()=>$('add-recipe').disabled=!$('recipe-picker').value || state.jobRunning);
  $('add-recipe').addEventListener('click',()=>{const id=$('recipe-picker').value;if(id)setSelection(id,true);});
  $('select-visible').addEventListener('click',()=>{if(state.jobRunning)return;matching().filter(selectable).forEach(recipe=>state.selected.add(recipe.id));renderLibrary();renderQueue();announce(`${state.selected.size} recipes selected.`);});
  $('clear-selection').addEventListener('click',()=>{if(state.jobRunning)return;state.selected.clear();renderLibrary();renderQueue();announce('Selection cleared.');});
  $('reset-filters').addEventListener('click',()=>{state.kind='all';state.gameplay='all';state.search='';$('search').value='';$('gameplay-filter').value='all';renderLibrary();});
  $('close-details').addEventListener('click',()=>$('recipe-dialog').close());
  $('recipe-dialog').addEventListener('close',()=>{state.detailRequest++;});
  $('settings-form').addEventListener('submit',async event=>{event.preventDefault();$('save-settings').disabled=true;$('settings-status').textContent='Saving local folder settings…';try {await api('/api/settings',{method:'POST',body:formPaths()});$('settings-status').textContent='Local folder settings saved.';}catch(error){$('settings-status').textContent='Folders were not saved.';notice(errorText(error));}finally{$('save-settings').disabled=false;}});
  $('settings-form').addEventListener('input',event=>{if(event.target.name)state.dirtyPaths.add(event.target.name);});
  $('convert').addEventListener('click',convert);$('refresh-job').addEventListener('click',pollJob);
  $('export-report').addEventListener('click',()=>{
    if(!state.job)return;
    const blob=new Blob([JSON.stringify({title:'World Between Worlds job report',exported_at:new Date().toISOString(),job:state.job},null,2)+'\n'],{type:'application/json'});
    const url=URL.createObjectURL(blob),link=el('a');link.href=url;link.download='wbw-job-'+String(state.job.id || 'report').replace(/[^a-zA-Z0-9_-]/g,'_')+'.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  $('export-selection').addEventListener('click',async()=>{
    const ids=selectedRecipes(state.recipes,state.selected).map(recipe=>recipe.id);if(!ids.length)return;
    $('export-selection').disabled=true;
    try {
      const data=await api('/api/export',{method:'POST',body:{ids}});
      const blob=new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),link=el('a');
      link.href=url;link.download='wbw-recipes.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);announce('Selected recipe instructions exported. No game assets are included.');
    }catch(error){notice('Recipes could not be exported: '+errorText(error));}
    finally{$('export-selection').disabled=!state.selected.size;}
  });
  document.addEventListener('keydown',event=>{if(event.key==='/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName) && !$('recipe-dialog').open){event.preventDefault();$('search').focus();}});
  renderQueue();
  Promise.allSettled([api('/api/health'),api('/api/catalog'),api('/api/settings')]).then(results=>{
    const [health,catalog,settings]=results;
    $('connection').classList.toggle('connected',health.status==='fulfilled');$('connection').classList.toggle('failed',health.status==='rejected');
    $('connection').replaceChildren(el('i'),document.createTextNode(health.status==='fulfilled'?'Local service connected':'Local service unavailable'));
    if(catalog.status==='fulfilled') {
      try {const data=validateCatalog(catalog.value);state.recipes=data.recipes;if(data.version)$('version').textContent='v'+String(data.version);renderLibrary();}
      catch(error) {notice(errorText(error));$('result-count').textContent='Catalog unavailable';$('recipe-list').setAttribute('aria-busy','false');}
    } else {notice('Could not load the local recipe catalog. '+errorText(catalog.reason));$('result-count').textContent='Catalog unavailable';$('recipe-list').setAttribute('aria-busy','false');}
    if(settings.status==='fulfilled') {const paths=settings.value.paths || settings.value;for(const [key,id] of Object.entries({jk_root:'jk-root',mots_root:'mots-root',archive_dir:'archive-dir',output_dir:'output-dir'})){if(typeof paths[key]==='string' && !state.dirtyPaths.has(key))$(id).value=paths[key];}}
    else notice('Saved folder settings could not be loaded. You can enter them above. '+errorText(settings.reason));
  });
}

if (typeof document!=='undefined') start();
