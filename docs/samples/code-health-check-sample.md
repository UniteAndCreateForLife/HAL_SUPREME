> **Sample report.** `sample-shop-api` is a made-up demo repository created to show the format; it is not anyone's real project. Real reports are delivered privately.

# Code Health Check: sample-shop-api (a made-up demo repository)

Commit `demo` · 5 tracked files · 2 pinned dependencies checked · generated 2026-09-27

**2 high · 5 medium · 3 low · 1 info**

Read-only audit by HAL SUPREME: nothing in the repository was changed. Findings are automated; each one names where it is and how to fix it.

## Fix first

1. **Script injection: untrusted event text is interpolated into a shell script** (high): Pass the value through an environment variable (env: TITLE: ${{ github.event.issue.title }}) and use "$TITLE" in the script.
2. **Fork pull request code checkout that actions/checkout now refuses (PRT002)** (high): Run fork code on `pull_request` without secrets. Add `allow-unsafe-pr-checkout: true` only when the checked-out files are read as data.
3. **1 Python lint finding that are usually real bugs** (medium): Fix each; most are one-line changes.
4. **2 pinned dependencies have known vulnerabilities** (medium): Upgrade each to a fixed version (the advisory lists it) and re-run the tests.
5. **No tests found** (medium): Start with tests for the most-used paths and run them in CI.

## All findings

### [HIGH] Script injection: untrusted event text is interpolated into a shell script

An issue or PR title, body, branch name or comment is written with ${{ }} straight into a `run:` step, so whoever writes that text can run commands in the job, with its token and secrets.

**Fix:** Pass the value through an environment variable (env: TITLE: ${{ github.event.issue.title }}) and use "$TITLE" in the script.

- `.github/workflows/triage.yml:11 github.event.issue.title`

### [HIGH] Fork pull request code checkout that actions/checkout now refuses (PRT002)

Checks out pull request code (${{ github.event.pull_request.head.sha }}) in a pull_request_target workflow. Since 2026-07-20 actions/checkout@v4 refuses this for pull requests from forks, so this step fails for every fork PR. Do not add allow-unsafe-pr-checkout unless the code is only read as data; prefer running untrusted code in a pull_request workflow. https://github.blog/changelog/2026-06-18-safer-pull_request_target-defaults-for-github-actions-checkout/

**Fix:** Run fork code on `pull_request` without secrets. Add `allow-unsafe-pr-checkout: true` only when the checked-out files are read as data.

- `.github/workflows/preview.yml:9`

### [MEDIUM] 1 Python lint finding that are usually real bugs

Undefined names, redefinitions and syntax errors (ruff's pyflakes rules) fail at run time, often only on the branch that is not tested.

**Fix:** Fix each; most are one-line changes.

- `app/server.py:5 F821 Undefined name `VERSION``

### [MEDIUM] 2 pinned dependencies have known vulnerabilities

These exact versions have published advisories in the OSV database.

**Fix:** Upgrade each to a fixed version (the advisory lists it) and re-run the tests.

- `requirements.txt: aiohttp 3.8.6 (GHSA-2fqr-mr3j-6wp8, GHSA-2vrm-gr82-f7m5, GHSA-3wq7-rqq7-wx6j…): aiohttp: Host-Only Cookies Become Domain Cookies After CookieJar Persistence`
- `requirements.txt: jinja2 2.11.0 (GHSA-cpwx-vrp4-4pq7, GHSA-g3rq-g295-4j3m, GHSA-h5c8-rqwp-cp95…): Jinja2 vulnerable to sandbox breakout through attr filter selecting format method`

### [MEDIUM] No tests found

Nothing checks that a change keeps working.

**Fix:** Start with tests for the most-used paths and run them in CI.

### [MEDIUM] Workflows that never limit their token's permissions

Without a `permissions:` block the GITHUB_TOKEN gets the repository's default, which is write access on many repositories.

**Fix:** Add `permissions: contents: read` at the top and grant more per job only where needed.

- `.github/workflows/preview.yml`
- `.github/workflows/triage.yml`

### [MEDIUM] Workflow runs on pull_request_target, blocked by default on public repos from 2026-11-02 (PRT001)

Triggered by pull_request_target. From 2026-11-02 GitHub blocks this trigger on public repositories unless an Actions policy allows it, and this workflow stops running. Move it to pull_request (plus workflow_run for steps that need write access), or allow the trigger in Settings > Actions > Policies after a review. https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/

**Fix:** Move work that needs no secrets to `pull_request`, and write access to a `workflow_run` workflow; or allow the trigger in an Actions policy after a review.

- `.github/workflows/preview.yml:2`

### [LOW] No license file

Others cannot legally reuse or contribute.

**Fix:** Add a LICENSE (MIT or Apache-2.0 are common).

### [LOW] No automated dependency updates

Vulnerable versions stay until someone notices.

**Fix:** Add .github/dependabot.yml for your package ecosystems and GitHub Actions.

### [LOW] Third-party actions pinned to a tag, not a commit

A tag can be moved to different code after you review it; a commit SHA cannot.

**Fix:** Pin third-party actions to a full commit SHA (with the version in a comment) and let Dependabot update them.

- `.github/workflows/triage.yml: someone/auto-label@v3`

### [INFO] No security policy

Reporters don't know how to report a vulnerability privately.

**Fix:** Add SECURITY.md with a private contact or enable GitHub's private reporting.
