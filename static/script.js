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

// Track the currently active tooltip for mobile dismissal
let activeTooltip = null;
let activeElement = null;

function setupTooltip(element) {
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = element.getAttribute('data-tooltip');
    document.body.appendChild(tooltip);
    
    function showTooltip() {
        // Hide any previously active tooltip
        if (activeTooltip && activeTooltip !== tooltip) {
            activeTooltip.style.opacity = '0';
            activeTooltip.style.visibility = 'hidden';
            if (activeElement) {
                activeElement.classList.remove('tooltip-active');
            }
        }
        
        const rect = element.getBoundingClientRect();
        const tooltipWidth = 280;
        
        // Calculate left position, keeping tooltip within viewport
        let left = rect.left + (rect.width / 2);
        const viewportWidth = window.innerWidth;
        
        // Clamp so tooltip doesn't go off-screen
        if (left - tooltipWidth / 2 < 10) {
            left = tooltipWidth / 2 + 10;
        } else if (left + tooltipWidth / 2 > viewportWidth - 10) {
            left = viewportWidth - tooltipWidth / 2 - 10;
        }
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = rect.bottom + 8 + window.scrollY + 'px';
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
        
        activeTooltip = tooltip;
        activeElement = element;
        element.classList.add('tooltip-active');
    }
    
    function hideTooltip() {
        tooltip.style.opacity = '0';
        tooltip.style.visibility = 'hidden';
        element.classList.remove('tooltip-active');
        if (activeTooltip === tooltip) {
            activeTooltip = null;
            activeElement = null;
        }
    }
    
    // Desktop: show on hover
    element.addEventListener('mouseenter', showTooltip);
    element.addEventListener('mouseleave', hideTooltip);
    
    // Mobile: toggle on tap
    element.addEventListener('touchstart', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (activeTooltip === tooltip && tooltip.style.opacity === '1') {
            hideTooltip();
        } else {
            showTooltip();
        }
    }, { passive: false });
}

// Dismiss tooltip when tapping outside on mobile
document.addEventListener('touchstart', function(e) {
    if (activeTooltip && activeElement && !activeElement.contains(e.target)) {
        activeTooltip.style.opacity = '0';
        activeTooltip.style.visibility = 'hidden';
        activeElement.classList.remove('tooltip-active');
        activeTooltip = null;
        activeElement = null;
    }
});

function loadExample(lang) {
    const pythonExample = `for i in range(5):
    print(i)`;
    
    const javaExample = `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}`;

    const javascriptExample = `async function fetchData() {
    const response = await fetch('https://api.example.com/data');
    const data = await response.json();
    console.log(data);
}

const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(n => n * 2);
console.log(doubled);`;

    const cppExample = `#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int> numbers = {1, 2, 3, 4, 5};
    
    for (int num : numbers) {
        cout << num << endl;
    }
    
    return 0;
}`;

    const sqlExample = `SELECT 
    e.name,
    e.department,
    COUNT(o.order_id) AS total_orders,
    SUM(o.amount) AS total_sales
FROM employees e
LEFT JOIN orders o ON e.id = o.employee_id
WHERE e.status = 'active'
    AND o.order_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY e.name, e.department
HAVING SUM(o.amount) > 10000
ORDER BY total_sales DESC
LIMIT 10;`;
    
    if (lang === 'python') {
        document.getElementById('code').value = pythonExample;
        document.getElementById('language').value = 'python';
    } else if (lang === 'java') {
        document.getElementById('code').value = javaExample;
        document.getElementById('language').value = 'java';
    } else if (lang === 'javascript') {
        document.getElementById('code').value = javascriptExample;
        document.getElementById('language').value = 'javascript';
    } else if (lang === 'cpp') {
        document.getElementById('code').value = cppExample;
        document.getElementById('language').value = 'cpp';
    } else if (lang === 'sql') {
        document.getElementById('code').value = sqlExample;
        document.getElementById('language').value = 'sql';
    }
}