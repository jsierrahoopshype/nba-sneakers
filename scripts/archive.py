#!/usr/bin/env python3
"""
Photo Archive Manager

Manages the historical archive of NBA shoe photos.
Stores all photos in a single JSON file, handles deduplication,
and provides query methods for building static pages.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict


class PhotoArchive:
    """Manages the photo archive stored in JSON"""
    
    def __init__(self, archive_path: str = "data/archive.json"):
        self.archive_path = archive_path
        self.photos: Dict[str, Dict] = {}  # keyed by imagn_id
        self.load()
    
    def load(self):
        """Load archive from disk"""
        if os.path.exists(self.archive_path):
            try:
                with open(self.archive_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.photos = {p['imagn_id']: p for p in data.get('photos', [])}
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load archive: {e}")
                self.photos = {}
        else:
            self.photos = {}
    
    def save(self):
        """Save archive to disk"""
        os.makedirs(os.path.dirname(self.archive_path), exist_ok=True)
        
        data = {
            "updated_at": datetime.now().isoformat(),
            "photo_count": len(self.photos),
            "photos": list(self.photos.values())
        }
        
        with open(self.archive_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_photos(self, photos: List[Dict]) -> int:
        """Add new photos to archive, returns count of new photos added"""
        new_count = 0
        for photo in photos:
            imagn_id = photo.get('imagn_id')
            if imagn_id and imagn_id not in self.photos:
                # Normalize and add
                photo['added_at'] = datetime.now().isoformat()
                photo['player_slug'] = self._make_slug(photo.get('player_name', ''))
                photo['brand_slug'] = self._extract_brand_slug(photo)
                self.photos[imagn_id] = photo
                new_count += 1
            elif imagn_id:
                # Update existing with any new fields (but preserve added_at)
                existing = self.photos[imagn_id]
                for key, value in photo.items():
                    if key not in existing or (value and not existing.get(key)):
                        existing[key] = value
        
        return new_count
    
    def _make_slug(self, name: str) -> str:
        """Convert name to URL-safe slug"""
        if not name:
            return ''
        import re
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    def _extract_brand_slug(self, photo: Dict) -> str:
        """Extract brand from photo caption/headline"""
        text = f"{photo.get('headline', '')} {photo.get('caption', '')}".lower()
        
        brands = [
            ('nike', 'nike'),
            ('jordan', 'jordan'),
            ('adidas', 'adidas'),
            ('under armour', 'under-armour'),
            ('new balance', 'new-balance'),
            ('puma', 'puma'),
            ('converse', 'converse'),
            ('anta', 'anta'),
            ('li-ning', 'li-ning'),
            ('peak', 'peak'),
        ]
        
        for keyword, slug in brands:
            if keyword in text:
                return slug
        
        return 'other'
    
    # Query methods for site generation
    
    def get_all_photos(self) -> List[Dict]:
        """Get all photos sorted by date (newest first)"""
        photos = list(self.photos.values())
        photos.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return photos
    
    def get_photos_by_player(self, player_slug: str) -> List[Dict]:
        """Get all photos for a specific player"""
        photos = [p for p in self.photos.values() if p.get('player_slug') == player_slug]
        photos.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return photos
    
    def get_photos_by_brand(self, brand_slug: str) -> List[Dict]:
        """Get all photos featuring a specific brand"""
        photos = [p for p in self.photos.values() if p.get('brand_slug') == brand_slug]
        photos.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return photos
    
    def get_photos_by_week(self, week: str) -> List[Dict]:
        """Get photos from a specific week (format: 2024-W52)"""
        photos = []
        for p in self.photos.values():
            try:
                date = datetime.strptime(p.get('photo_date', ''), '%Y-%m-%d')
                photo_week = date.strftime('%Y-W%W')
                if photo_week == week:
                    photos.append(p)
            except ValueError:
                continue
        photos.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return photos
    
    def get_recent_photos(self, days: int = 7) -> List[Dict]:
        """Get photos from the last N days"""
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        photos = [p for p in self.photos.values() if p.get('photo_date', '') >= cutoff]
        photos.sort(key=lambda p: p.get('photo_date', ''), reverse=True)
        return photos
    
    def get_all_players(self) -> List[Dict]:
        """Get list of all players with photo counts"""
        player_counts = defaultdict(lambda: {'name': '', 'slug': '', 'count': 0, 'latest_date': ''})
        
        for photo in self.photos.values():
            slug = photo.get('player_slug', '')
            name = photo.get('player_name', '')
            if slug and name:
                player_counts[slug]['name'] = name
                player_counts[slug]['slug'] = slug
                player_counts[slug]['count'] += 1
                date = photo.get('photo_date', '')
                if date > player_counts[slug]['latest_date']:
                    player_counts[slug]['latest_date'] = date
        
        players = list(player_counts.values())
        players.sort(key=lambda p: p['count'], reverse=True)
        return players
    
    def get_all_brands(self) -> List[Dict]:
        """Get list of all brands with photo counts"""
        brand_names = {
            'nike': 'Nike',
            'jordan': 'Jordan Brand',
            'adidas': 'Adidas',
            'under-armour': 'Under Armour',
            'new-balance': 'New Balance',
            'puma': 'Puma',
            'converse': 'Converse',
            'anta': 'Anta',
            'li-ning': 'Li-Ning',
            'peak': 'Peak',
            'other': 'Other',
        }
        
        brand_counts = defaultdict(int)
        for photo in self.photos.values():
            brand_counts[photo.get('brand_slug', 'other')] += 1
        
        brands = []
        for slug, count in brand_counts.items():
            if count > 0:
                brands.append({
                    'name': brand_names.get(slug, slug.title()),
                    'slug': slug,
                    'count': count
                })
        
        brands.sort(key=lambda b: b['count'], reverse=True)
        return brands
    
    def get_all_weeks(self) -> List[Dict]:
        """Get list of all weeks with photo counts"""
        week_counts = defaultdict(int)
        
        for photo in self.photos.values():
            try:
                date = datetime.strptime(photo.get('photo_date', ''), '%Y-%m-%d')
                week = date.strftime('%Y-W%W')
                week_counts[week] += 1
            except ValueError:
                continue
        
        weeks = [{'week': w, 'count': c} for w, c in week_counts.items()]
        weeks.sort(key=lambda w: w['week'], reverse=True)
        return weeks
    
    def get_stats(self) -> Dict:
        """Get archive statistics"""
        players = self.get_all_players()
        brands = self.get_all_brands()
        weeks = self.get_all_weeks()
        
        return {
            'total_photos': len(self.photos),
            'total_players': len(players),
            'total_brands': len([b for b in brands if b['slug'] != 'other']),
            'total_weeks': len(weeks),
            'top_players': players[:10],
            'top_brands': brands[:5],
            'recent_weeks': weeks[:4],
        }


if __name__ == '__main__':
    # Test the archive
    archive = PhotoArchive()
    print(f"Archive has {len(archive.photos)} photos")
    print(f"Players: {len(archive.get_all_players())}")
    print(f"Brands: {len(archive.get_all_brands())}")
