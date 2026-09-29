# Deploy CYBER TRIAGE to GitHub Pages

This edition can run on GitHub Pages with the same 32 observations, 42 rules, 12 sample scenarios, forward trace, backward proof, priorities, recommendations and case export.

GitHub Pages hosts static HTML, CSS, JavaScript and data files. It cannot run the project's Python server or SWI-Prolog process. The hosted edition therefore executes both inference modes in a browser JavaScript engine, using the original `knowledge.json`. Its engine badge reads **Browser JavaScript rule engine**. The Python and Prolog versions remain available for local use.

## 1. Extract and open the project

Extract the ZIP and open the **cyber-triage** folder in VS Code. You should see `README.md`, `knowledge.json`, `web`, `scripts`, `tests` and `.github` directly inside this folder.

Upload the contents of this folder to your repository root. Do not upload the ZIP itself or put everything inside an extra `cyber-triage` folder in the repository.

## 2. Create a GitHub repository

For a new project, create a repository named **cyber-triage**. Choose **Public** for GitHub Pages on GitHub Free. Add a README during creation so that the `main` branch exists.

If you already have a repository, use it instead. This workflow expects the deployment branch to be `main`. If yours is `master` or another name, change both the `branches: [main]` entry and the `refs/heads/main` condition in `.github/workflows/deploy-pages.yml` to your branch name.

## 3. Enable Pages

In your GitHub repository:

1. Open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Use the workflow included in this ZIP. You do not need to generate another workflow from a template.

You need repository access that allows you to change these settings.

## 4. Upload the updated files

From the repository's **Code** tab, choose **Add file → Upload files**. Drag the extracted project's files and folders into the upload area and commit them to `main`. This includes the updated README.

Check that these paths exist in GitHub after the upload:

| Path in the repository | Purpose |
| --- | --- |
| `.github/workflows/deploy-pages.yml` | Tests, builds and deploys the site |
| `scripts/build_pages.py` | Creates the static `dist/` directory |
| `web/index.html` | Shared interface template |
| `web/app.js` | Interface behavior |
| `web/style.css` | Interface styling |
| `web/engine.mjs` | Browser forward and backward inference |
| `web/runtime.mjs` | Selects browser or local server operation |
| `knowledge.json` | Original facts, rules and references |
| `scenarios.json` | Original fictional demonstrations |
| `tests/test_browser.mjs` | Browser engine and deployment checks |
| `tests/test_engine.py`, `tests/test_http.py` | Existing local engine/API checks |
| `engine.py`, `server.py`, `prolog/main.pl` | Original local engine support |

**The `.github` folder is essential.** If it was missed by your upload, use **Add file → Create new file**, enter `.github/workflows/deploy-pages.yml` as the filename, paste the contents of that file from the extracted ZIP, and commit it.

Alternatively, clone your existing GitHub repository into a separate folder, copy the updated project contents into the clone, then commit and push using VS Code Source Control. Include `.github` and `.gitignore`.

Do not commit exported real incident cases. `dist/` is generated and ignored by Git; GitHub Actions builds it for you.

## 5. Wait for the deployment

1. Open the repository's **Actions** tab.
2. Open **Deploy CYBER TRIAGE to GitHub Pages**.
3. Wait for both **build** and **deploy** to finish successfully.
4. Open the site link shown by the deployment or **Settings → Pages → Visit site**.

For a project repository, the address normally looks like:

```text
https://YOUR_USERNAME.github.io/cyber-triage/
```

Replace `YOUR_USERNAME` with your GitHub username and `cyber-triage` with your repository name. This is an example address; this package has not been deployed to your account yet.

If the first workflow ran before you enabled Pages, enable Pages as described above, then choose **Actions → Deploy CYBER TRIAGE to GitHub Pages → Run workflow**, select `main`, and run it again.

Future commits to `main` run the tests and publish the updated site automatically. You do not need to run `server.py` on your computer for visitors to use the hosted version.

## Check the deployed application

| What to do | What you should see |
| --- | --- |
| Open the site | Engine badge: **Browser JavaScript rule engine** |
| Select **Ransomware on a critical server**, then **Analyze incident** | Critical priority and ransomware indicators |
| Expand **Forward chaining trace** | R07 and supporting priority/action rules |
| Choose the **ransomware** goal and click **Check hypothesis** | A proven proof path for the original sample |
| Set **backup available** to **Unknown** and analyze again | Neither the available-backup nor the missing-backup recovery recommendation is inferred |
| Set **backup available** to **No** and analyze again | The recovery-gap recommendation is supported |
| Choose **Reset case**, then analyze | Unassessed priority; missing evidence stays unknown |
| Open **Knowledge base** and search for **R07** | The ransomware rule is displayed |
| Click **Export case and reasoning** after analysis | A JSON case file downloads to your device |

If you inspect browser Developer Tools → Network, the app initially downloads its JavaScript, styles and JSON data. Clicking Analyze should not send an `/api/analyze` request in this edition.

## Preview the Pages version locally in VS Code

In a terminal opened at the project root, run:

Windows:

```powershell
py -3 scripts/build_pages.py
py -3 -m http.server 9000 --bind 127.0.0.1 --directory dist
```

macOS/Linux:

```bash
python3 scripts/build_pages.py
python3 -m http.server 9000 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:9000/**. Keep that terminal running; press Ctrl+C to stop it. Use the HTTP address rather than double-clicking an HTML file: browser modules and JSON loading require a web server. Rebuild after changing the source files.

To run the original local Python edition instead:

```powershell
py -3 server.py --engine python
```

Then open **http://127.0.0.1:8000/**. For the local Prolog edition, install SWI-Prolog and replace `python` with `prolog` in that command.

## What the workflow does

The workflow checks out your source, installs Python and Node on the GitHub runner, runs the tests, and builds `dist/`. It uploads only eight static files: `index.html`, `app.js`, `style.css`, `engine.mjs`, `runtime.mjs`, `knowledge.json`, `scenarios.json` and `.nojekyll`. It then deploys that artifact using GitHub's Pages actions.

Python and Node are build/test tools on the runner. Visitors need only a modern browser. There are no npm packages, API keys, database settings or external backend services to configure. GitHub supplies the workflow's temporary token automatically.

All asset and data URLs are relative, so the same output works at `/` or a repository path such as `/cyber-triage/`. The repository itself does not need a root `index.html`: the build creates `dist/index.html`, which becomes the deployed site root.

Edit `knowledge.json`, `scenarios.json` or the files in `web/`, then commit to `main` to update the website. The tests intentionally check the current knowledge base's counts and expected scenarios; update those expectations deliberately when you change the knowledge base.

## New and changed files

| Status | Files | Reason |
| --- | --- | --- |
| New | `.github/workflows/deploy-pages.yml` | Automatic build, verification and deployment |
| New | `scripts/build_pages.py` | Produce static files and select browser mode |
| New | `web/engine.mjs` | Run the existing rule logic in the browser |
| New | `web/runtime.mjs` | Load JSON for Pages or use the local API |
| New | `tests/test_browser.mjs` | Check inference parity and static hosting |
| New | `.gitignore` | Exclude generated output, caches and default case exports |
| New | `DEPLOY_GITHUB_PAGES.md` | These setup instructions |
| New | `docs/github-pages-validation.txt` | Observed validation results and limits |
| Updated | `web/index.html`, `web/app.js` | Relative assets, module loading and runtime selection |
| Updated | `server.py`, `tests/test_http.py` | Serve and verify the two new JavaScript modules locally |
| Updated | `README.md` | Explain hosted and local operation |

The knowledge base, scenarios, styles, Python inference engine and Prolog inference source are unchanged.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| No deployment workflow appears | Ensure `.github/workflows/deploy-pages.yml` exists at the repository root, on the default branch, and that Actions is enabled |
| Configure Pages reports that the site is missing | Set **Settings → Pages → Source → GitHub Actions**, then rerun the workflow |
| Workflow cannot find a script or test | Move the project contents to the repository root; remove the accidental extra parent folder |
| Site returns 404 | Check that deployment succeeded and open its exact URL, including the repository path |
| Engine unavailable or empty fields | Check the workflow, reload the deployed URL, and confirm `knowledge.json` and `scenarios.json` return successfully in the Network tab |
| Old layout or engine remains visible | Hard-refresh with Ctrl+F5 after a successful deployment |
| A browser requests `/api/meta` or `/api/analyze` on Pages | You published the source template rather than the generated artifact; use the supplied Actions workflow |
| Actions or deployments are blocked by repository policy | Review the repository's Actions settings and `github-pages` environment rules with its owner |

## Data behavior and verification limits

The hosted app keeps entered observations and results in browser memory. Analysis does not send them to an analysis server; export downloads them to your device. GitHub serves the site files and may log normal website requests. Source-reference links open external websites. Public repository contents, rules and example scenarios are readable by anyone.

Automated validation compares the entire browser-engine result with Python for 6,210 input/goal combinations, excluding only the engine label. It also checks all 12 expected scenarios, all 42 rule firings, explicit No versus Unknown, state isolation, API compatibility and static HTTP loading under a repository subpath. See `docs/github-pages-validation.txt` for the observed results. This does not constitute exhaustive formal verification.

Actual GitHub deployment and interactive browser clicks must be checked after publishing. SWI-Prolog parity remains unverified in the preparation environment because SWI-Prolog was unavailable. If your assessment requires inference to execute in Prolog, demonstrate the local Prolog edition; identify the Pages demonstration as the JavaScript edition.

## Official GitHub references

- [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
