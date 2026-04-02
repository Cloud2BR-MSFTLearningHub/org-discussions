# Repository that hosts the discussions (Public)

**Organization:** [Cloud2BR Open Source Microsoft Cloud Sandbox - Learning Hub](https://github.com/Cloud2BR-MSFTLearningHub)

Costa Rica

[![GitHub](https://img.shields.io/badge/--181717?logo=github&logoColor=ffffff)](https://github.com/)
[brown9804](https://github.com/brown9804)

Last updated: 2026-03-04

----------

> This repository is the **home of GitHub Discussions** for the organization.

<details>
<summary>Table of contents</summary>

- [Start here](#start-here)
- [Categories](#categories)
- [Welcome templates](#welcome-templates)
- [Automation](#automation)
- [How we keep discussions useful](#how-we-keep-discussions-useful)

</details>

> E.g: 

<img width="1896" height="782" alt="image" src="https://github.com/user-attachments/assets/313bb41a-d11f-4f19-b5a4-7255a67e40c8" />

Use it to:
- Share announcements and updates
- Ask questions and get help (Q&A)
- Propose ideas and gather feedback
- Host lightweight RFCs / design discussions


## Start here

- **Want to ask a question?** Create a Discussion in [Q&A](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/q-a) and include:
	- What you expected vs what happened
	- Repro steps (or a minimal example)
	- Versions / environment details
- **Have an idea?** Post in [Ideas](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/ideas) with the problem, proposed solution, and trade-offs.
- **Need to report a security issue?** Do **not** post it publicly. Please see [SECURITY.md](SECURITY.md).

## Categories

> The Organization Discussions are organized into a few sections (Community / Product / Support)

The canonical “what goes where” guide lives in [docs/categories.md](docs/categories.md).

Quick pointers:
- [Q&A](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/q-a): clear questions with an accepted answer
- [Support / Troubleshooting](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/support-troubleshooting): longer debugging threads
- [Ideas](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/ideas): proposals and improvements
- [Show and tell](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/show-and-tell): what you built (demos/integrations)
- [Events](https://github.com/orgs/Cloud2BR-MSFTLearningHub/discussions/categories/events): meetups/livestreams/webinars

## Welcome templates

Use these drafts to create and pin a welcome post in each category.

| Category | Template |
|---|---|
| Community / General | [docs/welcome/community-general.md](docs/welcome/community-general.md) |
| Community / Events | [docs/welcome/community-events.md](docs/welcome/community-events.md) |
| Community / Polls | [docs/welcome/community-polls.md](docs/welcome/community-polls.md) |
| Community / Show and tell | [docs/welcome/community-show-and-tell.md](docs/welcome/community-show-and-tell.md) |
| Product / Announcements | [docs/welcome/product-announcements.md](docs/welcome/product-announcements.md) |
| Product / Ideas | [docs/welcome/product-ideas.md](docs/welcome/product-ideas.md) |
| Support / Q&A | [docs/welcome/support-qa.md](docs/welcome/support-qa.md) |
| Support / Support / Troubleshooting | [docs/welcome/support-troubleshooting.md](docs/welcome/support-troubleshooting.md) |

## Automation

| Workflow | Trigger | Purpose | Secrets |
|---|---|---|---|
| [Update Last Modified Date](.github/workflows/update-md-date.yml) | Pull request to main | Stamp changed markdown files with Last updated | `GITHUB_TOKEN` |
| [Use Visitor Counter Logic](.github/workflows/use-visitor-counter.yml) | Pull request to main, manual | Refresh view counter badges and metrics | `TRAFFIC_TOKEN` |

## How we keep discussions useful

- **Search first** (duplicate threads slow everyone down)
- **One topic per thread** (split if it drifts)
- **Use clear titles** (good: “CLI auth fails with 401 on Windows”, bad: “Help!!!”)
- **Close the loop** when solved (summarize the fix and mark the answer if applicable)

> [!IMPORTANT]
> Community & Conduct:
> - By participating, you agree to follow our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
> - If you’re not sure where to ask something, see [SUPPORT.md](SUPPORT.md).

<!-- START BADGE -->
<div align="center">
  <img src="https://img.shields.io/badge/Total%20views-1337-limegreen" alt="Total views">
  <p>Refresh Date: 2026-03-04</p>
</div>
<!-- END BADGE -->
