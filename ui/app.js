/* World Between Worlds: local browser UI. No external dependencies or automatic selection. */
const KINDS = {all:'All supported content',levels:'All levels',vanilla:'Vanilla JK',custom:'Custom levels',mod:'Gameplay mods'};
const MODES = {mp:'Multiplayer',ctf:'Capture the flag',sp:'Singleplayer'};
const ELIGIBLE = new Set(['verified','supported','ready','available','prototype']);
const TERMINAL = new Set(['complete','completed','done','success','succeeded','failed','error','cancelled','canceled','partial']);
const SCAN_STATUSES = {current:'Current',update_available:'Update available',newer:'Newer than this catalog',unversioned:'Unversioned',modified:'Modified',unrecognized:'Unrecognized',error:'Could not inspect'};
const PATH_FIELDS = {jk_root:'jk-root',mots_root:'mots-root',output_dir:'output-dir',archive_dir:'archive-dir'};

function validRevision(value) { return Number.isSafeInteger(value) && value>0; }
export function revisionLabel(value, missing='Not recorded') { return validRevision(value)?`wbw_v${value}`:missing; }
export function scanStatusLabel(status) { return Object.hasOwn(SCAN_STATUSES,status)?SCAN_STATUSES[status]:'Unrecognized'; }
export function validateScan(data) {
  if (!data || typeof data.root!=='string' || !Array.isArray(data.results) || !Array.isArray(data.warnings) || typeof data.truncated!=='boolean') throw new Error('The local service returned an invalid folder scan.');
  for (const row of data.results) {
    if (!row || typeof row.path!=='string' || typeof row.filename!=='string' || !Object.hasOwn(SCAN_STATUSES,row.status) || typeof row.can_update!=='boolean' ||
        (row.id!==null && (typeof row.id!=='string' || !row.id)) ||
        (row.installed_revision!==null && !validRevision(row.installed_revision)) || (row.current_revision!==null && !validRevision(row.current_revision))) {
      throw new Error('The local service returned an invalid installed-file result.');
    }
  }
  return data;
}
export function scanUpdateIds(recipes, results, {locked=false,outdatedOnly=false}={}) {
  if (locked) return [];
  const requested=new Set(results.filter(row=>row.can_update===true && (!outdatedOnly || row.status==='update_available')).map(row=>row.id));
  return selectedRecipes(recipes,requested).map(recipe=>recipe.id);
}
export function scanSummary(scan) {
  const errors=scan.results.filter(row=>row.status==='error').length;
  const incomplete=scan.truncated || errors>0;
  return `${incomplete?'Scan incomplete':scan.warnings.length?'Scan complete with warnings':'Scan complete'} · ${scan.results.length} ${scan.results.length===1?'file':'files'} listed${errors?` · ${errors} ${errors===1?'inspection error':'inspection errors'}`:''}.`;
}

export function selectable(recipe) { return ELIGIBLE.has(String(recipe.status || '').toLowerCase()); }
export function requiresCtfMod(recipe) { return Boolean(recipe?.gameplay?.includes('ctf')); }
export function ctfModSummary(recipe) {
  return recipe.startup_overlay==='bridge-ctf-ui'
    ? 'CTF mod required · WBW generates bridge-ctf-ui separately. Every host and client must install and load it to restore the red-flag HUD binding; copying only the level is insufficient.'
    : 'Additional CTF mod required · follow this custom recipe’s reviewed mod and launch requirements in Details. Native MotS Kill the Fool with the Ysalamiri is a different mode.';
}
export function visibleRecipes(recipes, {kind='all',gameplay='all',search=''}={}) {
  const words = search.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return recipes.filter(recipe => (kind==='all' || (kind==='levels' ? recipe.kind!=='mod' : recipe.kind===kind)) &&
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
    if (!recipe || typeof recipe.id!=='string' || !recipe.id || ids.has(recipe.id) || typeof recipe.title!=='string' || !['vanilla','custom','mod'].includes(recipe.kind) || !Array.isArray(recipe.gameplay) || (recipe.revision!==undefined && !validRevision(recipe.revision))) {
      throw new Error('The local service returned an invalid or duplicate recipe.');
    }
    ids.add(recipe.id);
  }
  return data;
}

function start() {
  const $ = id=>document.getElementById(id);
  const state = {recipes:[],selected:new Set(),archives:Object.create(null),dirtyPaths:new Set(),kind:'levels',gameplay:'all',search:'',job:null,jobId:null,jobRunning:false,pollTimer:null,detailRequest:0,scan:null,scanRunning:false,scanRequest:0,scanError:'',scanStale:false,pathPicking:null,pickerStatus:'',settingsSaving:false};
  const el = (tag,className='',text='')=>{const node=document.createElement(tag);if(className)node.className=className;node.textContent=text;return node;};
  const announce = text=>{$('announcements').textContent=text;};
  function ctfInstructions(recipe, generatedPath) {
    const box=el('aside','ctf-requirement');
    if(recipe.startup_overlay!=='bridge-ctf-ui') {
      box.append(el('strong','','Additional CTF mod required'),el('p','',ctfModSummary(recipe)),el('p','',recipe.ctf_instructions || 'This catalog has not supplied custom CTF installation instructions. Do not assume the stock CTF support mod is compatible; this setup needs recipe review before play.'));
      if(generatedPath)box.append(el('span','result-path','Generated mod folder: '+generatedPath));
      return box;
    }
    box.append(el('strong','','Required CTF support mod'),el('p','',`WBW generates ${recipe.startup_overlay} alongside this level. Install and load it on every host and client: the level alone cannot change MotS's startup inventory. This restores the red-flag HUD binding instead of the ysalamiri binding.`));
    if(generatedPath)box.append(el('span','result-path','Generated mod folder: '+generatedPath));
    box.append(el('p','',`Copy the whole ${recipe.startup_overlay} folder beside your MotS runtime's resource and episode folders. Put the selected converted level GOO in episode. From that runtime folder, launch OpenJKDF2 with:`),el('code','ctf-command',`-motsCompat -path ${recipe.startup_overlay}`),el('p','','In Multiplayer, choose the episode whose name starts CTF. Do not choose Kill the Fool with the Ysalamiri. Use matching files on all players. Keep this support mod separate from other mods; restart without -path before playing other modes. See the generated mod README for the full instructions.'));
    return box;
  }
  function notice(message) { $('notice-text').textContent=message;$('notice').classList.remove('hidden'); }
  function errorText(error) { return error instanceof Error ? error.message : String(error); }
  async function api(path, {method='GET',body,timeoutMs=15000}={}) {
    const token=document.querySelector('meta[name="blackwing-token"]')?.content;
    if (!token || token.includes('{{')) throw new Error('The local security token is missing. Reload this page through the World Between Worlds server.');
    const headers={Accept:'application/json','X-Blackwing-Token':token};
    if (method==='POST') {
      headers['Content-Type']='application/json';
    }
    const controller=new AbortController();const timeout=timeoutMs>0?setTimeout(()=>controller.abort(),timeoutMs):null;
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
  function pathChanged(kind) {
    state.dirtyPaths.add(kind);
    if(kind==='mots_root'){state.scanRequest++;state.scanStale=Boolean(state.scan || state.scanRunning);state.scanError='';}
    renderInstalled();
  }
  function renderPathControls() {
    const locked=state.jobRunning || Boolean(state.pathPicking);
    for(const [kind,id] of Object.entries(PATH_FIELDS)) {
      $(id).disabled=locked;
      $('browse-'+id).disabled=locked;
      $('browse-'+id).textContent=state.pathPicking?.kind===kind?'Choosing…':'Browse…';
    }
    $('save-settings').disabled=locked || state.settingsSaving;
    $('picker-status').textContent=state.pickerStatus;
  }
  async function pickPath(kind,recipeId) {
    if(state.jobRunning || state.pathPicking)return;
    const original=kind==='original_archive';
    const recipe=original?selectedRecipes(state.recipes,state.selected).find(row=>row.id===recipeId && row.requires_archive):null;
    if(original?!recipe:!Object.hasOwn(PATH_FIELDS,kind))return;
    const previous=original?state.archives[recipeId] || '':$(PATH_FIELDS[kind]).value;
    if(!original)state.dirtyPaths.add(kind);
    state.pathPicking={kind,recipeId};state.pickerStatus=original?`Choose the original archive for ${recipe.title} in the file window.`:'Choose a folder in the file window. Cancel to keep your existing choice.';renderQueue();
    try {
      const data=await api('/api/pick-path',{method:'POST',body:{kind,...(original?{recipe_id:recipeId}:{})},timeoutMs:0});
      if(!data || (data.path!==null && (typeof data.path!=='string' || !data.path.trim() || data.path.includes('\0'))))throw new Error('The local service returned an invalid file selection.');
      if(data.path===null){state.pickerStatus='Selection cancelled. Your existing choice is unchanged.';return;}
      if(original) {
        if(!state.selected.has(recipeId) || (state.archives[recipeId] || '')!==previous){state.pickerStatus='The queue or file choice changed. The returned file was not applied.';return;}
        state.archives[recipeId]=data.path;state.pickerStatus=`Original archive selected for ${recipe.title}.`;announce(state.pickerStatus);
      } else {
        if($(PATH_FIELDS[kind]).value!==previous){state.pickerStatus='The folder choice changed. The returned folder was not applied.';return;}
        $(PATH_FIELDS[kind]).value=data.path;pathChanged(kind);state.pickerStatus='Folder selected. Save folders to remember this choice.';
      }
    } catch(error) {state.pickerStatus='Browse could not complete. You can paste the path into its field.';notice(errorText(error));}
    finally {state.pathPicking=null;renderQueue();}
  }
  function renderInstalled() {
    const focusedPath=document.activeElement?.dataset?.scanPath;
    const locked=state.jobRunning || state.scanRunning || state.scanStale || Boolean(state.pathPicking);
    $('scan-mots').disabled=state.jobRunning || state.scanRunning || Boolean(state.pathPicking) || !$('mots-root').value.trim();
    $('scan-mots').textContent=state.scanRunning?'Scanning…':'Scan MotS folder';
    $('scan-results').setAttribute('aria-busy',String(state.scanRunning));
    $('scan-results').replaceChildren();$('scan-warnings').replaceChildren();
    $('scan-root').textContent=state.scan?'Scanned folder: '+state.scan.root:'';
    $('scan-status').classList.toggle('result-error',Boolean(state.scanError));
    $('scan-status').textContent=state.scanRunning?'Inspecting installed files…':state.scanError?'Scan failed: '+state.scanError:state.scanStale?'The MotS folder changed. Scan again to compare its installed files.':state.scan?scanSummary(state.scan):'Ready when you are. Choose your MotS folder above, then scan it.';
    $('scan-empty').classList.toggle('hidden',state.scanRunning || Boolean(state.scanError) || !state.scan || state.scan.results.length>0);
    $('scan-empty').textContent=state.scan?.truncated?'No files were listed in this incomplete scan. Review the warnings and try again.':state.scan?.warnings.length?'No installed GOO files were listed. Review the scan warnings.':'No installed GOO files were found in this scan.';
    const outdated=scanUpdateIds(state.recipes,state.scan?.results || [],{outdatedOnly:true});
    const remaining=outdated.filter(id=>!state.selected.has(id));
    $('queue-outdated').classList.toggle('hidden',!outdated.length);
    $('queue-outdated').disabled=locked || !remaining.length;
    $('queue-outdated').textContent=remaining.length?`Queue all outdated (${remaining.length})`:'Outdated recipes queued';
    if (state.scan) {
      if (state.scan.truncated) $('scan-warnings').append(el('li','','The scan reached its limit. These results do not cover every installed file.'));
      for (const warning of state.scan.warnings) $('scan-warnings').append(el('li','',typeof warning==='string'?warning:JSON.stringify(warning)));
      for (const result of state.scan.results) {
        const item=el('article','scan-item'),heading=el('div','scan-item-heading');
        heading.append(el('h3','',result.title || result.filename),el('span','badge'+(result.status==='current'?' supported':result.status==='error'?' error':' warning'),scanStatusLabel(result.status)));
        item.append(heading,el('span','result-path',result.path));
        const revisions=el('p','scan-revisions');revisions.append(el('span','',`Installed: ${revisionLabel(result.installed_revision,result.status==='unversioned'?'Unversioned':'Unknown')}`),el('span','',`Catalog: ${revisionLabel(result.current_revision,'No matching recipe')}`));item.append(revisions);
        if (result.duplicate) item.append(el('p','scan-duplicate','Multiple installed files match this recipe. Review each copy before using a new conversion.'));
        if (result.message) item.append(el('p','scan-message',String(result.message)));
        if (scanUpdateIds(state.recipes,[result]).length) {
          const button=el('button','text-button',state.selected.has(result.id)?'Already queued':'Queue updated recipe');button.type='button';button.disabled=locked || state.selected.has(result.id);button.dataset.scanPath=result.path;button.setAttribute('aria-label',`${state.selected.has(result.id)?'Already queued':'Queue updated recipe for'} ${result.title || result.filename}`);
          button.addEventListener('click',()=>{if(state.scanRunning || state.scanStale || state.jobRunning || state.pathPicking || !scanUpdateIds(state.recipes,[result]).length)return;setSelection(result.id,true);});item.append(button);
        }
        $('scan-results').append(item);
      }
    }
    if(focusedPath && !locked)[...$('scan-results').querySelectorAll('button')].find(button=>button.dataset.scanPath===focusedPath && !button.disabled)?.focus({preventScroll:true});
  }
  async function scanInstalled() {
    const mots_root=$('mots-root').value.trim();
    if (state.jobRunning || state.scanRunning || state.pathPicking || !mots_root) return;
    const request=++state.scanRequest;state.scanRunning=true;state.scan=null;state.scanError='';state.scanStale=false;renderInstalled();
    try {
      const data=validateScan(await api('/api/scan',{method:'POST',body:{mots_root},timeoutMs:120000}));
      if (request!==state.scanRequest) return;
      state.scan=data;announce(scanSummary(data));
    } catch(error) { if(request===state.scanRequest)state.scanError=errorText(error); }
    finally { state.scanRunning=false;renderInstalled(); }
  }
  function renderPicker() {
    const previous=$('recipe-picker').value;
    const noun=state.kind==='mod'?'mod':'level';
    $('recipe-picker').replaceChildren(new Option(`Add a ${noun}…`,''));
    $('recipe-picker-label').textContent=`Add a ${noun} to the queue`;
    $('library-title').textContent=`Choose a ${noun}`;
    $('selection-help').textContent=state.kind==='mod'?'Mods create separate gameplay packages. Choose the original archive in your queue; converting a mod never loads it automatically.':'Choose levels here. Ninja Kage and other gameplay conversions have their own Mods section. Each result stays separate.';
    for (const kind of ['vanilla','custom','mod']) {
      const rows=matching().filter(recipe=>recipe.kind===kind && selectable(recipe));
      if (!rows.length) continue;
      const group=document.createElement('optgroup');group.label=KINDS[kind];
      for (const recipe of rows) {const option=new Option(recipe.title+' · '+revisionLabel(recipe.revision,'Revision unavailable')+(requiresCtfMod(recipe)?' · CTF mod required':'')+(recipe.status==='prototype'?' (prototype)':''),recipe.id);option.disabled=state.selected.has(recipe.id) || state.jobRunning;group.append(option);}
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
    document.querySelectorAll('[data-count]').forEach(node=>{node.textContent=String(visibleRecipes(state.recipes,{kind:node.dataset.count}).filter(selectable).length);});
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
      bottom.append(el('span','badge revision-badge',revisionLabel(recipe.revision,'Revision unavailable')));
      for (const mode of recipe.gameplay) bottom.append(el('span','badge',MODES[mode] || mode));
      const details=el('button','card-details','Details');details.type='button';details.setAttribute('aria-label',`Details for ${recipe.title}`);details.addEventListener('click',()=>showDetails(recipe));bottom.append(details);card.append(bottom);
      if (requiresCtfMod(recipe)) card.append(el('p','overlay-note',ctfModSummary(recipe)+' See Details.'));
      else if (recipe.startup_overlay) card.append(el('p','overlay-note',recipe.kind==='mod'?'Creates a separate mod folder; load it only when you choose.':'Includes a required startup overlay for this map.'));
      $('recipe-list').append(card);
    }
    $('empty-state').classList.toggle('hidden',rows.length>0);
    if (!rows.length) {
      const unavailableMode=state.gameplay!=='all' && !state.recipes.some(recipe=>selectable(recipe) && recipe.gameplay.includes(state.gameplay));
      const unavailableKind=!visibleRecipes(state.recipes,{kind:state.kind}).some(selectable);
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
      const content=el('div','queue-item-content');content.append(el('div','queue-item-title',recipe.title),el('span','queue-item-kind',`${KINDS[recipe.kind]} · ${recipe.gameplay.map(mode=>MODES[mode] || mode).join(', ')} · ${revisionLabel(recipe.revision,'Revision unavailable')}`));
      if(requiresCtfMod(recipe))content.append(el('p','overlay-note',ctfModSummary(recipe)));
      const remove=el('button','remove-item','×');remove.type='button';remove.disabled=state.jobRunning;remove.setAttribute('aria-label',`Remove ${recipe.title} from queue`);remove.addEventListener('click',()=>setSelection(recipe.id,false));item.append(content,remove);$('queue-list').append(item);
    });
    $('clear-selection').disabled=!rows.length || state.jobRunning;
    $('export-selection').disabled=!rows.length;
    $('convert').disabled=!rows.length || state.jobRunning || Boolean(state.pathPicking);
    $('convert').textContent=state.jobRunning?'Conversion in progress…':`Convert selected (${rows.length}) →`;
    $('conversion-hint').textContent=state.jobRunning?'This queue is locked while its job runs.':rows.some(recipe=>recipe.status==='prototype')?'Includes a prototype with the compatibility limits shown in Details. Conversion creates files; it does not launch the game or load a mod.':rows.length?'Uses your original archives. Conversion creates files; it does not launch the game or load a mod.':'Select at least one available recipe.';
    $('archive-overrides').replaceChildren();
    const custom=rows.filter(recipe=>recipe.requires_archive);
    if (custom.length) {
      const sources=el('section','archive-details');sources.append(el('h3','','Choose the originals'),el('p','','For each custom level or mod, choose the original downloaded ZIP or GOB.'));
      for (const recipe of custom) {
        const item=el('div','archive-choice'),label=el('label','',recipe.title),input=document.createElement('input');input.type='text';input.autocomplete='off';input.spellcheck=false;input.value=state.archives[recipe.id] || '';input.placeholder='Browse to the original archive, or paste its path';input.disabled=state.jobRunning || Boolean(state.pathPicking);input.setAttribute('aria-label',`Original archive for ${recipe.title}`);input.dataset.archiveId=recipe.id;input.addEventListener('input',()=>{state.archives[recipe.id]=input.value;});label.append(input);item.append(label);
        const actions=el('div','archive-actions'),browse=el('button','button secondary',state.pathPicking?.recipeId===recipe.id?'Choosing…':'Browse original…');browse.type='button';browse.disabled=state.jobRunning || Boolean(state.pathPicking);browse.dataset.archiveBrowse=recipe.id;browse.setAttribute('aria-label',`Browse for the original archive of ${recipe.title}`);browse.addEventListener('click',()=>pickPath('original_archive',recipe.id));actions.append(browse);
        const source=safeSourceUrl(recipe.source_url);
        if(source){const link=el('a','download-original','Download original ↗');link.href=source;link.target='_blank';link.rel='noopener noreferrer';link.setAttribute('aria-label',`Open the reviewed download page for ${recipe.title}`);actions.append(link);}
        item.append(actions);
        if(source)item.append(el('p','source-help','Download original opens the reviewed source page. Download there, then Browse to the saved file.'));
        if(recipe.archive_hint)item.append(el('p','archive-hint','Reviewed source: '+recipe.archive_hint));
        if(!state.archives[recipe.id] && $('archive-dir').value.trim())item.append(el('p','archive-hint','Or use the original archive folder set in optional settings.'));
        sources.append(item);
      }
      $('archive-overrides').append(sources);
    }
    renderPathControls();renderInstalled();
  }
  async function showDetails(recipe) {
    const request=++state.detailRequest;
    $('detail-title').textContent=recipe.title;$('detail-content').replaceChildren(el('p','',recipe.summary || 'Recipe provenance and conversion details.'));
    $('detail-content').append(el('p','',`Recipe revision: ${revisionLabel(recipe.revision,'Unavailable')}`));
    if(requiresCtfMod(recipe))$('detail-content').append(ctfInstructions(recipe));
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
      const recipe=state.recipes.find(recipe=>recipe.id===result.id);
      const row=el('div','job-result'),heading=el('div','job-result-heading');
      heading.append(el('strong','',recipe?.title || result.id || 'Recipe'),el('span','badge'+(result.error?' error':''),String(result.status || 'pending').replaceAll('_',' ')));row.append(heading);
      row.append(el('p','',runtimeLabel(result)));
      if (result.output) row.append(el('span','result-path','Output: '+result.output));
      if (result.manifest) row.append(el('span','result-path','Manifest: '+result.manifest));
      if (result.error) row.append(el('p','result-error',String(result.error)));
      if (requiresCtfMod(recipe) && result.output && !result.error) row.append(ctfInstructions(recipe,typeof result.startup_overlay==='string'?result.startup_overlay:null));
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
    if(state.jobRunning || state.pathPicking)return;
    const payload=selectionPayload(state.recipes,state.selected,formPaths(),state.archives);
    if(!payload.ids.length)return;
    if(!payload.jk_root || !payload.mots_root) {notice('Choose your Jedi Knight and Mysteries of the Sith folders before converting.');$('setup-panel').open=true;$(!payload.jk_root?'browse-jk-root':'browse-mots-root').focus();return;}
    const missing=selectedRecipes(state.recipes,state.selected).find(recipe=>recipe.requires_archive && !payload.archive_dir && !payload.archives[recipe.id]);
    if(missing) {notice(`Choose the original archive for ${missing.title} in your queue. If you need it, open Download original first.`);[...$('archive-overrides').querySelectorAll('button')].find(button=>button.dataset.archiveBrowse===missing.id)?.focus();return;}
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
  $('reset-filters').addEventListener('click',()=>{state.kind=state.kind==='mod'?'mod':'levels';state.gameplay='all';state.search='';$('search').value='';$('gameplay-filter').value='all';renderLibrary();});
  $('close-details').addEventListener('click',()=>$('recipe-dialog').close());
  $('recipe-dialog').addEventListener('close',()=>{state.detailRequest++;});
  $('settings-form').addEventListener('submit',async event=>{event.preventDefault();if(state.pathPicking || state.jobRunning)return;state.settingsSaving=true;renderPathControls();$('settings-status').textContent='Saving local folder settings…';try {await api('/api/settings',{method:'POST',body:formPaths()});$('settings-status').textContent='Local folder settings saved.';}catch(error){$('settings-status').textContent='Folders were not saved.';notice(errorText(error));}finally{state.settingsSaving=false;renderPathControls();}});
  $('settings-form').addEventListener('input',event=>{if(event.target.name)pathChanged(event.target.name);});
  for(const [kind,id] of Object.entries(PATH_FIELDS))$('browse-'+id).addEventListener('click',()=>pickPath(kind));
  $('scan-mots').addEventListener('click',scanInstalled);
  $('queue-outdated').addEventListener('click',()=>{
    const ids=scanUpdateIds(state.recipes,state.scan?.results || [],{locked:state.jobRunning || state.scanRunning || state.scanStale || Boolean(state.pathPicking),outdatedOnly:true});
    if(!ids.length)return;ids.forEach(id=>state.selected.add(id));renderLibrary();renderQueue();announce(`${ids.length} outdated ${ids.length===1?'recipe':'recipes'} queued. Review your selection, source folders, and output folder before converting.`);
  });
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
  document.addEventListener('keydown',event=>{if(event.key==='/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT','TEXTAREA','SELECT'].includes(event.target.tagName) && !$('recipe-dialog').open){event.preventDefault();$('catalog-details').open=true;$('search').focus();}});
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
    renderInstalled();
  });
}

if (typeof document!=='undefined') start();
