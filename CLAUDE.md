# Robertwlt03: working notes for Claude

## Toolchain

- Markdown and SVG only: README.md is the GitHub profile of Robertwlt03.
- markdown-graphics draws the intro (`docs/pictures`, pinned to a tag in CI); `scripts/pictures.py`
  draws with its pieces the project cards (`docs/projects.json`: apps wide, libraries two to a
  row), the stack (`docs/stack.json`: each name with its homepage, its
  icon from skillicons.dev in `assets/stack/`; one picture per icon, each a link) and the hobby
  and contact pills (`docs/chips.json`), and writes their Markdown between the `<!-- projects -->`,
  `<!-- stack -->`, `<!-- hobbies -->` and `<!-- contact -->` markers. Section icons:
  `markdown-graphics icon <name> blue <glyph>`, all in blue. The PC CADDIE logo is drawn by hand.

## Commands

- Redraw the pictures: `markdown-graphics pictures`, in the root
- Redraw the project cards, the stack and the pills: `python3 scripts/pictures.py`, in the root
  (after `markdown-graphics pictures`; it joins the phone intro's light and dark drawings)
- Phones (500 pixels and less) get `<name>-phone.svg` for the intro and the cards: both themes
  in one file, as GitHub's light and dark switch would drop a screen-width condition
- All checks, as CI runs them: `check-pipeline` (check-pipeline.toml)

## Hard rules

- English everywhere; texts speak for Robert in the first person.
- Every picture shows in light and dark (`<picture>`), and its alt text holds all of its words.
- Images live in this repository, never in another one that might move or be deleted.
- No address, number or account beyond the contact section's.

## Where things go

- The profile: `README.md`; pictures: `docs/pictures/*.json`, `docs/projects.json` and
  `docs/chips.json` →
  `assets/pictures/`; never edit the Markdown between the markers by hand
- Section icons: `assets/icons/`; stack icons, a light and a dark file each: `assets/stack/`

## Before every commit

Redraw the pictures if a description, a project or its status changed, or once a repository went
public or grew; run `check-pipeline`, and look at the profile in
GitHub's light and dark mode.

## Git

- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:` …).
