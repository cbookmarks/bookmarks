# Community Bookmarks

A searchable, community-curated directory of tools, Apple documentation, blogs, podcasts, conferences and user groups for people who manage Apple devices.

The original `Apple_Community_Bookmarks.html` stays in this repository so existing links keep working. The site's `/bookmarks.html` is the up-to-date version, rebuilt on every change.

## Suggest a resource

Use the [submission form](../../issues/new?template=resource-submission.yml). No git needed. A maintainer reviews it, and once approved it's added automatically. Pull requests are welcome too; see [CONTRIBUTING.md](CONTRIBUTING.md).

## What the site offers

- Search across names, descriptions and domains, with `/` or ⌘K to jump to the search field
- Categories and subcategories, plus filters for GitHub projects and Apple pages
- `/bookmarks.html`: the whole directory as a browser bookmarks file, rebuilt on every change
- `/resources.json`: every resource and category, for scripts and other sites
- Light and dark mode, following the system setting

## How it's built

| Part | Where |
| --- | --- |
| Data, one YAML file per category | `data/resources/` |
| Category names, icons, colours and subcategories | `data/categories.yaml` |
| Page templates (Hugo) | `layouts/` |
| Theme | `assets/css/main.css` |
| Search and filters | `assets/js/app.js` |
| Submit and About pages | `content/` |
| Checks and helper scripts (Python) | `scripts/` |
| Submission form, workflows | `.github/` |

The site is plain [Hugo](https://gohugo.io) with no theme dependency, no Node.js and no build tools beyond the Hugo binary.

### Licence

The resource data (`data/`) is released under [CC0 1.0](LICENSE-DATA): anyone can reuse it without asking. The site code, theme and scripts are under the [MIT licence](LICENSE).

### Run it locally

```sh
brew install hugo
hugo server            # http://localhost:1313
```

Before opening a pull request:

```sh
pip3 install pyyaml
python3 scripts/validate.py --fix
```

### Automation

| Workflow | When | What it does |
| --- | --- | --- |
| `validate.yml` | Every pull request | Checks the data and that the site builds |
| `submission.yml` | `approved` label on a submission issue | Adds the resource, fills in missing details from GitHub and opens a pull request |
| `deploy.yml` | Every push to `main` | Builds the site and publishes it to GitHub Pages |
| `linkcheck.yml` | Mondays | Opens or updates one issue listing broken links |
| Dependabot | Monthly | Keeps the GitHub Actions versions current |

### One-time setup

1. Settings > Pages > Source: **GitHub Actions**.
2. Settings > Actions > General > Workflow permissions: allow GitHub Actions to **create and approve pull requests**.
3. Create the labels `resource-submission`, `resource-update`, `approved` and `broken-links` (GitHub skips form labels that don't exist).
4. Nothing to change when the repository moves: the deploy workflow points the Submit and GitHub links at the repository it builds from.
5. For a custom domain, add it under Settings > Pages and point a CNAME record at `<owner>.github.io`.

### Automatic fill-in

When a submission is approved, `scripts/enrich.py` fills in fields the submitter left empty. For GitHub projects it uses the GitHub API: the About text as description, topics as keywords, the licence and whether the repository is archived. For other sites it shows the site's own description in the pull request as a suggestion, without filling it in, because it is often marketing copy. Everything it did is listed in the pull request for the maintainer to check.

Pull requests opened by `submission.yml` use the default token, so GitHub doesn't run `validate.yml` on them. The validation result is written into the pull request description instead. To get the normal checks, use a GitHub App token in `submission.yml`.
