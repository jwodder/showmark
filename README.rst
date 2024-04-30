|repostatus| |ci-status| |license|

.. |repostatus| image:: https://www.repostatus.org/badges/latest/concept.svg
    :target: https://www.repostatus.org/#concept
    :alt: Project Status: Concept – Minimal or no implementation has been done
          yet, or the repository is only intended to be a limited example,
          demo, or proof-of-concept.

.. |ci-status| image:: https://github.com/jwodder/showmark/actions/workflows/test.yml/badge.svg
    :target: https://github.com/jwodder/showmark/actions/workflows/test.yml
    :alt: CI Status

.. |license| image:: https://img.shields.io/github/license/jwodder/showmark.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/showmark>`_
| `Issues <https://github.com/jwodder/showmark/issues>`_
| `Changelog <https://github.com/jwodder/showmark/blob/master/CHANGELOG.md>`_

``showmark`` is a Flask application for viewing rendered markup documents in a
browser.  It was developed solely for my personal use and is not intended to be
consumed generally; use it at your own risk.  In particular, it allows viewing
files located on the system where the Flask application runs; it is the
administrator's responsibility to secure this access appropriately.

``showmark`` supports the following markup formats, recognized by file
extension (case insensitive):

- reStructuredText_ (``.rst``) — rendered using docutils_

- Markdown (superset of CommonMark_) (``.md``) — rendered using myst-parser_

  - The following `parser extensions`_ are enabled:

    - ``deflist``
    - ``dollarmath``
    - ``linkify``
    - ``replacements``
    - ``smartquotes``

.. _reStructuredText: https://docutils.sourceforge.io/rst.html
.. _docutils: https://docutils.sourceforge.io
.. _CommonMark: https://commonmark.org
.. _myst-parser: https://myst-parser.readthedocs.io
.. _parser extensions: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html


Installation
============
``showmark`` requires Python 3.10 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install it::

    python3 -m pip install git+https://github.com/jwodder/showmark.git


Web Application
===============

The ``showmark`` web application consists of a single page.  At the top of this
page is a form with an input box, a "View" button, and a "List All" button.
The user is expected to enter a file path (bare basename, relative path, or
absolute path) in the input box, after which pressing the buttons has the
following effects:

- "View" — If the path supplied in the input box is a basename or relative
  path, then ``showmark`` performs a breadth-first traversal of each directory
  specified in the ``SHOWMARK_SEARCH_PATH`` configuration option (see below) in
  turn, looking for a directory to which appending the input path results in an
  extant file path; the first such file found has its contents rendered &
  displayed.

  If the input path is absolute, then if it also begins with one of the
  directories in ``SHOWMARK_SEARCH_PATH`` and points to an extant file, that
  file has its contents rendered & displayed.

  Any filesystem errors that occur while traversing or inspecting paths are
  ignored.

- "List All" — All files matching the input path (using the same rules as for
  "View") are found and displayed as a collection of hyperlinks; clicking on a
  link sends the user to a page displaying that file's rendered contents.


Configuration
=============

``showmark`` supports the following configuration options.  These can be set by
defining them in a Python source file that is then pointed to by the
environment variable ``SHOWMARK_SETTINGS`` and/or by setting each option as an
environment variable ``FLASK_{name}``.

``SHOWMARK_SEARCH_PATH``
    An ``os.pathsep``-separated list of directories (located on the system on
    which the application runs) to search for files to render.  Defaults to the
    user's home directory.

``SHOWMARK_WRITER_NAME``
    The name of the docutils writer to use for rendering markup.  Defaults to
    ``html5``.


Development Server
==================

``showmark`` can be served in a local development server on port 8080 by
running ``hatch run local:run``.  This sets ``SHOWMARK_SEARCH_PATH`` to
``$HOME/work``.


Installation on macOS
=====================

``showmark`` was successfully installed on a macOS Sonoma system as follows,
resulting in it being served by the built-in Apache server (already enabled) at
<http://localhost/showmark>:

- Install `uwsgi <https://uwsgi-docs.readthedocs.io/en/latest/>`_ via Homebrew:
  ``brew install uwsgi``

- Create a virtual environment at
  ``/Library/WebServer/Documents/venvs/showmark`` and install the ``showmark``
  package into it

- Create the file ``$HOMEBREW_PREFIX/etc/uwsgi/apps-enabled/showmark.ini`` with
  the following contents:

  .. code:: ini

    [uwsgi]
    plugin = python3
    socket = /tmp/org.varonathe.showmark.sock
    # Replace the below with your own search path:
    env = FLASK_SHOWMARK_SEARCH_PATH=/Users/jwodder/work
    module = showmark.app:app
    virtualenv = /Library/WebServer/Documents/venvs/showmark
    manage-script-name = true
    need-app = true
    master = true
    processes = 2
    threads = 5
    harakiri = 60
    vacuum = true

- Enable uwsgi as a system-level daemon: ``sudo brew services start uwsgi``

  - Using ``sudo`` is necessary so that the service will be system-level rather
    than a user agent, which is needed so that the service will run as the
    ``_www`` user and thus be able to read & write to the socket without
    messing with permissions.

- Configure Apache by editing ``/etc/apache2/httpd.conf`` as follows:

  - Uncomment the following lines::

        LoadModule proxy_module libexec/apache2/mod_proxy.so
        LoadModule proxy_uwsgi_module libexec/apache2/mod_proxy_uwsgi.so

  - Add the following line::

        ProxyPass /showmark unix:/tmp/org.varonathe.showmark.sock|uwsgi://showmark/

- Restart Apache: ``sudo apachectl restart``

Updating
--------

After installing ``showmark`` as shown above, the package can be updated to a
newer version by running:

.. code:: shell

    /Library/WebServer/Documents/venvs/showmark/bin/pip install --upgrade \
        git+https://github.com/jwodder/showmark.git

    sudo brew services restart uwsgi
