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

AFFILIATE_PROGRAMS = {
    "stockx": {
        "name": "StockX",
        "search_url": "https://stockx.com/search",
        "commission": 0.08,
        "priority": 1,
        "network": "sovrn",
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
            if config.get('network') == 'sovrn':
                if program_id == 'stockx':
                    dest_url = f"https://stockx.com/search?s={search_term_encoded}"
                elif program_id == 'goat':
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
                           position: str = "inline",
                           header_text: str = None,
                           photo_position: int = 0) -> str:
        links = self.get_affiliate_links(caption, player_name, num_links=3)

        if not links:
            return ""

        primary = links[0]

        # Position 1 = compact single-line module (top of page)
        # Later positions = engaging card module
        if photo_position == 1:
            return self._compact_module_html(primary, player_name)
        else:
            return self._engaging_module_html(primary, player_name, header_text)

    def _compact_module_html(self, link: AffiliateLink, player_name: str) -> str:
        """Compact single-line module for top of page — minimal, unobtrusive."""
        return (
            f'<div class="affiliate-module affiliate-compact">'
            f'<span class="aff-label">\U0001F45F {link.shoe_name} \u2192</span>'
            f'<a href="{link.url}" target="_blank" rel="noopener sponsored" '
            f'class="buy-btn buy-btn-compact">Shop on {link.program}</a>'
            f'</div>'
        )

    def _engaging_module_html(self, link: AffiliateLink, player_name: str,
                              header_text: str = None) -> str:
        """Engaging card module for deeper scroll positions — prominent, eye-catching."""
        title = header_text or "Get the Kicks"
        subtitle = f"As worn by {player_name}" if player_name and player_name != "NBA" else ""
        subtitle_html = f'<span class="aff-subtitle">{subtitle}</span>' if subtitle else ''
        return (
            f'<div class="affiliate-module affiliate-card">'
            f'<div class="aff-card-body">'
            f'<span class="aff-card-title">\U0001F45F {title}</span>'
            f'<span class="aff-card-shoe">{link.shoe_name}</span>'
            f'{subtitle_html}'
            f'</div>'
            f'<a href="{link.url}" target="_blank" rel="noopener sponsored" '
            f'class="buy-btn buy-btn-card">\U0001F6D2 Shop on {link.program} \u2192</a>'
            f'</div>'
        )


AFFILIATE_POSITIONS = [1, 20, 50, 100, 200, 500]

def should_insert_affiliate(photo_index: int) -> bool:
    return photo_index in AFFILIATE_POSITIONS

def get_affiliate_module_for_position(photo_index: int, caption: str,
                                      player_name: str) -> str:
    router = AffiliateRouter()
    return router.get_buy_button_html(caption, player_name, photo_position=photo_index)