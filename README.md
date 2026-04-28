# Content Dashboard

A self-hosted Instagram analytics dashboard built with Next.js and Claude. Track your own reels, scrape competitors, transcribe audio, and get AI-powered content ideas — all in one place.

Built by [@pooja daftary](https://www.instagram.com/marketing_withpia)/)

![Dashboard Preview](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js) ![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## What it does

- **My Reels** — Scrapes your last 30 days of reels via Apify, shows views, likes, comments, engagement rate, and flags top performers vs underperforming reels with a bar chart
- **Competitors** — Add any Instagram username, scrape their reels, see what's working for them
- **Compare** — Side-by-side analysis of your account vs competitors: avg views, engagement rate, content theme radar chart, your strengths and content gaps
- **Content Ideas** — GPT-4o reads your data + competitor data and generates a full content strategy: what to make, what to stop, 5 specific reel ideas with hooks
- **Transcription** — Per-reel transcription via OpenAI Whisper (click per reel, not bulk)
- **Local cache** — All scraped data is saved to `data/*.json` so you never re-scrape on refresh

---

## Tech stack

- [Next.js 14](https://nextjs.org/) — App Router, API routes
- [Apify](https://apify.com/) — Instagram scraper (`shu8hvrXbJbY3Eb9W` actor)
- [OpenAI](https://platform.openai.com/) — Whisper for transcription, GPT-4o-mini for content ideas
- [Recharts](https://recharts.org/) — Bar chart, radar chart
- [Tailwind CSS](https://tailwindcss.com/) — Styling

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/content-dashboard.git
cd content-dashboard
```

### 2. Install dependencies

```bash
npm install
```

### 3. Add your API keys

Copy the example env file and fill in your keys:

```bash
cp .env.local.example .env.local
```

Open `.env.local` and add:

```env
APIFY_TOKEN=your_apify_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Getting your keys:**

- **Apify token** → [console.apify.com/account/integrations](https://console.apify.com/account/integrations) — free tier gives ~$5/month credits, enough for daily scraping
- **OpenAI key** → [platform.openai.com/api-keys](https://platform.openai.com/api-keys) — transcription costs ~$0.006/min, content ideas ~$0.01 per run

### 4. Run it

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Usage

### Fetch your reels
1. Go to **My Reels** tab
2. Click **Fetch Reels** — Apify scrapes your last 30 days (takes 1–3 min)
3. Data is cached locally in `data/my_reels.json` — refresh the page anytime without re-scraping
4. Click **Re-sync** only when you want fresh data

### Add competitors
1. Go to **Competitors** tab
2. Type any Instagram username (without @) and click **Add & Scrape**
3. Each competitor is cached separately, re-sync individually whenever you want

### Compare
1. Go to **Compare** tab — requires at least your reels + one competitor
2. See avg views comparison, engagement rates, content theme radar, strengths vs gaps

### Content Ideas
1. Go to **Content Ideas** tab
2. Click **Generate Ideas** — works best after fetching your reels + at least one competitor
3. GPT-4o returns: themes that are working, themes to stop, 5 specific reel ideas with hooks

### Transcribe a reel
On any reel card in My Reels, click **Transcribe** — sends the audio to OpenAI Whisper and saves the transcript to the card (and updates the local cache).

---

## Project structure

```
src/
├── app/
│   ├── page.tsx                  # Main dashboard (4 tabs)
│   ├── globals.css
│   └── api/
│       ├── start-scrape/         # Starts Apify run
│       ├── scrape-status/        # Polls run status
│       ├── scrape-results/       # Fetches dataset results
│       ├── transcribe/           # OpenAI Whisper
│       ├── content-ideas/        # GPT-4o strategy
│       ├── proxy-image/          # Proxies Instagram CDN images
│       └── cache/                # Read/write local JSON cache
├── components/
│   ├── ReelCard.tsx
│   ├── MetricsOverview.tsx
│   ├── PerformanceChart.tsx
│   ├── CompetitorSection.tsx
│   ├── ComparisonView.tsx
│   └── ScrapeProgress.tsx
└── lib/
    ├── apify.ts                  # Apify API helpers
    └── types.ts                  # Shared types

data/                             # Auto-created, gitignored
├── my_reels.json
└── competitors.json
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APIFY_TOKEN` | Yes | Apify API token for Instagram scraping |
| `OPENAI_API_KEY` | Yes | OpenAI key for Whisper + GPT-4o-mini |

---

## Cost estimate

| Action | Approx cost |
|--------|-------------|
| Scrape 30 reels (your account) | ~$0.05 |
| Scrape 15 reels (one competitor) | ~$0.03 |
| Transcribe one reel (60s) | ~$0.006 |
| Generate content ideas | ~$0.01 |

All data is cached locally so you only pay when you explicitly re-sync.

---

## Customise for your account

To change the default Instagram account, update this line in [src/app/page.tsx](src/app/page.tsx):

```ts
const MY_URL = 'https://www.instagram.com/yourusername/'
```

---

## License

MIT — use it, fork it, build on it.

---

Built with [Claude](https://claude.ai) by [@manthanjethwani](https://www.instagram.com/manthanjethwani/)
