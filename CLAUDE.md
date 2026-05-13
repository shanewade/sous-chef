# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Sous-chef is a Python project in early development. A virtual environment is checked in at `venv/` (Python 3.9).

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt   # once a requirements file exists
```

## Environment

Secrets and configuration live in `.env` (gitignored). Copy from `.env.example` if one exists and fill in values before running.
