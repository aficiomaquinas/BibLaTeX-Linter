# BibLaTeX Linter

_A simple web app to lint BibLaTeX files_

**BibLaTeX Linter** is a small Python-powered web app. Paste in a `.bib` file, and it checks if certain required fields are available (e.g., if a publication has a year, or if a journal article has volume/issue numbers).

## Features
- Validates field requirements for various BibLaTeX entry types.
- Modernized with **Django 5.1+** and **Python 3.13**.
- Managed with **uv** for fast and reliable dependency resolution.
- Ready for **Docker** deployment.

## Running Locally

### 1. Using `uv` (Recommended)
Make sure you have [uv](https://docs.astral.sh/uv/) installed.

```sh
# Sync dependencies and create environment
uv sync

# Setup environment variables
cp .env.example .env

# Run development server
uv run python manage.py runserver
```

The app will be available at [http://localhost:8000/](http://localhost:8000/).

### 2. Using Docker
If you prefer Docker, you can start the app without installing Python locally:

```sh
docker compose up
```

## Configuration
The app uses environment variables for configuration. See `.env.example` for details:
- `DEBUG`: Set to `True` for development.
- `DJANGO_SECRET_KEY`: Your secret key.
- `ALLOWED_HOSTS`: Comma-separated list of allowed domains.

## License
MIT License
