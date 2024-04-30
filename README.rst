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

.. TODO: Insert long description here

Configuration
=============

``showmark`` supports the following configuration options.  These can be set by
defining them in a Python source file that is then pointed to by the
environment variable ``SHOWMARK_SETTINGS`` and/or by setting each option as an
environment variable ``FLASK_{name}``.

``SHOWMARK_SEARCH_PATH``
    An ``os.pathsep``-separated list of directories to search for filenames.
    Defaults to the user's home directory.

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
