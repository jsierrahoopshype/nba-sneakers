#!/usr/bin/env python3
"""
Static Site Generator for NBA Shoe Gallery

Generates:
- Homepage with recent photos and stats
- Player timeline pages (/players/lebron-james/)
- Brand hub pages (/brands/nike/)
- Weekly gallery pages (/weekly/2024-W52/)
- Browse pages (/players/, /brands/, /weekly/)

Usage:
    python generate_site.py
"""

import os
import sys
import json
from datetime import datetime
from html import escape
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import PhotoArchive


class SiteGenerator:
    """Generates static HTML pages from photo archive"""
    
    def __init__(self, archive_path: str = "data/archive.json", output_dir: str = "site"):
        self.archive = PhotoArchive(archive_path)
        self.output_dir = output_dir
        self.site_title = "NBA Sneakers"
        self.base_url = "https://jsierrahoopshype.github.io/nba-sneakers"  # GitHub Pages URL
        
    def generate_all(self):
        """Generate entire site"""
        print(f"Generating site from {len(self.archive.photos)} photos...", file=sys.stderr)
        
        # Create directories
        for subdir in ['players', 'brands', 'weekly', 'css', 'js', 'search']:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
        
        # Generate pages
        self._generate_css()
        self._generate_js()
        self._generate_homepage()
        self._generate_search_page()
        self._generate_players_index()
        self._generate_brands_index()
        self._generate_weekly_index()
        
        # Generate individual pages for all players
        players_generated = 0
        for player in self.archive.get_all_players():
            if player['count'] >= 1:  # Generate page for any player with photos
                self._generate_player_page(player)
                players_generated += 1
        
        print(f"Generated {players_generated} player timeline pages", file=sys.stderr)
        
        for brand in self.archive.get_all_brands():
            self._generate_brand_page(brand)
        
        for week in self.archive.get_all_weeks():
            self._generate_weekly_page(week)
        
        # Generate embeddable snippet for current week
        self._generate_embed_snippet()
        
        # Generate search index JSON
        self._generate_search_index()
        
        print(f"Site generated in {self.output_dir}/", file=sys.stderr)
    
    def _write_file(self, path: str, content: str):
        """Write content to file"""
        full_path = os.path.join(self.output_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_css(self):
        """Generate shared CSS"""
        css = '''
:root {
    --primary: #1a1a2e;
    --accent: #e94560;
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #666;
    --text-muted: #999;
    --border: #e0e0e0;
    --shadow: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-hover: 0 4px 16px rgba(0,0,0,0.12);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}

a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 16px;
}

/* Header */
.site-header {
    background: var(--primary);
    color: white;
    padding: 16px 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.site-header .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}

.site-logo {
    font-size: 20px;
    font-weight: 700;
    color: white;
}
.site-logo:hover { text-decoration: none; }

.site-nav {
    display: flex;
    gap: 24px;
}
.site-nav a {
    color: rgba(255,255,255,0.8);
    font-size: 14px;
}
.site-nav a:hover { color: white; text-decoration: none; }

/* Hero */
.hero {
    background: linear-gradient(135deg, var(--primary) 0%, #16213e 100%);
    color: white;
    padding: 48px 0;
    text-align: center;
}
.hero h1 { font-size: 32px; margin-bottom: 8px; }
.hero p { opacity: 0.8; font-size: 16px; }

/* Stats bar */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-top: 24px;
    flex-wrap: wrap;
}
.stat-item {
    text-align: center;
}
.stat-value {
    font-size: 28px;
    font-weight: 700;
}
.stat-label {
    font-size: 12px;
    opacity: 0.7;
    text-transform: uppercase;
}

/* Section */
.section {
    padding: 32px 0;
}
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.section-title {
    font-size: 20px;
    font-weight: 600;
}
.section-link {
    font-size: 14px;
}

/* Photo grid */
.photo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}

.photo-card {
    background: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.2s, box-shadow 0.2s;
    cursor: pointer;
}
.photo-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}
.photo-card .img-wrap {
    position: relative;
    padding-top: 66.67%;
    background: #f0f0f0;
}
.photo-card img {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: cover;
}
.photo-card .meta {
    padding: 12px;
}
.photo-card .player {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 2px;
}
.photo-card .headline {
    font-size: 13px;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin-bottom: 8px;
}
.photo-card .credit {
    font-size: 11px;
    color: var(--text-muted);
}

/* List grid (for player/brand lists) */
.list-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
}
.list-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--card-bg);
    border-radius: 8px;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s;
}
.list-item:hover {
    box-shadow: var(--shadow-hover);
    text-decoration: none;
}
.list-item .name {
    font-weight: 500;
    color: var(--text);
}
.list-item .count {
    font-size: 13px;
    color: var(--text-muted);
}

/* Page header */
.page-header {
    padding: 32px 0;
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
}
.page-header h1 {
    font-size: 28px;
    margin-bottom: 4px;
}
.page-header .subtitle {
    color: var(--text-secondary);
}

/* Breadcrumb */
.breadcrumb {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 8px;
}
.breadcrumb a { color: var(--text-secondary); }

/* Lightbox */
.lightbox {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.95);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}
.lightbox.active { display: flex; }
.lightbox img {
    max-width: 90vw;
    max-height: 70vh;
    object-fit: contain;
}
.lightbox .close {
    position: absolute;
    top: 16px; right: 16px;
    color: white;
    font-size: 32px;
    cursor: pointer;
    background: rgba(0,0,0,0.5);
    width: 48px; height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.lightbox .nav {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    color: white;
    font-size: 40px;
    cursor: pointer;
    padding: 16px;
    background: rgba(0,0,0,0.3);
    border-radius: 4px;
}
.lightbox .nav.prev { left: 16px; }
.lightbox .nav.next { right: 16px; }
.lightbox .info {
    color: white;
    text-align: center;
    padding: 16px;
    max-width: 90vw;
}
.lightbox .lb-player { font-size: 18px; font-weight: 600; }
.lightbox .lb-headline { font-size: 14px; color: #ccc; margin-top: 4px; }
.lightbox .lb-credit { font-size: 12px; color: #999; margin-top: 8px; }
.lightbox .counter {
    position: absolute;
    top: 16px; left: 16px;
    color: white;
    background: rgba(0,0,0,0.5);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 14px;
}

/* Footer */
.site-footer {
    background: var(--primary);
    color: rgba(255,255,255,0.6);
    padding: 24px 0;
    margin-top: 48px;
    text-align: center;
    font-size: 13px;
}

/* Homepage-specific */
.weekly-hero {
    margin-bottom: 32px;
}
.section-desc {
    color: var(--text-secondary);
    font-size: 14px;
    margin: -12px 0 16px 0;
}
.section-header .photo-count {
    font-size: 14px;
    color: var(--text-muted);
    font-weight: normal;
}
.section-header .section-note {
    font-size: 13px;
    color: var(--text-muted);
}
.view-more {
    text-align: center;
    margin-top: 24px;
}
.view-more a {
    display: inline-block;
    padding: 12px 24px;
    background: var(--primary);
    color: white;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
}
.view-more a:hover {
    text-decoration: none;
    opacity: 0.9;
}
.stats-section {
    background: var(--card-bg);
    border-radius: 12px;
    padding: 32px !important;
    margin-top: 32px;
}
.stats-section .stats-bar {
    margin-top: 0;
}
.brands-grid .brand-item {
    background: linear-gradient(135deg, var(--card-bg), #f8f9fa);
}

/* Search page */
.search-box {
    position: relative;
    max-width: 500px;
    margin: 0 auto 24px;
}
.search-box input {
    width: 100%;
    padding: 16px 20px;
    font-size: 18px;
    border: 2px solid var(--border);
    border-radius: 12px;
    outline: none;
    transition: border-color 0.2s;
}
.search-box input:focus {
    border-color: var(--accent);
}
.search-box input::placeholder {
    color: var(--text-muted);
}
.search-results {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow-hover);
    max-height: 400px;
    overflow-y: auto;
    z-index: 100;
}
.search-result-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    cursor: pointer;
}
.search-result-item:hover {
    background: var(--bg);
    text-decoration: none;
}
.search-result-item:last-child {
    border-bottom: none;
}
.search-result-item.no-page {
    opacity: 0.6;
    cursor: default;
}
.search-result-item .name {
    font-weight: 500;
}
.search-result-item .count {
    font-size: 13px;
    color: var(--text-muted);
}
.no-results {
    padding: 16px;
    text-align: center;
    color: var(--text-muted);
}
.search-stats {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin-bottom: 32px;
    font-size: 14px;
    color: var(--text-secondary);
}

/* Player grid for search page */
.player-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
}
.player-card {
    background: var(--card-bg);
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
}
.player-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}
.player-card .player-img {
    height: 120px;
    background-size: cover;
    background-position: center;
    background-color: var(--primary);
}
.player-card .player-info {
    padding: 12px;
}
.player-card .player-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--text);
    margin-bottom: 2px;
}
.player-card .player-count {
    font-size: 12px;
    color: var(--text-muted);
}

/* Alphabetical list */
.alpha-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}
.alpha-item {
    padding: 8px 14px;
    background: var(--card-bg);
    border-radius: 6px;
    font-size: 14px;
    color: var(--text);
    box-shadow: var(--shadow);
}
.alpha-item:hover {
    text-decoration: none;
    box-shadow: var(--shadow-hover);
}
.alpha-item.disabled {
    opacity: 0.5;
    cursor: default;
}
.alpha-item span {
    color: var(--text-muted);
    font-size: 12px;
}

/* Responsive */
@media (max-width: 768px) {
    .hero h1 { font-size: 24px; }
    .stats-bar { gap: 20px; }
    .stat-value { font-size: 22px; }
    .photo-grid { gap: 12px; }
    .lightbox .nav { font-size: 28px; padding: 10px; }
}
'''
        self._write_file('css/style.css', css)
    
    def _generate_js(self):
        """Generate shared JavaScript"""
        js = '''
// Lightbox functionality
document.addEventListener('DOMContentLoaded', function() {
    const photos = window.galleryPhotos || [];
    let currentIndex = 0;
    
    const lightbox = document.getElementById('lightbox');
    if (!lightbox || photos.length === 0) return;
    
    const lbImg = lightbox.querySelector('img');
    const lbPlayer = lightbox.querySelector('.lb-player');
    const lbHeadline = lightbox.querySelector('.lb-headline');
    const lbCredit = lightbox.querySelector('.lb-credit');
    const counter = lightbox.querySelector('.counter');
    
    function formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const d = new Date(dateStr + 'T00:00:00');
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        } catch(e) { return dateStr; }
    }
    
    function showPhoto() {
        const p = photos[currentIndex];
        lbImg.src = p.image_url;
        lbPlayer.textContent = p.player_name || 'NBA';
        lbHeadline.textContent = p.headline || '';
        lbCredit.textContent = '📷 ' + (p.photographer || 'Imagn') + ' · ' + (p.source || 'USA TODAY Sports') + ' · ' + formatDate(p.photo_date);
        counter.textContent = (currentIndex + 1) + ' / ' + photos.length;
    }
    
    function openLightbox(index) {
        currentIndex = index;
        showPhoto();
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeLightbox() {
        lightbox.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    function nextPhoto() {
        currentIndex = (currentIndex + 1) % photos.length;
        showPhoto();
    }
    
    function prevPhoto() {
        currentIndex = (currentIndex - 1 + photos.length) % photos.length;
        showPhoto();
    }
    
    // Bind click events to photo cards
    document.querySelectorAll('.photo-card').forEach(function(card, i) {
        card.addEventListener('click', function() {
            openLightbox(i);
        });
    });
    
    // Lightbox controls
    lightbox.querySelector('.close').addEventListener('click', closeLightbox);
    lightbox.querySelector('.next').addEventListener('click', function(e) { e.stopPropagation(); nextPhoto(); });
    lightbox.querySelector('.prev').addEventListener('click', function(e) { e.stopPropagation(); prevPhoto(); });
    lightbox.addEventListener('click', function(e) { if (e.target === lightbox) closeLightbox(); });
    
    // Keyboard nav
    document.addEventListener('keydown', function(e) {
        if (!lightbox.classList.contains('active')) return;
        if (e.key === 'Escape') closeLightbox();
        if (e.key === 'ArrowRight') nextPhoto();
        if (e.key === 'ArrowLeft') prevPhoto();
    });
    
    // Touch swipe
    let touchStartX = 0;
    lightbox.addEventListener('touchstart', function(e) { touchStartX = e.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener('touchend', function(e) {
        const diff = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(diff) > 50) { diff > 0 ? prevPhoto() : nextPhoto(); }
    });
});
'''
        self._write_file('js/gallery.js', js)
    
    def _base_template(self, title: str, content: str, photos_json: str = "[]") -> str:
        """Wrap content in base HTML template"""
        css = '''
:root {
    --primary: #1a1a2e;
    --accent: #e94560;
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #666;
    --text-muted: #999;
    --border: #e0e0e0;
    --shadow: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-hover: 0 4px 16px rgba(0,0,0,0.12);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 16px; }
.site-header { background: var(--primary); color: white; padding: 16px 0; position: sticky; top: 0; z-index: 100; }
.site-header .container { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.site-logo { font-size: 20px; font-weight: 700; color: white; }
.site-logo:hover { text-decoration: none; }
.site-nav { display: flex; gap: 24px; }
.site-nav a { color: rgba(255,255,255,0.8); font-size: 14px; }
.site-nav a:hover { color: white; text-decoration: none; }
.hero { background: linear-gradient(135deg, var(--primary) 0%, #16213e 100%); color: white; padding: 48px 0; text-align: center; }
.hero h1 { font-size: 32px; margin-bottom: 8px; }
.hero p { opacity: 0.8; font-size: 16px; }
.stats-bar { display: flex; justify-content: center; gap: 32px; margin-top: 24px; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 12px; opacity: 0.7; text-transform: uppercase; }
.section { padding: 32px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-title { font-size: 20px; font-weight: 600; }
.section-link { font-size: 14px; }
.photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.photo-card { background: var(--card-bg); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; }
.photo-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.photo-card .img-wrap { position: relative; padding-top: 66.67%; background: #f0f0f0; }
.photo-card img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
.photo-card .meta { padding: 12px; }
.photo-card .player { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.photo-card .headline { font-size: 13px; color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 8px; }
.photo-card .credit { font-size: 11px; color: var(--text-muted); }
.list-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.list-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow); transition: box-shadow 0.2s; }
.list-item:hover { box-shadow: var(--shadow-hover); text-decoration: none; }
.list-item .name { font-weight: 500; color: var(--text); }
.list-item .count { font-size: 13px; color: var(--text-muted); }
.page-header { padding: 32px 0; background: var(--card-bg); border-bottom: 1px solid var(--border); }
.page-header h1 { font-size: 28px; margin-bottom: 4px; }
.page-header .subtitle { color: var(--text-secondary); }
.breadcrumb { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.breadcrumb a { color: var(--text-secondary); }
.lightbox { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; flex-direction: column; }
.lightbox.active { display: flex; }
.lightbox img { max-width: 90vw; max-height: 70vh; object-fit: contain; }
.lightbox .close { position: absolute; top: 16px; right: 16px; color: white; font-size: 32px; cursor: pointer; background: rgba(0,0,0,0.5); width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.lightbox .nav { position: absolute; top: 50%; transform: translateY(-50%); color: white; font-size: 40px; cursor: pointer; padding: 16px; background: rgba(0,0,0,0.3); border-radius: 4px; }
.lightbox .nav.prev { left: 16px; }
.lightbox .nav.next { right: 16px; }
.lightbox .info { color: white; text-align: center; padding: 16px; max-width: 90vw; }
.lightbox .lb-player { font-size: 18px; font-weight: 600; }
.lightbox .lb-headline { font-size: 14px; color: #ccc; margin-top: 4px; }
.lightbox .lb-credit { font-size: 12px; color: #999; margin-top: 8px; }
.lightbox .counter { position: absolute; top: 16px; left: 16px; color: white; background: rgba(0,0,0,0.5); padding: 8px 12px; border-radius: 4px; font-size: 14px; }
.site-footer { background: var(--primary); color: rgba(255,255,255,0.6); padding: 24px 0; margin-top: 48px; text-align: center; font-size: 13px; }
.weekly-hero { margin-bottom: 32px; }
.section-desc { color: var(--text-secondary); font-size: 14px; margin: -12px 0 16px 0; }
.section-header .photo-count { font-size: 14px; color: var(--text-muted); font-weight: normal; }
.section-header .section-note { font-size: 13px; color: var(--text-muted); }
.view-more { text-align: center; margin-top: 24px; }
.view-more a { display: inline-block; padding: 12px 24px; background: var(--primary); color: white; border-radius: 6px; font-size: 14px; font-weight: 500; }
.view-more a:hover { text-decoration: none; opacity: 0.9; }
.stats-section { background: var(--card-bg); border-radius: 12px; padding: 32px !important; margin-top: 32px; }
.stats-section .stats-bar { margin-top: 0; }
.brands-grid .brand-item { background: linear-gradient(135deg, var(--card-bg), #f8f9fa); }
.search-box { position: relative; max-width: 500px; margin: 0 auto 24px; }
.search-box input { width: 100%; padding: 16px 20px; font-size: 18px; border: 2px solid var(--border); border-radius: 12px; outline: none; transition: border-color 0.2s; }
.search-box input:focus { border-color: var(--accent); }
.search-box input::placeholder { color: var(--text-muted); }
.search-results { display: none; position: absolute; top: 100%; left: 0; right: 0; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow-hover); max-height: 400px; overflow-y: auto; z-index: 100; }
.search-result-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--border); color: var(--text); cursor: pointer; }
.search-result-item:hover { background: var(--bg); text-decoration: none; }
.search-result-item:last-child { border-bottom: none; }
.search-result-item.no-page { opacity: 0.6; cursor: default; }
.search-result-item .name { font-weight: 500; }
.search-result-item .count { font-size: 13px; color: var(--text-muted); }
.no-results { padding: 16px; text-align: center; color: var(--text-muted); }
.search-stats { display: flex; justify-content: center; gap: 32px; margin-bottom: 32px; font-size: 14px; color: var(--text-secondary); }
.player-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
.player-card { background: var(--card-bg); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s; text-decoration: none; }
.player-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.player-card .player-img { height: 120px; background-size: cover; background-position: center; background-color: var(--primary); }
.player-card .player-info { padding: 12px; }
.player-card .player-name { font-weight: 600; font-size: 14px; color: var(--text); margin-bottom: 2px; }
.player-card .player-count { font-size: 12px; color: var(--text-muted); }
.alpha-list { display: flex; flex-wrap: wrap; gap: 8px; }
.alpha-item { padding: 8px 14px; background: var(--card-bg); border-radius: 6px; font-size: 14px; color: var(--text); box-shadow: var(--shadow); }
.alpha-item:hover { text-decoration: none; box-shadow: var(--shadow-hover); }
.alpha-item.disabled { opacity: 0.5; cursor: default; }
.alpha-item span { color: var(--text-muted); font-size: 12px; }
@media (max-width: 768px) { .hero h1 { font-size: 24px; } .stats-bar { gap: 20px; } .stat-value { font-size: 22px; } .photo-grid { gap: 12px; } .lightbox .nav { font-size: 28px; padding: 10px; } }
'''
        
        js = '''
document.addEventListener('DOMContentLoaded', function() {
    const photos = window.galleryPhotos || [];
    let currentIndex = 0;
    const lightbox = document.getElementById('lightbox');
    if (!lightbox || photos.length === 0) return;
    const lbImg = lightbox.querySelector('img');
    const lbPlayer = lightbox.querySelector('.lb-player');
    const lbHeadline = lightbox.querySelector('.lb-headline');
    const lbCredit = lightbox.querySelector('.lb-credit');
    const counter = lightbox.querySelector('.counter');
    function formatDate(dateStr) {
        if (!dateStr) return '';
        try { const d = new Date(dateStr + 'T00:00:00'); return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
        catch(e) { return dateStr; }
    }
    function showPhoto() {
        const p = photos[currentIndex];
        lbImg.src = p.image_url;
        lbPlayer.textContent = p.player_name || 'NBA';
        lbHeadline.textContent = p.headline || '';
        lbCredit.textContent = '📷 ' + (p.photographer || 'Imagn') + ' · ' + (p.source || 'USA TODAY Sports') + ' · ' + formatDate(p.photo_date);
        counter.textContent = (currentIndex + 1) + ' / ' + photos.length;
    }
    function openLightbox(index) { currentIndex = index; showPhoto(); lightbox.classList.add('active'); document.body.style.overflow = 'hidden'; }
    function closeLightbox() { lightbox.classList.remove('active'); document.body.style.overflow = ''; }
    function nextPhoto() { currentIndex = (currentIndex + 1) % photos.length; showPhoto(); }
    function prevPhoto() { currentIndex = (currentIndex - 1 + photos.length) % photos.length; showPhoto(); }
    document.querySelectorAll('.photo-card').forEach(function(card, i) { card.addEventListener('click', function() { openLightbox(i); }); });
    lightbox.querySelector('.close').addEventListener('click', closeLightbox);
    lightbox.querySelector('.next').addEventListener('click', function(e) { e.stopPropagation(); nextPhoto(); });
    lightbox.querySelector('.prev').addEventListener('click', function(e) { e.stopPropagation(); prevPhoto(); });
    lightbox.addEventListener('click', function(e) { if (e.target === lightbox) closeLightbox(); });
    document.addEventListener('keydown', function(e) { if (!lightbox.classList.contains('active')) return; if (e.key === 'Escape') closeLightbox(); if (e.key === 'ArrowRight') nextPhoto(); if (e.key === 'ArrowLeft') prevPhoto(); });
    let touchStartX = 0;
    lightbox.addEventListener('touchstart', function(e) { touchStartX = e.touches[0].clientX; }, { passive: true });
    lightbox.addEventListener('touchend', function(e) { const diff = e.changedTouches[0].clientX - touchStartX; if (Math.abs(diff) > 50) { diff > 0 ? prevPhoto() : nextPhoto(); } });
});
'''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} | {self.site_title}</title>
<style>{css}</style>
</head>
<body>

<header class="site-header">
    <div class="container">
        <a href="{self.base_url}/" class="site-logo">👟 NBA Sneakers</a>
        <nav class="site-nav">
            <a href="{self.base_url}/search/">🔍 Lookup</a>
            <a href="{self.base_url}/players/">Players</a>
            <a href="{self.base_url}/brands/">Brands</a>
            <a href="{self.base_url}/weekly/">Weekly</a>
        </nav>
    </div>
</header>

{content}

<div class="lightbox" id="lightbox">
    <span class="close">&times;</span>
    <span class="nav prev">&#10094;</span>
    <span class="nav next">&#10095;</span>
    <span class="counter"></span>
    <img src="" alt="">
    <div class="info">
        <div class="lb-player"></div>
        <div class="lb-headline"></div>
        <div class="lb-credit"></div>
    </div>
</div>

<footer class="site-footer">
    <div class="container">
        Photos © USA TODAY Sports / Imagn Images · Built for HoopsHype
    </div>
</footer>

<script>window.galleryPhotos = {photos_json};</script>
<script>{js}</script>
</body>
</html>'''
    
    def _photo_card_html(self, photo: Dict) -> str:
        """Generate HTML for a single photo card"""
        player = escape(photo.get('player_name') or 'NBA')
        headline = escape((photo.get('headline') or '')[:100])
        photographer = escape(photo.get('photographer') or 'Imagn')
        source = escape(photo.get('source') or 'USA TODAY Sports')
        date = photo.get('photo_date', '')
        thumb = escape(photo.get('thumbnail_url') or photo.get('image_url', ''))
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_fmt = date_obj.strftime('%b %d, %Y')
        except:
            date_fmt = date
        
        return f'''<div class="photo-card">
    <div class="img-wrap"><img src="{thumb}" alt="{headline}" loading="lazy"></div>
    <div class="meta">
        <div class="player">{player}</div>
        <div class="headline">{headline}</div>
        <div class="credit">📷 {photographer} · {source} · {date_fmt}</div>
    </div>
</div>'''
    
    def _generate_homepage(self):
        """Generate homepage - Weekly gallery as hero, then navigation to deeper content"""
        stats = self.archive.get_stats()
        
        # Get this week's photos as the hero content
        week = datetime.now().strftime('%Y-W%W')
        weekly_photos = self.archive.get_photos_by_week(week)
        
        # If no photos this week, use most recent week that has photos
        if not weekly_photos:
            weeks = self.archive.get_all_weeks()
            if weeks:
                week = weeks[0]['week']  # Most recent week
                weekly_photos = self.archive.get_photos_by_week(week)
        
        # Final fallback: just get all photos
        if not weekly_photos:
            weekly_photos = self.archive.get_all_photos()[:20]
        
        # Show up to 20 in the main gallery
        hero_photos = weekly_photos[:20]
        
        # Date range for display
        if hero_photos:
            dates = [p.get('photo_date', '') for p in hero_photos if p.get('photo_date')]
            if dates:
                from_date = min(dates)
                to_date = max(dates)
                try:
                    from_fmt = datetime.strptime(from_date, '%Y-%m-%d').strftime('%b %d')
                    to_fmt = datetime.strptime(to_date, '%Y-%m-%d').strftime('%b %d, %Y')
                    date_range = f"{from_fmt} – {to_fmt}"
                except:
                    date_range = week
            else:
                date_range = week
        else:
            date_range = "Latest"
        
        content = f'''
<section class="hero">
    <div class="container">
        <h1>NBA Sneakers</h1>
        <p>The best shoe photos from around the league · {date_range}</p>
    </div>
</section>

<main class="container">
    <!-- WEEKLY GALLERY (Hero Content) -->
    <section class="section weekly-hero">
        <div class="section-header">
            <h2 class="section-title">📸 Latest Kicks</h2>
            <span class="photo-count">{len(hero_photos)} photos</span>
        </div>
        <div class="photo-grid">
            {"".join(self._photo_card_html(p) for p in hero_photos)}
        </div>
        {f'<div class="view-more"><a href="{self.base_url}/weekly/{week}/">View all {len(weekly_photos)} photos from {week} →</a></div>' if len(weekly_photos) > 20 else ''}
    </section>
    
    <!-- PLAYER TIMELINES -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🏀 Player Timelines</h2>
            <a href="{self.base_url}/players/" class="section-link">View all {stats['total_players']} players →</a>
        </div>
        <p class="section-desc">See every shoe photo for your favorite players</p>
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/players/{p["slug"]}/" class="list-item"><span class="name">{escape(p["name"])}</span><span class="count">{p["count"]} photos</span></a>' for p in stats['top_players'][:12])}
        </div>
    </section>
    
    <!-- BRAND HUBS -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">👟 Shop by Brand</h2>
            <a href="{self.base_url}/brands/" class="section-link">View all →</a>
        </div>
        <div class="list-grid brands-grid">
            {"".join(f'<a href="{self.base_url}/brands/{b["slug"]}/" class="list-item brand-item"><span class="name">{escape(b["name"])}</span><span class="count">{b["count"]} photos</span></a>' for b in stats['top_brands'])}
        </div>
    </section>
    
    <!-- WEEKLY ARCHIVE -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">📅 Past Weeks</h2>
            <a href="{self.base_url}/weekly/" class="section-link">View all →</a>
        </div>
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/weekly/{w["week"]}/" class="list-item"><span class="name">{w["week"]}</span><span class="count">{w["count"]} photos</span></a>' for w in stats['recent_weeks'][:6] if w['week'] != week)}
        </div>
    </section>
    
    <!-- STATS FOOTER -->
    <section class="section stats-section">
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-value">{stats['total_photos']:,}</div>
                <div class="stat-label">Total Photos</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats['total_players']}</div>
                <div class="stat-label">Players</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats['total_brands']}</div>
                <div class="stat-label">Brands</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{stats['total_weeks']}</div>
                <div class="stat-label">Weeks</div>
            </div>
        </div>
    </section>
</main>
'''
        photos_json = json.dumps([{
            'image_url': p.get('image_url', ''),
            'player_name': p.get('player_name', ''),
            'headline': p.get('headline', ''),
            'photographer': p.get('photographer', ''),
            'source': p.get('source', ''),
            'photo_date': p.get('photo_date', '')
        } for p in hero_photos], ensure_ascii=False)
        
        html = self._base_template("NBA Sneakers", content, photos_json)
        self._write_file('index.html', html)
    
    def _generate_players_index(self):
        """Generate players listing page"""
        players = self.archive.get_all_players()
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / Players</div>
        <h1>Players</h1>
        <p class="subtitle">{len(players)} players in archive</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">All Players</h2>
            <span class="section-note">Click any player to see their shoe photos</span>
        </div>
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/players/{p["slug"]}/" class="list-item"><span class="name">{escape(p["name"])}</span><span class="count">{p["count"]} photo{"s" if p["count"] != 1 else ""}</span></a>' for p in players)}
        </div>
    </section>
</main>
'''
        html = self._base_template("Players", content)
        self._write_file('players/index.html', html)
    
    def _generate_brands_index(self):
        """Generate brands listing page"""
        brands = self.archive.get_all_brands()
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / Brands</div>
        <h1>Brands</h1>
        <p class="subtitle">{len(brands)} brands represented</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/brands/{b["slug"]}/" class="list-item"><span class="name">{escape(b["name"])}</span><span class="count">{b["count"]} photos</span></a>' for b in brands)}
        </div>
    </section>
</main>
'''
        html = self._base_template("Brands", content)
        self._write_file('brands/index.html', html)
    
    def _generate_weekly_index(self):
        """Generate weekly galleries listing"""
        weeks = self.archive.get_all_weeks()
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / Weekly</div>
        <h1>Weekly Galleries</h1>
        <p class="subtitle">{len(weeks)} weeks of shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/weekly/{w["week"]}/" class="list-item"><span class="name">{w["week"]}</span><span class="count">{w["count"]} photos</span></a>' for w in weeks)}
        </div>
    </section>
</main>
'''
        html = self._base_template("Weekly Galleries", content)
        self._write_file('weekly/index.html', html)
    
    def _generate_search_page(self):
        """Generate the player search/lookup page"""
        all_players = self.archive.get_all_players()
        
        # All players now have pages
        featured_players = all_players
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / Search</div>
        <h1>🔍 Player Sneaker Lookup</h1>
        <p class="subtitle">Search any NBA player's shoe history</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <!-- Search Box -->
        <div class="search-box">
            <input type="text" id="player-search" placeholder="Type a player name..." autocomplete="off">
            <div id="search-results" class="search-results"></div>
        </div>
        
        <!-- Quick Stats -->
        <div class="search-stats">
            <span><strong>{len(featured_players)}</strong> players with full timelines</span>
            <span><strong>{len(all_players)}</strong> total players in archive</span>
        </div>
    </section>
    
    <!-- All Players -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">Featured Players</h2>
            <span class="section-note">Players with 4+ shoe photos</span>
        </div>
        <div class="player-grid" id="featured-players">
            {"".join(self._player_card_html(p) for p in featured_players)}
        </div>
    </section>
    
    <!-- All Players Alphabetical -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">All Players A-Z</h2>
        </div>
        <div class="alpha-list" id="all-players">
            {"".join(self._player_list_item_html(p) for p in sorted(all_players, key=lambda x: x['name']))}
        </div>
    </section>
</main>

<script>
// Player search functionality
(function() {{
    const players = {json.dumps([{
        'name': p['name'],
        'slug': p['slug'],
        'count': p['count'],
        'hasPage': True
    } for p in all_players], ensure_ascii=False)};
    
    const searchInput = document.getElementById('player-search');
    const resultsDiv = document.getElementById('search-results');
    
    searchInput.addEventListener('input', function() {{
        const query = this.value.toLowerCase().trim();
        
        if (query.length < 2) {{
            resultsDiv.innerHTML = '';
            resultsDiv.style.display = 'none';
            return;
        }}
        
        const matches = players.filter(p => 
            p.name.toLowerCase().includes(query)
        ).slice(0, 10);
        
        if (matches.length === 0) {{
            resultsDiv.innerHTML = '<div class="no-results">No players found</div>';
        }} else {{
            resultsDiv.innerHTML = matches.map(p => {{
                return `<a href="{self.base_url}/players/${{p.slug}}/" class="search-result-item">
                    <span class="name">${{p.name}}</span>
                    <span class="count">${{p.count}} photo${{p.count > 1 ? 's' : ''}}</span>
                </a>`;
            }}).join('');
        }}
        resultsDiv.style.display = 'block';
    }});
    
    // Close results when clicking outside
    document.addEventListener('click', function(e) {{
        if (!e.target.closest('.search-box')) {{
            resultsDiv.style.display = 'none';
        }}
    }});
    
    // Keyboard navigation
    searchInput.addEventListener('keydown', function(e) {{
        if (e.key === 'Escape') {{
            resultsDiv.style.display = 'none';
            this.blur();
        }}
    }});
}})();
</script>
'''
        html = self._base_template("Player Lookup", content)
        self._write_file('search/index.html', html)
    
    def _player_card_html(self, player: Dict) -> str:
        """Generate a player card with photo count"""
        # Get their most recent photo for a preview
        photos = self.archive.get_photos_by_player(player['slug'])
        preview_img = photos[0].get('thumbnail_url', '') if photos else ''
        
        return f'''<a href="{self.base_url}/players/{player['slug']}/" class="player-card">
    <div class="player-img" style="background-image: url('{escape(preview_img)}')"></div>
    <div class="player-info">
        <div class="player-name">{escape(player['name'])}</div>
        <div class="player-count">{player['count']} photos</div>
    </div>
</a>'''
    
    def _player_list_item_html(self, player: Dict) -> str:
        """Generate a simple list item for a player"""
        return f'<a href="{self.base_url}/players/{player["slug"]}/" class="alpha-item">{escape(player["name"])} <span>({player["count"]})</span></a>'
    
    def _generate_search_index(self):
        """Generate JSON index for search functionality"""
        all_players = self.archive.get_all_players()
        
        index = {
            'generated_at': datetime.now().isoformat(),
            'players': [{
                'name': p['name'],
                'slug': p['slug'],
                'count': p['count'],
                'has_page': True,
                'latest_date': p.get('latest_date', '')
            } for p in all_players]
        }
        
        self._write_file('search/players.json', json.dumps(index, indent=2, ensure_ascii=False))
        print(f"Generated search index: {len(all_players)} players", file=sys.stderr)
    
    def _generate_player_page(self, player: Dict):
        """Generate individual player page"""
        photos = self.archive.get_photos_by_player(player['slug'])
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / <a href="{self.base_url}/players/">Players</a> / {escape(player['name'])}</div>
        <h1>{escape(player['name'])}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid">
            {"".join(self._photo_card_html(p) for p in photos)}
        </div>
    </section>
</main>
'''
        photos_json = json.dumps([{
            'image_url': p.get('image_url', ''),
            'player_name': p.get('player_name', ''),
            'headline': p.get('headline', ''),
            'photographer': p.get('photographer', ''),
            'source': p.get('source', ''),
            'photo_date': p.get('photo_date', '')
        } for p in photos], ensure_ascii=False)
        
        html = self._base_template(player['name'], content, photos_json)
        self._write_file(f"players/{player['slug']}/index.html", html)
    
    def _generate_brand_page(self, brand: Dict):
        """Generate individual brand page"""
        photos = self.archive.get_photos_by_brand(brand['slug'])
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / <a href="{self.base_url}/brands/">Brands</a> / {escape(brand['name'])}</div>
        <h1>{escape(brand['name'])}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid">
            {"".join(self._photo_card_html(p) for p in photos)}
        </div>
    </section>
</main>
'''
        photos_json = json.dumps([{
            'image_url': p.get('image_url', ''),
            'player_name': p.get('player_name', ''),
            'headline': p.get('headline', ''),
            'photographer': p.get('photographer', ''),
            'source': p.get('source', ''),
            'photo_date': p.get('photo_date', '')
        } for p in photos], ensure_ascii=False)
        
        html = self._base_template(brand['name'], content, photos_json)
        self._write_file(f"brands/{brand['slug']}/index.html", html)
    
    def _generate_weekly_page(self, week: Dict):
        """Generate weekly gallery page"""
        photos = self.archive.get_photos_by_week(week['week'])
        
        content = f'''
<div class="page-header">
    <div class="container">
        <div class="breadcrumb"><a href="{self.base_url}/">Home</a> / <a href="{self.base_url}/weekly/">Weekly</a> / {week['week']}</div>
        <h1>Week of {week['week']}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid">
            {"".join(self._photo_card_html(p) for p in photos)}
        </div>
    </section>
</main>
'''
        photos_json = json.dumps([{
            'image_url': p.get('image_url', ''),
            'player_name': p.get('player_name', ''),
            'headline': p.get('headline', ''),
            'photographer': p.get('photographer', ''),
            'source': p.get('source', ''),
            'photo_date': p.get('photo_date', '')
        } for p in photos], ensure_ascii=False)
        
        html = self._base_template(f"Week {week['week']}", content, photos_json)
        self._write_file(f"weekly/{week['week']}/index.html", html)
    
    def _generate_embed_snippet(self):
        """Generate embeddable snippet for Presto"""
        recent = self.archive.get_recent_photos(7)[:20]
        if not recent:
            # Fall back to all photos if no recent ones
            recent = self.archive.get_all_photos()[:20]
        if not recent:
            print("No photos for embed snippet", file=sys.stderr)
            return
        
        week = datetime.now().strftime('%Y-W%W')
        
        # Generate self-contained embed
        photos_json = json.dumps([{
            'src': p.get('image_url', ''),
            'thumb': p.get('thumbnail_url') or p.get('image_url', ''),
            'player': p.get('player_name') or 'NBA',
            'headline': (p.get('headline') or '')[:100],
            'photographer': p.get('photographer') or 'Imagn',
            'source': p.get('source') or 'USA TODAY Sports',
            'date': p.get('photo_date', '')
        } for p in recent], ensure_ascii=False)
        
        embed = f'''<!-- NBA Shoe Gallery Embed - Week {week} -->
<style>
.hh-embed * {{ box-sizing: border-box; margin: 0; padding: 0; }}
.hh-embed {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 16px; }}
.hh-embed h2 {{ font-size: 20px; margin-bottom: 16px; }}
.hh-embed .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }}
.hh-embed .card {{ background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); cursor: pointer; }}
.hh-embed .card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.hh-embed .card .img {{ position: relative; padding-top: 66%; background: #f0f0f0; }}
.hh-embed .card img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
.hh-embed .card .meta {{ padding: 10px; }}
.hh-embed .card .player {{ font-weight: 600; font-size: 13px; }}
.hh-embed .card .credit {{ font-size: 10px; color: #888; margin-top: 4px; }}
.hh-embed .lb {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 99999; align-items: center; justify-content: center; flex-direction: column; }}
.hh-embed .lb.active {{ display: flex; }}
.hh-embed .lb img {{ max-width: 90vw; max-height: 70vh; }}
.hh-embed .lb .close {{ position: absolute; top: 16px; right: 16px; color: #fff; font-size: 32px; cursor: pointer; }}
.hh-embed .lb .nav {{ position: absolute; top: 50%; transform: translateY(-50%); color: #fff; font-size: 36px; cursor: pointer; padding: 12px; }}
.hh-embed .lb .prev {{ left: 12px; }}
.hh-embed .lb .next {{ right: 12px; }}
.hh-embed .lb .info {{ color: #fff; text-align: center; padding: 12px; }}
</style>
<div class="hh-embed" id="hh-embed">
    <h2>NBA Shoe Photos of the Week</h2>
    <div class="grid" id="hh-grid"></div>
    <div class="lb" id="hh-lb">
        <span class="close" id="hh-close">&times;</span>
        <span class="nav prev" id="hh-prev">&#10094;</span>
        <span class="nav next" id="hh-next">&#10095;</span>
        <img src="" id="hh-img">
        <div class="info" id="hh-info"></div>
    </div>
</div>
<script>
(function(){{
var photos={photos_json};
var idx=0,grid=document.getElementById('hh-grid'),lb=document.getElementById('hh-lb'),img=document.getElementById('hh-img'),info=document.getElementById('hh-info');
function fmt(d){{try{{return new Date(d+'T00:00:00').toLocaleDateString('en-US',{{month:'short',day:'numeric',year:'numeric'}})}}catch(e){{return d}}}}
photos.forEach(function(p,i){{
var c=document.createElement('div');c.className='card';c.innerHTML='<div class="img"><img src="'+p.thumb+'" loading="lazy"></div><div class="meta"><div class="player">'+p.player+'</div><div class="credit">📷 '+p.photographer+' · '+fmt(p.date)+'</div></div>';
c.onclick=function(){{idx=i;show();lb.classList.add('active');document.body.style.overflow='hidden'}};
grid.appendChild(c);
}});
function show(){{var p=photos[idx];img.src=p.src;info.innerHTML='<div style="font-weight:600">'+p.player+'</div><div style="font-size:12px;color:#999;margin-top:4px">📷 '+p.photographer+' · '+p.source+' · '+fmt(p.date)+'</div>'}}
document.getElementById('hh-close').onclick=function(){{lb.classList.remove('active');document.body.style.overflow=''}};
document.getElementById('hh-next').onclick=function(e){{e.stopPropagation();idx=(idx+1)%photos.length;show()}};
document.getElementById('hh-prev').onclick=function(e){{e.stopPropagation();idx=(idx-1+photos.length)%photos.length;show()}};
lb.onclick=function(e){{if(e.target===lb){{lb.classList.remove('active');document.body.style.overflow=''}}}};
}})();
</script>'''
        
        self._write_file('embed.html', embed)
        self._write_file('weekly/latest.html', embed)
        print(f"Generated embed snippet: {len(recent)} photos", file=sys.stderr)


def main():
    # Use paths relative to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    generator = SiteGenerator(
        archive_path=os.path.join(repo_root, "data/archive.json"),
        output_dir=os.path.join(repo_root, "site")
    )
    generator.generate_all()


if __name__ == '__main__':
    main()
