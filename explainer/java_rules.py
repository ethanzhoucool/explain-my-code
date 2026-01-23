# Explanation templates for Java
TEMPLATES = {
    "for_loop": {
        "eli5": "This repeats something over and over, like counting on your fingers.",
        "beginner": "A for loop that repeats code a certain number of times.",
        "developer": "A for-loop with initialization, condition, and increment.",
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
    "else_statement": {
        "eli5": "This is what happens if the choice wasn't true.",
        "beginner": "An else clause that runs when the condition is false.",
        "developer": "An else clause for alternative execution path.",
        "color": "#c678dd"  # Purple
    },
    "method": {
        "eli5": "This is like a recipe - you give it ingredients and it makes something.",
        "beginner": "A method definition - a reusable block of code.",
        "developer": "A method definition that encapsulates logic.",
        "color": "#61afef"  # Blue
    },
    "main_method": {
        "eli5": "This is where the program starts - like the first page of a book.",
        "beginner": "The main method - where your Java program begins.",
        "developer": "The entry point of a Java application.",
        "color": "#61afef"  # Blue
    },
    "system_out": {
        "eli5": "This shows a message on the screen.",
        "beginner": "Prints output to the console.",
        "developer": "Outputs data to standard output using System.out.",
        "color": "#56b6c2"  # Cyan
    },
    "class": {
        "eli5": "This is a blueprint for making things, like LEGO instructions.",
        "beginner": "A class - a template for creating objects.",
        "developer": "A class definition encapsulating data and behavior.",
        "color": "#e5c07b"  # Yellow
    },
    "import": {
        "eli5": "This brings in extra tools, like getting crayons from another room.",
        "beginner": "Imports a package - bringing in code from libraries.",
        "developer": "Imports external packages into the current namespace.",
        "color": "#c678dd"  # Purple
    },
    "return": {
        "eli5": "This gives back an answer, like when someone answers '4' to '2+2?'",
        "beginner": "Returns a value from a method.",
        "developer": "Returns a value from a method, terminating execution.",
        "color": "#c678dd"  # Purple
    },
    "variable": {
        "eli5": "This is like a labeled box where you store something.",
        "beginner": "Declares a variable - a container with a type.",
        "developer": "Variable declaration with explicit type specification.",
        "color": "#d19a66"  # Orange
    },
    "comment": {
        "eli5": "This is a note to help people understand the code - the computer ignores it.",
        "beginner": "A comment that explains the code but doesn't run.",
        "developer": "A non-executable comment for code documentation.",
        "color": "#5c6370"  # Gray
    },
    "public": {
        "eli5": "This means anyone can use this part of the code.",
        "beginner": "A public access modifier - visible everywhere.",
        "developer": "Public access modifier for unrestricted visibility.",
        "color": "#c678dd"  # Purple
    },
    "static": {
        "eli5": "This means it belongs to the blueprint, not individual things made from it.",
        "beginner": "Static means it belongs to the class, not objects.",
        "developer": "Static modifier indicating class-level membership.",
        "color": "#c678dd"  # Purple
    },
    "void": {
        "eli5": "This means it doesn't give anything back.",
        "beginner": "Void means the method doesn't return a value.",
        "developer": "Void return type indicating no value is returned.",
        "color": "#c678dd"  # Purple
    },
    "string": {
        "eli5": "This is text - letters and words in quotes.",
        "beginner": "A string - text data enclosed in quotes.",
        "developer": "A string literal representing textual data.",
        "color": "#98c379"  # Green
    },
    "private": {
        "eli5": "This means only this class can use it - it's a secret.",
        "beginner": "Private access modifier - only visible within the class.",
        "developer": "Private access modifier restricting visibility to declaring class.",
        "color": "#c678dd"  # Purple
    },
    "protected": {
        "eli5": "This means only family members (related classes) can use it.",
        "beginner": "Protected - visible to the class and its subclasses.",
        "developer": "Protected access modifier for subclass and package visibility.",
        "color": "#c678dd"  # Purple
    },
    "final": {
        "eli5": "This means it can't be changed once it's set.",
        "beginner": "Final - a constant value that cannot be changed.",
        "developer": "Final modifier preventing reassignment or inheritance.",
        "color": "#c678dd"  # Purple
    },
    "new": {
        "eli5": "This creates a brand new thing from a blueprint.",
        "beginner": "New - creates a new instance of a class.",
        "developer": "Object instantiation operator allocating memory.",
        "color": "#c678dd"  # Purple
    },
    "this": {
        "eli5": "This refers to the current object itself.",
        "beginner": "This - refers to the current object instance.",
        "developer": "Reference to the current object instance.",
        "color": "#e5c07b"  # Yellow
    },
    "super": {
        "eli5": "This refers to the parent class.",
        "beginner": "Super - refers to the parent/superclass.",
        "developer": "Reference to the superclass for method or constructor calls.",
        "color": "#e5c07b"  # Yellow
    },
    "extends": {
        "eli5": "This means a class inherits from another class.",
        "beginner": "Extends - inherits from a parent class.",
        "developer": "Inheritance declaration extending a superclass.",
        "color": "#c678dd"  # Purple
    },
    "implements": {
        "eli5": "This means a class promises to have certain abilities.",
        "beginner": "Implements - the class follows an interface's rules.",
        "developer": "Interface implementation declaration.",
        "color": "#c678dd"  # Purple
    },
    "interface": {
        "eli5": "This is a contract - a list of things a class must do.",
        "beginner": "Interface - defines methods that classes must implement.",
        "developer": "Abstract type defining a contract for implementing classes.",
        "color": "#e5c07b"  # Yellow
    },
    "abstract": {
        "eli5": "This is incomplete and needs to be finished by another class.",
        "beginner": "Abstract - a class or method that must be completed by subclasses.",
        "developer": "Abstract modifier for incomplete class/method definitions.",
        "color": "#c678dd"  # Purple
    },
    "try": {
        "eli5": "This tries to do something that might not work.",
        "beginner": "Try block - attempts code that might cause an error.",
        "developer": "Exception handling block for potentially failing operations.",
        "color": "#e06c75"  # Red
    },
    "catch": {
        "eli5": "This catches mistakes and handles them nicely.",
        "beginner": "Catch block - handles errors when they happen.",
        "developer": "Exception handler catching specific exception types.",
        "color": "#e06c75"  # Red
    },
    "finally": {
        "eli5": "This always runs, no matter what happened before.",
        "beginner": "Finally block - code that always executes after try/catch.",
        "developer": "Cleanup block that executes regardless of exception occurrence.",
        "color": "#e06c75"  # Red
    },
    "throw": {
        "eli5": "This creates an error on purpose.",
        "beginner": "Throw - deliberately causes an exception.",
        "developer": "Statement throwing an exception object.",
        "color": "#e06c75"  # Red
    },
    "throws": {
        "eli5": "This warns that a method might cause an error.",
        "beginner": "Throws - declares that a method may throw an exception.",
        "developer": "Method signature declaring potential exceptions.",
        "color": "#e06c75"  # Red
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
    "switch": {
        "eli5": "This picks one choice from many options.",
        "beginner": "Switch - selects one of many code blocks to run.",
        "developer": "Multi-branch conditional based on value matching.",
        "color": "#c678dd"  # Purple
    },
    "case": {
        "eli5": "This is one of the choices in a switch.",
        "beginner": "Case - one option in a switch statement.",
        "developer": "Label in switch statement for value matching.",
        "color": "#c678dd"  # Purple
    },
    "default": {
        "eli5": "This happens when none of the other choices match.",
        "beginner": "Default - the fallback option in a switch.",
        "developer": "Default label in switch for unmatched cases.",
        "color": "#c678dd"  # Purple
    },
    "null": {
        "eli5": "This means nothing - like an empty box.",
        "beginner": "Null - represents no value or nothing.",
        "developer": "Null reference indicating absence of an object.",
        "color": "#d19a66"  # Orange
    },
    "true": {
        "eli5": "This means yes or correct.",
        "beginner": "True - a boolean value meaning yes/correct.",
        "developer": "Boolean literal representing logical truth.",
        "color": "#d19a66"  # Orange
    },
    "false": {
        "eli5": "This means no or incorrect.",
        "beginner": "False - a boolean value meaning no/incorrect.",
        "developer": "Boolean literal representing logical falsehood.",
        "color": "#d19a66"  # Orange
    },
    "array": {
        "eli5": "This is a row of boxes that hold things in order.",
        "beginner": "Array - a fixed-size collection of items.",
        "developer": "Fixed-length indexed collection of elements.",
        "color": "#98c379"  # Green
    },
    "ArrayList": {
        "eli5": "This is a list that can grow bigger as you add things.",
        "beginner": "ArrayList - a resizable list collection.",
        "developer": "Dynamic array implementation from Collections framework.",
        "color": "#98c379"  # Green
    },
    "HashMap": {
        "eli5": "This is like a dictionary - you look up a word to find its meaning.",
        "beginner": "HashMap - stores pairs of keys and values.",
        "developer": "Hash table based Map implementation for key-value storage.",
        "color": "#98c379"  # Green
    },
    "Scanner": {
        "eli5": "This reads what you type on the keyboard.",
        "beginner": "Scanner - reads input from the user.",
        "developer": "Input parser for reading primitive types and strings.",
        "color": "#56b6c2"  # Cyan
    },
    "constructor": {
        "eli5": "This sets up a new object when it's created.",
        "beginner": "Constructor - initializes a new object.",
        "developer": "Special method called during object instantiation.",
        "color": "#61afef"  # Blue
    },
    "instanceof": {
        "eli5": "This checks if something is a certain type.",
        "beginner": "Instanceof - checks if an object is of a specific type.",
        "developer": "Type comparison operator for runtime type checking.",
        "color": "#c678dd"  # Purple
    },
    "enum": {
        "eli5": "This is a list of named choices, like days of the week.",
        "beginner": "Enum - a set of named constant values.",
        "developer": "Enumerated type defining a fixed set of constants.",
        "color": "#e5c07b"  # Yellow
    }
}

def detect_features_in_line(line):
    """
    Detects all features in a line and returns them with their positions.
    """
    features = []
    line_lower = line.lower()
    
    patterns = [
        ('for ', 'for_loop'),
        ('for(', 'for_loop'),
        ('while ', 'while_loop'),
        ('while(', 'while_loop'),
        ('if ', 'if_statement'),
        ('if(', 'if_statement'),
        ('else', 'else_statement'),
        ('class ', 'class'),
        ('interface ', 'interface'),
        ('enum ', 'enum'),
        ('import ', 'import'),
        ('return ', 'return'),
        ('return;', 'return'),
        ('system.out.print', 'system_out'),
        ('//', 'comment'),
        ('/*', 'comment'),
        ('public ', 'public'),
        ('private ', 'private'),
        ('protected ', 'protected'),
        ('static ', 'static'),
        ('final ', 'final'),
        ('void ', 'void'),
        ('abstract ', 'abstract'),
        ('new ', 'new'),
        ('this.', 'this'),
        ('this)', 'this'),
        ('super.', 'super'),
        ('super(', 'super'),
        ('extends ', 'extends'),
        ('implements ', 'implements'),
        ('try ', 'try'),
        ('try{', 'try'),
        ('catch ', 'catch'),
        ('catch(', 'catch'),
        ('finally ', 'finally'),
        ('finally{', 'finally'),
        ('throw ', 'throw'),
        ('throws ', 'throws'),
        ('break;', 'break'),
        ('break ', 'break'),
        ('continue;', 'continue'),
        ('continue ', 'continue'),
        ('switch ', 'switch'),
        ('switch(', 'switch'),
        ('case ', 'case'),
        ('default:', 'default'),
        ('null', 'null'),
        ('true', 'true'),
        ('false', 'false'),
        ('instanceof ', 'instanceof'),
        ('ArrayList', 'ArrayList'),
        ('HashMap', 'HashMap'),
        ('Scanner', 'Scanner'),
    ]
    
    # Find all pattern matches
    for pattern, feature_type in patterns:
        start = 0
        while True:
            pos = line_lower.find(pattern, start)
            if pos == -1:
                break
            
            keyword = line[pos:pos + len(pattern)]
            features.append({
                'keyword': keyword.strip(),
                'start': pos,
                'end': pos + len(pattern),
                'type': feature_type
            })
            start = pos + 1
    
    # Check for variable types
    var_types = ['int ', 'String ', 'double ', 'float ', 'boolean ', 'char ', 'long ', 'short ', 'byte ', 'Object ', 'List ', 'Map ', 'Set ']
    for var_type in var_types:
        pos = line.find(var_type)
        if pos != -1:
            features.append({
                'keyword': var_type.strip(),
                'start': pos,
                'end': pos + len(var_type),
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