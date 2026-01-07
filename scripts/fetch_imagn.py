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
    
    def set_session_cookie(self, session_id: str) -> bool:
        """Use existing session cookie instead of login"""
        try:
            self.session.cookies.set('sessionid', session_id, domain='www.imagn.com', path='/')
            
            # Verify session is valid by checking a protected page
            resp = self.session.get(f"{self.BASE_URL}/search/", timeout=30)
            if 'logout' in resp.text.lower() or 'my account' in resp.text.lower() or resp.status_code == 200:
                self.logged_in = True
                return True
            return False
        except Exception as e:
            print(f"Session cookie error: {e}", file=sys.stderr)
            return False
        
    def login(self, username: str, password: str) -> bool:
        """Login to Imagn (may fail due to CAPTCHA)"""
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
    
    def fetch_nba_shoes(self, days_back: int = 365, max_photos: int = 3000) -> List[Dict]:
        """Fetch NBA shoe photos using Imagn API with pagination"""
        photos = []
        seen_ids = set()
        
        # Use the navigationSearchAjax endpoint with pagination
        search_url = f"{self.BASE_URL}/navigationSearchAjax/"
        
        # Content group IDs
        cg_ids = "44,45,328,129,180,164,127,143,300,192,306,312"
        
        # Calculate pages needed (20 results per page)
        pages_needed = (max_photos // 20) + 1
        
        for page in range(1, pages_needed + 1):
            if len(photos) >= max_photos:
                break
                
            params = {
                'q': 'NBA shoes',
                'tag': ',',
                'orientation': '',
                'widthMin': '',
                'widthMax': '',
                'frmdate': '',
                'todate': '',
                'keyWord': '',
                'keywordTypes': '',
                'searchCGOnly': cg_ids,
                'searchType': 'navigation',
                'sort': 'DESC',
                'npage': page,
                'searchWithin': 'searchWithin',
                'searchText': '',
                'isSiteSearch': '',
                'pageToken': '',
                'lastPage': '',
                'useAI': 'false'
            }
            
            try:
                print(f"Fetching page {page}...", file=sys.stderr)
                resp = self.session.get(search_url, params=params, timeout=60)
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        all_images = data.get('allImages', [])
                        
                        if not all_images:
                            print(f"  No more results at page {page}", file=sys.stderr)
                            break
                        
                        new_count = 0
                        for img in all_images:
                            photo = self._parse_api_image(img)
                            if photo and photo['imagn_id'] not in seen_ids:
                                seen_ids.add(photo['imagn_id'])
                                photos.append(photo)
                                new_count += 1
                        
                        print(f"  Page {page}: {len(all_images)} images, {new_count} new (total: {len(photos)})", file=sys.stderr)
                        
                        # Small delay to be respectful to the server
                        if page % 10 == 0:
                            import time
                            time.sleep(0.5)
                                
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error on page {page}: {e}", file=sys.stderr)
                        break
                else:
                    print(f"API returned status {resp.status_code} on page {page}", file=sys.stderr)
                    break
                    
            except Exception as e:
                print(f"Error fetching page {page}: {e}", file=sys.stderr)
                break
        
        print(f"Total fetched: {len(photos)} unique photos", file=sys.stderr)
        return photos[:max_photos]
    
    def _parse_api_image(self, img: Dict) -> Optional[Dict]:
        """Parse a single image from the API response"""
        try:
            img_id = str(img.get('id', ''))
            if not img_id:
                return None
            
            # Build image URLs from the ID
            # Full size: https://cdn.imagn.com/image/thumb/800-750/{id}.jpg
            # Thumbnail: https://cdn.imagn.com/image/thumb/250-225/{id}.jpg
            thumbnail_url = img.get('thumbnail_url') or f"https://cdn.imagn.com/image/thumb/250-225/{img_id}.jpg"
            hover_url = img.get('hover_url') or f"https://cdn.imagn.com/image/thumb/450-425/{img_id}.jpg"
            # Use larger size for main display
            image_url = f"https://cdn.imagn.com/image/thumb/800-750/{img_id}.jpg"
            
            # Extract player name from keywords or caption
            player_name = img.get('keywords', '')
            if not player_name:
                # Try to extract from caption
                caption = img.get('caption', '') or img.get('captionClean', '')
                player_name = self._extract_player_from_caption(caption)
            
            # Parse date
            photo_date = img.get('create_date', '')
            if photo_date and 'T' in photo_date:
                photo_date = photo_date.split('T')[0]
            
            return {
                'imagn_id': img_id,
                'image_url': image_url,
                'thumbnail_url': thumbnail_url,
                'headline': img.get('headLine', ''),
                'caption': img.get('captionClean', '') or img.get('caption', ''),
                'photographer': img.get('photographer', 'Imagn Images'),
                'source': img.get('source', 'USA TODAY Sports'),
                'photo_date': photo_date,
                'player_name': player_name,
                'keywords': img.get('keywords', ''),
            }
        except Exception as e:
            print(f"Error parsing image: {e}", file=sys.stderr)
            return None
    
    def _extract_player_from_caption(self, caption: str) -> str:
        """Extract player name from caption text"""
        if not caption:
            return ''
        
        # Common patterns in Imagn captions
        import re
        
        # Pattern: "shoes worn by [Team] [Position] [Name] (#)"
        match = re.search(r'(?:worn by|of)\s+(?:\w+\s+){1,3}(?:forward|guard|center)?\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(', caption)
        if match:
            return match.group(1).strip()
        
        # Pattern: "[Team] [position] [Name] (#)"
        match = re.search(r'(?:Magic|Lakers|Celtics|Warriors|Heat|Bulls|Nets|Knicks|Bucks|Suns|Mavericks|Nuggets|Clippers|Kings|Hawks|Raptors|76ers|Cavaliers|Pacers|Hornets|Wizards|Pistons|Thunder|Timberwolves|Trail Blazers|Pelicans|Spurs|Jazz|Rockets|Grizzlies)\s+(?:forward|guard|center)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\(', caption)
        if match:
            return match.group(1).strip()
        
        return ''
    
    def _placeholder_for_old_parse_card(self) -> Optional[Dict]:
        """Placeholder - old HTML parsing replaced by API"""
        return {
            'imagn_id': None,
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
    session_id = os.environ.get('IMAGN_SESSION', '')
    
    # Initialize archive - use path relative to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    archive_path = os.path.join(repo_root, 'data', 'archive.json')
    archive = PhotoArchive(archive_path)
    print(f"Archive loaded: {len(archive.photos)} existing photos", file=sys.stderr)
    
    # Fetch new photos
    fetcher = ImagnFetcher()
    
    # Try session cookie first (bypasses CAPTCHA)
    if session_id:
        if fetcher.set_session_cookie(session_id):
            print("Authenticated via session cookie", file=sys.stderr)
        else:
            print("Warning: Session cookie invalid or expired", file=sys.stderr)
    # Fall back to login (may fail due to CAPTCHA)
    elif username and password:
        if fetcher.login(username, password):
            print("Logged in to Imagn", file=sys.stderr)
        else:
            print("Warning: Login failed (likely CAPTCHA)", file=sys.stderr)
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
