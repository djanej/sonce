// Simple Markdown to HTML converter for news posts
class MarkdownConverter {
    constructor() {
        this.rules = [
            // Headers
            { pattern: /^### (.*$)/gim, replacement: '<h3 class="text-xl font-semibold mt-6 mb-3">$1</h3>' },
            { pattern: /^## (.*$)/gim, replacement: '<h2 class="text-2xl font-semibold mt-8 mb-4">$1</h2>' },
            { pattern: /^# (.*$)/gim, replacement: '<h1 class="text-3xl font-bold mt-8 mb-4">$1</h1>' },
            
            // Images (place before links so it doesn't get treated as a link)
            { pattern: /!\[([^\]]*)\]\(([^)]+)\)/g, replacement: '<img src="$2" alt="$1" class="my-4 rounded-lg max-w-full h-auto">' },

            // Bold and italic
            { pattern: /\*\*(.*?)\*\*/g, replacement: '<strong class="font-semibold">$1</strong>' },
            { pattern: /\*(.*?)\*/g, replacement: '<em class="italic">$1</em>' },
            
            // Code blocks
            { pattern: /```([\s\S]*?)```/g, replacement: '<pre><code>$1</code></pre>' },
            { pattern: /`([^`]+)`/g, replacement: '<code>$1</code>' },
            
            // Links
            { pattern: /\[([^\]]+)\]\(([^)]+)\)/g, replacement: '<a href="$2">$1</a>' },
            
            // Blockquotes
            { pattern: /^>\s?(.*$)/gim, replacement: '<blockquote>$1</blockquote>' },

            // Lists (use temporary flags to allow grouping later)
            { pattern: /^\* (.*$)/gim, replacement: '<li data-ul="1">$1</li>' },
            { pattern: /^- (.*$)/gim, replacement: '<li data-ul="1">$1</li>' },
            { pattern: /^(\d+)\. (.*$)/gim, replacement: '<li data-ol="1">$2</li>' },
            
            // Paragraphs
            { pattern: /^\s*(\n)?(.+)/gm, replacement: function(match) {
                return match.trim() ? '<p>' + match.trim() + '</p>' : '';
            }},
            
            // Line breaks
            { pattern: /\n\n/g, replacement: '</p>\n<p>' },
            
            // Clean up empty paragraphs
            { pattern: /<p><\/p>/g, replacement: '' },
            { pattern: /<p>\s*<\/p>/g, replacement: '' }
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
        // Remove paragraph wrappers around list items to avoid invalid markup
        html = html.replace(/<p>\s*(<li[^>]*>.*?<\/li>)\s*<\/p>/gs, '$1');
        // Group consecutive unordered list items
        html = html.replace(/(?:\n|^)((?:<li[^>]*data-ul=\"1\"[^>]*>.*?<\/li>\s*)+)/g, function(_m, list){
            return '<ul>' + list + '<\/ul>';
        });
        // Group consecutive ordered list items
        html = html.replace(/(?:\n|^)((?:<li[^>]*data-ol=\"1\"[^>]*>.*?<\/li>\s*)+)/g, function(_m, list){
            return '<ol>' + list + '<\/ol>';
        });
        // Remove temporary data flags
        html = html.replace(/\sdata-ul=\"1\"/g, '');
        html = html.replace(/\sdata-ol=\"1\"/g, '');
        // Remove paragraph wrappers around ul/ol that may have been introduced
        html = html.replace(/<p>\s*((?:<ul|<ol)[\s\S]*?<\/(?:ul|ol)>)\s*<\/p>/g, '$1');
        
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