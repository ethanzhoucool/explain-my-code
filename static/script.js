document.addEventListener('DOMContentLoaded', function() {
    // Handle example buttons
    const exampleButtons = document.querySelectorAll('.example-btn');
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const lang = this.getAttribute('data-lang');
            loadExample(lang);
        });
    });

    // Handle highlights for tooltips (if on result page)
    const highlights = document.querySelectorAll('.highlight');
    highlights.forEach(highlight => {
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = highlight.getAttribute('data-tooltip');
        document.body.appendChild(tooltip);
        
        // Show tooltip on hover
        highlight.addEventListener('mouseenter', function(e) {
            const rect = highlight.getBoundingClientRect();
            
            // Position tooltip below the highlight
            tooltip.style.left = rect.left + (rect.width / 2) + 'px';
            tooltip.style.top = rect.bottom + 8 + window.scrollY + 'px';
            tooltip.style.opacity = '1';
            tooltip.style.visibility = 'visible';
        });
        
        // Hide tooltip on mouse leave
        highlight.addEventListener('mouseleave', function() {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        });
    });
});

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