#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.join(__dirname, '..');
const CONTENT_DIR = path.join(ROOT, 'content', 'news');

function toSlug(input){
  return String(input || '')
    .trim()
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function truncate(text, max = 180){
  const s = String(text || '');
  if (s.length <= max) return s;
  const sliced = s.slice(0, max);
  const lastSpace = sliced.lastIndexOf(' ');
  const safeCut = lastSpace > max * 0.6 ? lastSpace : max;
  return sliced.slice(0, safeCut).trim() + '…';
}

function normalizeTags(tags){
  if (!tags) return [];
  if (Array.isArray(tags)) return tags.map(t => String(t).trim()).filter(Boolean);
  if (typeof tags === 'string') return tags.split(',').map(t => t.trim()).filter(Boolean);
  return [];
}

function pick(obj, keys){
  const out = {};
  for (const k of keys){ if (Object.prototype.hasOwnProperty.call(obj, k)) out[k] = obj[k]; }
  return out;
}

const FILENAME_RE = /^(?:\d{8}|\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const HERO_RE = /^\/static\/uploads\/news\/\d{4}\/\d{2}\/[A-Za-z0-9._/-]+$/;

async function readFileSafe(p){
  try { return await fs.readFile(p, 'utf8'); } catch { return null; }
}

async function listMarkdown(dir){
  try {
    const files = await fs.readdir(dir);
    return files.filter(f => f.toLowerCase().endsWith('.md'));
  } catch { return []; }
}

function parseFrontmatter(raw){
  const fmMatch = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) return null;
  const yaml = {};
  fmMatch[1].split('\n').forEach(line => {
    const idx = line.indexOf(':');
    if (idx === -1) return;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if (!key) return;
    if (value.startsWith('[') && value.endsWith(']')){
      value = value.slice(1, -1).split(',').map(v=>v.trim()).filter(Boolean);
    } else if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith('\'') && value.endsWith('\''))){
      value = value.slice(1, -1);
    }
    yaml[key] = value;
  });
  return yaml;
}

function validateFrontmatter(yaml, filename){
  const errors = [];
  if (!yaml || typeof yaml !== 'object'){
    errors.push('missing frontmatter block');
    return errors;
  }
  if (!yaml.title || String(yaml.title).trim() === '') errors.push('title is required');
  if (!yaml.date || !DATE_RE.test(String(yaml.date))) errors.push('date must be YYYY-MM-DD');
  if (yaml.slug && !SLUG_RE.test(String(yaml.slug))) errors.push('slug format invalid');
  if (yaml.image && !HERO_RE.test(String(yaml.image))) errors.push('image path must be under /static/uploads/news/YYYY/MM/');
  if (Array.isArray(yaml.tags) && !yaml.tags.every(t => typeof t === 'string')) errors.push('tags must be array of strings');
  // derived suggestions
  if (!yaml.slug && yaml.title){
    const derived = toSlug(yaml.title);
    if (!derived) errors.push('slug would be empty when derived from title');
  }
  // filename consistency (if date in filename uses 8-digit format, accept that)
  if (!FILENAME_RE.test(filename)) errors.push('filename must match YYYY-MM-DD-slug.md or YYYYMMDD-slug.md');
  return errors;
}

function toIsoDate(d){
  try { return new Date(d).toISOString().slice(0,10); } catch { return String(d || ''); }
}

async function buildIndexEntry(filename, yaml, markdown){
  const slug = yaml.slug ? String(yaml.slug) : toSlug(String(yaml.title || ''));
  const date = toIsoDate(yaml.date);
  const pathAbs = `/content/news/${filename}`;
  const bodyMatch = markdown.match(/^---\n[\s\S]*?\n---\n\n([\s\S]*)/);
  const body = bodyMatch ? bodyMatch[1] : '';
  const words = String(body).split(/\s+/).filter(Boolean).length;
  const readingTimeMinutes = Math.max(1, Math.ceil(words / 200));
  // Compute excerpt: prefer frontmatter summary/description, otherwise first paragraph of body (markdown stripped lightly)
  const firstPara = String(body).split(/\n{2,}/)[0] || '';
  const bodyPlain = firstPara
    .replace(/!\[[^\]]*\]\([^\)]+\)/g, '') // images
    .replace(/\[[^\]]*\]\([^\)]+\)/g, '$1') // links -> text
    .replace(/`{1,3}[^`]*`{1,3}/g, '') // inline code
    .replace(/^\s*[>#*-]+\s*/gm, '') // list markers / blockquotes
    .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1') // emphasis
    .replace(/\s+/g, ' ') // collapse whitespace
    .trim();
  const excerpt = truncate(yaml.excerpt || yaml.summary || yaml.description || bodyPlain, 180);
  const base = {
    id: `${date}-${slug}`,
    title: String(yaml.title || ''),
    date,
    author: String(yaml.author || ''),
    summary: String(yaml.summary || yaml.description || ''),
    excerpt,
    description: excerpt,
    hero: String(yaml.hero || yaml.image || ''),
    imageAlt: String(yaml.imageAlt || yaml.title || ''),
    tags: normalizeTags(yaml.tags),
    slug,
    filename,
    path: pathAbs,
    link: pathAbs,
    readingTimeMinutes,
    readingTimeLabel: `${readingTimeMinutes} min`
  };
  // remove empty optionals
  return Object.fromEntries(Object.entries(base).filter(([,v]) => v !== '' && !(Array.isArray(v) && v.length === 0)));
}

async function main(){
  const files = await listMarkdown(CONTENT_DIR);
  if (!files.length){
    console.log('No markdown files in content/news');
    return;
  }
  let hasErrors = false;
  const entries = [];
  for (const filename of files){
    const full = path.join(CONTENT_DIR, filename);
    const raw = await readFileSafe(full);
    if (!raw){
      console.error(`✖ Cannot read ${filename}`);
      hasErrors = true;
      continue;
    }
    const yaml = parseFrontmatter(raw);
    const errs = validateFrontmatter(yaml, filename);
    if (errs.length){
      hasErrors = true;
      console.error(`✖ ${filename}:`);
      errs.forEach(e => console.error(`  - ${e}`));
    } else {
      console.log(`✔ ${filename} OK`);
    }
    // Build entry regardless, for preview
    const entry = await buildIndexEntry(filename, yaml || {}, raw);
    entries.push(entry);
  }

  // Sort desc by date
  entries.sort((a,b) => String(b.date || '').localeCompare(String(a.date || '')));

  const indexPath = path.join(CONTENT_DIR, 'index.json');
  await fs.writeFile(indexPath, JSON.stringify(entries, null, 2) + '\n', 'utf8');
  console.log(`Wrote ${entries.length} entries to content/news/index.json`);

  if (hasErrors){
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`){
  main().catch(err => {
    console.error(err);
    process.exitCode = 1;
  });
}

