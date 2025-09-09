#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';

const ROOT = path.resolve('.');
const INDEX_PATH = path.join(ROOT, 'content', 'news', 'index.json');
const OUT_PATH = path.join(ROOT, 'sitemap-news.xml');
const SITE = 'https://sonce.org';

function esc(s){
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function postUrl(p){
  if (p.path || p.link){
    return `${SITE}/news/post.html?path=${encodeURIComponent(p.path || p.link)}`;
  }
  return `${SITE}/news/post.html?slug=${encodeURIComponent(p.slug)}`;
}

async function main(){
  let data = [];
  try {
    const raw = await fs.readFile(INDEX_PATH, 'utf8');
    const json = JSON.parse(raw);
    data = Array.isArray(json) ? json : Array.isArray(json.posts) ? json.posts : [];
  } catch {
    data = [];
  }

  const latest = new Date().toISOString().slice(0,10);
  const urls = data.slice(0, 100).map(p => {
    const title = p.title || '';
    const date = (p.date || '').slice(0,10) || latest;
    return `  <url>\n    <loc>${esc(postUrl(p))}</loc>\n    <news:news>\n      <news:publication>\n        <news:name>Sonce Slovenije</news:name>\n        <news:language>sl</news:language>\n      </news:publication>\n      <news:publication_date>${esc(date)}</news:publication_date>\n      <news:title>${esc(title)}</news:title>\n    </news:news>\n  </url>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n${urls}\n</urlset>\n`;

  await fs.writeFile(OUT_PATH, xml, 'utf8');
  console.log(`Wrote ${OUT_PATH}`);
}

if (import.meta.url === `file://${process.argv[1]}`){
  main().catch(err => { console.error(err); process.exitCode = 1; });
}

