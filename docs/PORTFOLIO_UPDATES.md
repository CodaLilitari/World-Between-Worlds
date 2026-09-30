# Portfolio update feed

RC7 checks a fixed HTTPS endpoint without GitHub API access or user credentials:

`https://richard-pemberton-research.darkahn.chatgpt.site/downloads/wbw/releases.json`

The initial feed contains RC7. Release candidates accept newer RCs and stable
releases; stable installations ignore prereleases. Normal version comparison,
platform/Python/glibc compatibility, size limits, package/member hashes, safe ZIP
paths, exact file manifests, readiness checks and fallback remain required.

## Publisher contract

The feed has this schema (placeholder values below are not a release):

```json
{
  "schema": 1,
  "repository": "CodaLilitari/World-Between-Worlds",
  "releases": [
    {
      "version": "0.2.0-rc7",
      "prerelease": true,
      "manifest": {"size": 1234, "sha256": "<64 lowercase hexadecimal characters>"}
    }
  ]
}
```

For each version the client derives
`/downloads/wbw/releases/<version>/wbw-release.json`. Keep the existing schema-1
release manifest and repository identity. A package's digest and filename derive
its path: `/downloads/wbw/packages/<sha256>/<filename>`. Metadata never supplies
an alternate URL or execution command. Feed, manifests and packages are served
anonymously from the same exact origin. Redirects are rejected.

Build all three packages from frozen source, inspect them, test the native
launchers, and hash the exact merged manifest. Publish the complete immutable
version directory, hash-addressed packages and feed in one Site deployment.
Do not overwrite a version with different bytes. Update the stable feed only
when all referenced files are ready. Verify the deployed feed and each package
using the actual updater headers and validation code; a browser landing page
or saved Site version is not proof of update delivery.

The feed is bounded to 30 releases. Keep older distributions available through
the release listings and recorded hashes. HTTPS and control of this fixed Site
are the trust boundary; these hashes are integrity checks, not an independent
publisher signature. GitLab/GitHub remain additional distribution routes.

## Existing installations

RC6 and earlier still check GitHub. Users must download RC7 manually, extract
it into a new folder, launch that copy, and point their shortcut to it. A remote
feed cannot redirect an old launcher's compiled trust policy. Settings, selected
game installations and generated conversions are not replaced by the upgrade.
The new launcher can still run offline or with `--no-update`.

Program versions and map recipe revisions remain separate. This updater change
does not alter map payloads, make blocked candidates selectable, or replace
runtime qualification of any level or mod.
