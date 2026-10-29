# Evidence guide

The committed successful-run directory contains reviewed historical lab results:
metrics, logs, three firing/resolved alert pairs, chart versions and pod diagnostics.
The screenshots directory contains workflow and dashboard captures.

New workflow artifacts use a fresh artifacts/runtime directory and record run.json
(commit, run URL and attempt). Keep that metadata with every newly curated run.
Existing historical results predate this metadata format.

Only preserve results from a successful run as successful evidence. Review artifacts
for secrets before committing them. Empty resolved query results prove absence of
firing series; stronger new checks also save healthy scrape/traffic responses.
Slack notification delivery has not been tested.

To replace a saved run, back up the old folder outside the repository, then extract
one fresh successful artifact into evidence/successful-run. Do not merge multiple
runs or recursively nest previous artifacts. Copy its dashboard screenshot into
evidence/screenshots for the README.
