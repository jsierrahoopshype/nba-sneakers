
document.addEventListener('contextmenu', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
document.addEventListener('dragstart', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });

// Header Quick Search
document.addEventListener('DOMContentLoaded', function() {
    var BASE_URL = "https://jsierrahoopshype.github.io/nba-sneakers";
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


// Infinite Scroll
document.addEventListener('DOMContentLoaded', function() {
    var data = window.__SCROLL_PHOTOS;
    if (!data || !data.photos || !data.photos.length) return;
    var grid = document.getElementById('photo-grid');
    if (!grid) return;
    var photos = data.photos;
    var baseUrl = data.baseUrl || '';
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
            var p = photos[i];
            var card = document.createElement('div');
            card.className = 'photo-card';
            card.innerHTML = '<a href="' + baseUrl + '/photos/' + p.id + '/" class="img-wrap"><img src="' + p.thumb + '" alt="' + p.headline + '" loading="lazy"></a>'
                + '<div class="meta"><a href="' + baseUrl + '/players/' + p.playerSlug + '/" class="player-link">' + p.player + '</a>'
                + '<div class="headline">' + p.headline + '</div>'
                + '<div class="credit">📷 ' + p.photographer + ' · ' + p.source + ' · ' + fmtDate(p.date) + '</div></div>';
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
