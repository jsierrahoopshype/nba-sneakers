
document.addEventListener('contextmenu', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });
document.addEventListener('dragstart', function(e) { if (e.target.tagName === 'IMG') { e.preventDefault(); } });

// Header Quick Search
document.addEventListener('DOMContentLoaded', function() {
    var BASE_URL = "https://jsierrahoopshype.github.io/nba-sneakers";
    var searchInput = document.getElementById('quick-search');
    var resultsDiv = document.getElementById('quick-results');

    if (!searchInput || !resultsDiv) return;

    var players = [];

    // 1. Fetch player index on page load
    fetch(BASE_URL + "/search/players.json")
        .then(function(r) { return r.json(); })
        .then(function(data) { players = data.players || []; })
        .catch(function(e) { console.log('Could not load player index', e); });

    // 2. Filter players as user types (minimum 2 characters)
    searchInput.addEventListener('input', function() {
        var query = this.value.toLowerCase().trim();

        if (query.length < 2) {
            resultsDiv.classList.remove('active');
            resultsDiv.innerHTML = '';
            return;
        }

        var matches = players.filter(function(p) {
            return p.name.toLowerCase().includes(query);
        }).slice(0, 8);

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

