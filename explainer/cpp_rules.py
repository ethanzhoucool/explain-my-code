# Explanation templates for C++
TEMPLATES = {
    "for_loop": {
        "eli5": "This repeats something over and over, like counting on your fingers.",
        "beginner": "A for loop that repeats code a certain number of times.",
        "developer": "A for-loop with initialization, condition, and increment.",
        "color": "#e06c75"  # Red
    },
    "range_for": {
        "eli5": "This goes through each item in a list, one by one.",
        "beginner": "A range-based for loop that iterates over each element.",
        "developer": "A range-based for loop (C++11) iterating over containers.",
        "color": "#e06c75"  # Red
    },
    "while_loop": {
        "eli5": "This keeps going until you say stop, like playing until dinner time.",
        "beginner": "A while loop that runs as long as a condition is true.",
        "developer": "A while-loop that executes while a boolean condition remains true.",
        "color": "#e06c75"  # Red
    },
    "do_while": {
        "eli5": "This does something at least once, then keeps going if the condition is true.",
        "beginner": "A do-while loop that always runs at least once.",
        "developer": "A do-while loop with post-condition evaluation.",
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
    "else_if": {
        "eli5": "This checks another choice if the first one wasn't true.",
        "beginner": "An else if that checks another condition.",
        "developer": "An else-if clause for additional conditional branching.",
        "color": "#c678dd"  # Purple
    },
    "function": {
        "eli5": "This is like a recipe - you give it ingredients and it makes something.",
        "beginner": "A function - a reusable block of code.",
        "developer": "A function definition that encapsulates logic and accepts parameters.",
        "color": "#61afef"  # Blue
    },
    "main": {
        "eli5": "This is where the program starts - like the first page of a book.",
        "beginner": "The main function - where your C++ program begins.",
        "developer": "The entry point of a C++ application.",
        "color": "#61afef"  # Blue
    },
    "cout": {
        "eli5": "This shows a message on the screen.",
        "beginner": "Prints output to the console.",
        "developer": "Standard output stream for console output.",
        "color": "#56b6c2"  # Cyan
    },
    "cin": {
        "eli5": "This asks you to type something.",
        "beginner": "Gets input from the user via the console.",
        "developer": "Standard input stream for console input.",
        "color": "#56b6c2"  # Cyan
    },
    "class": {
        "eli5": "This is a blueprint for making things, like LEGO instructions.",
        "beginner": "A class - a template for creating objects.",
        "developer": "A class definition encapsulating data and behavior.",
        "color": "#e5c07b"  # Yellow
    },
    "struct": {
        "eli5": "This groups related things together, like a form with fields.",
        "beginner": "A struct - a way to group related data together.",
        "developer": "A structure with public members by default.",
        "color": "#e5c07b"  # Yellow
    },
    "include": {
        "eli5": "This brings in extra tools, like getting crayons from another room.",
        "beginner": "Includes a header file - bringing in code from libraries.",
        "developer": "Preprocessor directive to include header files.",
        "color": "#c678dd"  # Purple
    },
    "namespace": {
        "eli5": "This is like a folder that keeps names organized.",
        "beginner": "A namespace groups related code together.",
        "developer": "Namespace declaration for scope organization.",
        "color": "#c678dd"  # Purple
    },
    "using": {
        "eli5": "This lets you use things without typing their full address.",
        "beginner": "Using lets you access names without the namespace prefix.",
        "developer": "Using directive/declaration for namespace access.",
        "color": "#c678dd"  # Purple
    },
    "return": {
        "eli5": "This gives back an answer, like when someone answers '4' to '2+2?'",
        "beginner": "Returns a value from a function.",
        "developer": "Returns a value from a function, terminating execution.",
        "color": "#c678dd"  # Purple
    },
    "int": {
        "eli5": "This stores whole numbers like 1, 2, 3.",
        "beginner": "An integer - a whole number without decimals.",
        "developer": "Integer data type for whole number storage.",
        "color": "#d19a66"  # Orange
    },
    "double": {
        "eli5": "This stores numbers with decimal points like 3.14.",
        "beginner": "A double - a number that can have decimals.",
        "developer": "Double-precision floating-point data type.",
        "color": "#d19a66"  # Orange
    },
    "float": {
        "eli5": "This stores numbers with decimal points (smaller than double).",
        "beginner": "A float - a decimal number with less precision than double.",
        "developer": "Single-precision floating-point data type.",
        "color": "#d19a66"  # Orange
    },
    "char": {
        "eli5": "This stores a single letter or symbol.",
        "beginner": "A char - a single character like 'a' or '!'.",
        "developer": "Character data type for single byte storage.",
        "color": "#d19a66"  # Orange
    },
    "bool": {
        "eli5": "This stores yes/no or true/false.",
        "beginner": "A bool - stores true or false.",
        "developer": "Boolean data type for logical values.",
        "color": "#d19a66"  # Orange
    },
    "string": {
        "eli5": "This is text - letters and words.",
        "beginner": "A string - text data like words and sentences.",
        "developer": "String class from the standard library for text handling.",
        "color": "#98c379"  # Green
    },
    "void": {
        "eli5": "This means it doesn't give anything back.",
        "beginner": "Void means the function doesn't return a value.",
        "developer": "Void return type indicating no value is returned.",
        "color": "#c678dd"  # Purple
    },
    "const": {
        "eli5": "This means it can't be changed once it's set.",
        "beginner": "Const - a value that cannot be changed.",
        "developer": "Const qualifier for immutable values.",
        "color": "#c678dd"  # Purple
    },
    "auto": {
        "eli5": "This lets the computer figure out what type something is.",
        "beginner": "Auto automatically determines the variable type.",
        "developer": "Type inference keyword (C++11) for automatic type deduction.",
        "color": "#c678dd"  # Purple
    },
    "comment": {
        "eli5": "This is a note to help people understand the code - the computer ignores it.",
        "beginner": "A comment that explains the code but doesn't run.",
        "developer": "A non-executable comment for code documentation.",
        "color": "#5c6370"  # Gray
    },
    "public": {
        "eli5": "This means anyone can use this part of the code.",
        "beginner": "Public - visible and accessible everywhere.",
        "developer": "Public access specifier for unrestricted member access.",
        "color": "#c678dd"  # Purple
    },
    "private": {
        "eli5": "This means only this class can use it - it's a secret.",
        "beginner": "Private - only visible within the class.",
        "developer": "Private access specifier restricting member access.",
        "color": "#c678dd"  # Purple
    },
    "protected": {
        "eli5": "This means only family members (related classes) can use it.",
        "beginner": "Protected - visible to the class and its children.",
        "developer": "Protected access specifier for inheritance visibility.",
        "color": "#c678dd"  # Purple
    },
    "static": {
        "eli5": "This means it belongs to the blueprint, not individual things made from it.",
        "beginner": "Static means it belongs to the class, not objects.",
        "developer": "Static modifier for class-level or persistent storage.",
        "color": "#c678dd"  # Purple
    },
    "virtual": {
        "eli5": "This lets child classes do something their own way.",
        "beginner": "Virtual allows child classes to override the function.",
        "developer": "Virtual function enabling runtime polymorphism.",
        "color": "#c678dd"  # Purple
    },
    "override": {
        "eli5": "This replaces what the parent class does.",
        "beginner": "Override replaces a parent class function.",
        "developer": "Override specifier for explicit virtual function override.",
        "color": "#c678dd"  # Purple
    },
    "new": {
        "eli5": "This creates something new and gives you its address.",
        "beginner": "New creates a new object in memory.",
        "developer": "Dynamic memory allocation operator.",
        "color": "#c678dd"  # Purple
    },
    "delete": {
        "eli5": "This removes something from memory when you're done with it.",
        "beginner": "Delete frees memory that was allocated with new.",
        "developer": "Memory deallocation operator for dynamic storage.",
        "color": "#c678dd"  # Purple
    },
    "nullptr": {
        "eli5": "This means 'points to nothing'.",
        "beginner": "Nullptr represents a pointer that points to nothing.",
        "developer": "Null pointer literal (C++11) for pointer initialization.",
        "color": "#d19a66"  # Orange
    },
    "this": {
        "eli5": "This refers to the current object itself.",
        "beginner": "This - a pointer to the current object.",
        "developer": "Pointer to the current object instance.",
        "color": "#e5c07b"  # Yellow
    },
    "try": {
        "eli5": "This tries to do something that might not work.",
        "beginner": "A try block that attempts code that might fail.",
        "developer": "Exception handling try block for error-prone code.",
        "color": "#e06c75"  # Red
    },
    "catch": {
        "eli5": "This catches mistakes if something goes wrong.",
        "beginner": "A catch block that handles errors.",
        "developer": "Exception handling catch clause for error recovery.",
        "color": "#e06c75"  # Red
    },
    "throw": {
        "eli5": "This creates an error on purpose.",
        "beginner": "Throw signals that an error occurred.",
        "developer": "Throws an exception to be caught by a try-catch block.",
        "color": "#e06c75"  # Red
    },
    "switch": {
        "eli5": "This checks multiple choices, like choosing from a menu.",
        "beginner": "A switch statement that selects from multiple options.",
        "developer": "Switch statement for multi-branch conditional logic.",
        "color": "#c678dd"  # Purple
    },
    "case": {
        "eli5": "This is one of the choices in a switch.",
        "beginner": "A case in a switch statement.",
        "developer": "Case label within a switch block.",
        "color": "#c678dd"  # Purple
    },
    "default": {
        "eli5": "This is what happens if no other choice matches.",
        "beginner": "Default case when no other cases match.",
        "developer": "Default label for unmatched switch cases.",
        "color": "#c678dd"  # Purple
    },
    "break": {
        "eli5": "This stops and exits the current loop or switch.",
        "beginner": "Break exits the current loop or switch.",
        "developer": "Break statement terminating loop or switch execution.",
        "color": "#c678dd"  # Purple
    },
    "continue": {
        "eli5": "This skips to the next round of the loop.",
        "beginner": "Continue skips to the next loop iteration.",
        "developer": "Continue statement jumping to next iteration.",
        "color": "#c678dd"  # Purple
    },
    "true": {
        "eli5": "This means 'yes' or 'correct'.",
        "beginner": "True - a boolean value meaning yes/correct.",
        "developer": "Boolean true literal.",
        "color": "#d19a66"  # Orange
    },
    "false": {
        "eli5": "This means 'no' or 'wrong'.",
        "beginner": "False - a boolean value meaning no/incorrect.",
        "developer": "Boolean false literal.",
        "color": "#d19a66"  # Orange
    },
    "vector": {
        "eli5": "This is like a list that can grow or shrink.",
        "beginner": "A vector - a dynamic array that can change size.",
        "developer": "STL vector container for dynamic arrays.",
        "color": "#98c379"  # Green
    },
    "array": {
        "eli5": "This is a fixed list of things.",
        "beginner": "An array - a fixed-size collection of items.",
        "developer": "Fixed-size array container or C-style array.",
        "color": "#98c379"  # Green
    },
    "map": {
        "eli5": "This stores pairs of things, like a dictionary.",
        "beginner": "A map stores key-value pairs.",
        "developer": "STL map container for associative key-value storage.",
        "color": "#98c379"  # Green
    },
    "set": {
        "eli5": "This stores unique things - no duplicates allowed.",
        "beginner": "A set stores unique values only.",
        "developer": "STL set container for unique sorted elements.",
        "color": "#98c379"  # Green
    },
    "pointer": {
        "eli5": "This stores the address of where something is in memory.",
        "beginner": "A pointer holds the memory address of a variable.",
        "developer": "Pointer type for indirect memory access.",
        "color": "#d19a66"  # Orange
    },
    "reference": {
        "eli5": "This is another name for the same thing.",
        "beginner": "A reference is an alias for another variable.",
        "developer": "Reference type for aliasing existing objects.",
        "color": "#d19a66"  # Orange
    },
    "template": {
        "eli5": "This is a pattern that works with different types.",
        "beginner": "A template creates code that works with any type.",
        "developer": "Template for generic programming and type parameterization.",
        "color": "#61afef"  # Blue
    },
    "typename": {
        "eli5": "This says 'this is a type name' in templates.",
        "beginner": "Typename declares a type parameter in templates.",
        "developer": "Typename keyword for template type parameters.",
        "color": "#c678dd"  # Purple
    },
    "endl": {
        "eli5": "This goes to a new line when printing.",
        "beginner": "Endl creates a new line in output.",
        "developer": "End-line manipulator flushing the output buffer.",
        "color": "#56b6c2"  # Cyan
    },
    "sizeof": {
        "eli5": "This tells you how much space something takes.",
        "beginner": "Sizeof returns the size of a type in bytes.",
        "developer": "Sizeof operator returning size in bytes.",
        "color": "#c678dd"  # Purple
    },
    "inline": {
        "eli5": "This suggests putting the function code directly where it's called.",
        "beginner": "Inline suggests the compiler expand the function at call sites.",
        "developer": "Inline specifier for potential function inlining.",
        "color": "#c678dd"  # Purple
    },
    "friend": {
        "eli5": "This lets another class or function access private things.",
        "beginner": "Friend gives another class access to private members.",
        "developer": "Friend declaration for external private member access.",
        "color": "#c678dd"  # Purple
    },
    "operator": {
        "eli5": "This defines how symbols like + or - work with your class.",
        "beginner": "Operator overloading defines custom behavior for operators.",
        "developer": "Operator overloading for custom type operations.",
        "color": "#61afef"  # Blue
    },
    "lambda": {
        "eli5": "This is a small unnamed function you write right where you need it.",
        "beginner": "A lambda is an inline anonymous function.",
        "developer": "Lambda expression for inline function objects (C++11).",
        "color": "#61afef"  # Blue
    },
    "unique_ptr": {
        "eli5": "This is a smart pointer that's the only one pointing to something.",
        "beginner": "Unique_ptr is a smart pointer with exclusive ownership.",
        "developer": "Unique pointer for exclusive ownership semantics.",
        "color": "#56b6c2"  # Cyan
    },
    "shared_ptr": {
        "eli5": "This is a smart pointer that can share with others.",
        "beginner": "Shared_ptr is a smart pointer that can be shared.",
        "developer": "Shared pointer for shared ownership with reference counting.",
        "color": "#56b6c2"  # Cyan
    },
}


def detect_features_in_line(line):
    """
    Detect C++ features in a single line of code.
    """
    features = []
    line_lower = line.lower()
    
    patterns = [
        # Preprocessor
        ('#include', 'include'),
        
        # Namespaces
        ('using namespace', 'using'),
        ('namespace ', 'namespace'),
        ('std::', 'namespace'),
        
        # Loops
        ('for (', 'for_loop'),
        ('for(', 'for_loop'),
        ('while (', 'while_loop'),
        ('while(', 'while_loop'),
        ('do {', 'do_while'),
        ('do{', 'do_while'),
        
        # Conditionals
        ('if (', 'if_statement'),
        ('if(', 'if_statement'),
        ('else if', 'else_if'),
        ('else {', 'else_statement'),
        ('else{', 'else_statement'),
        
        # I/O
        ('cout', 'cout'),
        ('cin', 'cin'),
        ('endl', 'endl'),
        
        # Classes and structs
        ('class ', 'class'),
        ('struct ', 'struct'),
        ('public:', 'public'),
        ('private:', 'private'),
        ('protected:', 'protected'),
        
        # Functions
        ('int main', 'main'),
        ('void main', 'main'),
        ('virtual ', 'virtual'),
        ('override', 'override'),
        ('inline ', 'inline'),
        ('friend ', 'friend'),
        ('operator', 'operator'),
        
        # Templates
        ('template', 'template'),
        ('typename', 'typename'),
        
        # Control flow
        ('return ', 'return'),
        ('return;', 'return'),
        ('switch ', 'switch'),
        ('switch(', 'switch'),
        ('case ', 'case'),
        ('default:', 'default'),
        ('break;', 'break'),
        ('break ', 'break'),
        ('continue;', 'continue'),
        ('continue ', 'continue'),
        
        # Exception handling
        ('try {', 'try'),
        ('try{', 'try'),
        ('catch ', 'catch'),
        ('catch(', 'catch'),
        ('throw ', 'throw'),
        
        # Memory
        ('new ', 'new'),
        ('delete ', 'delete'),
        ('delete[]', 'delete'),
        ('nullptr', 'nullptr'),
        
        # Modifiers
        ('const ', 'const'),
        ('static ', 'static'),
        ('auto ', 'auto'),
        ('void ', 'void'),
        
        # Pointers and references
        ('this->', 'this'),
        ('this)', 'this'),
        
        # Booleans
        ('true', 'true'),
        ('false', 'false'),
        
        # STL containers
        ('vector<', 'vector'),
        ('vector <', 'vector'),
        ('array<', 'array'),
        ('map<', 'map'),
        ('set<', 'set'),
        ('string ', 'string'),
        ('string>', 'string'),
        
        # Smart pointers
        ('unique_ptr', 'unique_ptr'),
        ('shared_ptr', 'shared_ptr'),
        
        # Other
        ('sizeof', 'sizeof'),
        ('[](', 'lambda'),
        ('[](' , 'lambda'),
        
        # Comments
        ('//', 'comment'),
        ('/*', 'comment'),
    ]
    
    # Find all pattern matches
    for pattern, feature_type in patterns:
        start = 0
        while True:
            pos = line_lower.find(pattern.lower(), start)
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
    var_types = ['int ', 'double ', 'float ', 'char ', 'bool ', 'long ', 'short ', 'unsigned ']
    for var_type in var_types:
        pos = line.find(var_type)
        if pos != -1:
            type_name = var_type.strip()
            features.append({
                'keyword': type_name,
                'start': pos,
                'end': pos + len(var_type),
                'type': type_name if type_name in TEMPLATES else 'int'
            })
    
    # Check for pointers and references
    if '*' in line and ('int*' in line or 'char*' in line or 'double*' in line or 'int *' in line):
        features.append({
            'keyword': '*',
            'start': line.find('*'),
            'end': line.find('*') + 1,
            'type': 'pointer'
        })
    
    if '&' in line and not '&&' in line:
        pos = line.find('&')
        if pos > 0 and line[pos-1] != '&' and (pos + 1 >= len(line) or line[pos+1] != '&'):
            features.append({
                'keyword': '&',
                'start': pos,
                'end': pos + 1,
                'type': 'reference'
            })
    
    # Sort by position
    features.sort(key=lambda x: x['start'])
    
    return features


def build_highlighted_line(line, level):
    """
    Builds HTML with highlighted keywords and tooltips.
    """
    # Skip lines that are comments
    stripped = line.strip()
    if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        return line, False
    
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
        
        if explanation:
            result.append(
                f'<span class="highlight" style="background-color: {color}; color: white;" '
                f'data-tooltip="{explanation}">{keyword}</span>'
            )
        else:
            result.append(keyword)
        
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
