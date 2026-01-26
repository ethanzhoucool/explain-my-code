import os
import json
import re
import html
import time
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
        'eli5': "like I'm 5 years old, using simple words and fun analogies",
        'beginner': "for a beginner programmer, being clear but somewhat technical",
        'developer': "for an experienced developer, being precise and technical"
    }
    return prompts.get(level, prompts['beginner'])

def get_line_explanations(code, language, level):
    """
    Uses Gemini AI to get explanations for each line of code.
    Returns a dict mapping line numbers to explanations.
    Includes retry logic for rate limiting.
    """
    if not configure_api():
        return {}, "Error: GEMINI_API_KEY environment variable is not set."
    
    # Retry configuration
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            level_desc = get_level_prompt(level)
            lines = code.split('\n')
            numbered_code = '\n'.join([f"{i+1}: {line}" for i, line in enumerate(lines)])
            
            prompt = f"""You are a coding teacher. Analyze this {language} code and provide:

1. A brief explanation for EACH line (explain {level_desc})
2. An overall summary of what the entire code does

Code (with line numbers):
{numbered_code}

IMPORTANT: Respond in this exact JSON format:
{{
  "lines": {{
    "1": "explanation for line 1",
    "2": "explanation for line 2"
  }},
  "summary": "Overall summary of what the code does"
}}

Rules:
- For blank lines or just closing braces/brackets, use "Empty line" or "Closes the block"
- Keep each line explanation SHORT (1 sentence, under 100 characters)
- The summary should be 2-3 sentences
- Return ONLY valid JSON, no markdown"""

            response = model.generate_content(prompt)
            
            if response and response.text:
                # Clean the response - remove markdown code blocks if present
                text = response.text.strip()
                if text.startswith('```'):
                    text = re.sub(r'^```\w*\n?', '', text)
                    text = re.sub(r'\n?```$', '', text)
                
                try:
                    data = json.loads(text)
                    line_explanations = {int(k): v for k, v in data.get('lines', {}).items()}
                    summary = data.get('summary', 'No summary available.')
                    return line_explanations, summary
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {}, response.text
            else:
                return {}, "Error: No response received from AI."
                
        except Exception as e:
            error_str = str(e)
            # Check if it's a rate limit error (429)
            if '429' in error_str or 'Resource exhausted' in error_str:
                if attempt < max_retries - 1:
                    # Wait and retry
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    return {}, "The AI service is busy. Please wait a moment and try again."
            else:
                return {}, f"Error: Could not get AI explanation. {error_str}"
    
    return {}, "Error: Failed after multiple attempts. Please try again later."

def generate_annotated_code_ai(code, language, level):
    """
    Generates line-by-line code display with AI-generated tooltips for each line.
    Returns a dict with annotated lines and overall summary.
    """
    lines = code.split('\n')
    
    # Get AI explanations for each line
    line_explanations, summary = get_line_explanations(code, language, level)
    
    annotated = []
    for i, line in enumerate(lines, 1):
        # Get the AI explanation for this line
        explanation = line_explanations.get(i, "")
        
        # Escape HTML in the line content
        escaped_line = html.escape(line)
        
        # If we have an explanation, wrap only the code part (not leading whitespace)
        if explanation and line.strip():
            # Separate leading whitespace from code
            stripped = line.lstrip()
            leading_spaces = line[:len(line) - len(stripped)]
            escaped_leading = html.escape(leading_spaces)
            escaped_code = html.escape(stripped)
            
            highlighted = f'{escaped_leading}<span class="ai-line-highlight" data-tooltip="{html.escape(explanation)}">{escaped_code}</span>'
            has_highlights = True
        else:
            highlighted = escaped_line
            has_highlights = False
        
        annotated.append({
            'number': i,
            'code': line,
            'highlighted': highlighted,
            'has_highlights': has_highlights
        })
    
    return {
        'lines': annotated,
        'explanation': summary
    }
