import fs from 'node:fs/promises';
import path from 'node:path';
import matter from 'gray-matter';
import { marked } from 'marked';

const ROOT = path.resolve('.');
const INPUT_DIR = path.join(ROOT, 'content', 'news-src');
const OUTPUT_DIR = path.join(ROOT, 'content', 'news');

function toSlug(input){
	return String(input || '')
		.trim()
		.toLowerCase()
		.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
		.replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function stripHtml(html){
	return String(html || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

function truncate(text, max=180){
	if (!text) return '';
	if (text.length <= max) return text;
	const sliced = text.slice(0, max);
	const lastSpace = sliced.lastIndexOf(' ');
	const safeCut = lastSpace > max * 0.6 ? lastSpace : max;
	return sliced.slice(0, safeCut).trim() + '…';
}

async function ensureDir(dir){
	await fs.mkdir(dir, { recursive: true });
}

async function listMarkdown(dir){
	try {
		const entries = await fs.readdir(dir, { withFileTypes: true });
		return entries.filter(e => e.isFile() && e.name.toLowerCase().endsWith('.md')).map(e => path.join(dir, e.name));
	} catch (e){
		return [];
	}
}

function computeExcerpt(frontmatter, markdown, html){
	if (frontmatter.excerpt) return truncate(String(frontmatter.excerpt));
	if (frontmatter.description) return truncate(String(frontmatter.description));
	const firstPara = String(markdown || '').split(/\n{2,}/)[0];
	if (firstPara) return truncate(stripHtml(firstPara));
	return truncate(stripHtml(html));
}

async function build(){
	await ensureDir(OUTPUT_DIR);
	const files = await listMarkdown(INPUT_DIR);
	const posts = [];
	for (const file of files){
		const raw = await fs.readFile(file, 'utf8');
		const parsed = matter(raw);
		const fm = parsed.data || {};
		const md = parsed.content || '';
		const title = fm.title || path.basename(file, path.extname(file));
		const slug = fm.slug ? toSlug(fm.slug) : toSlug(title);
		if (!slug){
			console.warn(`[warn] Skipping ${file} because slug is empty.`);
			continue;
		}
		const date = fm.date ? new Date(fm.date).toISOString() : new Date().toISOString();
		const author = fm.author || '';
		const hero = fm.hero || fm.image || fm.cover || '';
		const tags = Array.isArray(fm.tags) ? fm.tags : (typeof fm.tags === 'string' ? fm.tags.split(',').map(s => s.trim()).filter(Boolean) : []);
		const html = marked.parse(md);
		const excerpt = computeExcerpt(fm, md, html);
		await fs.writeFile(path.join(OUTPUT_DIR, `${slug}.html`), html, 'utf8');
		posts.push({ slug, title, date, author, hero, tags, excerpt });
	}
	posts.sort((a,b) => String(b.date || '').localeCompare(String(a.date || '')));
	await fs.writeFile(path.join(OUTPUT_DIR, 'index.json'), JSON.stringify(posts, null, 2), 'utf8');
	console.log(`[news-build] Generated ${posts.length} posts to ${path.relative(ROOT, OUTPUT_DIR)}`);
}

build().catch(err => {
	console.error('[news-build] Build failed:', err);
	process.exitCode = 1;
});