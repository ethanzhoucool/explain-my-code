# Explain Code Like I'm 5

A web application that analyzes Python and Java code and generates human-friendly explanations at multiple knowledge levels.

## Features

- **Multi-level explanations**: ELI5, Beginner, and Developer modes
- **Interactive highlighting**: Hover over keywords to see what they do
- **Color-coded syntax**: Different colors for loops, functions, variables, etc.
- **Two language support**: Python and Java

## Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, JavaScript
- **Parsing**: Rule-based keyword detection with custom templates

## How It Works

Instead of using AI or complex compilers, this app uses:
1. **Keyword Detection** - Scans code for programming constructs
2. **Template Matching** - Maps keywords to pre-written explanations
3. **Dynamic Highlighting** - Color-codes and adds tooltips to each feature

## Installation
```bash
# Clone the repository
git clone <your-repo-url>

# Navigate to project
cd explain-my-code

# Install dependencies
pip3 install flask

# Run the application
python3 app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Project Structure
```
explain-my-code/
├── app.py                 # Flask application
├── templates/
│   ├── index.html        # Home page
│   └── result.html       # Results page
├── static/
│   ├── style.css         # Styling
│   └── script.js         # Tooltip functionality
├── explainer/
│   ├── python_rules.py   # Python analysis logic
│   └── java_rules.py     # Java analysis logic
└── README.md
```

## Future Improvements

- Add more programming languages (JavaScript, C++, etc.)
- Support for more advanced syntax (classes, decorators, etc.)
- Export explanations as PDF
- Dark mode toggle


## License

MIT