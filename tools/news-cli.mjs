#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONTENT_DIR = path.join(__dirname, '..', 'content', 'news');
const UPLOADS_DIR = path.join(__dirname, '..', 'static', 'uploads', 'news');

// Ensure directories exist
async function ensureDirectories() {
    try {
        await fs.mkdir(CONTENT_DIR, { recursive: true });
        await fs.mkdir(UPLOADS_DIR, { recursive: true });
    } catch (error) {
        console.error('Error creating directories:', error.message);
        process.exit(1);
    }
}

// Generate slug from title
function generateSlug(title) {
    return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
}

// Generate filename from date and slug
function generateFilename(date, slug) {
    const dateStr = date.replace(/-/g, '');
    return `${dateStr}-${slug}.md`;
}

// Copy image to uploads directory
async function copyImage(imagePath, date, slug, description = 'hero') {
    if (!imagePath || !fs.existsSync(imagePath)) {
        console.warn(`Warning: Image not found at ${imagePath}`);
        return null;
    }

    const ext = path.extname(imagePath);
    const year = date.split('-')[0];
    const month = date.split('-')[1];
    
    // Create year/month directories
    const yearDir = path.join(UPLOADS_DIR, year);
    const monthDir = path.join(yearDir, month);
    await fs.mkdir(monthDir, { recursive: true });
    
    // Generate new filename
    const newFilename = `${date}-${slug}-${description}${ext}`;
    const newPath = path.join(monthDir, newFilename);
    
    // Copy image
    await fs.copyFile(imagePath, newPath);
    
    // Return web path
    return `/static/uploads/news/${year}/${month}/${newFilename}`;
}

// Create frontmatter
function createFrontmatter(data) {
    const frontmatter = {
        title: data.title,
        date: data.date,
        author: data.author || '',
        slug: data.slug || generateSlug(data.title),
        image: data.image || '',
        imageAlt: data.imageAlt || data.title,
        summary: data.summary || '',
        tags: data.tags ? data.tags.split(',').map(t => t.trim()) : []
    };

    // Filter out empty values
    Object.keys(frontmatter).forEach(key => {
        if (frontmatter[key] === '' || (Array.isArray(frontmatter[key]) && frontmatter[key].length === 0)) {
            delete frontmatter[key];
        }
    });

    return frontmatter;
}

// Create post content
function createPostContent(frontmatter, body) {
    const yaml = Object.entries(frontmatter)
        .map(([key, value]) => {
            if (Array.isArray(value)) {
                return `${key}: [${value.join(', ')}]`;
            }
            return `${key}: "${value}"`;
        })
        .join('\n');

    return `---\n${yaml}\n---\n\n${body || ''}`;
}

// Create new post
async function createPost(options) {
    await ensureDirectories();
    
    const {
        title,
        date,
        author,
        slug,
        image,
        copyImage: shouldCopyImage,
        tags,
        summary,
        body
    } = options;

    if (!title || !date) {
        console.error('Error: title and date are required');
        process.exit(1);
    }

    const finalSlug = slug || generateSlug(title);
    const filename = generateFilename(date, finalSlug);
    const filepath = path.join(CONTENT_DIR, filename);

    // Check if file already exists
    try {
        await fs.access(filepath);
        console.error(`Error: Post already exists at ${filepath}`);
        process.exit(1);
    } catch (error) {
        // File doesn't exist, continue
    }

    // Handle image copying
    let finalImage = image;
    if (shouldCopyImage && image) {
        finalImage = await copyImage(image, date, finalSlug);
        if (finalImage) {
            console.log(`Image copied to: ${finalImage}`);
        }
    }

    // Create frontmatter
    const frontmatter = createFrontmatter({
        title,
        date,
        author,
        slug: finalSlug,
        image: finalImage,
        tags,
        summary,
        body
    });

    // Create post content
    const content = createPostContent(frontmatter, body || '');

    // Write file
    try {
        await fs.writeFile(filepath, content, 'utf8');
        console.log(`✅ Post created: ${filepath}`);
        
        // Rebuild index
        await rebuildIndex();
        
        return {
            filename,
            filepath,
            slug: finalSlug,
            image: finalImage
        };
    } catch (error) {
        console.error('Error creating post:', error.message);
        process.exit(1);
    }
}

// Rebuild index.json
async function rebuildIndex() {
    await ensureDirectories();
    
    try {
        const files = await fs.readdir(CONTENT_DIR);
        const markdownFiles = files.filter(f => f.endsWith('.md'));
        
        const posts = [];
        
        for (const file of markdownFiles) {
            try {
                const filepath = path.join(CONTENT_DIR, file);
                const content = await fs.readFile(filepath, 'utf8');
                
                // Parse frontmatter
                const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
                if (!frontmatterMatch) continue;
                
                const frontmatter = frontmatterMatch[1];
                const yaml = {};
                
                frontmatter.split('\n').forEach(line => {
                    const [key, ...valueParts] = line.split(':');
                    if (key && valueParts.length > 0) {
                        let value = valueParts.join(':').trim();
                        
                        // Handle array values
                        if (value.startsWith('[') && value.endsWith(']')) {
                            value = value.slice(1, -1).split(',').map(v => v.trim());
                        }
                        
                        // Remove quotes from string values
                        if (typeof value === 'string' && value.startsWith('"') && value.endsWith('"')) {
                            value = value.slice(1, -1);
                        }
                        
                        yaml[key.trim()] = value;
                    }
                });
                
                // Extract body content
                const bodyMatch = content.match(/^---\n[\s\S]*?\n---\n\n([\s\S]*)/);
                const body = bodyMatch ? bodyMatch[1] : '';
                
                // Calculate reading time (rough estimate: 200 words per minute)
                const wordCount = body.split(/\s+/).length;
                const readingTimeMinutes = Math.ceil(wordCount / 200);
                
                const post = {
                    id: `${yaml.date}-${yaml.slug || generateSlug(yaml.title)}`,
                    title: yaml.title || '',
                    date: yaml.date || '',
                    author: yaml.author || '',
                    summary: yaml.summary || '',
                    image: yaml.image || '',
                    imageAlt: yaml.imageAlt || yaml.title || '',
                    tags: Array.isArray(yaml.tags) ? yaml.tags : [],
                    slug: yaml.slug || generateSlug(yaml.title),
                    filename: file,
                    path: `/content/news/${file}`,
                    link: `/content/news/${file}`,
                    readingTimeMinutes,
                    readingTimeLabel: `${readingTimeMinutes} min`
                };
                
                posts.push(post);
            } catch (error) {
                console.warn(`Warning: Could not parse ${file}:`, error.message);
            }
        }
        
        // Sort by date (newest first)
        posts.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        // Write index
        const indexPath = path.join(CONTENT_DIR, 'index.json');
        await fs.writeFile(indexPath, JSON.stringify(posts, null, 2), 'utf8');
        
        console.log(`✅ Index rebuilt: ${posts.length} posts indexed`);
        return posts;
        
    } catch (error) {
        console.error('Error rebuilding index:', error.message);
        process.exit(1);
    }
}

// Generate slug from title
async function generateSlugFromTitle(title) {
    if (!title) {
        console.error('Error: title is required');
        process.exit(1);
    }
    
    const slug = generateSlug(title);
    console.log(`Slug: ${slug}`);
    return slug;
}

// Show help
function showHelp() {
    console.log(`
Sonce News CLI Tool

Usage:
  node tools/news-cli.mjs <command> [options]

Commands:
  create                    Create a new post
  rebuild-index            Rebuild the index.json file
  slug <title>            Generate a slug from a title

Create Post Options:
  --title <title>         Post title (required)
  --date <date>           Publication date YYYY-MM-DD (required)
  --author <author>       Author name
  --slug <slug>           Custom URL slug
  --image <path>          Hero image path
  --copy-image            Copy image to uploads directory
  --tags <tags>           Comma-separated tags
  --summary <summary>     Post summary
  --body <content>        Post body content

Examples:
  node tools/news-cli.mjs create \\
    --title "Community Event Announcement" \\
    --date 2024-01-15 \\
    --author "John Doe" \\
    --tags "news,community,events" \\
    --summary "Join us for our annual community event" \\
    --body "This is the main content of the post..."

  node tools/news-cli.mjs rebuild-index
  node tools/news-cli.mjs slug "My Post Title"
`);
}

// Main function
async function main() {
    const args = process.argv.slice(2);
    const command = args[0];
    
    if (!command || command === '--help' || command === '-h') {
        showHelp();
        return;
    }
    
    switch (command) {
        case 'create':
            const options = {};
            for (let i = 1; i < args.length; i += 2) {
                if (args[i].startsWith('--')) {
                    const key = args[i].slice(2);
                    const value = args[i + 1];
                    if (value && !value.startsWith('--')) {
                        options[key] = value;
                    }
                }
            }
            await createPost(options);
            break;
            
        case 'rebuild-index':
            await rebuildIndex();
            break;
            
        case 'slug':
            const title = args[1];
            await generateSlugFromTitle(title);
            break;
            
        default:
            console.error(`Unknown command: ${command}`);
            showHelp();
            process.exit(1);
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch(error => {
        console.error('Error:', error.message);
        process.exit(1);
    });
}

export { createPost, rebuildIndex, generateSlug, ensureDirectories };