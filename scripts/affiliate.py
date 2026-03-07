#!/usr/bin/env python3
"""
Affiliate Module for NBA Sneakers

Handles:
- Shoe identification from photos
- Affiliate link routing
- Buy button generation
"""

import re
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class AffiliateLink:
    """Represents an affiliate link with metadata"""
    url: str
    program: str
    confidence: str
    shoe_name: str
    player_name: str
    commission_rate: float


# Player signature shoe database
PLAYER_SIGNATURES = {
    "LeBron James": [("LeBron", "Nike", "Nike LeBron")],
    "Kevin Durant": [("KD", "Nike", "Nike KD")],
    "Giannis Antetokounmpo": [("Zoom Freak", "Nike", "Nike Zoom Freak")],
    "Devin Booker": [("Book 1", "Nike", "Nike Book")],
    "Ja Morant": [("Ja", "Nike", "Nike Ja")],
    "Luka Doncic": [("Jordan Luka", "Jordan", "Jordan Luka")],
    "Jayson Tatum": [("Jordan Tatum", "Jordan", "Jordan Tatum")],
    "Zion Williamson": [("Jordan Zion", "Jordan", "Jordan Zion")],
    "James Harden": [("Harden", "Adidas", "Adidas Harden")],
    "Damian Lillard": [("Dame", "Adidas", "Adidas Dame")],
    "Anthony Edwards": [("AE", "Adidas", "Adidas AE1")],
    "Trae Young": [("Trae Young", "Adidas", "Adidas Trae Young")],
    "Stephen Curry": [("Curry", "Under Armour", "Under Armour Curry")],
    "Joel Embiid": [("Embiid", "Under Armour", "Under Armour Embiid")],
    "LaMelo Ball": [("MB", "Puma", "Puma MB")],
    "Scoot Henderson": [("Scoot", "Puma", "Puma Scoot")],
    "Kawhi Leonard": [("Kawhi", "New Balance", "New Balance Kawhi")],
    "Kyrie Irving": [("Anta Kai", "Anta", "Anta Kyrie Kai")],
    "Klay Thompson": [("KT", "Anta", "Anta KT")],
}

# Affiliate program configuration
SOVRN_API_KEY = "530e01008149e736f5173d2766644aff"
STOCKX_PARTNER_ID = "2686854"
STOCKX_CAMPAIGN_ID = "9060"
STOCKX_AD_ID = "530344"

AFFILIATE_PROGRAMS = {
    "stockx": {
        "name": "StockX",
        "search_url": "https://stockx.com/search",
        "tracking_params": {
            "utm_source": "impact",
            "utm_medium": "affiliate",
            "ir_campaignid": STOCKX_CAMPAIGN_ID,
            "ir_adid": STOCKX_AD_ID,
            "ir_partnerid": STOCKX_PARTNER_ID,
        },
        "commission": 0.08,
        "priority": 1,
        "network": "impact",
    },
    "goat": {
        "name": "GOAT",
        "search_url": "https://www.goat.com/search",
        "commission": 0.07,
        "priority": 2,
        "network": "sovrn",
    },
    "footlocker": {
        "name": "Foot Locker",
        "search_url": "https://www.footlocker.com/search",
        "commission": 0.06,
        "priority": 3,
        "network": "sovrn",
    },
    "finishline": {
        "name": "Finish Line",
        "search_url": "https://www.finishline.com/store/search",
        "commission": 0.06,
        "priority": 4,
        "network": "sovrn",
    },
    "dickssporting": {
        "name": "Dick's Sporting Goods",
        "search_url": "https://www.dickssportinggoods.com/search/SearchDisplay",
        "commission": 0.05,
        "priority": 5,
        "network": "sovrn",
    },
}


class ShoeIdentifier:
    """Identifies shoes from photo captions and metadata"""
    
    SHOE_PATTERNS = [
        (r'Nike\s+(LeBron\s*\d+)', 'Nike', 'LeBron'),
        (r'Nike\s+(KD\s*\d+)', 'Nike', 'KD'),
        (r'Nike\s+(Kobe\s*\d+)', 'Nike', 'Kobe'),
        (r'Nike\s+(Ja\s*\d+)', 'Nike', 'Ja'),
        (r'(Jordan\s+Luka\s*\d*)', 'Jordan', 'Luka'),
        (r'(Jordan\s+Tatum\s*\d*)', 'Jordan', 'Tatum'),
        (r'(Air\s+Jordan\s*\d+)', 'Jordan', 'Air Jordan'),
        (r'Adidas\s+(Harden\s*(?:Vol\.?\s*)?\d*)', 'Adidas', 'Harden'),
        (r'Adidas\s+(Dame\s*\d+)', 'Adidas', 'Dame'),
        (r'Adidas\s+(AE\s*\d*)', 'Adidas', 'AE'),
        (r'Under\s+Armour\s+(Curry\s*\d+)', 'Under Armour', 'Curry'),
        (r'Puma\s+(MB\.?\s*\d+)', 'Puma', 'MB'),
        (r'Anta\s+(Kai\s*\d*)', 'Anta', 'Kai'),
    ]
    
    def identify_shoe(self, caption: str, player_name: str) -> Tuple[Optional[str], str]:
        if not caption:
            return self._get_player_signature(player_name), "latest_model"
        
        for pattern, brand, line in self.SHOE_PATTERNS:
            match = re.search(pattern, caption, re.IGNORECASE)
            if match:
                shoe_name = match.group(1).strip()
                return f"{brand} {shoe_name}", "exact_match"
        
        return self._get_player_signature(player_name), "latest_model"
    
    def _get_player_signature(self, player_name: str) -> Optional[str]:
        if player_name in PLAYER_SIGNATURES:
            sigs = PLAYER_SIGNATURES[player_name]
            if sigs:
                return f"{sigs[0][1]} {sigs[0][0]}"
        return None


class AffiliateRouter:
    """Routes to best affiliate program based on shoe and context"""
    
    def __init__(self):
        self.identifier = ShoeIdentifier()
    
    def get_affiliate_links(self, caption: str, player_name: str, 
                           num_links: int = 3) -> List[AffiliateLink]:
        import urllib.parse
        
        shoe_name, confidence = self.identifier.identify_shoe(caption, player_name)
        
        if not shoe_name:
            shoe_name = f"{player_name} basketball shoes"
            confidence = "latest_model"
        
        links = []
        search_term_encoded = urllib.parse.quote_plus(shoe_name)
        
        sorted_programs = sorted(
            AFFILIATE_PROGRAMS.items(),
            key=lambda x: x[1]['priority']
        )
        
        for program_id, config in sorted_programs[:num_links]:
            if config.get('network') == 'impact':
                params = config['tracking_params'].copy()
                params['s'] = shoe_name
                url = config['search_url'] + '?' + urllib.parse.urlencode(params)
            elif config.get('network') == 'sovrn':
                if program_id == 'goat':
                    dest_url = f"https://www.goat.com/search?query={search_term_encoded}"
                elif program_id == 'footlocker':
                    dest_url = f"https://www.footlocker.com/search?query={search_term_encoded}"
                elif program_id == 'finishline':
                    dest_url = f"https://www.finishline.com/store/search?query={search_term_encoded}"
                elif program_id == 'dickssporting':
                    dest_url = f"https://www.dickssportinggoods.com/search/SearchDisplay?searchTerm={search_term_encoded}"
                else:
                    dest_url = f"{config['search_url']}?q={search_term_encoded}"
                
                encoded_dest = urllib.parse.quote(dest_url, safe='')
                url = f"https://sovrn.co?key={SOVRN_API_KEY}&u={encoded_dest}"
            else:
                url = f"{config['search_url']}?q={search_term_encoded}"
            
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
        links = self.get_affiliate_links(caption, player_name, num_links=1)
        return links[0] if links else None
    
    def get_buy_button_html(self, caption: str, player_name: str, 
                           position: str = "inline") -> str:
        links = self.get_affiliate_links(caption, player_name, num_links=3)
        
        if not links:
            return ""
        
        primary = links[0]
        
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
</div>'''
        
        else:
            return f'''
<div class="affiliate-module sidebar">
    <div class="sidebar-title">Shop the Look</div>
    <div class="sidebar-shoe">{primary.shoe_name}</div>
    <a href="{primary.url}" target="_blank" rel="noopener sponsored" class="buy-btn compact">
        Shop Now →
    </a>
</div>'''


AFFILIATE_POSITIONS = [1, 20, 50, 100, 200, 500]

def should_insert_affiliate(photo_index: int) -> bool:
    return photo_index in AFFILIATE_POSITIONS

def get_affiliate_module_for_position(photo_index: int, caption: str, 
                                      player_name: str) -> str:
    router = AffiliateRouter()
    if photo_index == 1:
        return router.get_buy_button_html(caption, player_name, "featured")
    else:
        return router.get_buy_button_html(caption, player_name, "inline")