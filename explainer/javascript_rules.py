# Explanation templates for JavaScript
TEMPLATES = {
    "for_loop": {
        "eli5": "This repeats something over and over, like counting on your fingers.",
        "beginner": "A for loop that repeats code a certain number of times.",
        "developer": "A for-loop with initialization, condition, and increment.",
        "color": "#e06c75"  # Red
    },
    "for_of": {
        "eli5": "This goes through each item in a list, one by one.",
        "beginner": "A for...of loop that iterates over each element in an array.",
        "developer": "A for-of loop iterating over iterable objects.",
        "color": "#e06c75"  # Red
    },
    "for_in": {
        "eli5": "This goes through each property name in an object.",
        "beginner": "A for...in loop that iterates over object properties.",
        "developer": "A for-in loop iterating over enumerable property keys.",
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
        "developer": "A function declaration that encapsulates logic and accepts parameters.",
        "color": "#61afef"  # Blue
    },
    "arrow_function": {
        "eli5": "This is a shorter way to write a recipe.",
        "beginner": "An arrow function - a shorter way to write functions.",
        "developer": "An arrow function expression with lexical 'this' binding.",
        "color": "#61afef"  # Blue
    },
    "async_function": {
        "eli5": "This is a function that can wait for things to finish.",
        "beginner": "An async function that can wait for operations to complete.",
        "developer": "An async function that returns a Promise and enables await.",
        "color": "#61afef"  # Blue
    },
    "await": {
        "eli5": "This waits for something to finish before continuing.",
        "beginner": "Await pauses until a promise resolves.",
        "developer": "Await operator that pauses async function execution until Promise settles.",
        "color": "#c678dd"  # Purple
    },
    "console_log": {
        "eli5": "This shows a message on the screen.",
        "beginner": "Prints output to the console.",
        "developer": "Outputs data to the browser or Node.js console.",
        "color": "#56b6c2"  # Cyan
    },
    "class": {
        "eli5": "This is a blueprint for making things, like LEGO instructions.",
        "beginner": "A class - a template for creating objects.",
        "developer": "A class definition encapsulating data and behavior (ES6+).",
        "color": "#e5c07b"  # Yellow
    },
    "constructor": {
        "eli5": "This sets up a new object when it's created.",
        "beginner": "A constructor that initializes new objects.",
        "developer": "Constructor method called during object instantiation.",
        "color": "#61afef"  # Blue
    },
    "import": {
        "eli5": "This brings in extra tools from another file.",
        "beginner": "Imports code from another module or file.",
        "developer": "ES6 module import statement.",
        "color": "#c678dd"  # Purple
    },
    "export": {
        "eli5": "This shares code so other files can use it.",
        "beginner": "Exports code to be used by other modules.",
        "developer": "ES6 module export statement.",
        "color": "#c678dd"  # Purple
    },
    "require": {
        "eli5": "This brings in extra tools from another file (Node.js style).",
        "beginner": "Requires a module in Node.js.",
        "developer": "CommonJS require statement for module loading.",
        "color": "#c678dd"  # Purple
    },
    "return": {
        "eli5": "This gives back an answer, like when someone answers '4' to '2+2?'",
        "beginner": "Returns a value from a function.",
        "developer": "Returns a value from a function, terminating execution.",
        "color": "#c678dd"  # Purple
    },
    "let": {
        "eli5": "This creates a box to store something that can change.",
        "beginner": "Declares a variable that can be reassigned.",
        "developer": "Block-scoped variable declaration with reassignment capability.",
        "color": "#d19a66"  # Orange
    },
    "const": {
        "eli5": "This creates a box that can't be swapped for a different box.",
        "beginner": "Declares a constant that cannot be reassigned.",
        "developer": "Block-scoped constant declaration preventing reassignment.",
        "color": "#d19a66"  # Orange
    },
    "var": {
        "eli5": "This creates a box to store something (older way).",
        "beginner": "Declares a variable (older style, use let instead).",
        "developer": "Function-scoped variable declaration with hoisting.",
        "color": "#d19a66"  # Orange
    },
    "comment": {
        "eli5": "This is a note to help people understand the code - the computer ignores it.",
        "beginner": "A comment that explains the code but doesn't run.",
        "developer": "A non-executable comment for code documentation.",
        "color": "#5c6370"  # Gray
    },
    "string": {
        "eli5": "This is text - letters and words in quotes.",
        "beginner": "A string - text data enclosed in quotes.",
        "developer": "A string literal representing textual data.",
        "color": "#98c379"  # Green
    },
    "template_literal": {
        "eli5": "This is a special string where you can put variables inside using ${}.",
        "beginner": "A template literal - a string with embedded expressions.",
        "developer": "Template literal with expression interpolation and multi-line support.",
        "color": "#98c379"  # Green
    },
    "array": {
        "eli5": "This is like a list where you keep many things together.",
        "beginner": "An array - a collection that holds multiple items.",
        "developer": "Array data structure storing ordered elements.",
        "color": "#98c379"  # Green
    },
    "object": {
        "eli5": "This is like a labeled box with compartments for different things.",
        "beginner": "An object - a collection of key-value pairs.",
        "developer": "Object literal for storing keyed data and functionality.",
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
    "finally": {
        "eli5": "This always runs at the end, no matter what happened.",
        "beginner": "Finally block that always executes after try/catch.",
        "developer": "Finally clause for guaranteed cleanup execution.",
        "color": "#e06c75"  # Red
    },
    "throw": {
        "eli5": "This creates an error on purpose.",
        "beginner": "Throws an error to signal something went wrong.",
        "developer": "Throws an exception to be caught by a try-catch block.",
        "color": "#e06c75"  # Red
    },
    "new": {
        "eli5": "This creates a brand new thing from a blueprint.",
        "beginner": "New - creates a new instance of a class or object.",
        "developer": "Object instantiation operator.",
        "color": "#c678dd"  # Purple
    },
    "this": {
        "eli5": "This refers to the current object itself.",
        "beginner": "This - refers to the current object or context.",
        "developer": "Reference to the execution context, varies by call site.",
        "color": "#e5c07b"  # Yellow
    },
    "extends": {
        "eli5": "This means a class inherits from another class.",
        "beginner": "Extends - inherits from a parent class.",
        "developer": "Class inheritance declaration extending a superclass.",
        "color": "#c678dd"  # Purple
    },
    "super": {
        "eli5": "This refers to the parent class.",
        "beginner": "Super - calls the parent class constructor or methods.",
        "developer": "Reference to the superclass for constructor or method calls.",
        "color": "#e5c07b"  # Yellow
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
    "null": {
        "eli5": "This means 'nothing' or 'empty' on purpose.",
        "beginner": "Null represents an intentional absence of value.",
        "developer": "Null primitive representing intentional absence of object value.",
        "color": "#d19a66"  # Orange
    },
    "undefined": {
        "eli5": "This means something hasn't been given a value yet.",
        "beginner": "Undefined means a variable hasn't been assigned.",
        "developer": "Undefined primitive for uninitialized or missing values.",
        "color": "#d19a66"  # Orange
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
    "typeof": {
        "eli5": "This tells you what kind of thing something is.",
        "beginner": "Typeof checks what type a value is.",
        "developer": "Typeof operator returning type as a string.",
        "color": "#c678dd"  # Purple
    },
    "instanceof": {
        "eli5": "This checks if something was made from a certain blueprint.",
        "beginner": "Instanceof checks if an object is from a specific class.",
        "developer": "Instanceof operator testing prototype chain membership.",
        "color": "#c678dd"  # Purple
    },
    "promise": {
        "eli5": "This is a promise to give you something later.",
        "beginner": "A Promise represents a value available in the future.",
        "developer": "Promise object for asynchronous operation handling.",
        "color": "#61afef"  # Blue
    },
    "then": {
        "eli5": "This says what to do after a promise is kept.",
        "beginner": "Then handles the result when a promise completes.",
        "developer": "Promise.then() for handling fulfilled promises.",
        "color": "#61afef"  # Blue
    },
    "fetch": {
        "eli5": "This goes and gets information from the internet.",
        "beginner": "Fetch retrieves data from a URL (like an API).",
        "developer": "Fetch API for making HTTP requests returning Promises.",
        "color": "#56b6c2"  # Cyan
    },
    "map": {
        "eli5": "This transforms each item in a list into something new.",
        "beginner": "Map creates a new array by transforming each element.",
        "developer": "Array.map() for functional transformation of array elements.",
        "color": "#56b6c2"  # Cyan
    },
    "filter": {
        "eli5": "This picks out only the items you want from a list.",
        "beginner": "Filter creates a new array with items that pass a test.",
        "developer": "Array.filter() for creating subset arrays based on predicate.",
        "color": "#56b6c2"  # Cyan
    },
    "reduce": {
        "eli5": "This combines all items in a list into one thing.",
        "beginner": "Reduce combines array elements into a single value.",
        "developer": "Array.reduce() for accumulating array values.",
        "color": "#56b6c2"  # Cyan
    },
    "foreach": {
        "eli5": "This does something to each item in a list.",
        "beginner": "ForEach runs a function on each array element.",
        "developer": "Array.forEach() for iterating with side effects.",
        "color": "#56b6c2"  # Cyan
    },
    "spread": {
        "eli5": "This spreads out items from an array or object.",
        "beginner": "Spread (...) expands arrays or objects.",
        "developer": "Spread syntax for expanding iterables or object properties.",
        "color": "#c678dd"  # Purple
    },
    "destructure": {
        "eli5": "This unpacks values from arrays or objects into variables.",
        "beginner": "Destructuring extracts values into separate variables.",
        "developer": "Destructuring assignment for extracting values from arrays/objects.",
        "color": "#d19a66"  # Orange
    },
    "document": {
        "eli5": "This represents the web page.",
        "beginner": "Document is the web page you can interact with.",
        "developer": "DOM Document object for web page manipulation.",
        "color": "#56b6c2"  # Cyan
    },
    "queryselector": {
        "eli5": "This finds an element on the web page.",
        "beginner": "querySelector finds an HTML element by CSS selector.",
        "developer": "DOM querySelector for CSS-based element selection.",
        "color": "#56b6c2"  # Cyan
    },
    "addeventlistener": {
        "eli5": "This makes something happen when you click or type.",
        "beginner": "addEventListener waits for user actions like clicks.",
        "developer": "DOM event listener registration for event handling.",
        "color": "#56b6c2"  # Cyan
    },
    "setinterval": {
        "eli5": "This repeats something every few seconds.",
        "beginner": "setInterval runs code repeatedly at set intervals.",
        "developer": "Timer function for recurring execution at specified intervals.",
        "color": "#56b6c2"  # Cyan
    },
    "settimeout": {
        "eli5": "This waits a bit, then does something once.",
        "beginner": "setTimeout runs code once after a delay.",
        "developer": "Timer function for delayed single execution.",
        "color": "#56b6c2"  # Cyan
    },
    "json": {
        "eli5": "This is a way to write data that computers can easily read.",
        "beginner": "JSON is a format for storing and sending data.",
        "developer": "JavaScript Object Notation for data serialization.",
        "color": "#98c379"  # Green
    },
}


def detect_features_in_line(line):
    """
    Detect JavaScript features in a single line of code.
    """
    features = []
    line_lower = line.lower()
    
    patterns = [
        # Loops
        ('for (', 'for_loop'),
        ('for(', 'for_loop'),
        ('for await', 'for_of'),
        (' of ', 'for_of'),
        (' in ', 'for_in'),
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
        
        # Functions
        ('function ', 'function'),
        ('function(', 'function'),
        ('=>', 'arrow_function'),
        ('async ', 'async_function'),
        ('await ', 'await'),
        
        # Output
        ('console.log', 'console_log'),
        ('console.error', 'console_log'),
        ('console.warn', 'console_log'),
        
        # Classes
        ('class ', 'class'),
        ('constructor(', 'constructor'),
        ('constructor (', 'constructor'),
        ('extends ', 'extends'),
        ('super(', 'super'),
        ('super.', 'super'),
        
        # Modules
        ('import ', 'import'),
        ('export ', 'export'),
        ('require(', 'require'),
        
        # Variables
        ('let ', 'let'),
        ('const ', 'const'),
        ('var ', 'var'),
        
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
        
        # Error handling
        ('try {', 'try'),
        ('try{', 'try'),
        ('catch ', 'catch'),
        ('catch(', 'catch'),
        ('finally ', 'finally'),
        ('finally{', 'finally'),
        ('throw ', 'throw'),
        
        # Objects and classes
        ('new ', 'new'),
        ('this.', 'this'),
        ('this)', 'this'),
        ('this,', 'this'),
        
        # Type checking
        ('typeof ', 'typeof'),
        ('instanceof ', 'instanceof'),
        
        # Literals
        ('null', 'null'),
        ('undefined', 'undefined'),
        ('true', 'true'),
        ('false', 'false'),
        
        # Promises and async
        ('new promise', 'promise'),
        ('promise.', 'promise'),
        ('.then(', 'then'),
        ('fetch(', 'fetch'),
        
        # Array methods
        ('.map(', 'map'),
        ('.filter(', 'filter'),
        ('.reduce(', 'reduce'),
        ('.foreach(', 'foreach'),
        
        # Spread and destructuring
        ('...', 'spread'),
        
        # DOM
        ('document.', 'document'),
        ('queryselector', 'queryselector'),
        ('addeventlistener', 'addeventlistener'),
        
        # Timers
        ('setinterval(', 'setinterval'),
        ('settimeout(', 'settimeout'),
        
        # JSON
        ('json.parse', 'json'),
        ('json.stringify', 'json'),
        
        # Comments
        ('//', 'comment'),
        ('/*', 'comment'),
        
        # Template literals
        ('`', 'template_literal'),
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
