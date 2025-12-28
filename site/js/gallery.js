
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
