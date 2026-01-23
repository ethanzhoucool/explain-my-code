from flask import Flask, render_template, request
from explainer.python_rules import generate_annotated_code as annotate_python
from explainer.java_rules import generate_annotated_code as annotate_java

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/explain', methods=['POST'])
def explain():
    code = request.form.get('code')
    language = request.form.get('language')
    level = request.form.get('level')
    
    # Check if code is empty
    if not code or code.strip() == '':
        return render_template('index.html', error="Please paste some code first!")
    
    # Generate line-by-line annotations
    if language == 'python':
        annotated_lines = annotate_python(code, level)
    elif language == 'java':
        annotated_lines = annotate_java(code, level)
    else:
        annotated_lines = []
    
    return render_template('result.html', 
                         annotated_lines=annotated_lines,
                         language=language,
                         level=level)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)