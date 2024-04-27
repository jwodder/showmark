#!/Library/WebServer/Documents/venv/bin/python
# See requirements.txt for dependencies
import cgitb
from collections import deque
import io
import os
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qs, urlencode
from xml.sax.saxutils import escape
from docutils.core import publish_parts
from docutils.io import FileInput
from myst_parser.parsers.docutils_ import Parser

PIM_PATHS = [
    Path("~jwodder/work").expanduser(),
    # Path('~jwodder/Documents').expanduser(),
]

HEADER = """\
Content-type: text/html; charset=utf-8

<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
 "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>showmark.cgi</title>
<link rel="stylesheet" type="text/css" href="styles/kbits.css"/>
<link rel="stylesheet" type="text/css" href="styles/kbits5.css"/>
<script type="text/javascript" id="MathJax-script" async
    src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</script>
</head>
<body>"""

FORM = """\
<form method="get">
<center>
<input type="text" name="file" size="20"/>
<input type="submit" name="action" value="Render"/>
<input type="submit" name="action" value="List All"/>
</center>
</form>"""

FOOTER = """\
</body>
</html>
"""


def render_markdown(path, writer):
    warnings = io.StringIO()
    with path.open(encoding="utf-8") as fp:
        parts = publish_parts(
            source=fp,
            source_class=FileInput,
            writer_name=writer,
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
    return parts["html_body"]


def render_restructuredtext(path, writer):
    warnings = io.StringIO()
    with path.open(encoding="utf-8") as fp:
        parts = publish_parts(
            source=fp,
            source_class=FileInput,
            writer_name=writer,
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
    return parts["html_body"]


ext2renderer = {
    ".md": render_markdown,
    ".rst": render_restructuredtext,
}


def main():
    print(HEADER)
    cgitb.enable()
    formdata = parse_qs(os.environ.get("QUERY_STRING", ""))
    fpath = formdata.get("file", [None])[0]
    action = formdata.get("action", ["Render"])[0]
    writer = formdata.get("writer", ["html5"])[0]
    if not fpath:
        print(FORM)
    else:
        path = Path(fpath)
        if path.suffix not in ext2renderer:
            # Poor man's security
            print("Markup files only, please.")
            print(FORM)
        elif action == "List All":
            print(FORM)
            for p in pim(path):
                print(
                    '<center><a href="showmark.cgi?{}">{}</a></center>'.format(
                        urlencode({"file": str(p)}), escape(str(p))
                    )
                )
        else:
            path = next(pim(path), None)
            if path is None:
                print("<tt>No such file</tt>")
                print(FORM)
            else:
                print(FORM)
                print(ext2renderer[path.suffix](path, writer))
    print(FOOTER)


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


if __name__ == "__main__":
    main()
