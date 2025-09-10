// Enhanced Markdown to HTML converter for news posts
class MarkdownConverter {
    constructor() {
        this.codeBlocks = [];
        this.blockquotes = [];
    }

    // Escape HTML entities for security
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Process code blocks first to protect them from other transformations
    protectCodeBlocks(text) {
        // Fenced code blocks with optional language
        text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const index = this.codeBlocks.length;
            const escapedCode = this.escapeHtml(code.trim());
            const langClass = lang ? ` language-${lang}` : '';
            this.codeBlocks.push(`<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="block${langClass}">${escapedCode}</code></pre>`);
            return `{{CODE_BLOCK_${index}}}`;
        });

        // Inline code
        text = text.replace(/`([^`]+)`/g, (match, code) => {
            const index = this.codeBlocks.length;
            const escapedCode = this.escapeHtml(code);
            this.codeBlocks.push(`<code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono text-gray-800">${escapedCode}</code>`);
            return `{{CODE_BLOCK_${index}}}`;
        });

        return text;
    }

    // Process blockquotes
    processBlockquotes(text) {
        // Multi-line blockquotes
        text = text.replace(/(?:^|\n)((?:>\s?.*\n?)+)/g, (match, quote) => {
            const index = this.blockquotes.length;
            const content = quote.replace(/^>\s?/gm, '').trim();
            const processed = this.processInlineElements(content);
            this.blockquotes.push(`<blockquote class="border-l-4 border-orange-400 bg-orange-50 pl-4 pr-4 py-3 italic text-gray-700 my-4 rounded-r">${processed}</blockquote>`);
            return `\n{{BLOCKQUOTE_${index}}}\n`;
        });
        return text;
    }

    // Process inline elements
    processInlineElements(text) {
        // Bold (must come before italic to handle **text**)
        text = text.replace(/\*\*([^\*]+)\*\*/g, '<strong class="font-bold">$1</strong>');
        text = text.replace(/__([^_]+)__/g, '<strong class="font-bold">$1</strong>');
        
        // Italic
        text = text.replace(/\*([^\*]+)\*/g, '<em class="italic">$1</em>');
        text = text.replace(/_([^_]+)_/g, '<em class="italic">$1</em>');
        
        // Strikethrough
        text = text.replace(/~~([^~]+)~~/g, '<del class="line-through">$1</del>');
        
        // Links with title
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\s+"([^"]+)"\)/g, 
            '<a href="$2" title="$3" class="text-orange-600 hover:text-orange-700 underline underline-offset-2 transition-colors">$1</a>');
        
        // Links without title
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, 
            '<a href="$2" class="text-orange-600 hover:text-orange-700 underline underline-offset-2 transition-colors">$1</a>');
        
        // Auto-link URLs
        text = text.replace(/(https?:\/\/[^\s<]+)/g, 
            '<a href="$1" class="text-orange-600 hover:text-orange-700 underline underline-offset-2 transition-colors">$1</a>');
        
        return text;
    }

    // Process images with better error handling
    processImages(text) {
        // Images with title
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\s+"([^"]+)"\)/g, 
            '<figure class="my-6"><img src="$2" alt="$1" title="$3" class="rounded-lg shadow-md max-w-full h-auto" loading="lazy" onerror="this.onerror=null;this.src=\'/images/placeholder-news.svg\';this.classList.add(\'bg-gray-100\')"><figcaption class="text-sm text-gray-600 mt-2 text-center">$1</figcaption></figure>');
        
        // Images without title
        text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, 
            '<figure class="my-6"><img src="$2" alt="$1" class="rounded-lg shadow-md max-w-full h-auto" loading="lazy" onerror="this.onerror=null;this.src=\'/images/placeholder-news.svg\';this.classList.add(\'bg-gray-100\')">$1</figure>'.replace(/>(<\/figure>)/, '><figcaption class="text-sm text-gray-600 mt-2 text-center">$1</figcaption>$2').replace(/>(<\/figure>)/, '$1'));
        
        return text;
    }

    // Process headers with IDs for anchor links
    processHeaders(text) {
        text = text.replace(/^#### (.*$)/gim, (match, content) => {
            const id = this.slugify(content);
            return `<h4 id="${id}" class="text-lg font-semibold mt-4 mb-2 text-gray-800">${this.processInlineElements(content)}</h4>`;
        });
        
        text = text.replace(/^### (.*$)/gim, (match, content) => {
            const id = this.slugify(content);
            return `<h3 id="${id}" class="text-xl font-semibold mt-6 mb-3 text-gray-800">${this.processInlineElements(content)}</h3>`;
        });
        
        text = text.replace(/^## (.*$)/gim, (match, content) => {
            const id = this.slugify(content);
            return `<h2 id="${id}" class="text-2xl font-bold mt-8 mb-4 text-gray-900 border-b border-gray-200 pb-2">${this.processInlineElements(content)}</h2>`;
        });
        
        text = text.replace(/^# (.*$)/gim, (match, content) => {
            const id = this.slugify(content);
            return `<h1 id="${id}" class="text-3xl font-bold mt-8 mb-4 text-gray-900">${this.processInlineElements(content)}</h1>`;
        });
        
        return text;
    }

    // Process lists with nesting support
    processLists(text) {
        // Process unordered lists
        const lines = text.split('\n');
        let inList = false;
        let listType = null;
        let listItems = [];
        let result = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const unorderedMatch = line.match(/^(\s*)[\*\-\+]\s+(.+)$/);
            const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.+)$/);

            if (unorderedMatch || orderedMatch) {
                if (!inList) {
                    inList = true;
                    listType = unorderedMatch ? 'ul' : 'ol';
                }
                
                const content = unorderedMatch ? unorderedMatch[2] : orderedMatch[3];
                const indent = (unorderedMatch ? unorderedMatch[1] : orderedMatch[1]).length;
                listItems.push({ content: this.processInlineElements(content), indent });
            } else {
                if (inList) {
                    result.push(this.buildList(listItems, listType));
                    listItems = [];
                    inList = false;
                    listType = null;
                }
                result.push(line);
            }
        }

        if (inList) {
            result.push(this.buildList(listItems, listType));
        }

        return result.join('\n');
    }

    buildList(items, type) {
        const listClass = type === 'ul' 
            ? 'list-disc list-inside mb-4 ml-4 space-y-1' 
            : 'list-decimal list-inside mb-4 ml-4 space-y-1';
        
        const listTag = type === 'ul' ? 'ul' : 'ol';
        const itemsHtml = items.map(item => 
            `<li class="text-gray-700 leading-relaxed">${item.content}</li>`
        ).join('\n');
        
        return `<${listTag} class="${listClass}">\n${itemsHtml}\n</${listTag}>`;
    }

    // Process horizontal rules
    processHorizontalRules(text) {
        return text.replace(/^(?:---|\*\*\*|___)\s*$/gm, 
            '<hr class="my-8 border-t border-gray-300">');
    }

    // Process tables
    processTables(text) {
        const lines = text.split('\n');
        let result = [];
        let i = 0;

        while (i < lines.length) {
            // Check for table pattern
            if (i + 1 < lines.length && 
                lines[i].includes('|') && 
                lines[i + 1].match(/^\|?\s*:?-+:?\s*\|/)) {
                
                let tableLines = [];
                let j = i;
                
                // Collect all table lines
                while (j < lines.length && lines[j].includes('|')) {
                    tableLines.push(lines[j]);
                    j++;
                }
                
                if (tableLines.length >= 2) {
                    result.push(this.buildTable(tableLines));
                    i = j;
                    continue;
                }
            }
            
            result.push(lines[i]);
            i++;
        }

        return result.join('\n');
    }

    buildTable(lines) {
        const headers = lines[0].split('|').map(h => h.trim()).filter(h => h);
        const alignments = lines[1].split('|').map(a => {
            a = a.trim();
            if (a.startsWith(':') && a.endsWith(':')) return 'center';
            if (a.endsWith(':')) return 'right';
            return 'left';
        }).filter((a, i) => i < headers.length);

        let html = '<div class="overflow-x-auto my-6"><table class="min-w-full border border-gray-200 rounded-lg overflow-hidden">';
        html += '<thead class="bg-gray-50"><tr>';
        
        headers.forEach((header, i) => {
            const align = alignments[i] || 'left';
            html += `<th class="px-4 py-2 text-${align} text-sm font-semibold text-gray-900 border-b">${this.processInlineElements(header)}</th>`;
        });
        
        html += '</tr></thead><tbody>';

        for (let i = 2; i < lines.length; i++) {
            const cells = lines[i].split('|').map(c => c.trim()).filter(c => c !== undefined);
            if (cells.length > 0) {
                html += '<tr class="hover:bg-gray-50">';
                cells.slice(0, headers.length).forEach((cell, j) => {
                    const align = alignments[j] || 'left';
                    html += `<td class="px-4 py-2 text-${align} text-sm text-gray-700 border-b">${this.processInlineElements(cell)}</td>`;
                });
                html += '</tr>';
            }
        }

        html += '</tbody></table></div>';
        return html;
    }

    // Convert text to slug for header IDs
    slugify(text) {
        return text.toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim();
    }

    // Process paragraphs
    processParagraphs(text) {
        const lines = text.split('\n');
        let result = [];
        let paragraph = [];

        for (const line of lines) {
            if (line.trim() === '') {
                if (paragraph.length > 0) {
                    const content = paragraph.join(' ').trim();
                    if (!content.startsWith('<') && content !== '') {
                        result.push(`<p class="mb-4 text-gray-700 leading-relaxed">${this.processInlineElements(content)}</p>`);
                    } else {
                        result.push(content);
                    }
                    paragraph = [];
                }
            } else if (line.startsWith('<')) {
                if (paragraph.length > 0) {
                    const content = paragraph.join(' ').trim();
                    result.push(`<p class="mb-4 text-gray-700 leading-relaxed">${this.processInlineElements(content)}</p>`);
                    paragraph = [];
                }
                result.push(line);
            } else {
                paragraph.push(line);
            }
        }

        if (paragraph.length > 0) {
            const content = paragraph.join(' ').trim();
            if (!content.startsWith('<') && content !== '') {
                result.push(`<p class="mb-4 text-gray-700 leading-relaxed">${this.processInlineElements(content)}</p>`);
            } else {
                result.push(content);
            }
        }

        return result.join('\n');
    }

    // Restore protected content
    restoreProtectedContent(text) {
        // Restore code blocks
        this.codeBlocks.forEach((code, index) => {
            text = text.replace(`{{CODE_BLOCK_${index}}}`, code);
        });

        // Restore blockquotes
        this.blockquotes.forEach((quote, index) => {
            text = text.replace(`{{BLOCKQUOTE_${index}}}`, quote);
        });

        return text;
    }

    convert(markdown) {
        if (!markdown) return '';
        
        // Reset protected content arrays
        this.codeBlocks = [];
        this.blockquotes = [];
        
        let html = markdown;
        
        // Process in specific order to avoid conflicts
        html = this.protectCodeBlocks(html);
        html = this.processBlockquotes(html);
        html = this.processImages(html);
        html = this.processHeaders(html);
        html = this.processHorizontalRules(html);
        html = this.processTables(html);
        html = this.processLists(html);
        html = this.processParagraphs(html);
        html = this.restoreProtectedContent(html);
        
        // Clean up
        html = html.replace(/<p[^>]*>\s*<\/p>/g, '');
        html = html.replace(/\n{3,}/g, '\n\n');
        
        return html.trim();
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownConverter;
} else if (typeof window !== 'undefined') {
    window.MarkdownConverter = MarkdownConverter;
}