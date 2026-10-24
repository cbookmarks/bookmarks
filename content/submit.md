---
title: Submit a resource
description: Know a tool, blog or documentation page other Apple admins should find? Suggest it here. You don't need to know git.
---

{{< callout title="Fill in the submission form" button="Open the form" href="issues/new?template=resource-submission.yml" >}}
It takes about two minutes and opens on GitHub, so you need a free GitHub account. A maintainer reviews every submission.
{{< /callout >}}

## What makes a good submission

- Useful to people who deploy, manage, secure or support Apple devices, at any scale.
- Actively maintained, or still valuable as a reference.
- A direct link to the project or page, not a referral or affiliate link.
- A one-line description that says what it does, not why it's great.

Not a fit: sales pages without technical content, gated content behind a lead form, and link shorteners.

## What happens next

1. Your submission becomes an issue in the repository.
2. A maintainer checks it against the points above and adds the `approved` label.
3. A GitHub Action adds the resource to the right data file and opens a pull request.
4. Automatic checks confirm the link works, the fields are valid and it isn't already listed.
5. Once the pull request is merged, the site and the bookmarks file update within minutes.
{.steps}

## Prefer a pull request?

Each category is a YAML file in {{< repo "data/resources" "data/resources/" >}}. Add your entry anywhere in the file, then run `python scripts/validate.py --fix` to sort it and check it. Only `name` and `url` are required, but please add a description.

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

The {{< repo "CONTRIBUTING.md" "contribution guide" >}} lists every field and the allowed values.

## Something wrong with a listing?

Report a broken link, an outdated description or an abandoned project with the {{< repo "issues/new?template=resource-update.yml" "update form" >}}.
