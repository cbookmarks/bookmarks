# Contributing

Thanks for helping other Apple admins find good resources.

## The easy way

Fill in the [submission form](../../issues/new?template=resource-submission.yml). To fix or remove a listing, use the [update form](../../issues/new?template=resource-update.yml).

## What we're looking for

- Useful to people who deploy, manage, secure or support Apple devices
- Actively maintained, or still valuable as a reference
- A direct link: no referral, affiliate, tracking or shortened links
- A one-sentence description of what it does (140 characters at most)

Not a fit: sales pages without technical content, content behind a lead form, and link shorteners.

## Pull requests

Each category is a file in `data/resources/`. Add your entry anywhere in the right file:

```yaml
- name: Installomator
  url: https://github.com/Installomator/Installomator
  subcategory: App management
  description: Installs and updates hundreds of Mac apps straight from the vendor.
  keywords: [patching, app updates, labels]
  platforms: [macOS]
  works_with: [any-mdm]
  cost: open-source
```

Then run `python3 scripts/validate.py --fix`. It sorts the file, applies the standard layout and reports anything that needs fixing. The same check runs on every pull request.

### Fields

| Field | Required | Allowed values |
| --- | --- | --- |
| `name` | Yes | |
| `url` | Yes | Full `https://` address, unique across all files |
| `subcategory` | No | One listed for that category in `data/categories.yaml` |
| `description` | For new entries | Up to 140 characters |
| `keywords` | No | Up to 8 lowercase search terms, for example `[filevault, escrow]`. Used by search, not shown |
| `platforms` | No | `macOS`, `iOS`, `iPadOS`, `tvOS`, `visionOS`, `watchOS` |
| `works_with` | No | `any-mdm`, `jamf`, `intune`, `iru`, `mosyle`, `addigy`, `filewave`, `workspace-one`, `hexnode`, `simplemdm`, `jumpcloud`, `fleet`, `munki` |
| `cost` | No | `free`, `open-source`, `freemium`, `paid` |
| `tags` | No | `apple` (published by Apple itself; shows the Apple badge and the "From Apple" filter), `rss`, `http-only` (for the rare site without https) |
| `added` | No | Date, set automatically for form submissions |
| `submitted_by` | No | Set automatically for form submissions |
| `archived` | No | `true` for projects that are no longer maintained but still worth listing |

### Adding a category or subcategory

Edit `data/categories.yaml`. A new category also needs an empty `data/resources/<id>.yaml` and its name added to the dropdown in `.github/ISSUE_TEMPLATE/resource-submission.yml`; the validator checks that the two lists match.

## For maintainers

1. New submissions arrive as issues labelled `resource-submission`.
2. Check them against the points above. If it's not a fit, close the issue with a short note.
3. If it is, add the `approved` label. A workflow adds the entry and opens a pull request.
4. Check the pull request description: it lists what was filled in automatically and the validation result. Fix anything that's off, adjust the subcategory if needed, and merge. The site updates a few minutes later.

If the workflow can't add the entry (for example, it's already listed), it comments on the issue with the reason.
