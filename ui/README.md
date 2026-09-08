The Blackwing UI is a local desktop-browser front end for the Python HTTP service. It uses system fonts, plain JavaScript, CSS, and an original inline SVG wing emblem. It loads no fonts, scripts, images, analytics, or other dependencies from an external service. Original-source links are opened only by an explicit user click; external links use `noopener noreferrer`.

Serve `index.html` from the local service, replacing `{{TOKEN}}` in its `blackwing-token` meta element. Serve the two assets at `/ui/styles.css` and `/ui/app.js`. Opening the HTML as a local file does not provide a working backend or security token. All API requests, including GET, carry `X-Blackwing-Token`; requests use same-origin credentials. The server remains responsible for Host/Origin validation, path validation, pinned source verification, and conversion isolation.

The initial selection is always empty. Neither loading settings nor applying filters adds a recipe. The native dropdown adds one eligible item after the user presses Add to queue. Each library card has its own checkbox. Select visible is an explicit bulk action limited to the current search/category/gameplay intersection. Selection persists across filters and is visible in the queue. Queue order follows catalog order. Unsupported content is disabled; a category with no recipes shows an explicit empty state, including singleplayer.

The browser treats recipe status `verified`, `supported`, `ready`, or `available` as eligible. Other or missing status tokens are not eligible. A conversion job locks its selection to avoid accidental changes during submission or execution. A rejected request unlocks the queue. If a submission response is lost, the queue stays locked and reports uncertainty instead of automatically retrying a possibly accepted conversion. A failed progress refresh provides a Retry status button and does not claim that the job stopped.

API contract:

| Method and path | Use |
| --- | --- |
| GET `/api/health` | Connection status; no runtime-compatibility claim. |
| GET `/api/catalog` | `{version,title,recipes:[{id,title,kind,gameplay,author,source_url,archive_hint,requires_archive,summary,status,startup_overlay}]}`. `kind` is `vanilla`, `custom`, or `mod`. |
| GET `/api/settings` | Flat `jk_root`, `mots_root`, `archive_dir`, and `output_dir` strings. A `paths` wrapper is also accepted. Late responses do not overwrite fields the user already edited. |
| POST `/api/settings` | Saves those four path fields; it does not start conversion. |
| GET `/api/recipes/<encoded-id>` | Read-only provenance and transformation details, fetched when the user opens the details dialog. Source and returned JSON are rendered as text. |
| POST `/api/convert` | `{ids,jk_root,mots_root,archive_dir,output_dir,archives:{id:absolutePath}}`; only selected eligible IDs and their relevant archive overrides are sent. Returns `{job_id}`. |
| GET `/api/jobs/<encoded-id>` | `{id,status,progress,total,current,results,logs}`. `progress` means completed recipe count, not a percentage. Results can include `output`, `manifest`, `error`, and `runtime_test`. |
| POST `/api/export` | `{ids}`. The returned asset-free recipe instructions are downloaded as `blackwing-recipes.json` only after the explicit export action. |

Terminal job statuses recognized by the UI are `complete`, `completed`, `done`, `success`, `succeeded`, `failed`, `error`, `cancelled`, `canceled`, and `partial`. The service should supply one of these when a job finishes. Result runtime testing is independent of conversion success: missing evidence and `not-run-on-this-output` display **Runtime test: not run on this output**. Historical catalog validation can appear in the details response and must not be supplied as a successful runtime result for a new output.

The separate Export job report action downloads the returned job JSON, including output/manifest paths and logs. It includes no game assets, but those paths/logs may be private; it performs no upload. The optional updates endpoint is not polled by this UI, and there is no invented game-launch, runtime-test, or archive-download endpoint.

Accessibility includes native form controls, explicit accessible labels, a skip link, visible keyboard focus, restored card-checkbox focus after selection, live count/status announcements, an Escape-dismissable native dialog, a slash shortcut for search outside editable controls, and reduced-motion handling. Layout breakpoints cover narrow windows and phones; the target experience is a desktop browser. These affordances require browser verification in addition to source tests.

Run UI-only tests from the repository root:

```powershell
node --test ui/test_ui.mjs
```

The tests exercise pure selection/filtering/payload logic, runtime-status separation, job-progress bounds, catalog validation, qualified DOM references, token plumbing, injection-safe rendering, empty defaults, and export shape. They launch no HTTP server, browser, converter, or game. Visual layout and actual HTTP job flow are separate integration checks performed against the backend.
