# BibLaTeX Linter (Modernized Fork)

_A streamlined, containerized web application to lint and validate BibLaTeX files._

This project is a modernized fork of [Pezmc/BibLaTeX-Check](https://github.com/Pezmc/BibLaTeX-Check). It has been refactored to run seamlessly in modern environments using **Docker Compose** and **uv**.

## Origins & Credits
BibLaTeX Linter is part of a lineage of academic tools:
1. Adapted from **[BibLaTeX-Check](https://github.com/Pezmc/BibLaTeX-Check)** by Pezmc.
2. Which was adapted from **[BibTex Check](https://code.google.com/p/bibtex-check/)** by **Fabian Beck**.

This version focuses on local developer experience and zero-configuration deployment.

---

## Quick Start (Docker Compose)

The fastest way to get the linter running is using Docker. No Python installation is required on your host machine.

```sh
# 1. Clone and enter the directory
git clone https://github.com/your-repo/BibLaTeX-Linter.git
cd BibLaTeX-Linter

# 2. Start the application
docker compose up
```

The app will be live at **[http://localhost:8000/](http://localhost:8000/)**.

---

## Alternative: Local Development with `uv`

If you prefer to run it natively for development:

```sh
# Install dependencies
uv sync

# Run development server
uv run python manage.py runserver
```

## How it works
Paste the contents of your `.bib` file into the validator. The tool checks for:
- Missing required fields (year, journal, etc.) based on entry type.
- Non-unique IDs.
- Common formatting flaws (abbreviated journal titles, missing commas).

## Configuration
Basic configuration is handled via environment variables (see `.env.example`). For local Docker usage, the defaults are already configured in `docker-compose.yml`.

## License
MIT License
