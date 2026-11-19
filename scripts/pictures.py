#!/usr/bin/env python3
"""Draws the profile's project cards, stack and pills, light and dark, with their Markdown.

Start:  python3 scripts/pictures.py, in the profile's root
Needs:  Python 3.13 or newer and markdown-graphics, whose fonts, colors and SVG pieces it uses
docs/projects.json lists the apps, drawn as wide cards one to a row, and the libraries, drawn as
small cards two to a row; every card links to its repository.
docs/stack.json lists the stack's rows, each name with its homepage and its icon in assets/stack/;
every icon is a picture of its own, so it can link to that homepage.
docs/chips.json lists the hobbies and the contact links, drawn as pills.
Phones get pictures of their own for the intro and the cards (assets/pictures/<name>-phone.svg):
GitHub's switch between light and dark rewrites every condition that names a color scheme, which
would drop a screen width with it, so a phone's picture holds both and picks one itself.
The pictures go to assets/pictures/<name>-light.svg and -dark.svg, and the Markdown that shows
them replaces what stands between <!-- projects --> and <!-- /projects --> in the README (and the
same for stack and each group of pills), so the alt texts always carry the pictures' words.
"""

import json
import re
from html import escape
from pathlib import Path

from console_look import SUCCESS, frame, heading
from markdown_graphics.banners import embedded
from markdown_graphics.pictures import (LETTER, THEMES, WIDTH, glyph_shapes, svg, text, tile,
                                        wrapped)

# MARK: Settings

OWNER = "Robertwlt03"
PROJECTS = Path("docs/projects.json")
CHIPS = Path("docs/chips.json")
STACK, ICONS = Path("docs/stack.json"), Path("assets/stack")
OUT = Path("assets/pictures")
README = Path("README.md")
# An app's card spans the page with its glyph; a library's takes half of it, two to a row.
# Sizes are font sizes, baselines count from the card's top, and `bottom` lies below the last line;
# the status chip and the languages stand right on the name's line, or below the name and below
# the sentence. The keys match the groups in docs/projects.json.
# Cards side by side are shown at exactly 50% each and keep `gap` free between them inside their
# pictures, so their outer edges line up with the wide cards and every gap looks the same.
LOOKS = {
    "apps": dict(width=WIDTH, padding=22, glyph=48, name_size=20, name_baseline=50,
                 sentence_size=14.5, sentence_baseline=76, line=21, bottom=24, corner=14,
                 per_row=1, gap=0, chip="right", languages="right"),
    "libraries": dict(width=440, padding=18, glyph=0, name_size=15, name_baseline=34,
                      sentence_size=13, sentence_baseline=58, line=18, bottom=20, corner=10,
                      per_row=2, gap=44, chip="right", languages="right"),
}
# The same cards on a phone, drawn about as wide as they show there, so their text keeps its size:
# an app's as wide as the phone's page, a library's half of it, upright.
PHONE_LOOKS = {
    "apps": LOOKS["apps"] | {"width": 343, "padding": 14, "glyph": 36, "name_size": 16,
                             "name_baseline": 33, "sentence_size": 13, "sentence_baseline": 55,
                             "line": 18, "bottom": 16, "corner": 12, "languages": "below"},
    "libraries": LOOKS["libraries"] | {"width": 172, "padding": 12, "name_size": 13,
                                       "name_baseline": 25, "sentence_size": 11.5,
                                       "sentence_baseline": 72, "line": 15, "bottom": 14,
                                       "gap": 12, "chip": "below", "languages": "below"},
}
PHONE = "(max-width: 500px)"  # the screens that get the phone pictures
PHONE_PICTURES = ["intro"]  # drawn by markdown-graphics from <name>-phone.json, light and dark
CHIP_HEIGHT, CHIP_SIZE, LANGUAGE_SIZE = 22, 12, 12.5
# The stack: a row title's picture, an icon, and an icon's picture with its name below it.
TITLE_WIDTH, TITLE_HEIGHT, STACK_ICON, STACK_STEP, STACK_HEIGHT = 124, 34, 44, 84, 68
# GitHub's README is 712 pixels wide, enough for the longest row with its title beside it, from a
# window of 1146 pixels on (measured on the profile page: below, the sidebar or the phone's margins
# take the room), so wider windows show the titles beside the rows and narrower ones above them.
BESIDE, ABOVE = "(min-width: 1150px)", "(max-width: 1149px)"
BLANK = "blank.svg"  # one transparent pixel, which a title shows where it is not wanted
# GitHub's own colors for the languages (github-linguist), for the dots on the project cards.
COLORS = {
    "Swift": "#F05138", "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "Java": "#B07219", "Shell": "#89E051", "Markdown": "#083FA1",
}
UNKNOWN_COLOR = "#8E8E93"
# Simple Icons' Discord logo (CC0), in its own 24-point grid.
DISCORD = ("M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 "
           "0-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 "
           "0-.617-1.25.077.077 0 0 0-.079-.037A19.74 19.74 0 0 0 3.677 4.37a.07.07 0 0 "
           "0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 "
           "5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 "
           "0-.041-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 "
           ".372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 "
           ".078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.3 12.3 0 0 "
           "1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 "
           ".084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 "
           ".032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 "
           "0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 "
           "2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 "
           "0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 "
           "2.418z")
PILL_HEIGHT, PILL_PADDING, PILL_GLYPH, PILL_TEXT_SIZE = 32, 12, 16, 14
# Glyphs beyond markdown-graphics' own, in its style: strokes in a 24-point grid. A filled one
# names its color {ink}.
GLYPHS = {
    "pie": '<path d="M11 4.5a7.5 7.5 0 1 0 7.5 7.5H11z"/>'
           '<path d="M14 2.5a7.5 7.5 0 0 1 7.5 7.5H14z"/>',
    "spark": '<path d="M12 3v6M12 15v6M3 12h6M15 12h6M5.6 5.6l4.2 4.2M14.2 14.2l4.2 4.2'
             'M18.4 5.6l-4.2 4.2M9.8 14.2l-4.2 4.2"/>',
    "discord": '<path transform="translate(2.4 2.4) scale(.8)" fill="{ink}" stroke="none" '
               'fill-rule="evenodd" d="' + DISCORD + '"/>',
    "headphones": '<path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3.5" y="14" width="4" '
                  'height="6.5" rx="1.5"/><rect x="16.5" y="14" width="4" height="6.5" rx="1.5"/>',
    "plane": '<path d="M20.5 3.5L3.5 10.5l7 3 3 7z"/><path d="M10.5 13.5l10-10"/>',
    "tv": '<rect x="3" y="6.5" width="18" height="12.5" rx="2.5"/>'
          '<path d="M8.5 3l3.5 3.5L15.5 3"/>',
    "gamepad": '<path d="M8 7.5h8a4.5 4.5 0 0 1 4.5 4.5v1.8a3.2 3.2 0 0 1-5.8 1.9L13.4 14h-2.8'
               'l-1.3 1.7A3.2 3.2 0 0 1 3.5 13.8V12A4.5 4.5 0 0 1 8 7.5z"/>'
               '<path d="M8 10v3.4M6.3 11.7h3.4M15.4 10.6h.01M17 12.6h.01"/>',
    "trend": '<path d="M3.5 17l5.5-5.5 4 4 7.5-8"/><path d="M15 7.5h5.5V13"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5L12 13l8.5-6.5"/>',
    "instagram": '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" '
                 'r="4"/><path d="M17 7h.01"/>',
}


def color(language: str) -> str:
    return COLORS.get(language, UNKNOWN_COLOR)


def shapes(glyph: str, ink: str) -> str:
    """The SVG shapes of a glyph of this profile or of markdown-graphics, filled ones in `ink`."""
    return GLYPHS[glyph].replace("{ink}", ink) if glyph in GLYPHS else glyph_shapes(glyph)


# Shares of the font size the system font's letters take, measured in a browser: narrow ones,
# wide ones, and all others. Close to 4% for the profile's words; text drawn with the estimate as
# its length is fitted to it, so it never runs into what sits beside it.
NARROW_LETTERS, WIDE_LETTERS = frozenset("ijlrtf.,:;'!|()I "), frozenset("mwMW@")
NARROW_SHARE, WIDE_SHARE, LETTER_SHARE = 0.32, 0.87, 0.58


def width_of(words: str, size: float) -> float:
    """How wide a line of the picture's font is, about; see NARROW_LETTERS."""
    return size * sum(NARROW_SHARE if letter in NARROW_LETTERS else
                      WIDE_SHARE if letter in WIDE_LETTERS else LETTER_SHARE for letter in words)


# MARK: Drawing


def slug(name: str) -> str:
    """A name as its files are named: only its small letters and digits."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def stack_title(title: str, height: float, baseline: float, theme: str) -> str:
    """A row's title: on a line of its own above the row, or as high as its icons beside them."""
    return svg(TITLE_WIDTH, height, title,
               [text(0, baseline, title, 14, THEMES[theme]["muted"], 600)])


def stack_item(name: str, theme: str) -> str:
    """One icon of the stack, its light or dark file, with its name below."""
    icon = ICONS / f"{slug(name)}-{theme}.svg"
    return svg(STACK_STEP, STACK_HEIGHT, name,
               [embedded(icon, (STACK_STEP - STACK_ICON) / 2, 0, STACK_ICON),
                text(STACK_STEP / 2, 62, name, 12, THEMES[theme]["text"], anchor="middle")])


def framed_width(look: dict) -> float:
    """The card's frame, without its share of the gap to the card beside it."""
    return look["width"] - look["gap"] / 2


def text_left(look: dict) -> float:
    """Where the name and the sentence start: right of the glyph, if the card has one."""
    return look["padding"] + (look["glyph"] + 16 if look["glyph"] else 0)


def sentence_lines(project: dict, look: dict) -> list[str]:
    return wrapped(project["text"], framed_width(look) - text_left(look) - look["padding"],
                   LETTER * look["sentence_size"] / 13.5)


def card(project: dict, look: dict, lines: int, column: int, theme: str) -> str:
    """A framed card: the glyph (apps only), the name, on the right its languages and status, and
    below the sentence. Every card of a kind leaves room for `lines` lines, so they all match;
    a card right of another leaves its share of the gap on its left, the others on their right."""
    colors = THEMES[theme]
    width, padding, name_baseline = framed_width(look), look["padding"], look["name_baseline"]
    left, languages = text_left(look), project["languages"]
    last_line = look["sentence_baseline"] + (lines - 1) * look["line"]
    below = look["languages"] == "below"
    languages_baseline = last_line + look["line"] + 6 if below else name_baseline - 1
    height = max(last_line, languages_baseline) + look["bottom"]
    body = [f'<rect x=".5" y=".5" width="{width - 1:g}" height="{height - 1:g}" '
            f'rx="{look["corner"]}" fill="none" stroke="{colors["edge"]}"/>',
            text(left, name_baseline, project["name"], look["name_size"], colors["text"], 600)]
    if look["glyph"]:
        body.append(tile(padding, padding, shapes(project["glyph"], colors["chip_text"]), colors,
                         look["glyph"]))
    body += [text(left, look["sentence_baseline"] + row * look["line"], line,
                  look["sentence_size"], colors["muted"])
             for row, line in enumerate(sentence_lines(project, look))]
    chip = width_of(project["status"], CHIP_SIZE) + 20
    if look["chip"] == "below":
        body += status_chip(project["status"], left, name_baseline + 8, chip, colors)
        right = width - padding
    else:
        right = width - padding - chip
        body += status_chip(project["status"], right, name_baseline - 16, chip, colors)
    start = left if below else right - 14 - marks_width(languages)
    body += language_marks(languages, start, languages_baseline, colors)
    shift = look["width"] - width if column else 0
    return svg(look["width"], height, alt_of(project),
               [f'<g transform="translate({shift:g} 0)">', *body, "</g>"])


def status_chip(status: str, left: float, top: float, width: float, colors: dict) -> list[str]:
    """A version such as v0.1.0 in the accent's chip; any other status, like rebuilding, quiet."""
    released = status.startswith("v")
    return [f'<rect x="{left:.1f}" y="{top:g}" width="{width:.1f}" height="{CHIP_HEIGHT}" '
            f'rx="{CHIP_HEIGHT / 2:g}" fill="{colors["chip" if released else "bar"]}"/>',
            text(left + width / 2, top + 15.5, status, CHIP_SIZE,
                 colors["chip_text" if released else "muted"], 600, "middle")]


def marks_width(languages: list[str]) -> float:
    """How wide language_marks draws the languages, gaps between them included."""
    return (sum(14 + width_of(language, LANGUAGE_SIZE) for language in languages)
            + 14 * (len(languages) - 1))


def language_marks(languages: list[str], left: float, baseline: float, colors: dict) -> list[str]:
    """Each language as a dot in its color and its name, from left to right; the names are fitted
    to their estimated width, so the next dot never runs into them."""
    body = []
    for language in languages:
        wide = width_of(language, LANGUAGE_SIZE)
        body += [f'<circle cx="{left + 5:.1f}" cy="{baseline - 4.5:g}" r="5" '
                 f'fill="{color(language)}"/>',
                 text(left + 14, baseline, language, LANGUAGE_SIZE, colors["muted"],
                      length=wide)]
        left += 14 + wide + 14
    return body


def inside(drawing: str) -> str:
    """What an SVG holds, without its own <svg> tag."""
    return drawing[drawing.index(">", drawing.index("<svg")) + 1:drawing.rindex("</svg>")]


def both_themes(light: str, dark: str) -> str:
    """One SVG that shows its light or its dark drawing, as the reader's system is set."""
    head = light[:light.index(">", light.index("<svg")) + 1]
    return (f'{head}<style>.dark{{display:none}}@media (prefers-color-scheme: dark)'
            f'{{.light{{display:none}}.dark{{display:inline}}}}</style>'
            f'<g class="light">{inside(light)}</g><g class="dark">{inside(dark)}</g></svg>\n')


def pill(item: dict, theme: str) -> str:
    """A pill in the accent's pale color: the glyph and the text, both in the accent."""
    colors = THEMES[theme]
    wide = width_of(item["text"], PILL_TEXT_SIZE)
    width = PILL_PADDING + PILL_GLYPH + 8 + wide + PILL_PADDING
    ink, scale = colors["chip_text"], PILL_GLYPH / 24
    body = [f'<rect width="{width:.1f}" height="{PILL_HEIGHT}" rx="{PILL_HEIGHT / 2:g}" '
            f'fill="{colors["chip"]}"/>',
            f'<g transform="translate({PILL_PADDING} {(PILL_HEIGHT - PILL_GLYPH) / 2:g}) '
            f'scale({scale:g})" fill="none" stroke="{ink}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{shapes(item["glyph"], ink)}</g>',
            text(PILL_PADDING + PILL_GLYPH + 8, PILL_HEIGHT / 2 + 5, item["text"], PILL_TEXT_SIZE,
                 ink, 500, length=wide)]
    return svg(width, PILL_HEIGHT, pill_alt(item), body)


def pill_alt(item: dict) -> str:
    return f"{item['label']}: {item['text']}" if "label" in item else item["text"]


def alt_of(project: dict) -> str:
    return (f"{project['name']}: {project['text']} Built with {', '.join(project['languages'])}; "
            f"{project['status']}.")


def save(name: str, draw, *details) -> None:
    """Draws one picture in every theme; `draw` gets `details` and the theme's name."""
    for theme in THEMES:
        (OUT / f"{name}-{theme}.svg").write_text(draw(*details, theme))


def save_phone(name: str, draw, *details) -> None:
    """Draws the picture a phone shows, both themes in one; see both_themes."""
    drawn = [draw(*details, theme) for theme in THEMES]
    (OUT / f"{name}-phone.svg").write_text(both_themes(*drawn))


# MARK: Markdown


def picture(name: str, alt: str, width: str = "", screens: tuple = ()) -> str:
    """A picture GitHub shows light or dark, as the reader's page is; without a width, at its own
    size. `screens` are (condition, file) pairs that come first: a screen that meets one shows that
    file, whatever the theme, as GitHub rewrites only the conditions that name a color scheme."""
    sized = f' width="{width}"' if width else ""
    first = "".join(f'<source media="{condition}" srcset="{OUT.as_posix()}/{file}">'
                    for condition, file in screens)
    return (f'<picture>{first}<source media="(prefers-color-scheme: dark)" '
            f'srcset="{OUT.as_posix()}/{name}-dark.svg"><img alt="{escape(alt)}" '
            f'src="{OUT.as_posix()}/{name}-light.svg"{sized}></picture>')


def pills_markdown(group: str, items: list[dict]) -> str:
    """Every pill of a group in one line, each a link where it has one; a narrow page wraps it."""
    pictures = [(item, picture(f"{group}-{number}", pill_alt(item)))
                for number, item in enumerate(items, 1)]
    return " ".join(f'<a href="{escape(item["link"])}">{shown}</a>' if "link" in item else shown
                    for item, shown in pictures)


def cards_markdown(projects: list[dict], look: dict) -> list[str]:
    """Every card as a link to its repository, `per_row` of them to a paragraph, with nothing
    between them: their pictures hold the gap, and a space would push the second one down."""
    step, links = look["per_row"], []
    for project in projects:
        name = f"project-{project['name']}"
        shown = picture(name, alt_of(project), f"{100 // step}%", ((PHONE, f"{name}-phone.svg"),))
        links.append(f'<a href="https://github.com/{OWNER}/{project["name"]}">{shown}</a>')
    return ["".join(links[start:start + step]) for start in range(0, len(links), step)]


def stack_markdown(rows: dict) -> str:
    """Each row its title on a line of its own, then its title again beside its icons, each icon a
    link to its homepage; on a wide window the first title is blank, on a narrow one the second,
    so the rows read like a table where they fit and wrap into the same columns where not."""
    return "<br>".join(
        picture(f"stack-above-{slug(title)}", title, screens=((BESIDE, BLANK),)) + "<br>"
        + picture(f"stack-beside-{slug(title)}", "", screens=((ABOVE, BLANK),))
        + "".join(f'<a href="{escape(link)}">{picture(f"stack-{slug(name)}", name)}</a>'
                  for name, link in links.items())
        for title, links in rows.items())


def draw_cards(projects: list[dict], look: dict, saving) -> None:
    """Every card of a kind in one look, all as high as the one with the longest sentence."""
    lines = max((len(sentence_lines(project, look)) for project in projects), default=1)
    for number, project in enumerate(projects):
        saving(f"project-{project['name']}", card, project, look, lines, number % look["per_row"])


def with_block(readme: str, name: str, markup: str) -> str:
    """The README with `markup` between the <!-- name --> and <!-- /name --> lines."""
    start, end = f"<!-- {name} -->\n", f"<!-- /{name} -->"
    head, opened, rest = readme.partition(start)
    _, closed, tail = rest.partition(end)
    if not (opened and closed):
        raise SystemExit(f"{README} needs the lines {start.strip()} and {end}.")
    return f"{head}{start}{markup}\n{end}{tail}"


# MARK: Run


def main() -> None:
    heading(f"{OWNER} · pictures", str(OUT))
    groups = json.loads(PROJECTS.read_text())
    rows = json.loads(STACK.read_text())
    paragraphs = [paragraph for kind, projects in groups.items()
                  for paragraph in cards_markdown(projects, LOOKS[kind])]
    readme = with_block(README.read_text(), "projects", "\n\n".join(paragraphs))
    readme = with_block(readme, "stack", stack_markdown(rows))
    chips = json.loads(CHIPS.read_text())
    for group, items in chips.items():
        readme = with_block(readme, group, pills_markdown(group, items))
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):  # a project or pill that left its list leaves no picture behind
        if old.name.startswith(("project-", "stack-", *chips)):
            old.unlink()
    for kind, projects in groups.items():
        draw_cards(projects, LOOKS[kind], save)
        draw_cards(projects, PHONE_LOOKS[kind], save_phone)
    for name in PHONE_PICTURES:  # markdown-graphics drew them, one file for each theme
        drawn = [(OUT / f"{name}-phone-{theme}.svg").read_text() for theme in THEMES]
        (OUT / f"{name}-phone.svg").write_text(both_themes(*drawn))
    for group, items in chips.items():
        for number, item in enumerate(items, 1):  # by place, as two pills may share a glyph
            save(f"{group}-{number}", pill, item)
    (OUT / BLANK).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>\n')
    for title, links in rows.items():
        save(f"stack-above-{slug(title)}", stack_title, title, TITLE_HEIGHT, 26)
        save(f"stack-beside-{slug(title)}", stack_title, title, STACK_HEIGHT, 27)
        for name in links:
            save(f"stack-{slug(name)}", stack_item, name)
    README.write_text(readme)
    cards = sum(len(projects) for projects in groups.values())
    pills = sum(len(items) for items in chips.values())
    frame("Drawn", [f"{cards} project cards, the stack and {pills} pills"], SUCCESS)


if __name__ == "__main__":
    main()
