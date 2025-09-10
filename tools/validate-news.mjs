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
  const warnings = [];
  
  if (!yaml || typeof yaml !== 'object'){
    errors.push('missing frontmatter block');
    return { errors, warnings };
  }
  
  // Required fields
  if (!yaml.title || String(yaml.title).trim() === '') {
    errors.push('title is required');
  } else {
    const title = String(yaml.title).trim();
    // Check for test/placeholder content
    if (title.length < 3) warnings.push('title is too short (min 3 characters)');
    if (title.length > 100) warnings.push('title is too long (max 100 characters)');
    if (/^(test|asdf|qwerty|lorem|example|sample|demo)/i.test(title)) {
      warnings.push('title appears to be test/placeholder content');
    }
    if (!/^[A-Z]/.test(title) && !/^[0-9]/.test(title)) {
      warnings.push('title should start with a capital letter');
    }
    // Check for random gibberish
    if (/^[a-z]{15,}$/i.test(title.replace(/\s/g, '')) || /([a-z])\1{4,}/i.test(title)) {
      warnings.push('title appears to contain random/repeated characters');
    }
  }
  
  if (!yaml.date || !DATE_RE.test(String(yaml.date))) {
    errors.push('date must be YYYY-MM-DD');
  } else {
    const date = new Date(yaml.date);
    const now = new Date();
    const futureLimit = new Date();
    futureLimit.setDate(futureLimit.getDate() + 30);
    
    if (date > futureLimit) {
      warnings.push('date is more than 30 days in the future');
    }
    if (date < new Date('2020-01-01')) {
      warnings.push('date seems too old (before 2020)');
    }
  }
  
  // Optional fields validation
  if (yaml.slug && !SLUG_RE.test(String(yaml.slug))) {
    errors.push('slug format invalid (must be lowercase letters, numbers, and hyphens)');
  }
  
  if (yaml.image) {
    if (!HERO_RE.test(String(yaml.image))) {
      errors.push('image path must be under /static/uploads/news/YYYY/MM/');
    }
    // Check if image path matches the date in frontmatter
    const imagePath = String(yaml.image);
    const dateMatch = imagePath.match(/\/(\d{4})\/(\d{2})\//);  
    if (dateMatch && yaml.date) {
      const [, year, month] = dateMatch;
      const postDate = new Date(yaml.date);
      if (parseInt(year) !== postDate.getFullYear() || parseInt(month) !== postDate.getMonth() + 1) {
        warnings.push('image path year/month does not match post date');
      }
    }
  }
  
  if (yaml.author) {
    const author = String(yaml.author).trim();
    if (author.length < 2) warnings.push('author name is too short');
    if (/^(test|admin|user|author|writer)/i.test(author)) {
      warnings.push('author appears to be a placeholder');
    }
  }
  
  if (yaml.summary) {
    const summary = String(yaml.summary).trim();
    if (summary.length < 10) warnings.push('summary is too short (min 10 characters)');
    if (summary.length > 200) warnings.push('summary is too long (max 200 characters)');
    if (/^(test|lorem ipsum|summary|description)/i.test(summary)) {
      warnings.push('summary appears to be placeholder content');
    }
  }
  
  if (Array.isArray(yaml.tags)) {
    if (!yaml.tags.every(t => typeof t === 'string')) {
      errors.push('tags must be array of strings');
    } else if (yaml.tags.length > 10) {
      warnings.push('too many tags (max 10 recommended)');
    }
  }
  
  // Filename consistency
  if (!FILENAME_RE.test(filename)) {
    errors.push('filename must match YYYY-MM-DD-slug.md format');
  } else {
    // Check if filename date matches frontmatter date
    const filenameDateMatch = filename.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (filenameDateMatch && yaml.date) {
      const filenameDate = `${filenameDateMatch[1]}-${filenameDateMatch[2]}-${filenameDateMatch[3]}`;
      if (filenameDate !== yaml.date) {
        warnings.push('filename date does not match frontmatter date');
      }
    }
  }
  
  // Derived slug validation
  if (!yaml.slug && yaml.title){
    const derived = toSlug(yaml.title);
    if (!derived) errors.push('slug would be empty when derived from title');
  }
  
  return { errors, warnings };
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

async function validateContent(markdown) {
  const warnings = [];
  
  // Extract body content (after frontmatter)
  const bodyMatch = markdown.match(/^---\n[\s\S]*?\n---\n\n([\s\S]*)/);
  const body = bodyMatch ? bodyMatch[1] : '';
  
  if (!body || body.trim().length === 0) {
    warnings.push('post has no content body');
  } else {
    const wordCount = body.split(/\s+/).filter(Boolean).length;
    if (wordCount < 50) warnings.push(`content is very short (${wordCount} words, recommended min 50)`);
    if (wordCount > 10000) warnings.push(`content is very long (${wordCount} words, consider splitting)`);
    
    // Check for placeholder content
    if (/^(test|lorem ipsum|content goes here|placeholder)/i.test(body.substring(0, 100))) {
      warnings.push('content appears to be placeholder text');
    }
    
    // Check for broken markdown links/images
    const brokenLinks = body.match(/\[([^\]]*?)\]\(\s*\)/g);
    if (brokenLinks) warnings.push('found broken markdown links (empty href)');
    
    const brokenImages = body.match(/!\[([^\]]*?)\]\(\s*\)/g);
    if (brokenImages) warnings.push('found broken markdown images (empty src)');
  }
  
  return warnings;
}

async function main(){
  const files = await listMarkdown(CONTENT_DIR);
  if (!files.length){
    console.log('No markdown files in content/news');
    return;
  }
  let hasErrors = false;
  let hasWarnings = false;
  const entries = [];
  
  console.log('\n🔍 Validating news content...\n');
  
  for (const filename of files){
    const full = path.join(CONTENT_DIR, filename);
    const raw = await readFileSafe(full);
    if (!raw){
      console.error(`✖ Cannot read ${filename}`);
      hasErrors = true;
      continue;
    }
    
    const yaml = parseFrontmatter(raw);
    const { errors, warnings } = validateFrontmatter(yaml, filename);
    const contentWarnings = await validateContent(raw);
    const allWarnings = [...warnings, ...contentWarnings];
    
    if (errors.length > 0){
      hasErrors = true;
      console.error(`\n❌ ${filename}:`);
      console.error('  Errors:');
      errors.forEach(e => console.error(`    • ${e}`));
      if (allWarnings.length > 0) {
        console.error('  Warnings:');
        allWarnings.forEach(w => console.error(`    ⚠ ${w}`));
      }
    } else if (allWarnings.length > 0) {
      hasWarnings = true;
      console.warn(`\n⚠️  ${filename}:`);
      allWarnings.forEach(w => console.warn(`    • ${w}`));
    } else {
      console.log(`✅ ${filename}`);
    }
    
    // Build entry regardless, for preview
    const entry = await buildIndexEntry(filename, yaml || {}, raw);
    entries.push(entry);
  }

  // Sort desc by date
  entries.sort((a,b) => String(b.date || '').localeCompare(String(a.date || '')));

  const indexPath = path.join(CONTENT_DIR, 'index.json');
  await fs.writeFile(indexPath, JSON.stringify(entries, null, 2) + '\n', 'utf8');
  
  console.log(`\n📊 Summary:`);
  console.log(`   Total posts: ${entries.length}`);
  console.log(`   Index written to: content/news/index.json`);
  
  if (hasErrors) {
    console.error('\n❌ Validation failed with errors');
    process.exitCode = 1;
  } else if (hasWarnings) {
    console.warn('\n⚠️  Validation passed with warnings');
  } else {
    console.log('\n✅ All posts validated successfully!');
  }
}

if (import.meta.url === `file://${process.argv[1]}`){
  main().catch(err => {
    console.error(err);
    process.exitCode = 1;
  });
}

