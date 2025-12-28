# NBA Sneakers

**Fully automated, zero-cost NBA shoe photo gallery for HoopsHype**

Generates:
- 🏠 **Homepage** with weekly gallery as hero content
- 🔍 **Player Lookup** — search any player's shoe history
- 👟 **Player Timelines** (`/players/lebron-james/`) — 4+ photos required
- 🏷️ **Brand Hub Pages** (`/brands/nike/`)
- 📅 **Weekly Galleries** (`/weekly/2024-W52/`)
- 📋 **Presto Embed Snippet** (copy-paste ready)

---

## Key Features

### 🔍 Player Sneaker Lookup (`/search/`)

Search any NBA player's shoe history:
- **Instant search** — results appear as you type
- **Featured players** — those with 4+ photos get full timeline pages
- **All players indexed** — everyone in the archive is searchable
- **Visual player cards** — thumbnails from their most recent photos

### 📸 Weekly Gallery (Homepage)

- Homepage leads with the latest week's photos
- Automatically refreshes every Monday
- Full photographer attribution on every image

### 👟 Player Timelines (`/players/{name}/`)

- Individual pages for players with **4+ shoe photos**
- Chronological history of their kicks
- Lightbox viewer with keyboard + swipe support
- Players with fewer photos appear in search but marked "coming soon"

---

## How It Works

```
Every Monday 6 AM EST
        │
        ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│  Fetch new photos │────▶│  Add to archive   │────▶│  Generate static  │
│  from Imagn       │     │  (data/archive)   │     │  site (site/)     │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                                             │
                                                             ▼
                                                    ┌───────────────────┐
                                                    │  Deploy to GitHub │
                                                    │  Pages (FREE)     │
                                                    └───────────────────┘
```

**Cost: $0** — Uses GitHub Actions (2,000 free minutes/month) and GitHub Pages (free hosting).

---

## Quick Setup (15 minutes)

### 1. Create Repository

```bash
# Option A: Use this as a template
# Click "Use this template" on GitHub

# Option B: Clone and push to your own repo
git clone https://github.com/YOUR_ORG/nba-shoe-gallery.git
cd nba-shoe-gallery
git remote set-url origin https://github.com/YOUR_USERNAME/nba-shoe-gallery.git
git push -u origin main
```

### 2. Add Secrets

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Description |
|--------|-------------|
| `IMAGN_USERNAME` | Your Imagn login email |
| `IMAGN_PASSWORD` | Your Imagn password |
| `IMAGN_LIGHTBOX_ID` | (Optional) Saved lightbox ID |

### 3. Enable GitHub Pages

Go to **Settings** → **Pages**:
- Source: **GitHub Actions**

### 4. Run First Build

Go to **Actions** → **Weekly Update** → **Run workflow**

Your site will be live at: `https://YOUR_USERNAME.github.io/nba-shoe-gallery/`

---

## Using in Presto

### Option 1: iframe (Fully Automated)

Add this to your Presto article — it updates automatically every week:

```html
<iframe 
    src="https://YOUR_USERNAME.github.io/nba-shoe-gallery/embed.html"
    style="width: 100%; min-height: 700px; border: none;"
    loading="lazy"
    title="NBA Shoe Photos of the Week">
</iframe>
```

### Option 2: Copy-Paste Snippet

1. Open `https://YOUR_USERNAME.github.io/nba-shoe-gallery/embed.html`
2. View page source
3. Copy everything
4. Paste in Presto's HTML/Source mode

### Option 3: Link to Full Pages

Link to specific sections:

| Page | URL |
|------|-----|
| Homepage | `/` |
| All Players | `/players/` |
| LeBron James | `/players/lebron-james/` |
| All Brands | `/brands/` |
| Nike | `/brands/nike/` |
| This Week | `/weekly/2024-W52/` |
| Embed Only | `/embed.html` |

---

## Site Structure

```
site/
├── index.html              # Homepage
├── embed.html              # Presto embed snippet
├── players/
│   ├── index.html          # All players list
│   ├── lebron-james/
│   │   └── index.html      # LeBron's timeline
│   └── stephen-curry/
│       └── index.html      # Curry's timeline
├── brands/
│   ├── index.html          # All brands list
│   ├── nike/
│   │   └── index.html      # Nike photos
│   └── jordan/
│       └── index.html      # Jordan photos
├── weekly/
│   ├── index.html          # All weeks list
│   ├── latest.html         # Current week (same as embed)
│   └── 2024-W52/
│       └── index.html      # Specific week
├── css/
│   └── style.css
└── js/
    └── gallery.js
```

---

## Data Storage

All photos are stored in `data/archive.json`:

```json
{
  "updated_at": "2024-12-27T10:00:00",
  "photo_count": 150,
  "photos": [
    {
      "imagn_id": "12345",
      "image_url": "https://imagn.com/...",
      "thumbnail_url": "https://imagn.com/.../thumb",
      "headline": "NBA: Lakers at Celtics",
      "photographer": "David Butler II",
      "source": "USA TODAY Sports",
      "photo_date": "2024-12-25",
      "player_name": "LeBron James",
      "player_slug": "lebron-james",
      "brand_slug": "nike"
    }
  ]
}
```

This file grows over time as new photos are added weekly.

---

## Customization

### Change Site Title

Edit `scripts/generate_site.py`:
```python
self.site_title = "HoopsHype Shoe Gallery"
```

### Change Schedule

Edit `.github/workflows/weekly-update.yml`:
```yaml
schedule:
  - cron: '0 11 * * 1'  # Monday 6 AM EST
  # Change to:
  - cron: '0 11 * * *'  # Daily at 6 AM EST
```

### Change Colors

Edit the CSS variables in `scripts/generate_site.py`:
```css
:root {
    --primary: #1a1a2e;    /* Header/footer background */
    --accent: #e94560;     /* Links, highlights */
    --bg: #f8f9fa;         /* Page background */
}
```

### Add More Search Terms

Edit `scripts/fetch_imagn.py`:
```python
queries = ["NBA shoe", "NBA sneaker", "basketball shoe", "NBA kicks"]
```

---

## Local Development

```bash
# Install dependencies
pip install requests beautifulsoup4

# Fetch photos (requires Imagn credentials)
export IMAGN_USERNAME="your_email"
export IMAGN_PASSWORD="your_password"
python scripts/fetch_imagn.py

# Generate site
python scripts/generate_site.py

# Preview locally
cd site
python -m http.server 8000
# Open http://localhost:8000
```

---

## Troubleshooting

### "No photos fetched"

1. Check Imagn credentials are correct
2. Try logging into imagn.com manually
3. Check workflow logs in Actions tab

### "Site not updating"

1. Check Actions tab for failed runs
2. Verify secrets are set correctly
3. Try running workflow manually

### "Embed looks broken in Presto"

1. Use iframe method (more reliable)
2. Check if Presto strips `<script>` tags
3. Try the simpler weekly gallery page

### "Player names not detected"

The system uses pattern matching on photo captions. If a player isn't detected:
1. They'll appear as "NBA" in the gallery
2. Edit `data/archive.json` to manually add `player_name` and `player_slug`
3. Re-run `python scripts/generate_site.py`

---

## Legal Compliance

✅ **Images stay on Imagn CDN** — We link, never re-host

✅ **Full attribution** — Photographer, source, date on every photo

✅ **Editorial use** — News/editorial content coverage

✅ **Authorized access** — Uses your legitimate Imagn credentials

---

## Phase 2 Ideas (Future)

Once the core system is running:

- [ ] Shoe model identification from captions
- [ ] Affiliate links (StockX, GOAT)
- [ ] Search functionality
- [ ] RSS feed
- [ ] Email notifications for new photos
- [ ] "Same shoe worn by..." crosslinks

---

## Files

| File | Purpose |
|------|---------|
| `scripts/archive.py` | Photo archive manager |
| `scripts/fetch_imagn.py` | Fetches photos from Imagn |
| `scripts/generate_site.py` | Generates all static pages |
| `data/archive.json` | Historical photo database |
| `site/` | Generated static site |
| `.github/workflows/weekly-update.yml` | Automation |

---

## License

Internal use for HoopsHype / Gannett properties.

Photo content © USA TODAY Sports / Imagn Images
