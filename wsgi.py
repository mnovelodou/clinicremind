"""WSGI entrypoint.

Run locally with ``flask --app wsgi run`` or via a WSGI server pointed at
``wsgi:app``.
"""

from app import create_app

app = create_app()


if __name__ == "__main__":
    app.run()
