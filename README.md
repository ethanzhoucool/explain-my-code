# Explain My Code

A small web app that analyzes Python and Java source code and produces human-friendly, line-level explanations at three knowledge levels (ELI5, Beginner, Developer).

Live demo: https://explain-my-code-w3sj.onrender.com

## Features

- Multi-level explanations: ELI5, Beginner, Developer
- Interactive highlighting: hover keywords to see explanations
- Rule-based parsing: lightweight keyword templates (no AI required)
- Supports Python and Java (easy to extend)

## Tech Stack

- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript

## How it works

1. Scan each line for known language keywords/patterns
2. Match detected patterns to template explanations
3. Render highlighted lines with tooltip text for quick reading

## Run locally

Recommended: use Python 3.10+ (the project uses 3.13 in `runtime.txt` but 3.10+ works fine).

Install and run:

```bash
git clone https://github.com/ethanzhoucool/explain-my-code.git
cd explain-my-code
python3 -m venv .venv        # optional, recommended
source .venv/bin/activate    # macOS / Linux
pip install -r requirements.txt
python3 app.py
```

Open your browser at: http://127.0.0.1:5000

## Project structure

```
explain-my-code/
├── app.py                 # Flask application (entrypoint)
├── Procfile               # Gunicorn start command for Render
├── requirements.txt       # Python dependencies
├── runtime.txt            # Python runtime used on Render
├── templates/             # Jinja2 HTML templates
├── static/                # CSS and JS
└── explainer/             # language-specific rules and templates
	├── python_rules.py
	└── java_rules.py
```

## Extending rules

Add keywords and text templates in `explainer/python_rules.py` and `explainer/java_rules.py`. Each feature has multi-level template text (ELI5 / beginner / developer) and an optional color.

## Notes and TODOs

- The parser is intentionally simple and rule-based — it works well for quick explanations but won't fully parse complex syntax.
- Future ideas: add more languages, improve parsing with tokenizers (or optional LSP/AST use), and add unit tests.

## License

MIT
