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


NBA_TEAM_NAMES = {
    'hawks', 'celtics', 'nets', 'hornets', 'bulls', 'cavaliers', 'mavericks',
    'nuggets', 'pistons', 'warriors', 'rockets', 'pacers', 'clippers', 'lakers',
    'grizzlies', 'heat', 'bucks', 'timberwolves', 'pelicans', 'knicks', 'thunder',
    'magic', 'sixers', '76ers', 'suns', 'trail blazers', 'blazers', 'kings',
    'spurs', 'raptors', 'jazz', 'wizards',
    # Full names
    'atlanta hawks', 'boston celtics', 'brooklyn nets', 'charlotte hornets',
    'chicago bulls', 'cleveland cavaliers', 'dallas mavericks', 'denver nuggets',
    'detroit pistons', 'golden state warriors', 'houston rockets', 'indiana pacers',
    'la clippers', 'los angeles clippers', 'los angeles lakers', 'memphis grizzlies',
    'memphis grizzles', 'miami heat', 'milwaukee bucks', 'minnesota timberwolves',
    'new orleans pelicans', 'new york knicks', 'oklahoma city thunder',
    'orlando magic', 'philadelphia 76ers', 'phoenix suns',
    'portland trail blazers', 'sacramento kings', 'san antonio spurs',
    'toronto raptors', 'utah jazz', 'washington wizards',
    # Common variants
    'team lebron', 'team durant', 'team giannis', 'team usa', 'nba', 'all-star',
}


def _looks_like_person_name(name: str) -> bool:
    """Check if a string looks like a person's name (not a team or generic term)"""
    if not name or len(name.strip()) < 3:
        return False
    name_clean = name.strip()
    # Must contain a space (first + last name)
    if ' ' not in name_clean:
        return False
    # Must not be a team name
    if name_clean.lower() in NBA_TEAM_NAMES:
        return False
    # Each word should start with a capital letter (person name pattern)
    words = name_clean.split()
    if len(words) < 2:
        return False
    # At least first and last word should look like name parts
    for word in [words[0], words[-1]]:
        # Allow hyphens, apostrophes in names (e.g. O'Neal, Abdul-Jabbar)
        cleaned = word.replace('-', '').replace("'", '')
        if not cleaned or not cleaned[0].isupper():
            return False
    return True


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

    def _login(self) -> Optional[str]:
        """Re-authenticate using IMAGN_USERNAME/IMAGN_PASSWORD env vars.

        Posts credentials to the login endpoint, extracts the new sessionid
        cookie, and returns it. Returns None on failure.
        """
        username = os.environ.get('IMAGN_USERNAME', '')
        password = os.environ.get('IMAGN_PASSWORD', '')
        if not username or not password:
            print("Cannot re-authenticate: IMAGN_USERNAME/IMAGN_PASSWORD not set",
                  file=sys.stderr)
            return None

        print("Session expired, re-authenticating...", file=sys.stderr)
        if self.login(username, password):
            session_cookie = self.session.cookies.get('sessionid')
            if session_cookie:
                print("Re-authentication successful", file=sys.stderr)
                return session_cookie
            print("Re-authentication succeeded but no sessionid cookie found",
                  file=sys.stderr)
        else:
            print("Re-authentication failed", file=sys.stderr)
        return None
    
    def fetch_nba_shoes(self, days_back: int = 365, max_photos: int = 20000) -> List[Dict]:
        """Fetch NBA shoe photos using Imagn API with pagination.

        Args:
            days_back: Number of days to look back from today. Use 0 for no date filter.
            max_photos: Maximum number of photos to fetch.
        """
        photos = []
        seen_ids = set()

        # Use the navigationSearchAjax endpoint with pagination
        search_url = f"{self.BASE_URL}/navigationSearchAjax/"

        # Content group IDs
        cg_ids = "44,45,328,129,180,164,127,143,300,192,306,312"

        # Calculate date range from days_back
        if days_back > 0:
            to_date = datetime.now().strftime('%m/%d/%Y')
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
        else:
            from_date = ''
            to_date = ''

        # Calculate pages needed (20 results per page)
        pages_needed = (max_photos // 20) + 1

        for page in range(1, pages_needed + 1):
            if len(photos) >= max_photos:
                break

            # Progress update every 50 pages
            if page % 50 == 0:
                print(f"Progress: {len(photos)} photos fetched so far...", file=sys.stderr)

            params = {
                'q': 'NBA shoes',
                'tag': ',',
                'orientation': '',
                'widthMin': '',
                'widthMax': '',
                'frmdate': from_date,
                'todate': to_date,
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

                # Re-authenticate on 400/401 and retry once
                if resp.status_code in (400, 401):
                    print(f"Got {resp.status_code} on page {page}, attempting re-auth...",
                          file=sys.stderr)
                    new_cookie = self._login()
                    if new_cookie:
                        resp = self.session.get(search_url, params=params, timeout=60)
                    else:
                        print("Re-auth failed, stopping fetch", file=sys.stderr)
                        break

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
                        import time
                        time.sleep(0.2)  # 200ms between requests

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
            
            # Extract player name from keywords, handling pipe-delimited values
            raw_keywords = img.get('keywords', '')
            keyword_name = self._best_name_from_keywords(raw_keywords)

            # Always try caption extraction as validation/fallback
            caption = img.get('caption', '') or img.get('captionClean', '')
            caption_name = self._extract_player_from_caption(caption)

            # Decide which name to use:
            # - If keyword looks like a person name, use it (unless caption disagrees
            #   and keyword looks like a team name)
            # - If keyword is a team/generic, prefer caption extraction
            # - Fall back to whatever we have
            if keyword_name and _looks_like_person_name(keyword_name):
                player_name = keyword_name
            elif caption_name and _looks_like_person_name(caption_name):
                player_name = caption_name
            elif keyword_name:
                player_name = keyword_name
            else:
                player_name = caption_name

            # FILTER: Skip if player name is empty or too generic
            if not player_name or len(player_name.strip()) < 3:
                return None
            
            # Build image URLs from the ID (full-resolution)
            thumbnail_url = img.get('thumbnail_url') or f"https://www.imagn.com/image/{img_id}.jpg"
            hover_url = img.get('hover_url') or f"https://www.imagn.com/image/{img_id}.jpg"
            image_url = f"https://www.imagn.com/image/{img_id}.jpg"
            
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
                'player_name': player_name.strip(),
                'keywords': img.get('keywords', ''),
            }
        except Exception as e:
            print(f"Error parsing image: {e}", file=sys.stderr)
            return None
    
    def _best_name_from_keywords(self, raw_keywords: str) -> str:
        """Parse pipe-delimited keywords and return the best player name candidate"""
        if not raw_keywords:
            return ''
        # Split on pipe and evaluate each segment
        parts = [p.strip() for p in raw_keywords.split('|') if p.strip()]
        # First pass: find a segment that looks like a person name
        for part in parts:
            if _looks_like_person_name(part):
                return part
        # Second pass: return first non-empty part (may be team name, caller decides)
        return parts[0] if parts else ''

    def _extract_player_from_caption(self, caption: str) -> str:
        """Extract player name from caption text"""
        if not caption:
            return ''

        # Name part pattern: handles LeBron, O'Neal, Abdul-Jabbar, McCollum, etc.
        _NP = r"[A-Z][A-Za-z']+(?:-[A-Z][A-Za-z']+)*"
        _FULL_NAME = rf"({_NP}\s+{_NP}(?:\s+{_NP})?)"

        # Pattern: "[position] Name (#)" — most specific, avoids team name capture
        match = re.search(
            rf"(?:forward|guard|center)\s+{_FULL_NAME}\s*\(\d{{1,2}}\)",
            caption
        )
        if match and _looks_like_person_name(match.group(1)):
            return match.group(1).strip()

        # Pattern: "shoes worn by [Team] [Position] [Name] (#)"
        match = re.search(
            rf"(?:worn by|of)\s+(?:\w+\s+){{1,3}}(?:forward|guard|center)?\s*{_FULL_NAME}\s*\(",
            caption
        )
        if match and _looks_like_person_name(match.group(1)):
            return match.group(1).strip()

        # Pattern: "[Team] [position] [Name] (#)"
        match = re.search(
            rf"(?:Magic|Lakers|Celtics|Warriors|Heat|Bulls|Nets|Knicks|Bucks|Suns|"
            rf"Mavericks|Nuggets|Clippers|Kings|Hawks|Raptors|76ers|Cavaliers|Pacers|"
            rf"Hornets|Wizards|Pistons|Thunder|Timberwolves|Trail Blazers|Pelicans|"
            rf"Spurs|Jazz|Rockets|Grizzlies)\s+(?:forward|guard|center)\s+"
            rf"{_FULL_NAME}\s*\(",
            caption
        )
        if match:
            return match.group(1).strip()

        # Pattern: "Name (#)" — broadest, validate with _looks_like_person_name
        match = re.search(rf"{_FULL_NAME}\s*\(\d{{1,2}}\)", caption)
        if match and _looks_like_person_name(match.group(1)):
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


def reparse_archive(archive_path: str, dry_run: bool = False) -> Dict:
    """Re-process existing archive entries to fix misattributed player names.

    Uses the improved _extract_player_from_caption and _best_name_from_keywords
    logic to correct player_name for photos that were attributed to team names
    or other incorrect values.

    Returns a summary dict with counts and list of changes made.
    """
    archive = PhotoArchive(archive_path)
    fetcher = ImagnFetcher()

    fixes = []
    for imagn_id, photo in archive.photos.items():
        old_name = photo.get('player_name', '')
        keywords = photo.get('keywords', '')
        caption = photo.get('caption', '')

        # Re-derive player name using improved logic
        keyword_name = fetcher._best_name_from_keywords(keywords)
        caption_name = fetcher._extract_player_from_caption(caption)

        if keyword_name and _looks_like_person_name(keyword_name):
            new_name = keyword_name
        elif caption_name and _looks_like_person_name(caption_name):
            new_name = caption_name
        elif keyword_name:
            new_name = keyword_name
        else:
            new_name = caption_name

        if not new_name or len(new_name.strip()) < 3:
            continue

        new_name = new_name.strip()

        # Only fix if the name actually changed
        if new_name != old_name:
            fixes.append({
                'imagn_id': imagn_id,
                'old_name': old_name,
                'new_name': new_name,
                'photo_date': photo.get('photo_date', ''),
                'caption_snippet': caption[:100] if caption else '',
            })
            if not dry_run:
                photo['player_name'] = new_name
                photo['player_slug'] = archive._make_slug(new_name)

    if not dry_run and fixes:
        archive.save()

    return {
        'total_photos': len(archive.photos),
        'fixes_applied': len(fixes),
        'dry_run': dry_run,
        'changes': fixes,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fetch NBA shoe photos from Imagn')
    parser.add_argument('--reparse', action='store_true',
                        help='Re-process existing archive to fix misattributed player names')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what reparse would change without modifying the archive')
    parser.add_argument('--days-back', type=int, default=7,
                        help='Number of days to look back (default: 7, 0 for no limit)')
    parser.add_argument('--max-photos', type=int, default=20000,
                        help='Maximum number of photos to fetch (default: 20000)')
    parser.add_argument('--clear-archive', action='store_true',
                        help='Clear the archive before fetching (for full re-fetch)')
    args = parser.parse_args()

    # Initialize archive - use path relative to repo root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    archive_path = os.path.join(repo_root, 'data', 'archive.json')

    if args.reparse:
        print(f"Re-parsing archive to fix player names (dry_run={args.dry_run})...",
              file=sys.stderr)
        result = reparse_archive(archive_path, dry_run=args.dry_run)
        print(f"Scanned {result['total_photos']} photos, "
              f"{'would fix' if args.dry_run else 'fixed'} {result['fixes_applied']} entries",
              file=sys.stderr)
        for change in result['changes']:
            print(f"  {change['photo_date']} | "
                  f"\"{change['old_name']}\" -> \"{change['new_name']}\" | "
                  f"{change['caption_snippet']}", file=sys.stderr)
        print(json.dumps(result, indent=2))
        return

    username = os.environ.get('IMAGN_USERNAME', '')
    password = os.environ.get('IMAGN_PASSWORD', '')
    session_id = os.environ.get('IMAGN_SESSION', '')

    archive = PhotoArchive(archive_path)

    if args.clear_archive:
        print(f"Clearing archive ({len(archive.photos)} photos)...", file=sys.stderr)
        archive.photos = {}
        archive.save()

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

    photos = fetcher.fetch_nba_shoes(days_back=args.days_back, max_photos=args.max_photos)
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
