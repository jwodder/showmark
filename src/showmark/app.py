from __future__ import annotations
import os
from pathlib import Path
from flask import Flask, render_template, request
from . import NotFound, RenderError, Showmark, UnsupportedExtension

app = Flask(__name__)
app.config["SHOWMARK_SEARCH_PATH"] = str(Path.home())
app.config["SHOWMARK_WRITER_NAME"] = "html5"
if "SHOWMARK_SETTINGS" in os.environ:
    app.config.from_envvar("SHOWMARK_SETTINGS")
app.config.from_prefixed_env()

sm = Showmark()
sm.init_app(app)


@app.get("/")
def root() -> str:
    fpath = request.args.get("file")
    action = request.args.get("action", "Render")
    if not fpath:
        return render_template("blank.html")
    path = Path(fpath)
    if action == "List All":
        return render_template("listall.html", files=[str(p) for p in sm.findall(path)])
    else:
        try:
            content = sm.find_and_render(path)
        except NotFound:
            return render_template("not-found.html")
        except UnsupportedExtension as e:
            return render_template("not-markup.html", msg=str(e))
        except RenderError as e:
            return render_template("rendering-error.html", msg=str(e))
        else:
            return render_template("rendered.html", content=content)
