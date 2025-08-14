#!/usr/bin/env bash
set -e
echo "Building Jekyll site..."
bundle install || true
bundle exec jekyll build
echo "Built to _site/"
