"""
Serve rendered markup documents

Visit <https://github.com/jwodder/showmark> for more information.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import io
import os
from pathlib import Path
from typing import Iterator
from docutils.core import publish_parts
from docutils.io import FileInput
from flask import Flask, current_app, render_template, request
from markupsafe import Markup
from myst_parser.parsers.docutils_ import Parser

__version__ = "0.1.0.dev1"
__author__ = "John Thorvald Wodder II"
__author_email__ = "showmark@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/showmark"

app = Flask(__name__)
app.config["SHOWMARK_SEARCH_PATH"] = str(Path.home())
app.config["SHOWMARK_WRITER_NAME"] = "html5"
if "SHOWMARK_SETTINGS" in os.environ:
    app.config.from_envvar("SHOWMARK_SETTINGS")


@app.get("/")
def root() -> str:
    fpath = request.args.get("file")
    action = request.args.get("action", "Render")
    if not fpath:
        return render_template("blank.html")
    path = Path(fpath)
    if action == "List All":
        return render_template("listall.html", files=[str(p) for p in findfile(path)])
    elif (p := next(findfile(path), None)) is not None:
        try:
            return render_template("rendered.html", content=render(p))
        except UnsupportedExtension as e:
            return render_template("not-markup.html", msg=str(e))
    else:
        return render_template("not-found.html")


def render(path: Path) -> Markup:
    match path.suffix.lower():
        case ".md":
            return Markup(render_markdown(path))
        case ".rst":
            return Markup(render_restructuredtext(path))
        case ext:
            raise UnsupportedExtension(ext)


def render_markdown(path: Path) -> str:
    warnings = io.StringIO()
    with path.open(encoding="utf-8") as fp:
        parts = publish_parts(
            source=fp,
            source_class=FileInput,
            writer_name=current_app.config["SHOWMARK_WRITER_NAME"],
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
            writer_name=current_app.config["SHOWMARK_WRITER_NAME"],
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


@dataclass
class UnsupportedExtension(Exception):
    ext: str

    def __str__(self) -> str:
        return f"Invalid/unsupported markup file extension: {self.ext!r}"


def findfile(p: Path) -> Iterator[Path]:
    if p.is_absolute():
        if p.exists():
            yield p
        return
    dirs = deque(
        map(Path, current_app.config["SHOWMARK_SEARCH_PATH"].split(os.pathsep))
    )
    while dirs:
        dirpath = dirs.popleft()
        path = dirpath / p
        if path.exists():
            yield path
        for sub in sorted(dirpath.iterdir()):
            if sub.is_dir() and not sub.name.startswith("."):
                dirs.append(sub)
