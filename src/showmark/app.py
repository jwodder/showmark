from __future__ import annotations
import os
from pathlib import Path
from flask import Flask, render_template, request
from . import NotFound, ReadError, RenderError, Showmark, UnsupportedExtension

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
    action = request.args.get("action", "View")
    if not fpath:
        return render_template("nop.html")
    path = Path(fpath)
    if action == "List All":
        return render_template("listall.html", files=[str(p) for p in sm.findall(path)])
    else:
        try:
            content = sm.find_and_render(path)
        except NotFound:
            return render_template("errors/not-found.html")
        except UnsupportedExtension as e:
            return render_template("errors/bad-ext.html", path=e.path)
        except ReadError as e:
            return render_template("errors/read.html", path=e.path, msg=str(e.inner))
        except RenderError as e:
            return render_template("errors/render.html", path=e.path, msg=e.msg)
        else:
            return render_template("view.html", content=content)
