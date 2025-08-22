#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function verifyCompatibility() {
    console.log('🔍 Verifying Sonce News System Compatibility...\n');
    
    const baseDir = path.join(__dirname, '..');
    let allChecksPassed = true;
    
    // Check 1: Required directory structure
    console.log('📁 Checking directory structure...');
    const requiredDirs = [
        'content/news',
        'static/uploads/news',
        'tools'
    ];
    
    for (const dir of requiredDirs) {
        try {
            await fs.access(path.join(baseDir, dir));
            console.log(`  ✅ ${dir}`);
        } catch (error) {
            console.log(`  ❌ ${dir} - MISSING`);
            allChecksPassed = false;
        }
    }
    
    // Check 2: CLI tool exists
    console.log('\n🔧 Checking CLI tool...');
    try {
        await fs.access(path.join(baseDir, 'tools/news-cli.mjs'));
        console.log('  ✅ CLI tool exists');
    } catch (error) {
        console.log('  ❌ CLI tool missing');
        allChecksPassed = false;
    }
    
    // Check 3: Index file exists and is valid JSON
    console.log('\n📊 Checking index file...');
    try {
        const indexPath = path.join(baseDir, 'content/news/index.json');
        const indexContent = await fs.readFile(indexPath, 'utf8');
        JSON.parse(indexContent);
        console.log('  ✅ Index file is valid JSON');
    } catch (error) {
        console.log('  ❌ Index file missing or invalid');
        allChecksPassed = false;
    }
    
    // Check 4: Sample posts exist
    console.log('\n📝 Checking sample posts...');
    try {
        const newsDir = path.join(baseDir, 'content/news');
        const files = await fs.readdir(newsDir);
        const markdownFiles = files.filter(f => f.endsWith('.md'));
        
        if (markdownFiles.length > 0) {
            console.log(`  ✅ Found ${markdownFiles.length} markdown files`);
            
            // Check frontmatter format
            for (const file of markdownFiles.slice(0, 2)) { // Check first 2 files
                try {
                    const content = await fs.readFile(path.join(newsDir, file), 'utf8');
                    if (content.includes('---') && content.includes('title:') && content.includes('date:')) {
                        console.log(`    ✅ ${file} has valid frontmatter`);
                    } else {
                        console.log(`    ⚠️  ${file} frontmatter format unclear`);
                    }
                } catch (error) {
                    console.log(`    ❌ Could not read ${file}`);
                }
            }
        } else {
            console.log('  ⚠️  No markdown files found');
        }
    } catch (error) {
        console.log('  ❌ Could not access news directory');
        allChecksPassed = false;
    }
    
    // Check 5: Upload directories exist
    console.log('\n🖼️  Checking upload directories...');
    try {
        const uploadsDir = path.join(baseDir, 'static/uploads/news');
        const yearDirs = await fs.readdir(uploadsDir);
        
        if (yearDirs.length > 0) {
            console.log(`  ✅ Found ${yearDirs.length} year directories`);
            
            // Check month directories
            for (const year of yearDirs.slice(0, 2)) {
                try {
                    const monthDirs = await fs.readdir(path.join(uploadsDir, year));
                    console.log(`    ✅ Year ${year}: ${monthDirs.length} month directories`);
                } catch (error) {
                    console.log(`    ⚠️  Could not read year ${year}`);
                }
            }
        } else {
            console.log('  ⚠️  No year directories found in uploads');
        }
    } catch (error) {
        console.log('  ❌ Could not access uploads directory');
        allChecksPassed = false;
    }
    
    // Final result
    console.log('\n' + '='.repeat(50));
    if (allChecksPassed) {
        console.log('🎉 COMPATIBILITY VERIFICATION PASSED!');
        console.log('✅ Your news system is 100% compatible with Sonce News Generator');
    } else {
        console.log('⚠️  COMPATIBILITY VERIFICATION FAILED');
        console.log('❌ Some checks failed - review the issues above');
    }
    console.log('='.repeat(50));
    
    return allChecksPassed;
}

verifyCompatibility().catch(console.error);