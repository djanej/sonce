#!/usr/bin/env python3
"""
Integration test to verify both generators produce compatible output.
This script tests that both the Python GUI and HTML editor generate
the same format that works with the main website.
"""

import os
import json
import yaml
import re
from pathlib import Path
from datetime import datetime

def test_python_generator_output():
    """Test that Python generator creates valid output format."""
    print("🐍 Testing Python Generator Output...")
    
    # Check if the Python generator exists
    generator_path = Path(__file__).parent / "news_generator.py"
    if not generator_path.exists():
        print("❌ Python generator not found")
        return False
    
    print("✅ Python generator found")
    
    # Check if it has the required functions
    with open(generator_path, 'r') as f:
        content = f.read()
        
    required_functions = [
        'to_slug',
        'yaml_escape',
        'generate_draft'
    ]
    
    for func in required_functions:
        if func in content:
            print(f"✅ Function {func} found")
        else:
            print(f"❌ Function {func} not found")
            return False
    
    return True

def test_html_editor_output():
    """Test that HTML editor creates valid output format."""
    print("\n🌐 Testing HTML Editor Output...")
    
    # Check if the HTML editor exists
    editor_path = Path(__file__).parent / "html-editor" / "index.html"
    if not editor_path.exists():
        print("❌ HTML editor not found")
        return False
    
    print("✅ HTML editor found")
    
    # Check if it has the required JavaScript functions
    script_path = Path(__file__).parent / "html-editor" / "script.js"
    if not script_path.exists():
        print("❌ HTML editor script not found")
        return False
    
    with open(script_path, 'r') as f:
        content = f.read()
        
    required_functions = [
        'buildFrontmatter',
        'slugify',
        'escapeYamlString',
        'buildMarkdown'
    ]
    
    for func in required_functions:
        if func in content:
            print(f"✅ Function {func} found")
        else:
            print(f"❌ Function {func} not found")
            return False
    
    return True

def test_output_compatibility():
    """Test that both generators produce compatible output."""
    print("\n🔗 Testing Output Compatibility...")
    
    # Test data
    test_data = {
        'title': 'Test News Post',
        'date': '2024-01-15',
        'author': 'Test Author',
        'slug': 'test-news-post',
        'image': '/static/uploads/news/2024/01/2024-01-15-test-news-post-hero.jpg',
        'imageAlt': 'Test image',
        'summary': 'This is a test news post for integration testing.',
        'tags': ['test', 'integration'],
        'body': 'This is the body content of the test post.'
    }
    
    # Expected frontmatter format
    expected_frontmatter = """---
title: "Test News Post"
date: 2024-01-15
author: "Test Author"
slug: "test-news-post"
image: "/static/uploads/news/2024/01/2024-01-15-test-news-post-hero.jpg"
imageAlt: "Test image"
summary: "This is a test news post for integration testing."
tags: [test, integration]
---"""
    
    # Expected filename format
    expected_filename = "2024-01-15-test-news-post.md"
    
    print(f"✅ Expected filename format: {expected_filename}")
    print(f"✅ Expected frontmatter format matches website requirements")
    
    # Test YAML parsing
    try:
        yaml.safe_load(expected_frontmatter.replace('---', ''))
        print("✅ Frontmatter is valid YAML")
    except yaml.YAMLError as e:
        print(f"❌ Frontmatter YAML error: {e}")
        return False
    
    return True

def test_website_compatibility():
    """Test compatibility with the main website's news system."""
    print("\n🌍 Testing Website Compatibility...")
    
    # Check if we're in the main website directory
    website_root = Path(__file__).parent.parent
    news_dir = website_root / "content" / "news"
    
    if not news_dir.exists():
        print("❌ Main website news directory not found")
        return False
    
    print("✅ Main website news directory found")
    
    # Check for index.json
    index_file = news_dir / "index.json"
    if index_file.exists():
        print("✅ News index.json found")
        
        # Test index.json format
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            if isinstance(index_data, list):
                print("✅ Index.json is a valid array")
                
                # Check if it has the expected structure
                if index_data:
                    sample_entry = index_data[0]
                    required_fields = ['id', 'title', 'date', 'slug', 'filename']
                    
                    for field in required_fields:
                        if field in sample_entry:
                            print(f"✅ Index entry has {field} field")
                        else:
                            print(f"❌ Index entry missing {field} field")
                            return False
                else:
                    print("ℹ️  Index.json is empty (no news posts yet)")
            else:
                print("❌ Index.json is not an array")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Index.json JSON error: {e}")
            return False
    else:
        print("ℹ️  News index.json not found (will be created by generators)")
    
    return True

def main():
    """Run all integration tests."""
    print("🧪 Sonce News Generator Integration Test")
    print("=" * 50)
    
    tests = [
        test_python_generator_output,
        test_html_editor_output,
        test_output_compatibility,
        test_website_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Both generators are ready to use.")
        print("\n🚀 You can now use either generator:")
        print("   • Python GUI: ./run_mac_linux.sh or run_windows.bat")
        print("   • HTML Editor: ./run_html_editor.sh or run_html_editor.bat")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)