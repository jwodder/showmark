"""
Serve rendered markup documents

``showmark`` is a Flask application for viewing rendered markup documents
located on a web server in a browser.  It was developed solely for my personal
use and is not intended to be consumed generally; use it at your own risk.

Visit <https://github.com/jwodder/showmark> for more information.
"""

from __future__ import annotations
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib.metadata import version
import os
from pathlib import Path
from typing import Any, ClassVar
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
        app.extensions["showmark"] = Extension.for_app(app)
        app.add_template_global(showmark_imprint)

    @property
    def ext(self) -> Extension:
        sm = current_app.extensions["showmark"]
        assert isinstance(sm, Extension)
        return sm

    def findall(self, path: Path) -> Iterator[Path]:
        if path.suffix.lower() not in Extension.RENDERERS:
            raise UnsupportedExtension(path)
        return self.ext.findfile(path)

    def find_and_render(self, path: Path) -> str:
        if path.suffix.lower() not in Extension.RENDERERS:
            raise UnsupportedExtension(path)
        x = self.ext
        if (p := next(x.findfile(path), None)) is not None:
            return x.render(p)
        else:
            raise NotFound(path)


@dataclass
class Extension:
    RENDERERS: ClassVar[dict[str, Callable[[Extension, Path], Markup]]] = {}

    search_paths: list[Path]
    writer_name: str
    exclude_dirs: set[str]

    @classmethod
    def for_app(cls, app: Flask) -> Extension:
        sp = app.config.get("SHOWMARK_SEARCH_PATH", str(Path.home()))
        search_paths = list(map(Path, sp.split(os.pathsep)))
        writer_name = app.config.get("SHOWMARK_WRITER_NAME", "html5")
        exclude_dirs = set(
            app.config.get("SHOWMARK_EXCLUDE_DIRS", "").split(os.pathsep)
        )
        return cls(
            search_paths=search_paths,
            writer_name=writer_name,
            exclude_dirs=exclude_dirs,
        )

    def findfile(self, p: Path) -> Iterator[Path]:
        try:
            if p.is_absolute():
                if p.is_file() and any(
                    p.is_relative_to(sp) for sp in self.search_paths
                ):
                    yield p
                return
        except OSError:
            return
        dirs = deque(self.search_paths)
        while dirs:
            dirpath = dirs.popleft()
            path = dirpath / p
            try:
                if path.is_file():
                    yield path
            except OSError:
                pass
            try:
                subs = sorted(dirpath.iterdir())
            except OSError:
                pass
            else:
                for sub in subs:
                    try:
                        if (
                            sub.is_dir()
                            and not sub.name.startswith(".")
                            and sub.name not in self.exclude_dirs
                        ):
                            dirs.append(sub)
                    except OSError:
                        pass

    def render(self, path: Path) -> Markup:
        ext = path.suffix.lower()
        try:
            renderer = self.RENDERERS[ext]
        except KeyError:
            raise UnsupportedExtension(path)
        else:
            return renderer(self, path)

    def render_restructuredtext(self, path: Path) -> Markup:
        return self.inner_render(path, settings=BASE_SETTINGS | {"smart_quotes": True})

    def render_markdown(self, path: Path) -> Markup:
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
    ) -> Markup:
        try:
            with path.open(encoding="utf-8") as fp:
                parts = publish_parts(
                    source=fp,
                    source_class=FileInput,
                    writer_name=self.writer_name,
                    parser=parser,
                    settings_overrides=settings,
                )
        except (OSError, UnicodeDecodeError) as e:
            raise ReadError(path=path, inner=e)
        except SystemMessage as e:
            raise RenderError(path=path, msg=str(e))
        body = parts["html_body"]
        assert isinstance(body, str)
        return Markup(body)


Extension.RENDERERS[".md"] = Extension.render_markdown
Extension.RENDERERS[".rst"] = Extension.render_restructuredtext


@dataclass
class NotFound(Exception):
    path: Path

    def __str__(self) -> str:
        return f"File not found: {self.path}"


@dataclass
class UnsupportedExtension(Exception):
    path: Path

    def __str__(self) -> str:
        return f"Unsupported/invalid markup file extension: {self.path}"


@dataclass
class RenderError(Exception):
    path: Path
    msg: str

    def __str__(self) -> str:
        return f"{self.path}: {self.msg}"


@dataclass
class ReadError(Exception):
    path: Path
    inner: Exception

    def __str__(self) -> str:
        return f"{self.path}: {self.inner}"


def showmark_imprint() -> Markup:
    return Markup(f'<a href="{__url__}">showmark</a> v{__version__}')
