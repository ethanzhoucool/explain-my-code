document.addEventListener('DOMContentLoaded', function() {
    // Handle Tab key in textarea for code input
    const codeTextarea = document.getElementById('code');
    if (codeTextarea) {
        codeTextarea.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.selectionStart;
                const end = this.selectionEnd;
                
                // Insert 4 spaces at cursor position
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                
                // Move cursor after the inserted spaces
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });
    }

    // Handle example buttons
    const exampleButtons = document.querySelectorAll('.example-btn');
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            loadExample(lang);
        });
    });

    // Handle highlights for tooltips (rule-based mode)
    const highlights = document.querySelectorAll('.highlight');
    highlights.forEach(highlight => {
        setupTooltip(highlight);
    });

    // Handle AI line highlights (AI mode)
    const aiHighlights = document.querySelectorAll('.ai-line-highlight');
    aiHighlights.forEach(highlight => {
        setupTooltip(highlight);
    });
});

function setupTooltip(element) {
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = element.getAttribute('data-tooltip');
    document.body.appendChild(tooltip);
    
    // Show tooltip on hover
    element.addEventListener('mouseenter', function(e) {
        const rect = element.getBoundingClientRect();
        
        // Position tooltip below the element
        tooltip.style.left = rect.left + (rect.width / 2) + 'px';
        tooltip.style.top = rect.bottom + 8 + window.scrollY + 'px';
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
    });
    
    // Hide tooltip on mouse leave
    element.addEventListener('mouseleave', function() {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
    });
}

function loadExample(lang) {
    const pythonExample = `for i in range(5):
    print(i)`;
    
    const javaExample = `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}`;
    
    if (lang === 'python') {
        document.getElementById('code').value = pythonExample;
        document.getElementById('language').value = 'python';
    } else {
        document.getElementById('code').value = javaExample;
        document.getElementById('language').value = 'java';
    }
}