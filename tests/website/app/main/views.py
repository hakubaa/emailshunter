from flask import render_template

from . import main


@main.route("/", methods=["GET"])
def index(): 
    fakes = ["test", "alis", "bob", "mike", "kate", "kate"]
    return render_template("index.html", fakes=fakes)

@main.route("/fake/<name>")
def fake(name):
    return render_template("fake.html", name=name)

@main.route("/test", methods=["GET"])
def test():
    return render_template("test.html")
