# -*- coding: utf-8 -*-
import os


def read(*names, **kwargs):
    with open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8"),
    ) as fh:
        return fh.read()


# Warn about all references to unknown targets
nitpicky = True
# Except for these ones, which we expect to point to unknown targets:
nitpick_ignore = [
    # Perhaps this is "obvious" to those that know type hints.  Perhaps we should
    # explain briefly with a link to the typing docs.
    ("py:class", "desert.T"),
]


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",  # Must come *after* sphinx.ext.napoleon.
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]
if os.getenv("SPELLCHECK"):
    extensions += ("sphinxcontrib.spelling",)
    spelling_show_suggestions = True
    spelling_lang = "en_US"

source_suffix = ".rst"
master_doc = "index"
project = "desert"
year = "2019"
author = "Desert contributors"
copyright = "{0}, {1}".format(year, author)

ns = {}
exec(read("..", "src/desert/_version.py"), ns)
version = release = ns["__version__"]


pygments_style = "trac"
templates_path = ["."]
extlinks = {
    "issue": ("https://github.com/python-desert/desert/issues/%s", "#"),
    "pr": ("https://github.com/python-desert/desert/pull/%s", "PR #"),
}
# on_rtd is whether we are on readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

if not on_rtd:  # only set the theme if we"re building docs locally
    html_theme = "sphinx_rtd_theme"

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_sidebars = {"**": ["searchbox.html", "globaltoc.html", "sourcelink.html"]}
html_short_title = "%s-%s" % (project, version)

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = True

autoapi_dirs = ["../src/desert"]


# Specify the baseurls for the projects I want to link to
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "marshmallow": ("https://marshmallow.readthedocs.io/en/latest/", None),
    "attrs": ("https://www.attrs.org/en/latest/", None),
    "attr": ("https://www.attrs.org/en/latest/", None),
    "marshmallow_union": (
        "https://python-marshmallow-union.readthedocs.io/en/latest/",
        None,
    ),
}


# codecov.io is unreliable so allow some retries in the
# `linkcheck` to avoid failing the build.
linkcheck_retries = 3
