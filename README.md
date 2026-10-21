# Palm Beach Inspection Finder (v1)

Static directory of Palm Beach County, FL wind mitigation (OIR-B1-1802), 4-point and roof certification inspectors. Owner: Leonard Ponce.

- `data/inspectors.json`: inspector records (source URL + date checked on every record). `data/inspectors.csv` is regenerated from it.
- `data/cities.json`: one entry per city page.
- `build.py`: zero-dependency generator (Python 3). Writes the site to `docs/`.
- `src/style.css`: stylesheet, copied into `docs/`.

## Build & preview
    python3 build.py
    python3 -m http.server 8080 -d docs

Set `BASE_URL=https://yourdomain.com python3 build.py` so the canonical tags, sitemap and robots use your real domain.

## Deploy (GitHub Pages)
Commit everything and push. In the repo, go to Settings > Pages > Deploy from a branch, pick `main` and `/docs`. `docs/` is committed, so no build step is needed on GitHub.

## Add a city page
1. Add `{"slug":"west-palm-beach","name":"West Palm Beach","intro":"..."}` to `data/cities.json`.
2. For each inspector who serves that city, add the slug to their `cities` array, or add a new record to `data/inspectors.json`. Only use data the inspector publishes. If there is no price, write `"Call for price"`. Always fill in `source` and `checked`.
3. Run `python3 build.py`. The page, nav, homepage links and sitemap update automatically. A nightly job can do steps 2 and 3.

## Add a guide
Add a `layout("guides/<slug>.html", title, description, body_html)` call in `build.py`, link it from the homepage block, then rebuild.

## Status / TODOs
- Contact: listings@pbcinspections.com (set up Porkbun email forwarding before relying on it)
- Insurance-quote widget: hidden; hook is the `QUOTE-WIDGET-HOOK` HTML comment in build.py
- Affiliate disclosure: written on about.html (no paid relationships yet)
- Custom domain: docs/CNAME = pbcinspections.com
