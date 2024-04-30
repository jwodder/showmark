"""
Serve rendered markup documents

Visit <https://github.com/jwodder/showmark> for more information.
"""

from __future__ import annotations
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.metadata import version
import os
from pathlib import Path
from typing import Any
from docutils.core import publish_parts
from docutils.io import FileInput
from docutils.parsers import Parser
from docutils.utils import SystemMessage
from flask import Flask, current_app
from markupsafe import Markup
from myst_parser.parsers.docutils_ import Parser as MdParser

__version__ = version("showmark")
__author__ = "John Thorvald Wodder II"
__author_email__ = "showmark@varonathe.org"
__license__ = "MIT"
__url__ = "https://github.com/jwodder/showmark"

BASE_SETTINGS = {
    "field_name_limit": 0,
    "halt_level": 2,
    "input_encoding": "utf-8",
    "math_output": "mathjax irrelevant-value",
    "syntax_highlight": "short",
    # `halt_level=2` plus the default setting of `report_level=2` means that no
    # warnings will ever be emitted, so just disable them:
    "warning_stream": False,
}


class Showmark:
    def __init__(self, app: Flask | None = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        if "showmark" in app.extensions:
            raise RuntimeError("showmark extension already registered on app")
        app.extensions["showmark"] = Inner.for_app(app)
        app.add_template_global(showmark_imprint)

    @property
    def inner(self) -> Inner:
        sm = current_app.extensions["showmark"]
        assert isinstance(sm, Inner)
        return sm

    def findall(self, path: Path) -> Iterator[Path]:
        return self.inner.findfile(path)

    def find_and_render(self, path: Path) -> str:
        s = self.inner
        if (p := next(s.findfile(path), None)) is not None:
            return s.render(p)
        else:
            raise NotFound(path)


@dataclass
class Inner:
    search_paths: list[Path]
    writer_name: str

    @classmethod
    def for_app(cls, app: Flask) -> Inner:
        sp = app.config.get("SHOWMARK_SEARCH_PATH", str(Path.home()))
        search_paths = list(map(Path, sp.split(os.pathsep)))
        writer_name = app.config.get("SHOWMARK_WRITER_NAME", "html5")
        return cls(search_paths=search_paths, writer_name=writer_name)

    def findfile(self, p: Path) -> Iterator[Path]:
        if p.is_absolute():
            if p.is_file() and any(p.is_relative_to(sp) for sp in self.search_paths):
                yield p
            return
        dirs = deque(self.search_paths)
        while dirs:
            dirpath = dirs.popleft()
            path = dirpath / p
            if path.is_file():
                yield path
            for sub in sorted(dirpath.iterdir()):
                if sub.is_dir() and not sub.name.startswith("."):
                    dirs.append(sub)

    def render(self, path: Path) -> Markup:
        match path.suffix.lower():
            case ".rst":
                return Markup(self.render_restructuredtext(path))
            case ".md":
                return Markup(self.render_markdown(path))
            case ext:
                raise UnsupportedExtension(ext)

    def render_restructuredtext(self, path: Path) -> str:
        return self.inner_render(path, settings=BASE_SETTINGS | {"smart_quotes": True})

    def render_markdown(self, path: Path) -> str:
        return self.inner_render(
            path,
            parser=MdParser(),
            settings=BASE_SETTINGS
            | {
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

    def inner_render(
        self, path: Path, *, parser: Parser | None = None, settings: dict[str, Any]
    ) -> str:
        with path.open(encoding="utf-8") as fp:
            try:
                parts = publish_parts(
                    source=fp,
                    source_class=FileInput,
                    writer_name=self.writer_name,
                    parser=parser,
                    settings_overrides=settings,
                )
            except SystemMessage as e:
                raise RenderError(msg=str(e))
        body = parts["html_body"]
        assert isinstance(body, str)
        return body


@dataclass
class NotFound(Exception):
    path: Path

    def __str__(self) -> str:
        return f"File not found: {self.path}"


@dataclass
class UnsupportedExtension(Exception):
    ext: str

    def __str__(self) -> str:
        return f"Invalid/unsupported markup file extension: {self.ext!r}"


@dataclass
class RenderError(Exception):
    msg: str

    def __str__(self) -> str:
        return self.msg


def showmark_imprint() -> Markup:
    return Markup(f'<a href="{__url__}">showmark</a> v{__version__}')
