// Simple Markdown to HTML converter for news posts
class MarkdownConverter {
    constructor() {
        this.rules = [
            // Headers
            { pattern: /^### (.*$)/gim, replacement: (m, t) => `<h3 id="${String(t).toLowerCase().replace(/[^a-z0-9]+/g,'-')}" class="text-xl font-semibold mt-6 mb-3 text-gray-800">${t}</h3>` },
            { pattern: /^## (.*$)/gim, replacement: (m, t) => `<h2 id="${String(t).toLowerCase().replace(/[^a-z0-9]+/g,'-')}" class="text-2xl font-semibold mt-8 mb-4 text-gray-900">${t}</h2>` },
            { pattern: /^# (.*$)/gim, replacement: (m, t) => `<h1 id="${String(t).toLowerCase().replace(/[^a-z0-9]+/g,'-')}" class="text-3xl font-bold mt-8 mb-4 text-gray-900">${t}</h1>` },
            
            // Images (place before links so it doesn't get treated as a link)
            { pattern: /!\[([^\]]*)\]\(([^)]+)\)/g, replacement: '<img src="$2" alt="$1" class="my-4 rounded-lg max-w-full h-auto">' },

            // Bold and italic
            { pattern: /\*\*(.*?)\*\*/g, replacement: '<strong class="font-semibold">$1</strong>' },
            { pattern: /\*(.*?)\*/g, replacement: '<em class="italic">$1</em>' },
            
            // Code blocks
            { pattern: /```([\s\S]*?)```/g, replacement: '<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code>$1</code></pre>' },
            { pattern: /`([^`]+)`/g, replacement: '<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">$1</code>' },
            
            // Links (open external in new tab, add rel)
            { pattern: /\[([^\]]+)\]\(([^)]+)\)/g, replacement: (m, text, href) => {
                const safeText = text;
                const url = href;
                const external = /^(?:https?:)?\/\//i.test(url);
                const attrs = external ? ' target="_blank" rel="noopener noreferrer"' : '';
                return `<a href="${url}" class="text-primary hover:underline"${attrs}>${safeText}</a>`;
            } },
            
            // Blockquotes
            { pattern: /^>\s?(.*$)/gim, replacement: '<blockquote class="border-l-4 border-gray-200 pl-4 italic text-gray-700 my-4">$1</blockquote>' },

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
        
        // Group consecutive list items into a single unordered list (simple heuristic)
        html = html.replace(/(?:<li[^>]*>.*?<\/li>\s*)+/gs, (match) => {
            return `<ul class="list-disc mb-4 ml-6">${match.replace(/\n/g,'')}</ul>`;
        });
        
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