"""
Serve rendered markup documents

Visit <https://github.com/jwodder/showmark> for more information.
"""

from __future__ import annotations
from collections import deque
import io
from pathlib import Path
from typing import Iterator
from docutils.core import publish_parts
from docutils.io import FileInput
from flask import Flask, render_template, request
from markupsafe import Markup
from myst_parser.parsers.docutils_ import Parser

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "showmark@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/showmark"

PIM_PATHS = [
    Path("~jwodder/work").expanduser(),
    # Path('~jwodder/Documents').expanduser(),
]

WRITER_NAME = "html5"

app = Flask(__name__)


@app.get("/")
def root() -> str:
    fpath = request.args.get("file")
    action = request.args.get("action", "Render")
    if not fpath:
        return render_template("blank.html")
    else:
        path = Path(fpath)
        if path.suffix not in ext2renderer:
            # Poor man's security
            return render_template("not-markup.html")
        elif action == "List All":
            return render_template("listall.html", files=[str(p) for p in pim(path)])
        elif (p := next(pim(path), None)) is not None:
            return render_template(
                "rendered.html", content=Markup(ext2renderer[p.suffix](p))
            )
        else:
            return render_template("not-found.html")


def render_markdown(path: Path) -> str:
    warnings = io.StringIO()
    with path.open(encoding="utf-8") as fp:
        parts = publish_parts(
            source=fp,
            source_class=FileInput,
            writer_name=WRITER_NAME,
            parser=Parser(),
            settings_overrides={
                "field_name_limit": 0,
                "halt_level": 2,
                "input_encoding": "utf-8",
                "math_output": "mathjax irrelevant-value",
                "syntax_highlight": "short",
                "warning_stream": warnings,
                "myst_suppress_warnings": ["myst.header"],
                "myst_enable_extensions": [
                    "dollarmath",
                    "smartquotes",
                    "replacements",
                    "linkify",
                    "deflist",
                ],
            },
        )
    ### TODO: Do something with `warnings`!
    body = parts["html_body"]
    assert isinstance(body, str)
    return body


def render_restructuredtext(path: Path) -> str:
    warnings = io.StringIO()
    with path.open(encoding="utf-8") as fp:
        parts = publish_parts(
            source=fp,
            source_class=FileInput,
            writer_name=WRITER_NAME,
            settings_overrides={
                "field_name_limit": 0,
                "halt_level": 2,
                "input_encoding": "utf-8",
                "math_output": "mathjax irrelevant-value",
                "smart_quotes": True,
                "syntax_highlight": "short",
                "warning_stream": warnings,
            },
        )
    ### TODO: Do something with `warnings`!
    body = parts["html_body"]
    assert isinstance(body, str)
    return body


ext2renderer = {
    ".md": render_markdown,
    ".rst": render_restructuredtext,
}


def pim(p: Path) -> Iterator[Path]:
    if p.is_absolute():
        if p.exists():
            yield p
        return
    dirs = deque(PIM_PATHS)
    while dirs:
        dirpath = dirs.popleft()
        path = dirpath / p
        if path.exists():
            yield path
        for sub in sorted(dirpath.iterdir()):
            if sub.is_dir() and not sub.name.startswith("."):
                dirs.append(sub)
