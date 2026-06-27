# pw-insight

> Playwright test failure analyser — ownership, plain English reasons, filterable dashboard.  
> No API keys. No internet. Fully local.

[![CI](https://github.com/mandavillivijay/pw-insight/actions/workflows/ci.yml/badge.svg)](https://github.com/mandavillivijay/pw-insight/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pw-insight)](https://pypi.org/project/pw-insight/)
[![Python](https://img.shields.io/pypi/pyversions/pw-insight)](https://pypi.org/project/pw-insight/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

![pw-insight dashboard](docs/screenshot.png)

## What it does

Point it at your Playwright test output and get a self-contained HTML dashboard that shows:

- **Who owns failing tests** — last git author per test file
- **Why tests failed** — plain English, from pattern matching (no LLM, no AI)
- **What kind of failures** — Timeout, Element Not Found, Assertion, Network, Auth, Server, JS Error, Visual Diff
- **Filterable table** — search by test name, filter by owner or category, sort by any column
- **Insights panels** — failures by owner, by category, top 10 most common reasons

## Supported inputs

| Input | Works? | Notes |
|-------|--------|-------|
| `playwright-report/` directory | ✅ | Full directory with `data/` subfolder — default output of `npx playwright test` |
| `.zip` of `playwright-report/` | ✅ | CI artifact downloaded as a zip — must contain the full directory, not just `index.html` |
| `results.json` | ✅ | Generated with `--reporter=json` |
| `index.html` alone | ❌ | Just the viewer shell — test data lives in `data/` alongside it |

> If your CI artifact only contains `index.html`, see [CI setup](#ci-setup) to fix the upload, or add a JSON reporter to get `results.json` instead.

## Install

```bash
pip install pw-insight
```

Or from source:

```bash
git clone https://github.com/mandavillivijay/pw-insight.git
cd pw-insight
pip install .
```

With optional progress bars:

```bash
pip install "pw-insight[progress]"
```

Requires Python 3.9+. Zero external runtime dependencies.

## Usage

### From a CI artifact zip (most common)

Download the `playwright-report` artifact from your CI run — it arrives as a `.zip` file. Pass it directly:

```bash
pw-insight --report playwright-report.zip --output ./pw-insight-report.html
```

> **Note:** the zip must contain the full `playwright-report/` folder structure (i.e. `data/*.zip` inside it), not just `index.html`. See [CI setup](#ci-setup) below.

### From the report directory on the same machine

```bash
pw-insight --report ./playwright-report --repo . --output ./pw-insight-report.html
```

### From a JSON report

```bash
npx playwright test --reporter=json > playwright-report/results.json
pw-insight --report ./playwright-report/results.json --repo . --output ./pw-insight-report.html
```

Then open `pw-insight-report.html` in any browser.

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `--report` | *(required)* | `playwright-report/` directory, `.zip` of it, `index.html`, or `results.json` |
| `--repo` | `.` | Git repository root for ownership lookup |
| `--output` | `./pw-insight-report.html` | Output HTML path |
| `--limit` | *(none)* | Cap the number of failures processed |

### CI setup

For the zip workflow to work your CI must upload the **full** `playwright-report/` directory — not just `index.html`.

**GitHub Actions:**
```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: playwright-report
    path: playwright-report/
```

**GitLab CI:**
```yaml
artifacts:
  paths:
    - playwright-report/
```

Download the artifact → run `pw-insight --report playwright-report.zip` → open the HTML.

## Example output

```
pw-insight v1.0.0
──────────────────────────────
→ Parsing playwright-report... 1,342 tests found
→ Extracting failures... 312 failed
→ Looking up git ownership... done (4 unique authors)
→ Explaining failures... done (local, instant)
→ Generating report...

✓ Report ready: ./pw-insight-report.html

Summary:
  Failed:  312    (23.2%)
  Passed:  1030   (76.8%)
  Authors: 4
  Top failure: Timeout (141 tests)
```

## Failure categories

| Category | Triggered by |
|----------|-------------|
| Timeout | `timeout`, `timed out` |
| Element Not Found | `toBeVisible`, `not visible`, locator not found |
| Assertion Failed | `expect`, `toBe`, `toHave`, `toContain` |
| Network Error | `net::`, `ECONNREFUSED`, navigation timeout |
| Auth Error | 401, 403, unauthorized, forbidden |
| Server Error | 500, internal server error |
| JS Error | `TypeError`, `cannot read`, `undefined is not` |
| Visual Diff | screenshot, visual comparison |
| Other | everything else |

## How it works

```
playwright-report/          (HTML or JSON)
        │
        ▼
   parser.py / html_report_parser.py   — extract failed tests
        │
        ▼
   git_blame.py             — git log --follow per test file
        │
        ▼
   explainer.py             — 24 ordered regex rules → plain English
   categoriser.py           — 8 category rules → badge label
        │
        ▼
   reporter.py              — single self-contained HTML file
```

No network calls are made at any stage. The generated HTML has all CSS and JS inline and works fully offline.

## Contributing

Bug reports and pull requests are welcome.

1. Fork the repo and create a branch from `main`
2. Make your change — keep modules focused, no new runtime dependencies
3. Open a pull request with a clear description of what changed and why

For bugs please use the [bug report template](https://github.com/mandavillivijay/pw-insight/issues/new?template=bug_report.yml).  
For ideas use the [feature request template](https://github.com/mandavillivijay/pw-insight/issues/new?template=feature_request.yml).

## License

[MIT](LICENSE) © Vijay Mandavilli
