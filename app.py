from flask import Flask, render_template, request
from explainer.python_rules import generate_annotated_code as annotate_python
from explainer.java_rules import generate_annotated_code as annotate_java
from explainer.ai_explainer import generate_annotated_code_ai

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/explain', methods=['POST'])
def explain():
    code = request.form.get('code')
    language = request.form.get('language')
    level = request.form.get('level')
    mode = request.form.get('mode', 'rule-based')
    
    # Check if code is empty
    if not code or code.strip() == '':
        return render_template('index.html', error="Please paste some code first!")
    
    # Always generate rule-based annotations (needed for both modes)
    if language == 'python':
        rule_annotated_lines = annotate_python(code, level)
    elif language == 'java':
        rule_annotated_lines = annotate_java(code, level)
    else:
        rule_annotated_lines = []
    
    # AI-powered mode
    if mode == 'ai':
        result = generate_annotated_code_ai(code, language, level)
        return render_template('result.html', 
                             annotated_lines=result['lines'],
                             rule_annotated_lines=rule_annotated_lines,
                             ai_explanation=result['explanation'],
                             language=language,
                             level=level,
                             mode=mode,
                             code=code)
    
    # Rule-based mode (default)
    return render_template('result.html', 
                         annotated_lines=rule_annotated_lines,
                         rule_annotated_lines=rule_annotated_lines,
                         language=language,
                         level=level,
                         mode=mode,
                         code=code)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)