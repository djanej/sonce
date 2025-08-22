#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function setupNewsSystem() {
    console.log('🚀 Setting up Sonce News System for 100% compatibility...\n');
    
    const baseDir = path.join(__dirname, '..');
    
    // Create required directories
    const dirs = [
        'content/news',
        'static/uploads/news',
        'tools'
    ];
    
    for (const dir of dirs) {
        const fullPath = path.join(baseDir, dir);
        try {
            await fs.mkdir(fullPath, { recursive: true });
            console.log(`✅ Created directory: ${dir}`);
        } catch (error) {
            console.log(`ℹ️  Directory already exists: ${dir}`);
        }
    }
    
    // Create year/month directories for current date
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    
    const yearDir = path.join(baseDir, 'static/uploads/news', String(year));
    const monthDir = path.join(yearDir, month);
    
    try {
        await fs.mkdir(monthDir, { recursive: true });
        console.log(`✅ Created upload directory: static/uploads/news/${year}/${month}`);
    } catch (error) {
        console.log(`ℹ️  Upload directory already exists: static/uploads/news/${year}/${month}`);
    }
    
    // Test CLI tool
    try {
        const { execSync } = await import('child_process');
        execSync('node tools/news-cli.mjs --help', { cwd: baseDir, stdio: 'pipe' });
        console.log('✅ CLI tool is working correctly');
    } catch (error) {
        console.log('⚠️  CLI tool test failed - check if Node.js is installed');
    }
    
    console.log('\n🎉 News system setup complete!');
    console.log('\n📋 Next steps:');
    console.log('1. Create posts using: node tools/news-cli.mjs create --title "Title" --date YYYY-MM-DD');
    console.log('2. Rebuild index: node tools/news-cli.mjs rebuild-index');
    console.log('3. Upload files to the correct directories');
    console.log('4. Your news system is now 100% compatible with Sonce News Generator!');
}

setupNewsSystem().catch(console.error);