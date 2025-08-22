// Simple Markdown to HTML converter for news posts
class MarkdownConverter {
    constructor() {
        this.rules = [
            // Headers
            { pattern: /^### (.*$)/gim, replacement: '<h3 class="text-xl font-semibold mt-6 mb-3 text-gray-800">$1</h3>' },
            { pattern: /^## (.*$)/gim, replacement: '<h2 class="text-2xl font-semibold mt-8 mb-4 text-gray-900">$1</h2>' },
            { pattern: /^# (.*$)/gim, replacement: '<h1 class="text-3xl font-bold mt-8 mb-4 text-gray-900">$1</h1>' },
            
            // Bold and italic
            { pattern: /\*\*(.*?)\*\*/g, replacement: '<strong class="font-semibold">$1</strong>' },
            { pattern: /\*(.*?)\*/g, replacement: '<em class="italic">$1</em>' },
            
            // Code blocks
            { pattern: /```([\s\S]*?)```/g, replacement: '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>$1</code></pre>' },
            { pattern: /`([^`]+)`/g, replacement: '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>' },
            
            // Links
            { pattern: /\[([^\]]+)\]\(([^)]+)\)/g, replacement: '<a href="$2" class="text-primary hover:underline">$1</a>' },
            
            // Lists
            { pattern: /^\* (.*$)/gim, replacement: '<li class="ml-4">$1</li>' },
            { pattern: /^- (.*$)/gim, replacement: '<li class="ml-4">$1</li>' },
            { pattern: /^(\d+)\. (.*$)/gim, replacement: '<li class="ml-4">$2</li>' },
            
            // Paragraphs
            { pattern: /^\s*(\n)?(.+)/gm, replacement: function(match) {
                return match.trim() ? '<p class="mb-4 text-gray-700 leading-relaxed">' + match.trim() + '</p>' : '';
            }},
            
            // Line breaks
            { pattern: /\n\n/g, replacement: '</p>\n<p class="mb-4 text-gray-700 leading-relaxed">' },
            
            // Clean up empty paragraphs
            { pattern: /<p class="mb-4 text-gray-700 leading-relaxed"><\/p>/g, replacement: '' },
            { pattern: /<p class="mb-4 text-gray-700 leading-relaxed">\s*<\/p>/g, replacement: '' }
        ];
    }

    convert(markdown) {
        if (!markdown) return '';
        
        let html = markdown;
        
        // Apply all conversion rules
        this.rules.forEach(rule => {
            if (typeof rule.replacement === 'function') {
                html = html.replace(rule.pattern, rule.replacement);
            } else {
                html = html.replace(rule.pattern, rule.replacement);
            }
        });
        
        // Wrap lists properly
        html = html.replace(/(<li.*<\/li>)/gs, '<ul class="list-disc mb-4 ml-6">$1</ul>');
        html = html.replace(/(<li.*<\/li>)/gs, '<ol class="list-decimal mb-4 ml-6">$1</ol>');
        
        // Clean up multiple list wrappers
        html = html.replace(/<\/ul>\s*<ul[^>]*>/g, '');
        html = html.replace(/<\/ol>\s*<ol[^>]*>/g, '');
        
        // Clean up empty content
        html = html.replace(/<p[^>]*>\s*<\/p>/g, '');
        
        return html.trim();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownConverter;
} else if (typeof window !== 'undefined') {
    window.MarkdownConverter = MarkdownConverter;
}