
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

// Header Quick Search
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('quick-search');
    const resultsDiv = document.getElementById('quick-results');
    
    if (!searchInput || !resultsDiv) return;
    
    let players = [];
    fetch("https://jsierrahoopshype.github.io/nba-sneakers/search/players.json")
        .then(r => r.json())
        .then(data => { players = data.players || []; })
        .catch(e => console.log('Could not load player index'));
    
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        
        if (query.length < 2) {
            resultsDiv.classList.remove('active');
            return;
        }
        
        const matches = players.filter(p => 
            p.name.toLowerCase().includes(query)
        ).slice(0, 8);
        
        if (matches.length === 0) {
            resultsDiv.innerHTML = '<div class="quick-result-item"><span class="name">No players found</span></div>';
        } else {
            resultsDiv.innerHTML = matches.map(p => 
                `<a href="https://jsierrahoopshype.github.io/nba-sneakers/players/${p.slug}/" class="quick-result-item">
                    <span class="name">${p.name}</span>
                    <span class="count">${p.count} photos</span>
                </a>`
            ).join('');
        }
        resultsDiv.classList.add('active');
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.header-search')) {
            resultsDiv.classList.remove('active');
        }
    });
    
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            const firstLink = resultsDiv.querySelector('a');
            if (firstLink) window.location.href = firstLink.href;
        }
    });
});

// Price Tracking
const PriceTracker = {
    tracks: JSON.parse(localStorage.getItem('shoeTracking') || '[]'),
    addTrack: function(shoe, player) {
        this.tracks.push({ shoe, player, added: new Date().toISOString() });
        localStorage.setItem('shoeTracking', JSON.stringify(this.tracks));
        this.showConfirmation(shoe);
    },
    showConfirmation: function(shoe) {
        const toast = document.createElement('div');
        toast.className = 'track-toast';
        toast.innerHTML = '<span>🔔 Now tracking: ' + shoe + '</span><small>We\'ll notify you of price drops</small>';
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 3000);
    }
};

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.track-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            PriceTracker.addTrack(this.dataset.shoe, this.dataset.player);
            this.textContent = '✓ Tracking';
            this.disabled = true;
        });
    });
});
