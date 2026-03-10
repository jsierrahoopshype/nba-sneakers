# Last updated: 2026-03-07 - force rebuild
#!/usr/bin/env python3
"""
Static Site Generator for NBA Shoe Gallery

Generates:
- Homepage with recent photos and stats
- Player timeline pages (/players/lebron-james/)
- Weekly gallery pages (/weekly/2024-W52/)
- Browse pages (/players/, /weekly/)
- Affiliate monetization modules

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

# Try to import affiliate module
try:
    from affiliate import AffiliateRouter, AFFILIATE_POSITIONS
    HAS_AFFILIATE = True
except ImportError:
    HAS_AFFILIATE = False
    AFFILIATE_POSITIONS = []


class SiteGenerator:
    """Generates static HTML pages from photo archive"""
    
    def __init__(self, archive_path: str = "data/archive.json", output_dir: str = "site"):
        self.archive = PhotoArchive(archive_path)
        self.output_dir = output_dir
        self.site_title = "NBA Sneakers"
        self.base_url = "https://jsierrahoopshype.github.io/nba-sneakers"  # GitHub Pages URL
        
        # Initialize affiliate router if available
        if HAS_AFFILIATE:
            self.affiliate = AffiliateRouter()
        else:
            self.affiliate = None
        
    def generate_all(self):
        """Generate entire site"""
        print(f"Generating site from {len(self.archive.photos)} photos...", file=sys.stderr)
        
        # Create directories
        for subdir in ['players', 'teams', 'weekly', 'css', 'js', 'search', 'photos']:
            os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
        
        # Generate pages
        self._generate_css()
        self._generate_js()
        self._generate_homepage()
        self._generate_search_page()
        self._generate_players_index()
        self._generate_teams_index()
        self._generate_weekly_index()
        
        # Generate individual pages for all players
        players_generated = 0
        for player in self.archive.get_all_players():
            if player['count'] >= 1:  # Generate page for any player with photos
                self._generate_player_page(player)
                players_generated += 1
        
        print(f"Generated {players_generated} player timeline pages", file=sys.stderr)
        
        # Generate team pages
        teams = self._get_all_teams()
        for team in teams:
            self._generate_team_page(team)
        print(f"Generated {len(teams)} team pages", file=sys.stderr)

        for week in self.archive.get_all_weeks():
            self._generate_weekly_page(week)
        
        # Generate individual photo pages
        all_photos = sorted(self.archive.photos.values(), key=lambda p: p.get('photo_date', ''), reverse=True)
        for idx, photo in enumerate(all_photos):
            prev_photo = all_photos[idx - 1] if idx > 0 else None
            next_photo = all_photos[idx + 1] if idx < len(all_photos) - 1 else None
            self._generate_photo_page(photo, prev_photo, next_photo)
        print(f"Generated {len(all_photos)} individual photo pages", file=sys.stderr)

        # Generate embeddable snippet for current week
        self._generate_embed_snippet()
        
        # Generate search index JSON
        self._generate_search_index()

        # Generate robots.txt
        self._generate_robots_txt()

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
    --primary-dark: #0d0d1a;
    --accent: #ff6b00;
    --accent-hover: #e55d00;
    --bg: #f5f5f5;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #555;
    --text-muted: #888;
    --border: #e0e0e0;
    --shadow: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-hover: 0 4px 16px rgba(0,0,0,0.15);
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
    background: linear-gradient(180deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    padding: 12px 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.site-header .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.site-logo {
    font-size: 22px;
    font-weight: 700;
    color: white;
    display: flex;
    align-items: center;
    gap: 8px;
}
.site-logo:hover { text-decoration: none; color: var(--accent); }

.site-nav {
    display: flex;
    gap: 24px;
}
.site-nav a {
    color: rgba(255,255,255,0.85);
    font-size: 14px;
    font-weight: 500;
    padding: 8px 0;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
}
.site-nav a:hover { 
    color: white; 
    text-decoration: none;
    border-bottom-color: var(--accent);
}

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
    display: block;
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
.player-link {
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 2px;
    color: var(--text);
    text-decoration: none;
    display: block;
}
.player-link:hover {
    color: var(--accent);
    text-decoration: none;
}

/* Photo detail page */
.photo-detail {
    max-width: 800px;
    margin: 0 auto;
}
.photo-detail-img {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow);
    margin-bottom: 20px;
}
.photo-detail-img img {
    width: 100%;
    height: auto;
    display: block;
}
.photo-detail-info {
    margin-bottom: 24px;
}
.photo-detail-info .headline {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 8px;
}
.photo-detail-info .credit {
    font-size: 13px;
    color: var(--text-muted);
}
.photo-detail-actions {
    margin-bottom: 24px;
}
.back-btn {
    display: inline-block;
    padding: 10px 20px;
    background: var(--primary);
    color: white;
    border-radius: 8px;
    font-weight: 500;
    font-size: 14px;
}
.back-btn:hover {
    background: var(--primary-dark);
    text-decoration: none;
    color: white;
}
.photo-nav {
    display: flex;
    justify-content: space-between;
    padding-top: 20px;
    border-top: 1px solid var(--border);
}
.photo-nav-link {
    font-size: 14px;
    font-weight: 500;
}
.photo-nav-link.next {
    margin-left: auto;
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

/* Header Search - Prominent */
.header-search {
    position: relative;
    flex: 1;
    max-width: 400px;
    margin: 0 24px;
}
.header-search input {
    width: 100%;
    padding: 12px 20px;
    border: 2px solid var(--accent);
    border-radius: 25px;
    background: white;
    color: var(--text);
    font-size: 15px;
    font-weight: 500;
    transition: all 0.2s;
}
.header-search input::placeholder {
    color: #888;
}
.header-search input:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.2);
}
.header-search::before {
    content: '🔍';
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 16px;
    pointer-events: none;
}
.quick-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    display: none;
    max-height: 350px;
    overflow-y: auto;
    z-index: 1000;
    margin-top: 8px;
    border: 1px solid var(--border);
}
.quick-results.active {
    display: block;
}
.quick-result-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
}
.quick-result-item:hover {
    background: #fff5eb;
    text-decoration: none;
}
.quick-result-item:last-child {
    border-bottom: none;
}
.quick-result-item .name {
    font-weight: 600;
    color: var(--text);
}
.quick-result-item .count {
    color: var(--accent);
    font-size: 13px;
    font-weight: 500;
    background: #fff5eb;
    padding: 2px 8px;
    border-radius: 12px;
}

/* Affiliate Module Styles */
.affiliate-module {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
    color: white;
    grid-column: 1 / -1;
}
.affiliate-module.inline {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
}
.affiliate-module.featured {
    text-align: center;
    padding: 24px;
}
.buy-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--accent);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s;
}
.buy-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-2px);
    text-decoration: none;
    color: white;
}
.buy-btn.large {
    padding: 16px 32px;
    font-size: 18px;
}
.btn-icon { font-size: 16px; }
.btn-text { font-weight: 600; }
.badge-success { background: #28a745; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-warning { background: #ffc107; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-info { background: #17a2b8; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.module-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 12px;
}
.module-icon { font-size: 24px; }
.module-title { font-size: 18px; font-weight: 600; }
.shoe-info { margin-bottom: 16px; }
.shoe-name {
    display: block;
    font-size: 16px;
    margin-bottom: 8px;
    color: rgba(255,255,255,0.9);
}
.compare-prices {
    margin-top: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
}
.compare-label {
    font-size: 12px;
    color: rgba(255,255,255,0.6);
}
.compare-link {
    font-size: 12px;
    color: rgba(255,255,255,0.8);
    text-decoration: underline;
}
.compare-link:hover { color: white; }

/* Responsive */
@media (max-width: 768px) {
    .site-header .container {
        flex-wrap: wrap;
    }
    .header-search {
        order: 3;
        max-width: 100%;
        margin: 12px 0 0 0;
        width: 100%;
    }
    .header-search input {
        padding: 10px 16px;
    }
    .stats-bar { gap: 20px; }
    .stat-value { font-size: 22px; }
    .photo-grid { gap: 12px; }
    .affiliate-module.featured { padding: 16px; }
    .buy-btn.large { padding: 12px 20px; font-size: 16px; }
    .site-nav { gap: 16px; }
    .site-nav a { font-size: 13px; }
}

img { -webkit-user-select: none; user-select: none; -webkit-user-drag: none; }
'''
        self._write_file('css/style.css', css)
    
    def _generate_js(self):
        """Generate shared JavaScript"""
        js = '''
document.addEventListener('contextmenu', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
document.addEventListener('dragstart', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
'''
        
        # Header search and tracking - needs variable interpolation
        base_url = self.base_url
        js += '''
// Header Quick Search
document.addEventListener('DOMContentLoaded', function() {
    var BASE_URL = "''' + base_url + '''";
    var searchInput = document.getElementById('quick-search');
    var resultsDiv = document.getElementById('quick-results');

    if (!searchInput || !resultsDiv) {
        console.log('[Search] Missing elements - searchInput:', !!searchInput, 'resultsDiv:', !!resultsDiv);
        return;
    }

    var players = [];

    // 1. Fetch player index on page load
    var fetchUrl = BASE_URL + "/search/players.json";
    console.log('[Search] Fetching player index from:', fetchUrl);
    fetch(fetchUrl)
        .then(function(r) {
            console.log('[Search] Fetch response status:', r.status);
            return r.json();
        })
        .then(function(data) {
            players = data.players || [];
            console.log('[Search] Loaded', players.length, 'players');
        })
        .catch(function(e) { console.log('[Search] Could not load player index', e); });

    // 2. Filter players as user types (minimum 2 characters)
    searchInput.addEventListener('input', function() {
        var query = this.value.toLowerCase().trim();
        console.log('[Search] Input:', query, '| Players loaded:', players.length);

        if (query.length < 2) {
            resultsDiv.classList.remove('active');
            resultsDiv.innerHTML = '';
            return;
        }

        var matches = players.filter(function(p) {
            return p.name.toLowerCase().includes(query);
        }).slice(0, 8);
        console.log('[Search] Matches found:', matches.length);

        // 3. Show dropdown with matching player names and photo counts
        if (matches.length === 0) {
            resultsDiv.innerHTML = '<div class="quick-result-item"><span class="name">No players found</span></div>';
        } else {
            resultsDiv.innerHTML = matches.map(function(p) {
                return '<a href="' + BASE_URL + '/players/' + p.slug + '/" class="quick-result-item">'
                    + '<span class="name">' + p.name + '</span>'
                    + '<span class="count">' + p.count + ' photo' + (p.count !== 1 ? 's' : '') + '</span>'
                    + '</a>';
            }).join('');
        }
        resultsDiv.classList.add('active');
    });

    // 4. Navigate to player page on click (handled by <a> href) or Enter key
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            var firstLink = resultsDiv.querySelector('a');
            if (firstLink) {
                window.location.href = firstLink.href;
            }
        }
    });

    // 5. Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.header-search')) {
            resultsDiv.classList.remove('active');
            resultsDiv.innerHTML = '';
        }
    });
});

'''
        # Infinite scroll logic
        js += '''
// Infinite Scroll
document.addEventListener('DOMContentLoaded', function() {
    var data = window.__SCROLL_PHOTOS;
    if (!data || !data.photos || !data.photos.length) return;
    var grid = document.getElementById('photo-grid');
    if (!grid) return;
    var photos = data.photos;
    var baseUrl = data.baseUrl || '';
    var affiliateAt = data.affiliateAt || {};
    var batch = 24;
    var loaded = 0;

    // Create sentinel element
    var sentinel = document.createElement('div');
    sentinel.className = 'scroll-sentinel';
    sentinel.innerHTML = '<div class="scroll-spinner"></div>';
    grid.parentNode.insertBefore(sentinel, grid.nextSibling);

    function fmtDate(d) {
        try { return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric'}); }
        catch(e) { return d; }
    }

    function loadBatch() {
        var end = Math.min(loaded + batch, photos.length);
        if (loaded >= photos.length) return;
        for (var i = loaded; i < end; i++) {
            // Insert affiliate module before this photo if scheduled
            var aff = affiliateAt[String(i)];
            if (aff) {
                var tmp = document.createElement('div');
                tmp.innerHTML = aff;
                while (tmp.firstChild) { grid.appendChild(tmp.firstChild); }
            }
            var p = photos[i];
            var card = document.createElement('div');
            card.className = 'photo-card';
            card.innerHTML = '<a href="' + baseUrl + '/photos/' + p.id + '/" class="img-wrap"><img src="' + p.thumb + '" alt="' + p.headline + '" loading="lazy"></a>'
                + '<div class="meta"><a href="' + baseUrl + '/players/' + p.playerSlug + '/" class="player-link">' + p.player + '</a>'
                + '<div class="headline">' + p.headline + '</div>'
                + '<div class="credit">\U0001F4F7 ' + p.photographer + ' \u00b7 ' + p.source + ' \u00b7 ' + fmtDate(p.date) + '</div></div>';
            grid.appendChild(card);
        }
        loaded = end;
        if (loaded >= photos.length) {
            sentinel.innerHTML = '<div class="scroll-done">All photos loaded</div>';
            sentinel.className = 'scroll-done';
            if (observer) observer.disconnect();
        }
    }

    var observer = null;
    if ('IntersectionObserver' in window) {
        observer = new IntersectionObserver(function(entries) {
            if (entries[0].isIntersecting) { loadBatch(); }
        }, { rootMargin: '200px' });
        observer.observe(sentinel);
    } else {
        // Fallback: load all at once
        while (loaded < photos.length) { loadBatch(); }
    }
});
'''
        self._write_file('js/gallery.js', js)

    def _base_template(self, title: str, content: str, photos_json: str = None, meta: Dict = None, breadcrumb: str = '') -> str:
        """Wrap content in base HTML template

        meta dict supports: description, og_image, canonical
        """
        css = '''
:root {
    --primary: #1a1a2e;
    --primary-dark: #0d0d1a;
    --accent: #ff6b00;
    --accent-hover: #e55d00;
    --bg: #f5f5f5;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-secondary: #555;
    --text-muted: #888;
    --border: #e0e0e0;
    --shadow: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-hover: 0 4px 16px rgba(0,0,0,0.15);
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
.site-header { background: linear-gradient(180deg, var(--primary) 0%, var(--primary-dark) 100%); color: white; padding: 12px 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 10px rgba(0,0,0,0.3); }
.site-header .container { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.header-left { display: flex; align-items: center; gap: 12px; min-width: 0; }
.site-logo { font-size: 22px; font-weight: 700; color: white; white-space: nowrap; }
.site-logo:hover { text-decoration: none; color: var(--accent); }
.header-breadcrumb { font-size: 13px; color: rgba(255,255,255,0.6); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.header-breadcrumb::before { content: '/'; margin-right: 10px; color: rgba(255,255,255,0.3); }
.header-breadcrumb a { color: rgba(255,255,255,0.7); }
.header-breadcrumb a:hover { color: white; text-decoration: none; }
.site-nav { display: flex; gap: 24px; }
.site-nav a { color: rgba(255,255,255,0.85); font-size: 14px; font-weight: 500; padding: 8px 0; border-bottom: 2px solid transparent; }
.site-nav a:hover { color: white; text-decoration: none; border-bottom-color: var(--accent); }
.stats-bar { display: flex; justify-content: center; gap: 32px; margin-top: 24px; flex-wrap: wrap; }
.stat-item { text-align: center; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 12px; opacity: 0.7; text-transform: uppercase; }
.section { padding: 32px 0; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.section-title { font-size: 20px; font-weight: 600; }
.section-link { font-size: 14px; }
.photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.scroll-sentinel { grid-column: 1 / -1; display: flex; justify-content: center; padding: 24px 0; }
.scroll-spinner { width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
.scroll-done { grid-column: 1 / -1; text-align: center; padding: 16px 0; color: var(--text-muted); font-size: 14px; }
@keyframes spin { to { transform: rotate(360deg); } }
.photo-card { background: var(--card-bg); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s; }
.photo-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.photo-card .img-wrap { display: block; position: relative; padding-top: 66.67%; background: #f0f0f0; }
.photo-card img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }
.photo-card .meta { padding: 12px; }
.photo-card .player { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.photo-card .headline { font-size: 13px; color: var(--text-secondary); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 8px; }
.photo-card .credit { font-size: 11px; color: var(--text-muted); }
.player-link { font-weight: 600; font-size: 14px; margin-bottom: 2px; color: var(--text); text-decoration: none; display: block; }
.player-link:hover { color: var(--accent); text-decoration: none; }
.photo-detail { max-width: 800px; margin: 0 auto; }
.photo-detail-img { border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); margin-bottom: 20px; }
.photo-detail-img img { width: 100%; height: auto; display: block; }
.photo-detail-info { margin-bottom: 24px; }
.photo-detail-info .headline { font-size: 16px; color: var(--text-secondary); margin-bottom: 8px; }
.photo-detail-info .credit { font-size: 13px; color: var(--text-muted); }
.photo-detail-actions { margin-bottom: 24px; }
.back-btn { display: inline-block; padding: 10px 20px; background: var(--primary); color: white; border-radius: 8px; font-weight: 500; font-size: 14px; }
.back-btn:hover { background: var(--primary-dark); text-decoration: none; color: white; }
.photo-nav { display: flex; justify-content: space-between; padding-top: 20px; border-top: 1px solid var(--border); }
.photo-nav-link { font-size: 14px; font-weight: 500; }
.photo-nav-link.next { margin-left: auto; }
.list-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.list-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow); transition: box-shadow 0.2s; }
.list-item:hover { box-shadow: var(--shadow-hover); text-decoration: none; }
.list-item .name { font-weight: 500; color: var(--text); }
.list-item .count { font-size: 13px; color: var(--text-muted); }
.page-header { padding: 32px 0; background: var(--card-bg); border-bottom: 1px solid var(--border); }
.page-header h1 { font-size: 28px; margin-bottom: 4px; }
.page-header .subtitle { color: var(--text-secondary); }
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
.header-search { position: relative; flex: 1; max-width: 400px; margin: 0 24px; }
.header-search input { width: 100%; padding: 12px 20px; border: 2px solid var(--accent); border-radius: 25px; background: white; color: var(--text); font-size: 15px; font-weight: 500; }
.header-search input::placeholder { color: #888; }
.header-search input:focus { outline: none; box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.2); }
.quick-results { position: absolute; top: 100%; left: 0; right: 0; background: white; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.2); display: none; max-height: 350px; overflow-y: auto; z-index: 1000; margin-top: 8px; }
.quick-results.active { display: block; }
.quick-result-item { display: flex; justify-content: space-between; padding: 12px 16px; color: var(--text); border-bottom: 1px solid var(--border); }
.quick-result-item:hover { background: #fff5eb; text-decoration: none; }
.quick-result-item .name { font-weight: 600; }
.quick-result-item .count { color: var(--accent); font-size: 13px; font-weight: 500; background: #fff5eb; padding: 2px 8px; border-radius: 12px; }
.affiliate-module { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); border-radius: 12px; padding: 16px; margin: 16px 0; color: white; grid-column: 1 / -1; }
.affiliate-module.inline { display: flex; align-items: center; justify-content: center; padding: 12px; }
.affiliate-module.featured { text-align: center; padding: 24px; }
.buy-btn { display: inline-flex; align-items: center; gap: 8px; background: var(--accent); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; }
.buy-btn:hover { background: var(--accent-hover); transform: translateY(-2px); text-decoration: none; color: white; }
.buy-btn.large { padding: 16px 32px; font-size: 18px; }
.badge-success { background: #28a745; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-warning { background: #ffc107; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-info { background: #17a2b8; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.module-header { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; }
.shoe-info { margin-bottom: 16px; }
.shoe-name { display: block; font-size: 16px; margin-bottom: 8px; color: rgba(255,255,255,0.9); }
.compare-prices { margin-top: 12px; display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; }
.compare-link { font-size: 12px; color: rgba(255,255,255,0.8); text-decoration: underline; }
.more-players { padding: 32px 0; }
.more-players h2 { font-size: 20px; font-weight: 600; margin-bottom: 16px; }
.more-players-row { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 12px; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }
.more-players-row::-webkit-scrollbar { height: 6px; }
.more-players-row::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
.more-player-card { flex: 0 0 160px; scroll-snap-align: start; background: var(--card-bg); border-radius: 8px; overflow: hidden; box-shadow: var(--shadow); transition: transform 0.2s, box-shadow 0.2s; text-decoration: none; }
.more-player-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); text-decoration: none; }
.more-player-card .mp-img { height: 100px; background-size: cover; background-position: center; background-color: var(--primary); }
.more-player-card .mp-info { padding: 10px 12px; }
.more-player-card .mp-name { font-weight: 600; font-size: 13px; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.more-player-card .mp-count { font-size: 11px; color: var(--text-muted); }
@media (max-width: 768px) { .stats-bar { gap: 20px; } .stat-value { font-size: 22px; } .photo-grid { gap: 12px; } .site-header .container { flex-wrap: wrap; } .header-left { flex: 1 1 auto; min-width: 0; } .header-breadcrumb { display: none; } .header-search { order: 3; max-width: 100%; margin: 12px 0 0 0; width: 100%; } .more-player-card { flex: 0 0 140px; } }
img { -webkit-user-select: none; user-select: none; -webkit-user-drag: none; }
'''

        js = '''
document.addEventListener('contextmenu', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
document.addEventListener('dragstart', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
'''
        
        meta = meta or {}
        full_title = f"{escape(title)} | {self.site_title}"
        meta_desc = escape(meta.get('description', ''))
        og_image = escape(meta.get('og_image', ''))
        canonical = escape(meta.get('canonical', ''))

        meta_tags = ''
        if meta_desc:
            meta_tags += f'\n<meta name="description" content="{meta_desc}">'
        meta_tags += f'\n<meta property="og:title" content="{full_title}">'
        if meta_desc:
            meta_tags += f'\n<meta property="og:description" content="{meta_desc}">'
        if og_image:
            meta_tags += f'\n<meta property="og:image" content="{og_image}">'
        if canonical:
            meta_tags += f'\n<link rel="canonical" href="{canonical}">'

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{full_title}</title>{meta_tags}
<style>{css}</style>
</head>
<body>

<header class="site-header">
    <div class="container">
        <div class="header-left">
            <a href="{self.base_url}/" class="site-logo">👟 NBA Sneakers</a>
            {f'<span class="header-breadcrumb">{breadcrumb}</span>' if breadcrumb else ''}
        </div>
        <div class="header-search">
            <input type="text" id="quick-search" placeholder="Search players..." autocomplete="off">
            <div id="quick-results" class="quick-results"></div>
        </div>
        <nav class="site-nav">
            <a href="{self.base_url}/players/">Players</a>
            <a href="{self.base_url}/teams/">Teams</a>
            <a href="{self.base_url}/weekly/">Weekly</a>
        </nav>
    </div>
</header>

{content}

<footer class="site-footer">
    <div class="container">
        Photos © USA TODAY Sports / Imagn Images · Built for HoopsHype
    </div>
</footer>

<script>{js}</script>
<script src="{self.base_url}/js/gallery.js"></script>
</body>
</html>'''
    
    def _name_to_slug(self, name: str) -> str:
        """Convert a player name to a URL-safe slug"""
        import re
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    def _photo_card_html(self, photo: Dict, idx: int = None) -> str:
        """Generate HTML for a single photo card"""
        player = escape(photo.get('player_name') or 'NBA')
        player_slug = photo.get('player_slug') or self._name_to_slug(photo.get('player_name') or '')
        imagn_id = escape(photo.get('imagn_id') or '')
        headline = escape((photo.get('headline') or '')[:100])
        photographer = escape(photo.get('photographer') or 'Imagn')
        source = escape(photo.get('source') or 'USA TODAY Sports')
        date = photo.get('photo_date', '')
        thumb_url = photo.get('thumbnail_url') or (f"https://www.imagn.com/image/{imagn_id}.jpg" if imagn_id else '')
        thumb = escape(thumb_url)

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_fmt = date_obj.strftime('%b %d, %Y')
        except:
            date_fmt = date

        return f'''<div class="photo-card">
    <a href="{self.base_url}/photos/{imagn_id}/" class="img-wrap"><img src="{thumb}" alt="{headline}" loading="lazy"></a>
    <div class="meta">
        <a href="{self.base_url}/players/{player_slug}/" class="player-link">{player}</a>
        <div class="headline">{headline}</div>
        <div class="credit">📷 {photographer} · {source} · {date_fmt}</div>
    </div>
</div>'''
    
    def _scroll_photos_script(self, photos: list, affiliate_html: Dict[int, str] = None) -> str:
        """Generate a <script> tag setting window.__SCROLL_PHOTOS for infinite scroll.

        affiliate_html: optional dict mapping 0-based index in *photos* to
        pre-rendered affiliate module HTML to insert before that photo.
        """
        if not photos:
            return ''
        items = []
        for p in photos:
            imagn_id = p.get('imagn_id') or ''
            player_name = p.get('player_name') or 'NBA'
            player_slug = p.get('player_slug') or self._name_to_slug(player_name)
            items.append({
                'id': escape(imagn_id),
                'thumb': escape(p.get('thumbnail_url') or f"https://www.imagn.com/image/{imagn_id}.jpg"),
                'headline': escape((p.get('headline') or '')[:100]),
                'player': escape(player_name),
                'playerSlug': player_slug,
                'photographer': escape(p.get('photographer') or 'Imagn'),
                'source': escape(p.get('source') or 'USA TODAY Sports'),
                'date': p.get('photo_date', ''),
            })
        data_dict = {'baseUrl': self.base_url, 'photos': items}
        if affiliate_html:
            # Convert int keys to strings for JSON
            data_dict['affiliateAt'] = {str(k): v for k, v in affiliate_html.items()}
        data = json.dumps(data_dict, ensure_ascii=False)
        return f'<script>window.__SCROLL_PHOTOS={data};</script>'

    def _more_players_html(self, exclude_slug: str = '') -> str:
        """Generate 'More Players to Explore' section with 8 random players (≥10 photos)"""
        import random
        all_players = self.archive.get_all_players()
        candidates = [p for p in all_players if p['count'] >= 10 and p['slug'] != exclude_slug]
        if not candidates:
            return ''
        selected = random.sample(candidates, min(8, len(candidates)))

        cards = []
        for p in selected:
            photos = self.archive.get_photos_by_player(p['slug'])
            bg_img = ''
            if photos:
                thumb = photos[0].get('thumbnail_url') or f"https://www.imagn.com/image/{photos[0].get('imagn_id', '')}.jpg"
                bg_img = f' style="background-image:url({escape(thumb)})"'
            cards.append(f'''<a href="{self.base_url}/players/{p['slug']}/" class="more-player-card">
    <div class="mp-img"{bg_img}></div>
    <div class="mp-info">
        <div class="mp-name">{escape(p['name'])}</div>
        <div class="mp-count">{p['count']} photos</div>
    </div>
</a>''')

        return f'''
<section class="more-players">
    <div class="container">
        <h2>More Players to Explore</h2>
        <div class="more-players-row">
            {"".join(cards)}
        </div>
    </div>
</section>
'''

    @staticmethod
    def _week_label(iso_week: str) -> str:
        """Convert ISO week like '2026-W06' to 'Week of Feb 9' format."""
        try:
            parts = iso_week.split('-W')
            year, wk = int(parts[0]), int(parts[1])
            monday = datetime.strptime(f'{year}-W{wk:02d}-1', '%G-W%V-%u')
            return f"Week of {monday.strftime('%b %-d')}"
        except Exception:
            return iso_week

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
        
        # Show initial batch in the grid, rest via infinite scroll
        initial_count = 24
        hero_photos = weekly_photos[:initial_count]
        remaining_photos = weekly_photos[initial_count:]

        # Build photo grid with affiliate modules at key positions
        hero_html_parts = []
        affiliate_positions = [1, 20, 50, 100, 200]
        for idx, photo in enumerate(hero_photos):
            position = idx + 1
            if self.affiliate and position in affiliate_positions:
                module_type = "featured" if position == 1 else "inline"
                caption = photo.get('caption', '')
                player_name = photo.get('player_name', 'NBA')
                module_html = self.affiliate.get_buy_button_html(caption, player_name, module_type)
                hero_html_parts.append(module_html)
            hero_html_parts.append(self._photo_card_html(photo))
        hero_grid_html = "".join(hero_html_parts)
        scroll_script = self._scroll_photos_script(remaining_photos)

        content = f'''
{scroll_script}
<main class="container">
    <!-- WEEKLY GALLERY -->
    <section class="section weekly-hero" style="margin-top: 24px;">
        <div class="section-header">
            <h2 class="section-title">📸 Latest Kicks</h2>
            <span class="photo-count">{len(weekly_photos)} photos</span>
        </div>
        <div class="photo-grid" id="photo-grid">
            {hero_grid_html}
        </div>
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
    
    <!-- BROWSE BY TEAM -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">🏀 Browse by Team</h2>
            <a href="{self.base_url}/teams/" class="section-link">View all →</a>
        </div>
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/teams/{t["slug"]}/" class="list-item"><span class="name">{escape(t["name"])}</span><span class="count">{t["count"]} photos</span></a>' for t in self._get_all_teams()[:15])}
        </div>
    </section>
    
    <!-- WEEKLY ARCHIVE -->
    <section class="section">
        <div class="section-header">
            <h2 class="section-title">📅 Past Weeks</h2>
            <a href="{self.base_url}/weekly/" class="section-link">View all →</a>
        </div>
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/weekly/{w["week"]}/" class="list-item"><span class="name">{self._week_label(w["week"])}</span><span class="count">{w["count"]} photos</span></a>' for w in stats['recent_weeks'][:6] if w['week'] != week)}
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
        
        og_image = hero_photos[0].get('thumbnail_url') or hero_photos[0].get('image_url', '') if hero_photos else ''
        meta = {
            'description': 'Daily NBA sneaker photos from every game. Browse by player, team, and week.',
            'og_image': og_image,
            'canonical': f"{self.base_url}/",
        }
        html = self._base_template("NBA Sneakers", content, photos_json, meta=meta)
        self._write_file('index.html', html)
    
    def _generate_players_index(self):
        """Generate players listing page"""
        players = self.archive.get_all_players()
        
        content = f'''
<div class="page-header">
    <div class="container">
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
        html = self._base_template("Players", content, breadcrumb='Players')
        self._write_file('players/index.html', html)
    
    # --- Teams ---

    NBA_TEAMS = [
        ('Atlanta Hawks', 'hawks', ['Hawks', 'Atlanta Hawks']),
        ('Boston Celtics', 'celtics', ['Celtics', 'Boston Celtics']),
        ('Brooklyn Nets', 'nets', ['Nets', 'Brooklyn Nets']),
        ('Charlotte Hornets', 'hornets', ['Hornets', 'Charlotte Hornets']),
        ('Chicago Bulls', 'bulls', ['Bulls', 'Chicago Bulls']),
        ('Cleveland Cavaliers', 'cavaliers', ['Cavaliers', 'Cleveland Cavaliers', 'Cavs']),
        ('Dallas Mavericks', 'mavericks', ['Mavericks', 'Dallas Mavericks', 'Mavs']),
        ('Denver Nuggets', 'nuggets', ['Nuggets', 'Denver Nuggets']),
        ('Detroit Pistons', 'pistons', ['Pistons', 'Detroit Pistons']),
        ('Golden State Warriors', 'warriors', ['Warriors', 'Golden State Warriors']),
        ('Houston Rockets', 'rockets', ['Rockets', 'Houston Rockets']),
        ('Indiana Pacers', 'pacers', ['Pacers', 'Indiana Pacers']),
        ('LA Clippers', 'clippers', ['Clippers', 'LA Clippers', 'Los Angeles Clippers']),
        ('Los Angeles Lakers', 'lakers', ['Lakers', 'Los Angeles Lakers']),
        ('Memphis Grizzlies', 'grizzlies', ['Grizzlies', 'Memphis Grizzlies', 'Memphis Grizzles']),
        ('Miami Heat', 'heat', ['Heat', 'Miami Heat']),
        ('Milwaukee Bucks', 'bucks', ['Bucks', 'Milwaukee Bucks']),
        ('Minnesota Timberwolves', 'timberwolves', ['Timberwolves', 'Minnesota Timberwolves']),
        ('New Orleans Pelicans', 'pelicans', ['Pelicans', 'New Orleans Pelicans']),
        ('New York Knicks', 'knicks', ['Knicks', 'New York Knicks']),
        ('Oklahoma City Thunder', 'thunder', ['Thunder', 'Oklahoma City Thunder', 'OKC Thunder']),
        ('Orlando Magic', 'magic', ['Magic', 'Orlando Magic']),
        ('Philadelphia 76ers', '76ers', ['76ers', 'Philadelphia 76ers', 'Sixers']),
        ('Phoenix Suns', 'suns', ['Suns', 'Phoenix Suns']),
        ('Portland Trail Blazers', 'trail-blazers', ['Trail Blazers', 'Portland Trail Blazers', 'Blazers']),
        ('Sacramento Kings', 'kings', ['Kings', 'Sacramento Kings']),
        ('San Antonio Spurs', 'spurs', ['Spurs', 'San Antonio Spurs']),
        ('Toronto Raptors', 'raptors', ['Raptors', 'Toronto Raptors']),
        ('Utah Jazz', 'jazz', ['Jazz', 'Utah Jazz']),
        ('Washington Wizards', 'wizards', ['Wizards', 'Washington Wizards']),
    ]

    _POSITION_WORDS = {'guard', 'forward', 'center', 'wing', 'point'}

    def _photo_belongs_to_team(self, photo: Dict, search_terms: List[str]) -> bool:
        """Check if a photo belongs to a team by parsing caption for 'TeamName position PlayerName' pattern.

        Only assigns the photo to the team that appears directly before a position word
        and player name, so 'Detroit Pistons guard Javonte Green' matches Detroit only,
        even if 'Miami Heat' appears elsewhere in the headline.
        """
        caption = photo.get('caption', '')
        player_name = photo.get('player_name', '')

        # Try caption-based attribution: look for "{team} {position} {player}"
        if caption and player_name:
            caption_lower = caption.lower()
            for term in search_terms:
                term_lower = term.lower()
                # Find all occurrences of this team term in the caption
                start = 0
                while True:
                    idx = caption_lower.find(term_lower, start)
                    if idx == -1:
                        break
                    # Check if a position word follows the team name
                    after_team = caption_lower[idx + len(term_lower):].lstrip(' ,')
                    for pos_word in self._POSITION_WORDS:
                        if after_team.startswith(pos_word):
                            # Check if the player name follows the position word
                            after_pos = after_team[len(pos_word):].lstrip()
                            if player_name.lower() in after_pos[:len(player_name) + 10].lower():
                                return True
                    start = idx + 1

        # Fallback: if no "{team} position player" pattern was found for ANY team,
        # use simple matching (covers photos without standard caption format)
        text = f"{photo.get('headline', '')} {caption}".lower()
        has_position_pattern = False
        for _, _, terms in self.NBA_TEAMS:
            for term in terms:
                term_lower = term.lower()
                if term_lower in text:
                    cap_lower = caption.lower() if caption else ''
                    idx = 0
                    while True:
                        idx = cap_lower.find(term_lower, idx)
                        if idx == -1:
                            break
                        after = cap_lower[idx + len(term_lower):].lstrip(' ,')
                        if any(after.startswith(pw) for pw in self._POSITION_WORDS):
                            has_position_pattern = True
                            break
                        idx += 1
                    if has_position_pattern:
                        break
            if has_position_pattern:
                break

        if has_position_pattern:
            # The caption has structured team+position patterns but none matched
            # this team with this player — don't include it
            return False

        # No structured pattern found at all — fall back to simple term matching
        for term in search_terms:
            if term.lower() in text:
                return True
        return False

    def _get_photos_for_team(self, search_terms: List[str]) -> List[Dict]:
        """Get photos that belong to this team, using caption parsing to avoid duplicates."""
        results = [p for p in self.archive.photos.values()
                   if self._photo_belongs_to_team(p, search_terms)]
        results.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return results

    def _get_all_teams(self) -> List[Dict]:
        """Get all teams with photo counts, sorted by count descending"""
        teams = []
        for name, slug, search_terms in self.NBA_TEAMS:
            count = len(self._get_photos_for_team(search_terms))
            teams.append({'name': name, 'slug': slug, 'search_terms': search_terms, 'count': count})
        teams.sort(key=lambda t: t['count'], reverse=True)
        return teams

    def _generate_teams_index(self):
        """Generate teams listing page"""
        teams = self._get_all_teams()

        content = f'''
<div class="page-header">
    <div class="container">
        <h1>Teams</h1>
        <p class="subtitle">Browse shoe photos by NBA team</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/teams/{t["slug"]}/" class="list-item"><span class="name">{escape(t["name"])}</span><span class="count">{t["count"]} photos</span></a>' for t in teams)}
        </div>
    </section>
</main>
'''
        html = self._base_template("Teams", content, breadcrumb='Teams')
        self._write_file('teams/index.html', html)

    def _more_teams_html(self, exclude_slug: str = '') -> str:
        """Generate 'More Teams to Explore' section with 8 random teams (with photos)"""
        import random
        all_teams = self._get_all_teams()
        candidates = [t for t in all_teams if t['count'] >= 1 and t['slug'] != exclude_slug]
        if not candidates:
            return ''
        selected = random.sample(candidates, min(8, len(candidates)))

        cards = []
        for t in selected:
            photos = self._get_photos_for_team(t['search_terms'])
            bg_img = ''
            if photos:
                thumb = photos[0].get('thumbnail_url') or f"https://www.imagn.com/image/{photos[0].get('imagn_id', '')}.jpg"
                bg_img = f' style="background-image:url({escape(thumb)})"'
            cards.append(f'''<a href="{self.base_url}/teams/{t['slug']}/" class="more-player-card">
    <div class="mp-img"{bg_img}></div>
    <div class="mp-info">
        <div class="mp-name">{escape(t['name'])}</div>
        <div class="mp-count">{t['count']} photos</div>
    </div>
</a>''')

        return f'''
<section class="more-players">
    <div class="container">
        <h2>More Teams to Explore</h2>
        <div class="more-players-row">
            {"".join(cards)}
        </div>
    </div>
</section>
'''

    def _generate_team_page(self, team: Dict):
        """Generate individual team page with affiliate modules"""
        photos = self._get_photos_for_team(team['search_terms'])

        # Show initial batch, rest via infinite scroll
        initial_count = 24
        initial_photos = photos[:initial_count]
        remaining_photos = photos[initial_count:]

        # Use short team name (e.g. "Warriors") for clean affiliate display
        short_name = team['search_terms'][0] if team.get('search_terms') else team['name']

        # Build photo grid with affiliate modules inserted at key positions
        photo_html_parts = []
        affiliate_positions = [1, 20, 50, 100, 200]

        for idx, photo in enumerate(initial_photos):
            position = idx + 1  # 1-indexed (position in full photo list)

            # Insert affiliate module at designated positions
            if self.affiliate and position in affiliate_positions:
                module_type = "featured" if position == 1 else "inline"
                caption = photo.get('caption', '')
                header = f"Shop {short_name} Gear" if module_type == "featured" else None
                module_html = self.affiliate.get_buy_button_html(caption, short_name, module_type, header_text=header)
                photo_html_parts.append(module_html)

            photo_html_parts.append(self._photo_card_html(photo))

        # Pre-render affiliate modules for positions that fall in the scroll portion
        scroll_affiliate_html = {}
        if self.affiliate and remaining_photos:
            for pos in affiliate_positions:
                # pos is 1-indexed in the full list; convert to 0-indexed in remaining_photos
                scroll_idx = pos - 1 - initial_count
                if scroll_idx >= 0 and scroll_idx < len(remaining_photos):
                    caption = remaining_photos[scroll_idx].get('caption', '')
                    module_html = self.affiliate.get_buy_button_html(caption, short_name, "inline")
                    scroll_affiliate_html[scroll_idx] = module_html

        scroll_script = self._scroll_photos_script(remaining_photos, affiliate_html=scroll_affiliate_html)

        photos_json = json.dumps([{
            'id': p.get('imagn_id', ''),
            'url': p.get('thumbnail_url', p.get('image_url', '')),
            'full': p.get('image_url', ''),
            'player': escape(p.get('player_name', '')),
            'date': p.get('photo_date', ''),
            'caption': escape(p.get('caption', '')[:200]),
            'detail_url': f"{self.base_url}/photos/{p.get('imagn_id', '')}/",
        } for p in photos], indent=None)

        content = f'''
{scroll_script}
<div class="page-header">
    <div class="container">
        <h1>{escape(team["name"])}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid" id="photo-grid">
            {"".join(photo_html_parts)}
        </div>
    </section>
</main>
'''
        content += self._more_teams_html(exclude_slug=team['slug'])

        html = self._base_template(team['name'], content, photos_json, breadcrumb=f'<a href="{self.base_url}/teams/">Teams</a> / {escape(team["name"])}')
        self._write_file(f"teams/{team['slug']}/index.html", html)

    def _generate_brands_index(self):
        """Generate brands listing page"""
        brands = self.archive.get_all_brands()
        
        content = f'''
<div class="page-header">
    <div class="container">
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
        html = self._base_template("Brands", content, breadcrumb='Brands')
        self._write_file('brands/index.html', html)
    
    def _generate_weekly_index(self):
        """Generate weekly galleries listing"""
        weeks = self.archive.get_all_weeks()
        
        content = f'''
<div class="page-header">
    <div class="container">
        <h1>Weekly Galleries</h1>
        <p class="subtitle">{len(weeks)} weeks of shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="list-grid">
            {"".join(f'<a href="{self.base_url}/weekly/{w["week"]}/" class="list-item"><span class="name">{self._week_label(w["week"])}</span><span class="count">{w["count"]} photos</span></a>' for w in weeks)}
        </div>
    </section>
</main>
'''
        html = self._base_template("Weekly Galleries", content, breadcrumb='Weekly')
        self._write_file('weekly/index.html', html)
    
    def _generate_search_page(self):
        """Generate the player search/lookup page"""
        all_players = self.archive.get_all_players()
        
        # All players now have pages
        featured_players = all_players
        
        content = f'''
<div class="page-header">
    <div class="container">
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
        html = self._base_template("Player Lookup", content, breadcrumb='Search')
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

    def _generate_robots_txt(self):
        """Generate robots.txt to block crawlers from data and search index"""
        robots = '''User-agent: *
Disallow: /data/
Disallow: /search/players.json
'''
        self._write_file('robots.txt', robots)

    def _generate_photo_page(self, photo: Dict, prev_photo: Dict = None, next_photo: Dict = None):
        """Generate individual photo detail page at /photos/{imagn_id}/index.html"""
        imagn_id = photo.get('imagn_id', '')
        if not imagn_id:
            return

        player = escape(photo.get('player_name') or 'NBA')
        player_slug = photo.get('player_slug') or self._name_to_slug(photo.get('player_name') or '')
        headline = escape(photo.get('headline') or '')
        caption = escape(photo.get('caption') or '')
        photographer = escape(photo.get('photographer') or 'Imagn')
        source = escape(photo.get('source') or 'USA TODAY Sports')
        image_url = escape(photo.get('thumbnail_url') or f"https://www.imagn.com/image/{imagn_id}.jpg")
        date = photo.get('photo_date', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_fmt = date_obj.strftime('%b %d, %Y')
        except Exception:
            date_fmt = date

        # SEO meta description from caption
        meta_desc = (photo.get('caption') or headline or '')[:160]

        # Affiliate module
        affiliate_html = ''
        if self.affiliate:
            affiliate_html = self.affiliate.get_buy_button_html(
                photo.get('caption', ''), photo.get('player_name', ''), 'featured'
            )

        # Prev/Next navigation
        nav_parts = []
        if prev_photo:
            prev_id = prev_photo.get('imagn_id', '')
            prev_player = escape(prev_photo.get('player_name') or 'NBA')
            nav_parts.append(f'<a href="{self.base_url}/photos/{prev_id}/" class="photo-nav-link prev">&laquo; {prev_player}</a>')
        if next_photo:
            next_id = next_photo.get('imagn_id', '')
            next_player = escape(next_photo.get('player_name') or 'NBA')
            nav_parts.append(f'<a href="{self.base_url}/photos/{next_id}/" class="photo-nav-link next">{next_player} &raquo;</a>')
        nav_html = f'<div class="photo-nav">{"".join(nav_parts)}</div>' if nav_parts else ''

        content = f'''
<main class="container">
    <section class="section photo-detail">
        <div class="photo-detail-img">
            <img src="{image_url}" alt="{headline}" loading="lazy">
        </div>
        <div class="photo-detail-info">
            <a href="{self.base_url}/players/{player_slug}/" class="player-link">{player}</a>
            <div class="headline">{headline}</div>
            <div class="credit">📷 {photographer} · {source} · {date_fmt}</div>
        </div>
        {affiliate_html}
        <div class="photo-detail-actions">
            <a href="{self.base_url}/players/{player_slug}/" class="back-btn">&larr; Back to {player}</a>
        </div>
        {nav_html}
    </section>
</main>
'''

        content += self._more_players_html(exclude_slug=player_slug)

        seo_title = f"{photo.get('player_name') or 'NBA'} Sneakers - {date_fmt}"

        meta = {
            'description': meta_desc,
            'og_image': photo.get('thumbnail_url') or photo.get('image_url', ''),
            'canonical': f"{self.base_url}/photos/{imagn_id}/",
        }
        html = self._base_template(seo_title, content, meta=meta, breadcrumb=f'<a href="{self.base_url}/players/{player_slug}/">{player}</a> / Photo')

        self._write_file(f"photos/{imagn_id}/index.html", html)

    def _generate_player_page(self, player: Dict):
        """Generate individual player page with affiliate modules"""
        photos = self.archive.get_photos_by_player(player['slug'])

        # Show initial batch, rest via infinite scroll
        initial_count = 24
        initial_photos = photos[:initial_count]
        remaining_photos = photos[initial_count:]

        # Build photo grid with affiliate modules inserted at key positions
        photo_html_parts = []
        affiliate_positions = [1, 20, 50, 100, 200, 500]

        for idx, photo in enumerate(initial_photos):
            position = idx + 1  # 1-indexed

            # Insert affiliate module at designated positions
            if self.affiliate and position in affiliate_positions:
                module_type = "featured" if position == 1 else "inline"
                caption = photo.get('caption', '')
                module_html = self.affiliate.get_buy_button_html(caption, player['name'], module_type)
                photo_html_parts.append(module_html)

            # Add photo card
            photo_html_parts.append(self._photo_card_html(photo, idx))

        # Pre-render affiliate modules for positions that fall in the scroll portion
        scroll_affiliate_html = {}
        if self.affiliate and remaining_photos:
            for pos in affiliate_positions:
                scroll_idx = pos - 1 - initial_count
                if scroll_idx >= 0 and scroll_idx < len(remaining_photos):
                    caption = remaining_photos[scroll_idx].get('caption', '')
                    module_html = self.affiliate.get_buy_button_html(caption, player['name'], "inline")
                    scroll_affiliate_html[scroll_idx] = module_html

        scroll_script = self._scroll_photos_script(remaining_photos, affiliate_html=scroll_affiliate_html)

        content = f'''
{scroll_script}
<div class="page-header">
    <div class="container">
        <h1>{escape(player['name'])}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid" id="photo-grid">
            {"".join(photo_html_parts)}
        </div>
    </section>
</main>
'''
        content += self._more_players_html(exclude_slug=player['slug'])

        photos_json = json.dumps([{
            'image_url': p.get('image_url', ''),
            'player_name': p.get('player_name', ''),
            'headline': p.get('headline', ''),
            'photographer': p.get('photographer', ''),
            'source': p.get('source', ''),
            'photo_date': p.get('photo_date', '')
        } for p in photos], ensure_ascii=False)

        og_image = photos[0].get('thumbnail_url') or photos[0].get('image_url', '') if photos else ''
        meta = {
            'description': f"Browse {len(photos)} sneaker photos of {player['name']} from NBA games.",
            'og_image': og_image,
            'canonical': f"{self.base_url}/players/{player['slug']}/",
        }
        html = self._base_template(player['name'], content, photos_json, meta=meta, breadcrumb=f'<a href="{self.base_url}/players/">Players</a> / {escape(player["name"])}')
        self._write_file(f"players/{player['slug']}/index.html", html)
    
    def _generate_brand_page(self, brand: Dict):
        """Generate individual brand page"""
        photos = self.archive.get_photos_by_brand(brand['slug'])
        
        content = f'''
<div class="page-header">
    <div class="container">
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
        
        html = self._base_template(brand['name'], content, photos_json, breadcrumb=f'<a href="{self.base_url}/brands/">Brands</a> / {escape(brand["name"])}')
        self._write_file(f"brands/{brand['slug']}/index.html", html)
    
    def _generate_weekly_page(self, week: Dict):
        """Generate weekly gallery page"""
        photos = self.archive.get_photos_by_week(week['week'])
        label = self._week_label(week['week'])

        # Show initial batch, rest via infinite scroll
        initial_count = 24
        initial_photos = photos[:initial_count]
        remaining_photos = photos[initial_count:]
        scroll_script = self._scroll_photos_script(remaining_photos)

        content = f'''
{scroll_script}
<div class="page-header">
    <div class="container">
        <h1>{label}</h1>
        <p class="subtitle">{len(photos)} shoe photos</p>
    </div>
</div>

<main class="container">
    <section class="section">
        <div class="photo-grid" id="photo-grid">
            {"".join(self._photo_card_html(p) for p in initial_photos)}
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
        
        og_image = photos[0].get('thumbnail_url') or photos[0].get('image_url', '') if photos else ''
        meta = {
            'description': f"{len(photos)} NBA sneaker photos from {label}.",
            'og_image': og_image,
            'canonical': f"{self.base_url}/weekly/{week['week']}/",
        }
        html = self._base_template(label, content, photos_json, meta=meta, breadcrumb=f'<a href="{self.base_url}/weekly/">Weekly</a> / {label}')
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
