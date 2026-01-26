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
        model = genai.GenerativeModel('gemini-pro')
        
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
    Generates line-by-line code display with AI explanation.
    Returns a dict with lines and the AI explanation.
    """
    lines = code.split('\n')
    annotated = []
    
    for i, line in enumerate(lines, 1):
        annotated.append({
            'number': i,
            'code': line,
            'highlighted': line,  # No highlighting in AI mode
            'has_highlights': False
        })
    
    # Get the AI explanation
    ai_explanation = explain_with_ai(code, language, level)
    
    return {
        'lines': annotated,
        'explanation': ai_explanation
    }
