#!/bin/bash

# Build script for Sonce website
echo "Building Sonce website..."

# Check if Jekyll is installed
if ! command -v jekyll &> /dev/null; then
    echo "Error: Jekyll is not installed. Please install Ruby and Jekyll first."
    echo "See README.md for installation instructions."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "vendor" ]; then
    echo "Installing dependencies..."
    bundle install
fi

# Clean previous build
echo "Cleaning previous build..."
bundle exec jekyll clean

# Build the site
echo "Building site..."
bundle exec jekyll build

if [ $? -eq 0 ]; then
    echo "✅ Build successful! Site is ready in _site/ folder"
    echo "📁 You can now upload the _site/ folder to your web server"
    echo "🌐 Or test locally with: bundle exec jekyll serve"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi