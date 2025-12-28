#!/usr/bin/env python3
"""
Fetches NBA shoe photos from Imagn and adds to archive.

Usage:
    python fetch_imagn.py
    
Environment variables:
    IMAGN_USERNAME - Your Imagn login
    IMAGN_PASSWORD - Your Imagn password  
    IMAGN_LIGHTBOX_ID - (Optional) Saved lightbox ID
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Add parent to path for archive import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import PhotoArchive


class ImagnFetcher:
    """Fetches photos from Imagn using authenticated session"""
    
    BASE_URL = "https://imagn.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.logged_in = False
        
    def login(self, username: str, password: str) -> bool:
        """Login to Imagn"""
        try:
            resp = self.session.get(f"{self.BASE_URL}/login", timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find CSRF token
            csrf = None
            for inp in soup.find_all('input', {'type': 'hidden'}):
                name = inp.get('name', '').lower()
                if 'csrf' in name or 'token' in name:
                    csrf = inp.get('value')
                    break
            
            payload = {
                'email': username,
                'username': username,
                'password': password,
            }
            if csrf:
                payload['_token'] = csrf
                payload['csrf_token'] = csrf
            
            resp = self.session.post(
                f"{self.BASE_URL}/login",
                data=payload,
                allow_redirects=True,
                timeout=30
            )
            
            self.logged_in = 'logout' in resp.text.lower() or '/dashboard' in resp.url
            return self.logged_in
            
        except Exception as e:
            print(f"Login error: {e}", file=sys.stderr)
            return False
    
    def fetch_nba_shoes(self, days_back: int = 7) -> List[Dict]:
        """Fetch NBA shoe photos from the last N days"""
        photos = []
        seen_ids = set()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        queries = ["NBA shoe", "NBA sneaker", "basketball shoe"]
        
        for query in queries:
            try:
                results = self._search(query, start_date, end_date)
                for photo in results:
                    if photo['imagn_id'] not in seen_ids:
                        seen_ids.add(photo['imagn_id'])
                        photos.append(photo)
            except Exception as e:
                print(f"Search error for '{query}': {e}", file=sys.stderr)
        
        # Filter to shoe-related
        shoe_keywords = [
            'shoe', 'sneaker', 'kick', 'footwear',
            'nike', 'jordan', 'adidas', 'puma', 'new balance',
            'under armour', 'lebron', 'kobe', 'kd', 'kyrie', 
            'giannis', 'curry', 'harden', 'luka'
        ]
        
        filtered = []
        for photo in photos:
            text = f"{photo.get('headline', '')} {photo.get('caption', '')}".lower()
            if any(kw in text for kw in shoe_keywords):
                # Extract player name
                photo['player_name'] = self._extract_player(photo)
                filtered.append(photo)
        
        return filtered
    
    def _search(self, query: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Execute search query"""
        photos = []
        
        search_urls = [
            f"{self.BASE_URL}/sports/nba",
            f"{self.BASE_URL}/search",
        ]
        
        params = {
            'q': query,
            'query': query,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'sort': 'date',
        }
        
        for url in search_urls:
            try:
                resp = self.session.get(url, params=params, timeout=60)
                if resp.status_code == 200:
                    html_photos = self._parse_html(resp.text)
                    if html_photos:
                        photos.extend(html_photos)
                        break
            except Exception as e:
                continue
        
        return photos
    
    def _parse_html(self, html: str) -> List[Dict]:
        """Parse HTML search results"""
        photos = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try various selectors
        selectors = ['.image-card', '.photo-item', '.gallery-item', '[data-image-id]', '.search-result']
        
        cards = []
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                break
        
        # Fallback: find img tags
        if not cards:
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if any(x in src.lower() for x in ['imagn', 'usatsimg', 'gannett']):
                    cards.append(img.parent or img)
        
        for card in cards:
            try:
                photo = self._parse_card(card)
                if photo and photo.get('image_url'):
                    photos.append(photo)
            except Exception:
                continue
        
        return photos
    
    def _parse_card(self, card) -> Optional[Dict]:
        """Parse a single photo card"""
        img = card.find('img') if hasattr(card, 'find') else card
        if not img:
            return None
        
        image_url = img.get('src') or img.get('data-src') or ''
        if not image_url:
            return None
        
        # Make absolute
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = urljoin(self.BASE_URL, image_url)
        
        thumbnail_url = image_url
        for old, new in [('/thumb/', '/full/'), ('_thumb', ''), ('/small/', '/large/')]:
            if old in image_url:
                image_url = image_url.replace(old, new)
                break
        
        # Extract metadata
        headline = ''
        photographer = 'Imagn Images'
        photo_date = ''
        
        if hasattr(card, 'select_one'):
            for sel in ['.headline', '.title', 'h3', 'h4', '.caption']:
                elem = card.select_one(sel)
                if elem:
                    headline = elem.get_text(strip=True)
                    break
            
            for sel in ['.photographer', '.credit', '.author']:
                elem = card.select_one(sel)
                if elem:
                    photographer = elem.get_text(strip=True)
                    break
            
            for sel in ['.date', 'time', '[data-date]']:
                elem = card.select_one(sel)
                if elem:
                    photo_date = elem.get('datetime') or elem.get_text(strip=True)
                    break
        
        if not headline:
            headline = img.get('alt', img.get('title', ''))
        
        imagn_id = (
            card.get('data-image-id') if hasattr(card, 'get') else None
        ) or card.get('data-id') if hasattr(card, 'get') else None
        
        if not imagn_id:
            imagn_id = self._extract_id(image_url)
        
        return {
            'imagn_id': imagn_id,
            'image_url': image_url,
            'thumbnail_url': thumbnail_url,
            'headline': headline,
            'photographer': photographer,
            'source': 'USA TODAY Sports',
            'photo_date': self._parse_date(photo_date),
            'caption': headline,
        }
    
    def _extract_id(self, url: str) -> str:
        """Extract photo ID from URL"""
        patterns = [r'/images?/(\d+)', r'image[_-]?(\d+)', r'/(\d{6,})', r'id=(\d+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url.split('/')[-1].split('.')[0].split('?')[0]
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date to YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        date_str = str(date_str).strip()
        
        formats = [
            '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ',
            '%a, %d %b %Y %H:%M:%S %z', '%B %d, %Y', '%b %d, %Y',
            '%m/%d/%Y',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str[:26], fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if match:
            return match.group(0)
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_player(self, photo: Dict) -> Optional[str]:
        """Extract player name from photo metadata"""
        text = f"{photo.get('headline', '')} {photo.get('caption', '')}"
        
        # Pattern: Name (number)
        match = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(\d{1,2}\)', text)
        if match:
            return match.group(1)
        
        # Pattern: position Name
        match = re.search(
            r'(?:guard|forward|center)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            text, re.I
        )
        if match:
            return match.group(1)
        
        # Pattern: Team's Name
        teams = (
            'Lakers|Celtics|Warriors|Bulls|Heat|Nets|Knicks|Mavericks|Suns|Bucks|'
            '76ers|Sixers|Nuggets|Clippers|Kings|Grizzlies|Cavaliers|Hawks|Raptors|'
            'Pacers|Magic|Hornets|Wizards|Pistons|Thunder|Timberwolves|Trail Blazers|'
            'Pelicans|Spurs|Jazz|Rockets'
        )
        match = re.search(
            rf'(?:{teams})[\s\']+(?:guard|forward|center|player)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            text, re.I
        )
        if match:
            return match.group(1)
        
        return None


def main():
    username = os.environ.get('IMAGN_USERNAME', '')
    password = os.environ.get('IMAGN_PASSWORD', '')
    
    # Initialize archive
    archive = PhotoArchive('data/archive.json')
    print(f"Archive loaded: {len(archive.photos)} existing photos", file=sys.stderr)
    
    # Fetch new photos
    fetcher = ImagnFetcher()
    
    if username and password:
        if fetcher.login(username, password):
            print("Logged in to Imagn", file=sys.stderr)
        else:
            print("Warning: Login failed", file=sys.stderr)
    else:
        print("Warning: No credentials provided", file=sys.stderr)
    
    photos = fetcher.fetch_nba_shoes(days_back=7)
    print(f"Fetched {len(photos)} photos from Imagn", file=sys.stderr)
    
    # Add to archive
    new_count = archive.add_photos(photos)
    print(f"Added {new_count} new photos to archive", file=sys.stderr)
    
    # Save archive
    archive.save()
    print(f"Archive saved: {len(archive.photos)} total photos", file=sys.stderr)
    
    # Output summary
    stats = archive.get_stats()
    output = {
        'fetched_at': datetime.now().isoformat(),
        'new_photos': new_count,
        'total_photos': stats['total_photos'],
        'total_players': stats['total_players'],
        'recent_photos': [p for p in archive.get_recent_photos(7)][:20]
    }
    
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
