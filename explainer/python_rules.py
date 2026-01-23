# Explanation templates for different levels
TEMPLATES = {
    "for_loop": {
        "eli5": "This repeats something over and over, like counting on your fingers.",
        "beginner": "A for loop that repeats code a certain number of times.",
        "developer": "A for-loop that iterates over a sequence or range.",
        "color": "#e06c75"  # Red
    },
    "while_loop": {
        "eli5": "This keeps going until you say stop, like playing until dinner time.",
        "beginner": "A while loop that runs as long as a condition is true.",
        "developer": "A while-loop that executes while a boolean condition remains true.",
        "color": "#e06c75"  # Red
    },
    "if_statement": {
        "eli5": "This makes a choice - like 'if it's raining, bring an umbrella'.",
        "beginner": "An if statement that runs code only when a condition is met.",
        "developer": "A conditional statement that executes based on a boolean expression.",
        "color": "#c678dd"  # Purple
    },
    "elif_statement": {
        "eli5": "This checks another choice if the first one wasn't true.",
        "beginner": "An elif (else if) that checks another condition.",
        "developer": "An else-if clause for additional conditional branching.",
        "color": "#c678dd"  # Purple
    },
    "else_statement": {
        "eli5": "This is what happens if none of the other choices were true.",
        "beginner": "An else clause that runs when no conditions are met.",
        "developer": "An else clause for default execution path.",
        "color": "#c678dd"  # Purple
    },
    "function": {
        "eli5": "This is like a recipe - you give it ingredients and it makes something.",
        "beginner": "A function definition - a reusable block of code.",
        "developer": "A function definition that encapsulates logic and accepts parameters.",
        "color": "#61afef"  # Blue
    },
    "print": {
        "eli5": "This shows a message on the screen.",
        "beginner": "Prints output to the console.",
        "developer": "Outputs data to the standard output stream.",
        "color": "#56b6c2"  # Cyan
    },
    "class": {
        "eli5": "This is a blueprint for making things, like LEGO instructions.",
        "beginner": "A class - a template for creating objects.",
        "developer": "A class definition encapsulating data and behavior.",
        "color": "#e5c07b"  # Yellow
    },
    "list": {
        "eli5": "This is like a box where you keep many things together.",
        "beginner": "A list - a collection that holds multiple items in order.",
        "developer": "A mutable sequence data structure storing ordered elements.",
        "color": "#98c379"  # Green
    },
    "import": {
        "eli5": "This brings in extra tools, like getting crayons from another room.",
        "beginner": "Imports a module - bringing in code from other files.",
        "developer": "Imports external modules into the current namespace.",
        "color": "#c678dd"  # Purple
    },
    "return": {
        "eli5": "This gives back an answer, like when someone answers '4' to '2+2?'",
        "beginner": "Returns a value from a function.",
        "developer": "Returns a value from a function, terminating execution.",
        "color": "#c678dd"  # Purple
    },
    "variable": {
        "eli5": "This is like a labeled box where you store something.",
        "beginner": "Creates a variable - a container that stores a value.",
        "developer": "Variable assignment binding a value to a name.",
        "color": "#d19a66"  # Orange
    },
    "comment": {
        "eli5": "This is a note to help people understand the code - the computer ignores it.",
        "beginner": "A comment that explains the code but doesn't run.",
        "developer": "A non-executable comment for code documentation.",
        "color": "#5c6370"  # Gray
    },
    "input": {
        "eli5": "This asks you to type something, like when someone asks your name.",
        "beginner": "Gets input from the user via the console.",
        "developer": "Reads user input from standard input stream.",
        "color": "#56b6c2"  # Cyan
    },
    "range": {
        "eli5": "This creates a list of numbers to count with.",
        "beginner": "Creates a sequence of numbers.",
        "developer": "Generates an immutable sequence of numbers.",
        "color": "#56b6c2"  # Cyan
    },
    "string": {
        "eli5": "This is text - letters and words in quotes.",
        "beginner": "A string - text data enclosed in quotes.",
        "developer": "A string literal representing textual data.",
        "color": "#98c379"  # Green
    },
    "try": {
        "eli5": "This tries to do something that might not work.",
        "beginner": "Try block - attempts code that might cause an error.",
        "developer": "Exception handling block for potentially failing operations.",
        "color": "#e06c75"  # Red
    },
    "except": {
        "eli5": "This catches mistakes and handles them nicely.",
        "beginner": "Except block - handles errors when they happen.",
        "developer": "Exception handler catching specific or generic exceptions.",
        "color": "#e06c75"  # Red
    },
    "finally": {
        "eli5": "This always runs, no matter what happened before.",
        "beginner": "Finally block - code that always executes after try/except.",
        "developer": "Cleanup block that executes regardless of exception occurrence.",
        "color": "#e06c75"  # Red
    },
    "with": {
        "eli5": "This opens something and closes it automatically when done.",
        "beginner": "With statement - manages resources like files automatically.",
        "developer": "Context manager ensuring proper resource acquisition and release.",
        "color": "#c678dd"  # Purple
    },
    "lambda": {
        "eli5": "This is a tiny function that fits on one line.",
        "beginner": "Lambda - a small anonymous function.",
        "developer": "Anonymous function expression for inline operations.",
        "color": "#61afef"  # Blue
    },
    "dict": {
        "eli5": "This is like a dictionary - you look up a word to find its meaning.",
        "beginner": "Dictionary - stores pairs of keys and values.",
        "developer": "Hash map data structure with key-value pairs.",
        "color": "#98c379"  # Green
    },
    "set": {
        "eli5": "This is a bag of unique items - no duplicates allowed!",
        "beginner": "Set - a collection with no duplicate items.",
        "developer": "Unordered collection of unique hashable elements.",
        "color": "#98c379"  # Green
    },
    "tuple": {
        "eli5": "This is like a list that can't be changed.",
        "beginner": "Tuple - an unchangeable ordered collection.",
        "developer": "Immutable sequence type for fixed collections.",
        "color": "#98c379"  # Green
    },
    "break": {
        "eli5": "This stops the loop right away, like pressing stop.",
        "beginner": "Break - exits the loop immediately.",
        "developer": "Control statement terminating the nearest enclosing loop.",
        "color": "#e06c75"  # Red
    },
    "continue": {
        "eli5": "This skips to the next round of the loop.",
        "beginner": "Continue - skips to the next iteration of the loop.",
        "developer": "Control statement skipping to the next loop iteration.",
        "color": "#e06c75"  # Red
    },
    "pass": {
        "eli5": "This does nothing - it's a placeholder.",
        "beginner": "Pass - a placeholder that does nothing.",
        "developer": "Null operation statement used as a placeholder.",
        "color": "#5c6370"  # Gray
    },
    "None": {
        "eli5": "This means nothing - like an empty box.",
        "beginner": "None - represents no value or nothing.",
        "developer": "Singleton object representing the absence of a value.",
        "color": "#d19a66"  # Orange
    },
    "True": {
        "eli5": "This means yes or correct.",
        "beginner": "True - a boolean value meaning yes/correct.",
        "developer": "Boolean literal representing logical truth.",
        "color": "#d19a66"  # Orange
    },
    "False": {
        "eli5": "This means no or incorrect.",
        "beginner": "False - a boolean value meaning no/incorrect.",
        "developer": "Boolean literal representing logical falsehood.",
        "color": "#d19a66"  # Orange
    },
    "in": {
        "eli5": "This checks if something is inside something else.",
        "beginner": "In - checks if an item is in a collection.",
        "developer": "Membership test operator or iteration keyword.",
        "color": "#c678dd"  # Purple
    },
    "not": {
        "eli5": "This flips true to false and false to true.",
        "beginner": "Not - reverses a boolean value.",
        "developer": "Logical negation operator.",
        "color": "#c678dd"  # Purple
    },
    "and": {
        "eli5": "This means both things must be true.",
        "beginner": "And - both conditions must be true.",
        "developer": "Logical conjunction operator.",
        "color": "#c678dd"  # Purple
    },
    "or": {
        "eli5": "This means at least one thing must be true.",
        "beginner": "Or - at least one condition must be true.",
        "developer": "Logical disjunction operator.",
        "color": "#c678dd"  # Purple
    },
    "len": {
        "eli5": "This counts how many items are in something.",
        "beginner": "Len - returns the length/size of a collection.",
        "developer": "Built-in function returning the number of items.",
        "color": "#56b6c2"  # Cyan
    },
    "append": {
        "eli5": "This adds something to the end of a list.",
        "beginner": "Append - adds an item to the end of a list.",
        "developer": "List method appending an element to the end.",
        "color": "#56b6c2"  # Cyan
    },
    "open": {
        "eli5": "This opens a file so you can read or write to it.",
        "beginner": "Open - opens a file for reading or writing.",
        "developer": "Built-in function returning a file object.",
        "color": "#56b6c2"  # Cyan
    },
    "self": {
        "eli5": "This refers to the object itself.",
        "beginner": "Self - refers to the current object instance.",
        "developer": "Reference to the instance on which a method is called.",
        "color": "#e5c07b"  # Yellow
    },
    "init": {
        "eli5": "This sets up a new object when it's created.",
        "beginner": "__init__ - the constructor that initializes objects.",
        "developer": "Initializer method called when instantiating a class.",
        "color": "#61afef"  # Blue
    },
    "async": {
        "eli5": "This lets the program do other things while waiting.",
        "beginner": "Async - marks a function as asynchronous.",
        "developer": "Declares a coroutine function for asynchronous execution.",
        "color": "#c678dd"  # Purple
    },
    "await": {
        "eli5": "This waits for something to finish without blocking.",
        "beginner": "Await - waits for an async operation to complete.",
        "developer": "Suspends coroutine execution until awaitable completes.",
        "color": "#c678dd"  # Purple
    },
    "global": {
        "eli5": "This lets you use a variable from anywhere in the program.",
        "beginner": "Global - accesses a variable from outside the function.",
        "developer": "Declares a variable as global scope within a function.",
        "color": "#c678dd"  # Purple
    },
    "yield": {
        "eli5": "This gives back a value but remembers where it was.",
        "beginner": "Yield - returns a value and pauses the function.",
        "developer": "Generator expression yielding values lazily.",
        "color": "#c678dd"  # Purple
    }
}

def detect_features_in_line(line):
    """
    Detects all features in a line and returns them with their positions.
    Returns a list of tuples: (keyword, start_pos, end_pos, feature_type)
    """
    features = []
    line_lower = line.lower()
    
    # Define patterns to search for (keyword, feature_type)
    patterns = [
        ('for ', 'for_loop'),
        ('for(', 'for_loop'),
        ('while ', 'while_loop'),
        ('if ', 'if_statement'),
        ('elif ', 'elif_statement'),
        ('else:', 'else_statement'),
        ('else ', 'else_statement'),
        ('def ', 'function'),
        ('class ', 'class'),
        ('import ', 'import'),
        ('from ', 'import'),
        ('return ', 'return'),
        ('return\n', 'return'),
        ('print(', 'print'),
        ('input(', 'input'),
        ('range(', 'range'),
        ('len(', 'len'),
        ('open(', 'open'),
        ('.append(', 'append'),
        ('try:', 'try'),
        ('except ', 'except'),
        ('except:', 'except'),
        ('finally:', 'finally'),
        ('with ', 'with'),
        ('lambda ', 'lambda'),
        ('lambda:', 'lambda'),
        ('break', 'break'),
        ('continue', 'continue'),
        ('pass', 'pass'),
        ('None', 'None'),
        ('True', 'True'),
        ('False', 'False'),
        (' in ', 'in'),
        (' not ', 'not'),
        (' and ', 'and'),
        (' or ', 'or'),
        ('self', 'self'),
        ('__init__', 'init'),
        ('async ', 'async'),
        ('await ', 'await'),
        ('global ', 'global'),
        ('yield ', 'yield'),
        ('#', 'comment'),
    ]
    
    # Find all pattern matches
    for pattern, feature_type in patterns:
        start = 0
        while True:
            pos = line_lower.find(pattern, start)
            if pos == -1:
                break
            
            # Find the actual keyword in original case
            keyword = line[pos:pos + len(pattern)]
            features.append({
                'keyword': keyword.strip(),
                'start': pos,
                'end': pos + len(pattern),
                'type': feature_type
            })
            start = pos + 1
    
    # Check for variable assignment (=)
    if '=' in line and '==' not in line and 'def ' not in line_lower and 'class ' not in line_lower:
        pos = line.find('=')
        features.append({
            'keyword': '=',
            'start': pos,
            'end': pos + 1,
            'type': 'variable'
        })
    
    # Sort by position
    features.sort(key=lambda x: x['start'])
    
    return features

def build_highlighted_line(line, level):
    """
    Builds HTML with highlighted keywords and tooltips.
    """
    features = detect_features_in_line(line)
    
    if not features:
        return line, False
    
    # Build the HTML with highlights
    result = []
    last_pos = 0
    
    for feature in features:
        # Add text before the keyword
        result.append(line[last_pos:feature['start']])
        
        # Add highlighted keyword with tooltip
        keyword = feature['keyword']
        feature_type = feature['type']
        explanation = TEMPLATES.get(feature_type, {}).get(level, '')
        color = TEMPLATES.get(feature_type, {}).get('color', '#666')
        
        result.append(
            f'<span class="highlight" style="background-color: {color}; color: white;" '
            f'data-tooltip="{explanation}">{keyword}</span>'
        )
        
        last_pos = feature['end']
    
    # Add remaining text
    result.append(line[last_pos:])
    
    return ''.join(result), True

def generate_annotated_code(code, level):
    """
    Generates code with line-by-line highlighting.
    """
    lines = code.split('\n')
    annotated = []
    
    for i, line in enumerate(lines, 1):
        highlighted_line, has_highlights = build_highlighted_line(line, level)
        annotated.append({
            'number': i,
            'code': line,
            'highlighted': highlighted_line,
            'has_highlights': has_highlights
        })
    
    return annotated