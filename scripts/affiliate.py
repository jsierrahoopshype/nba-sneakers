#!/usr/bin/env python3
"""
Affiliate Module for NBA Sneakers

Handles:
- Shoe identification from photos
- Affiliate link routing
- Buy button generation
- Price tracking integration
"""

import re
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AffiliateLink:
    """Represents an affiliate link with metadata"""
    url: str
    program: str  # stockx, goat, nike, footlocker, amazon, etc.
    confidence: str  # exact_match, closest_match, latest_model
    shoe_name: str
    player_name: str
    commission_rate: float  # estimated %


# Player signature shoe database
# Maps player name -> [(shoe_line, brand, affiliate_search_term)]
PLAYER_SIGNATURES = {
    # Nike Athletes
    "LeBron James": [("LeBron", "Nike", "Nike LeBron")],
    "Kevin Durant": [("KD", "Nike", "Nike KD")],
    "Giannis Antetokounmpo": [("Zoom Freak", "Nike", "Nike Zoom Freak")],
    "Devin Booker": [("Book 1", "Nike", "Nike Book")],
    "Ja Morant": [("Ja", "Nike", "Nike Ja")],
    "Sabrina Ionescu": [("Sabrina", "Nike", "Nike Sabrina")],
    
    # Jordan Athletes
    "Luka Doncic": [("Jordan Luka", "Jordan", "Jordan Luka")],
    "Jayson Tatum": [("Jordan Tatum", "Jordan", "Jordan Tatum")],
    "Zion Williamson": [("Jordan Zion", "Jordan", "Jordan Zion")],
    
    # Adidas Athletes
    "James Harden": [("Harden", "Adidas", "Adidas Harden")],
    "Damian Lillard": [("Dame", "Adidas", "Adidas Dame")],
    "Anthony Edwards": [("AE", "Adidas", "Adidas AE1")],
    "Trae Young": [("Trae Young", "Adidas", "Adidas Trae Young")],
    
    # Under Armour Athletes
    "Stephen Curry": [("Curry", "Under Armour", "Under Armour Curry")],
    "Joel Embiid": [("Embiid", "Under Armour", "Under Armour Embiid")],
    
    # Puma Athletes
    "LaMelo Ball": [("MB", "Puma", "Puma MB")],
    "Scoot Henderson": [("Scoot", "Puma", "Puma Scoot")],
    
    # New Balance Athletes
    "Kawhi Leonard": [("Kawhi", "New Balance", "New Balance Kawhi")],
    "Jamal Murray": [("Two WXY", "New Balance", "New Balance Two WXY")],
    
    # Converse Athletes
    "Draymond Green": [("All Star Pro BB", "Converse", "Converse All Star BB")],
    
    # Anta Athletes
    "Kyrie Irving": [("Anta Kai", "Anta", "Anta Kyrie Kai")],
    "Klay Thompson": [("KT", "Anta", "Anta KT")],
}


# Affiliate program configuration
# Real credentials for HoopsHype

# Sovrn API Key (for GOAT, Foot Locker, Finish Line, Dick's)
SOVRN_API_KEY = "530e01008149e736f5173d2766644aff"

# Impact/StockX Partner ID
STOCKX_PARTNER_ID = "2686854"

AFFILIATE_PROGRAMS = {
    "stockx": {
        "name": "StockX",
        "base_url": "https://stockx.pxf.io/c/{partner_id}/1192164/9498?subId1=nbasneakers&u=https://stockx.com/search?s=",
        "partner_id": STOCKX_PARTNER_ID,
        "commission": 0.08,  # 8%
        "priority": 1,
        "best_for": ["rare", "limited", "retro"],
        "network": "impact",
    },
    "goat": {
        "name": "GOAT",
        "base_url": "https://redirect.viglink.com?key={api_key}&u=https://www.goat.com/search?query=",
        "api_key": SOVRN_API_KEY,
        "commission": 0.07,
        "priority": 2,
        "best_for": ["rare", "limited", "retro"],
        "network": "sovrn",
    },
    "footlocker": {
        "name": "Foot Locker",
        "base_url": "https://redirect.viglink.com?key={api_key}&u=https://www.footlocker.com/search?query=",
        "api_key": SOVRN_API_KEY,
        "commission": 0.06,
        "priority": 3,
        "best_for": ["general", "availability"],
        "network": "sovrn",
    },
    "finishline": {
        "name": "Finish Line",
        "base_url": "https://redirect.viglink.com?key={api_key}&u=https://www.finishline.com/store/search?query=",
        "api_key": SOVRN_API_KEY,
        "commission": 0.06,
        "priority": 4,
        "best_for": ["general", "availability"],
        "network": "sovrn",
    },
    "dickssporting": {
        "name": "Dick's Sporting Goods",
        "base_url": "https://redirect.viglink.com?key={api_key}&u=https://www.dickssportinggoods.com/search/SearchDisplay?searchTerm=",
        "api_key": SOVRN_API_KEY,
        "commission": 0.05,
        "priority": 5,
        "best_for": ["general", "performance"],
        "network": "sovrn",
    },
}


class ShoeIdentifier:
    """Identifies shoes from photo captions and metadata"""
    
    # Common shoe model patterns
    SHOE_PATTERNS = [
        # Nike patterns
        (r'Nike\s+(LeBron\s*\d+)', 'Nike', 'LeBron'),
        (r'Nike\s+(KD\s*\d+)', 'Nike', 'KD'),
        (r'Nike\s+(Zoom\s+Freak\s*\d+)', 'Nike', 'Zoom Freak'),
        (r'Nike\s+(Book\s*\d*)', 'Nike', 'Book'),
        (r'Nike\s+(Ja\s*\d+)', 'Nike', 'Ja'),
        (r'Nike\s+(Kobe\s*\d+)', 'Nike', 'Kobe'),
        (r'Nike\s+(PG\s*\d+)', 'Nike', 'PG'),
        (r'Nike\s+(Kyrie\s*\d+)', 'Nike', 'Kyrie'),
        
        # Jordan patterns
        (r'(Jordan\s+Luka\s*\d*)', 'Jordan', 'Luka'),
        (r'(Jordan\s+Tatum\s*\d*)', 'Jordan', 'Tatum'),
        (r'(Jordan\s+Zion\s*\d*)', 'Jordan', 'Zion'),
        (r'(Air\s+Jordan\s*\d+)', 'Jordan', 'Air Jordan'),
        (r'(Jordan\s*\d+)', 'Jordan', 'Air Jordan'),
        
        # Adidas patterns
        (r'Adidas\s+(Harden\s*(?:Vol\.?\s*)?\d*)', 'Adidas', 'Harden'),
        (r'Adidas\s+(Dame\s*\d+)', 'Adidas', 'Dame'),
        (r'Adidas\s+(AE\s*\d*)', 'Adidas', 'AE'),
        (r'Adidas\s+(Trae\s+Young\s*\d*)', 'Adidas', 'Trae Young'),
        
        # Under Armour patterns
        (r'Under\s+Armour\s+(Curry\s*\d+)', 'Under Armour', 'Curry'),
        (r'(Curry\s+Flow\s*\d*)', 'Under Armour', 'Curry'),
        (r'Under\s+Armour\s+(Embiid\s*\d*)', 'Under Armour', 'Embiid'),
        
        # Puma patterns
        (r'Puma\s+(MB\.?\s*\d+)', 'Puma', 'MB'),
        (r'Puma\s+(Scoot\s*\d*)', 'Puma', 'Scoot'),
        
        # New Balance patterns
        (r'New\s+Balance\s+(Kawhi\s*\d*)', 'New Balance', 'Kawhi'),
        (r'New\s+Balance\s+(Two\s+WXY)', 'New Balance', 'Two WXY'),
        
        # Anta patterns
        (r'Anta\s+(Kai\s*\d*)', 'Anta', 'Kai'),
        (r'Anta\s+(KT\s*\d+)', 'Anta', 'KT'),
    ]
    
    def identify_shoe(self, caption: str, player_name: str) -> Tuple[Optional[str], str]:
        """
        Identify shoe from caption text.
        Returns (shoe_name, confidence_level)
        
        Confidence levels:
        - exact_match: Found specific shoe model in caption
        - closest_match: Found shoe line but not exact model
        - latest_model: Using player's current signature shoe
        """
        if not caption:
            return self._get_player_signature(player_name), "latest_model"
        
        caption_upper = caption.upper()
        
        # Try to find exact shoe model
        for pattern, brand, line in self.SHOE_PATTERNS:
            match = re.search(pattern, caption, re.IGNORECASE)
            if match:
                shoe_name = match.group(1).strip()
                return f"{brand} {shoe_name}", "exact_match"
        
        # Check for brand mentions without specific model
        brands = ['Nike', 'Jordan', 'Adidas', 'Under Armour', 'Puma', 'New Balance', 'Anta', 'Converse', 'Li-Ning']
        for brand in brands:
            if brand.upper() in caption_upper:
                # Found brand, try to get player signature for that brand
                sig = self._get_player_signature_for_brand(player_name, brand)
                if sig:
                    return sig, "closest_match"
        
        # Fall back to player's signature shoe
        return self._get_player_signature(player_name), "latest_model"
    
    def _get_player_signature(self, player_name: str) -> Optional[str]:
        """Get player's primary signature shoe"""
        if player_name in PLAYER_SIGNATURES:
            sigs = PLAYER_SIGNATURES[player_name]
            if sigs:
                return f"{sigs[0][1]} {sigs[0][0]}"
        return None
    
    def _get_player_signature_for_brand(self, player_name: str, brand: str) -> Optional[str]:
        """Get player's signature for specific brand"""
        if player_name in PLAYER_SIGNATURES:
            for line, shoe_brand, _ in PLAYER_SIGNATURES[player_name]:
                if shoe_brand.lower() == brand.lower():
                    return f"{shoe_brand} {line}"
        return None


class AffiliateRouter:
    """Routes to best affiliate program based on shoe and context"""
    
    def __init__(self):
        self.identifier = ShoeIdentifier()
    
    def get_affiliate_links(self, caption: str, player_name: str, 
                           num_links: int = 3) -> List[AffiliateLink]:
        """
        Get ranked affiliate links for a shoe.
        Returns multiple options for comparison shopping.
        """
        shoe_name, confidence = self.identifier.identify_shoe(caption, player_name)
        
        if not shoe_name:
            # No shoe identified, use generic basketball shoe search
            shoe_name = f"{player_name} basketball shoes"
            confidence = "latest_model"
        
        links = []
        
        # URL encode the search term
        import urllib.parse
        search_term = urllib.parse.quote_plus(shoe_name)
        
        # Sort programs by priority
        sorted_programs = sorted(
            AFFILIATE_PROGRAMS.items(),
            key=lambda x: x[1]['priority']
        )
        
        for program_id, config in sorted_programs[:num_links]:
            # Build URL based on network type
            if config.get('network') == 'impact':
                # StockX via Impact
                url = config['base_url'].format(partner_id=config['partner_id'])
                url += search_term
            elif config.get('network') == 'sovrn':
                # GOAT, Foot Locker, Finish Line, Dick's via Sovrn/VigLink
                base = config['base_url'].format(api_key=config['api_key'])
                url = base + search_term
            else:
                # Fallback for any other network
                url = config['base_url'] + search_term
            
            links.append(AffiliateLink(
                url=url,
                program=config['name'],
                confidence=confidence,
                shoe_name=shoe_name,
                player_name=player_name,
                commission_rate=config['commission']
            ))
        
        return links
    
    def get_best_link(self, caption: str, player_name: str) -> AffiliateLink:
        """Get single best affiliate link"""
        links = self.get_affiliate_links(caption, player_name, num_links=1)
        return links[0] if links else None
    
    def get_buy_button_html(self, caption: str, player_name: str, 
                           position: str = "inline") -> str:
        """
        Generate HTML for buy button module.
        
        Position options:
        - inline: Small button within timeline
        - featured: Larger module with multiple options
        - sidebar: Compact sidebar widget
        """
        links = self.get_affiliate_links(caption, player_name, num_links=3)
        
        if not links:
            return ""
        
        primary = links[0]
        
        # Confidence badge
        confidence_badges = {
            "exact_match": ("✓ Exact Match", "badge-success"),
            "closest_match": ("≈ Closest Match", "badge-warning"),
            "latest_model": ("★ Latest Model", "badge-info"),
        }
        badge_text, badge_class = confidence_badges.get(
            primary.confidence, 
            ("Shop Now", "badge-default")
        )
        
        if position == "inline":
            return f'''
<div class="affiliate-module inline">
    <a href="{primary.url}" target="_blank" rel="noopener sponsored" class="buy-btn primary">
        <span class="btn-icon">🛒</span>
        <span class="btn-text">Shop {primary.shoe_name}</span>
        <span class="{badge_class}">{badge_text}</span>
    </a>
</div>'''
        
        elif position == "featured":
            secondary_html = ""
            if len(links) > 1:
                secondary_html = '<div class="compare-prices">'
                secondary_html += '<span class="compare-label">Compare prices:</span>'
                for link in links[1:]:
                    secondary_html += f'<a href="{link.url}" target="_blank" rel="noopener sponsored" class="compare-link">{link.program}</a>'
                secondary_html += '</div>'
            
            return f'''
<div class="affiliate-module featured">
    <div class="module-header">
        <span class="module-icon">👟</span>
        <span class="module-title">Shop {player_name}'s Kicks</span>
    </div>
    <div class="shoe-info">
        <span class="shoe-name">{primary.shoe_name}</span>
        <span class="{badge_class}">{badge_text}</span>
    </div>
    <a href="{primary.url}" target="_blank" rel="noopener sponsored" class="buy-btn large">
        Buy on {primary.program}
    </a>
    {secondary_html}
    <div class="track-shoe">
        <button class="track-btn" data-shoe="{primary.shoe_name}" data-player="{player_name}">
            🔔 Track Price Drops
        </button>
    </div>
</div>'''
        
        else:  # sidebar
            return f'''
<div class="affiliate-module sidebar">
    <div class="sidebar-title">Shop the Look</div>
    <div class="sidebar-shoe">{primary.shoe_name}</div>
    <a href="{primary.url}" target="_blank" rel="noopener sponsored" class="buy-btn compact">
        Shop Now →
    </a>
</div>'''


def get_affiliate_css() -> str:
    """Return CSS for affiliate modules"""
    return '''
/* Affiliate Module Styles */
.affiliate-module {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border-radius: 12px;
    padding: 16px;
    margin: 16px 0;
    color: white;
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

.affiliate-module.sidebar {
    padding: 12px;
    font-size: 14px;
}

.buy-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #e94560;
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s;
}

.buy-btn:hover {
    background: #d63850;
    transform: translateY(-2px);
    text-decoration: none;
}

.buy-btn.large {
    padding: 16px 32px;
    font-size: 18px;
}

.buy-btn.compact {
    padding: 8px 16px;
    font-size: 13px;
    width: 100%;
    justify-content: center;
}

.badge-success { background: #28a745; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-warning { background: #ffc107; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-info { background: #17a2b8; padding: 4px 8px; border-radius: 4px; font-size: 11px; }
.badge-default { background: #6c757d; padding: 4px 8px; border-radius: 4px; font-size: 11px; }

.module-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-bottom: 12px;
}

.module-icon { font-size: 24px; }
.module-title { font-size: 18px; font-weight: 600; }

.shoe-info {
    margin-bottom: 16px;
}

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

.compare-link:hover {
    color: white;
}

.track-shoe {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
}

.track-btn {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.3);
    color: rgba(255,255,255,0.8);
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
}

.track-btn:hover {
    border-color: white;
    color: white;
}

.sidebar-title {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(255,255,255,0.6);
    margin-bottom: 8px;
}

.sidebar-shoe {
    font-weight: 600;
    margin-bottom: 12px;
}

/* Contextual Ad Slots */
.sponsor-slot {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 24px 0;
    text-align: center;
}

.sponsor-slot .sponsor-label {
    font-size: 10px;
    text-transform: uppercase;
    color: #999;
    margin-bottom: 8px;
}

.sponsor-slot .sponsor-content {
    min-height: 90px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
}

/* Player Page Sponsor Module */
.player-sponsor {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 24px 0;
    text-align: center;
}

.player-sponsor .sponsor-title {
    font-size: 14px;
    color: #666;
    margin-bottom: 12px;
}

.player-sponsor .sponsor-cta {
    display: inline-block;
    background: #1a1a2e;
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
}

.player-sponsor .sponsor-cta:hover {
    background: #16213e;
    text-decoration: none;
}
'''


def get_tracking_js() -> str:
    """Return JavaScript for price tracking functionality"""
    return '''
// Price Tracking Module
const PriceTracker = {
    tracks: JSON.parse(localStorage.getItem('shoeTracking') || '[]'),
    
    addTrack: function(shoe, player) {
        const track = { shoe, player, added: new Date().toISOString() };
        this.tracks.push(track);
        localStorage.setItem('shoeTracking', JSON.stringify(this.tracks));
        this.showConfirmation(shoe);
    },
    
    showConfirmation: function(shoe) {
        const toast = document.createElement('div');
        toast.className = 'track-toast';
        toast.innerHTML = `
            <span>🔔 Now tracking: ${shoe}</span>
            <small>We'll notify you of price drops</small>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Initialize track buttons
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.track-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const shoe = this.dataset.shoe;
            const player = this.dataset.player;
            PriceTracker.addTrack(shoe, player);
            this.textContent = '✓ Tracking';
            this.disabled = true;
        });
    });
});
'''


# Module insertion positions for player timelines
AFFILIATE_POSITIONS = [1, 20, 50, 100, 200, 500]  # Insert after these photo indices


def should_insert_affiliate(photo_index: int) -> bool:
    """Check if we should insert affiliate module at this position"""
    return photo_index in AFFILIATE_POSITIONS


def get_affiliate_module_for_position(photo_index: int, caption: str, 
                                      player_name: str) -> str:
    """Get appropriate affiliate module based on position"""
    router = AffiliateRouter()
    
    if photo_index == 1:
        # Top of page - featured module
        return router.get_buy_button_html(caption, player_name, "featured")
    elif photo_index in [20, 50]:
        # Mid-timeline - inline buttons
        return router.get_buy_button_html(caption, player_name, "inline")
    else:
        # Deep in timeline - smaller inline
        return router.get_buy_button_html(caption, player_name, "inline")


if __name__ == '__main__':
    # Test the module
    router = AffiliateRouter()
    
    test_cases = [
        ("A detailed view of the Nike LeBron 21 worn by LeBron James", "LeBron James"),
        ("Stephen Curry wears Curry Flow 10", "Stephen Curry"),
        ("Generic shoe photo at the game", "Unknown Player"),
    ]
    
    for caption, player in test_cases:
        print(f"\n=== {player} ===")
        print(f"Caption: {caption}")
        links = router.get_affiliate_links(caption, player)
        for link in links:
            print(f"  {link.confidence}: {link.shoe_name} -> {link.program}")
