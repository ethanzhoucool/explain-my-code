import os
import google.generativeai as genai

# Configure API key from environment variable
def configure_api():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return False
    genai.configure(api_key=api_key)
    return True

def get_level_prompt(level):
    """Returns the appropriate prompt based on explanation level."""
    prompts = {
        'eli5': "Explain this code like I'm 5 years old. Use simple language and fun analogies.",
        'beginner': "Explain this code for a beginner programmer. Be clear but technical.",
        'developer': "Explain this code for an experienced developer. Be precise and technical."
    }
    return prompts.get(level, prompts['beginner'])

def explain_with_ai(code, language, level):
    """
    Uses Gemini AI to explain the provided code.
    Returns a string explanation or an error message.
    """
    if not configure_api():
        return "Error: GEMINI_API_KEY environment variable is not set."
    
    try:
        # Use gemini-1.5-flash (current model name)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        level_prompt = get_level_prompt(level)
        
        prompt = f"""You are a helpful coding teacher. {level_prompt}

Here is {language} code to explain:

```{language}
{code}
```

Provide a clear explanation of what this code does. If there are multiple parts, explain each one. Format your response nicely with line breaks between sections."""

        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "Error: No response received from AI. Please try again."
            
    except Exception as e:
        return f"Error: Could not get AI explanation. {str(e)}"

def generate_annotated_code_ai(code, language, level):
    """
    Generates line-by-line code display with keyword highlighting AND AI explanation.
    Returns a dict with highlighted lines and the AI explanation.
    """
    # Import the rule-based highlighters to reuse their highlighting
    from explainer.python_rules import build_highlighted_line as python_highlight
    from explainer.java_rules import build_highlighted_line as java_highlight
    
    lines = code.split('\n')
    annotated = []
    
    for i, line in enumerate(lines, 1):
        # Apply keyword highlighting based on language
        if language == 'python':
            highlighted_line, has_highlights = python_highlight(line, level)
        elif language == 'java':
            highlighted_line, has_highlights = java_highlight(line, level)
        else:
            highlighted_line, has_highlights = line, False
        
        annotated.append({
            'number': i,
            'code': line,
            'highlighted': highlighted_line,
            'has_highlights': has_highlights
        })
    
    # Get the AI explanation
    ai_explanation = explain_with_ai(code, language, level)
    
    return {
        'lines': annotated,
        'explanation': ai_explanation
    }
