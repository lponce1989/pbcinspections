#!/usr/bin/env python3
"""Zero-dependency static generator. Output -> docs/ (GitHub Pages: main /docs)."""
import json, csv, os, html, datetime, statistics, shutil, re, posixpath, urllib.parse
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,"docs")
SITE="PBC Inspections"; LONG="PBC Inspections"
BASE_URL=os.environ.get("BASE_URL","https://pbcinspections.com").rstrip("/")
CONTACT="listings@pbcinspections.com"      # Porkbun email forwarding
CORRECTIONS="corrections@pbcinspections.com"
e=html.escape
import hashlib
ASSET_V=hashlib.sha1((open(f"{ROOT}/src/style.css").read()+open(f"{ROOT}/src/site.js").read()).encode()).hexdigest()[:8]
import base64
_svg=open(f"{ROOT}/src/favicon.svg").read().strip()
LOGO=_svg.replace('<svg ','<svg class="logo" aria-hidden="true" width="28" height="28" ',1)
# PNG fallbacks are inlined as data URIs (generated from src/favicon.svg; see src/favicon-32.png.b64, src/apple-touch-icon.png.b64)
FAV_PNG="data:image/png;base64,"+open(f"{ROOT}/src/favicon-32.png.b64").read().strip()
TOUCH_PNG="data:image/png;base64,"+open(f"{ROOT}/src/apple-touch-icon.png.b64").read().strip()
data=json.load(open(f"{ROOT}/data/inspectors.json")); cities=json.load(open(f"{ROOT}/data/cities.json"))
INS=data["inspectors"]; CHECKED=data["checked"]
pages=[]
G="guides/"
GUIDE_LINE={"4-point-vs-wind-mitigation-vs-roof-certification":"What each report covers and when Citizens asks for it.",
 "oir-b1-1802-rev-04-26-changes":"What's new on the wind mitigation form effective April 1, 2026.",
 "how-long-inspection-reports-are-valid":"Wind mitigation reports last up to five years; Citizens wants 4-point reports within 12 months.",
 "look-up-inspector-license-dbpr":"Check an inspector's Florida license yourself on the DBPR search.",
 "my-safe-florida-home-vs-private-wind-mitigation":"The free program inspection includes the OIR-B1-1802 form; when a private one is faster."}
def guide_list(pre=""):
    return '<div class="glist">'+"".join(f'<a class="gitem" href="{pre}{s}.html"><span class="g-t">{e(t)}</span><span class="g-d">{e(GUIDE_LINE[s])}</span><span class="g-c">Checked {nice_date(CHECKED)}</span></a>' for s,t in GUIDES)+'</div>'
def city_stat(c):
    recs=[i for i in INS if c["slug"] in i["cities"]]; byf={}
    for i in recs: byf.setdefault(i["firm"],[]).append(i)
    return len(recs),stats(byf,"wind")
def city_grid(pre=""):
    out=""
    for c in cities:
        n,w=city_stat(c); h=c["housing"]
        out+=(f'<a class="ccard" href="{pre}{c["slug"]}.html"><span class="c-n">{e(c["name"])}</span><span class="c-k">{n} inspectors</span>'
              f'<span class="c-s">Median wind mit. <b>{money(w["med"])}</b></span><span class="c-s">Median home built <b>{h["median_year"]}</b></span></a>')
    return f'<div class="cgrid">{out}</div>'
GUIDES=[("4-point-vs-wind-mitigation-vs-roof-certification","4-point vs. wind mitigation vs. roof certification"),
 ("oir-b1-1802-rev-04-26-changes","What changed on the OIR-B1-1802 (Rev. 04/26) wind mitigation form"),
 ("how-long-inspection-reports-are-valid","How long a wind mitigation, 4-point or roof report stays valid"),
 ("look-up-inspector-license-dbpr","How to look up a Florida inspector's license on DBPR"),
 ("my-safe-florida-home-vs-private-wind-mitigation","My Safe Florida Home inspection vs. a private wind mitigation")]
BASE_LABEL={"pbc":"Local (PBC-based)","bd":"Serves area from Broward/Miami-Dade","other":"Based elsewhere in Florida","unknown":"Address not stated"}
LIC_LABEL={"verified":"Verified","not_verified":"Not verified","note":"See note"}
TYPES=[("wind","Wind mitigation"),("four","4-point"),("roof","Roof certification"),("bundle","4-point + wind bundle")]
TXT={"wind":"wind_mit","four":"four_point","roof":"roof_cert","bundle":"bundle"}

def url(path): return f"{BASE_URL}/{path}".replace("index.html","")
def ld(obj): return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False)+'</script>'
def ago(d): return f'<time class="ago" datetime="{e(d)}">{e(d)}</time>'

def layout(path,title,desc,body,crumbs,extra_ld=()):
    pre="../"*path.count("/")
    if "PBC Inspections" not in title: title=f"{title} | PBC Inspections"
    nav=(f'<a href="{pre}index.html">Home</a><a href="{pre}cities/index.html">Cities</a><a href="{pre}prices/index.html">Prices</a>'
         f'<a href="{pre}guides/index.html">Guides</a><a href="{pre}about.html">About</a>')
    canon=url(path)
    bc={"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":url("index.html")}]+
        [{"@type":"ListItem","position":n+2,"name":nm,"item":url(p)} for n,(nm,p) in enumerate(crumbs)]}
    crumb_html='' if not crumbs else '<nav class="crumbs" aria-label="Breadcrumb"><a href="'+pre+'index.html">Home</a>'+"".join(f' &rsaquo; <a href="{pre}{p}">{e(nm)}</a>' for nm,p in crumbs)+'</nav>'
    doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{canon}"><meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap"><link rel="icon" href="{pre}favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="32x32" href="{FAV_PNG}"><link rel="apple-touch-icon" href="{TOUCH_PNG}"><meta name="theme-color" content="#0b3d4f"><link rel="stylesheet" href="{pre}style.css?v={ASSET_V}">{ld(bc)}{"".join(ld(x) for x in extra_ld)}</head><body>
<a class="skip" href="#main">Skip to content</a><header><div class="wrap"><a class="brand" href="{pre}index.html">{LOGO}<span>{LONG}</span></a><nav>{nav}</nav></div></header>
<main class="wrap" id="main" tabindex="-1">{crumb_html}{body}</main>
<footer><div class="wrap"><p>Informational directory only, not insurance advice. Listings and prices are copied from inspectors' own websites on the date shown and may have changed; always confirm with the inspector. <a href="{pre}about.html">Disclaimer, disclosures &amp; listing criteria</a>. Corrections: <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p><p>&copy; {datetime.date.today().year} {LONG} &middot; Owner: Leonard Ponce</p></div></footer>
<script src="{pre}site.js?v={ASSET_V}" defer></script>
<script data-goatcounter="https://pbcinspections.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script></body></html>'''
    doc=canon_links(doc,path)
    fp=os.path.join(OUT,path); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w").write(doc); pages.append(path)
def canon_links(doc,path):
    base=posixpath.dirname(path)
    def fix(m):
        attr,u=m.group(1),m.group(2)
        if re.match(r"^(?:[a-z]+:|#|/)",u): return m.group(0)
        frag=""
        if "#" in u: u,frag=u.split("#",1); frag="#"+frag
        p=posixpath.normpath(posixpath.join(base,u))
        p="/"+("" if p in (".","index.html") else p)
        if p.endswith("/index.html"): p=p[:-10]
        return f'{attr}="{p}{frag}"'
    return re.sub(r'\b(href|src)="([^"]+)"',fix,doc)

# ---------- price helpers ----------
def pr(i,t): return i["prices"][t]
CAPMARK={"homes up to 2,000 sq ft":"a","up to 2,500 sq ft":"b","homes up to 3,000 sq ft":"c"}
def mark_html(i,t):
    p=pr(i,t)
    if p["amt"] is None:
        txt=i[TXT[t]]
        if txt.startswith(("Free","Included","Wind Mit +")): return 'Incl.<sup class="mk">&#9674;</sup>'
        if t=="bundle": return "Yes" if txt.startswith("Yes") else "&ndash;"
        return '<span class="muted">Call</span>'
    m="" if p["cap"] else "&dagger;"
    if p["note"]: m+="*"
    capt=f'<span class="capi">&le;{e(re.sub(r"^(homes )?up to ","",p["cap"]))}</span>' if p["cap"] else ""
    return f'${p["amt"]}'+(f'<sup class="mk">{m}</sup>' if m else '')+capt
LEGEND=('<p class="legend small"><strong>Key:</strong> <sup>&dagger;</sup> no size cap stated &middot; &le; sq ft = largest home the price covers &middot; '
        '<sup>*</sup> see note in the listing card &middot; <sup>&#9674;</sup> included free with a full home inspection &middot; Call = no published price. '
        '"From" prices can rise with size, age and travel.</p>')
def price_html(i,t):
    p=pr(i,t)
    if p["amt"] is None: return e(i[TXT[t]])
    cap=f'homes {p["cap"]}' if p["cap"] and not p["cap"].startswith("homes") else (p["cap"] or "no size cap stated")
    note=f'; {p["note"]}' if p["note"] else ''
    return f'${p["amt"]}<span class="cap"> ({e(cap)}{e(note)})</span>'
def at2000(i):
    bits=[f'{lbl} ${pr(i,t)["amt"]}' for t,lbl in (("wind","Wind"),("four","4-pt"),("roof","Roof")) if pr(i,t)["amt"] is not None and pr(i,t)["covers2000"]]
    return " &middot; ".join(bits) if bits else '<span class="muted">Not stated</span>'
def firms():
    f={}
    for i in INS: f.setdefault(i["firm"],[]).append(i)
    return f
def firm_value(recs,t):
    v=[pr(i,t)["amt"] for i in recs if pr(i,t)["amt"] is not None]
    return statistics.median(v) if v else None
def stats(recs_by_firm,t):
    v=[firm_value(r,t) for r in recs_by_firm.values()]; v=[x for x in v if x is not None]
    allp=[pr(i,t)["amt"] for r in recs_by_firm.values() for i in r if pr(i,t)["amt"] is not None]  # every listing, incl. per-city prices
    return dict(n=len(v),total=len(recs_by_firm),lo=min(allp) if allp else None,hi=max(allp) if allp else None,med=statistics.median(v) if v else None)
STATNOTE=('<p class="legend small">Range = lowest and highest price published in any listing, including each per-city price a company publishes. '
  'Median and "Companies publishing a price" count each company once (a company with different city prices counts once, at the median of its city prices). '
  'City figures use only the listings on that city page, so every city range falls inside the county range.</p>')
def money(x): return "—" if x is None else (f"${x:,.0f}" if float(x).is_integer() else f"${x:,.2f}")
FIRMS=firms()

def stats_table(byfirm,caption=""):
    rows="".join(f'<tr><td>{lbl}</td><td class="num">{money(s["lo"])}&ndash;{money(s["hi"])}</td><td class="num">{money(s["med"])}</td><td class="num">{s["n"]} of {s["total"]}</td></tr>' for t,lbl in TYPES for s in [stats(byfirm,t)])
    return f'<table class="stats"><thead><tr><th>Inspection</th><th>Published price range</th><th>Median (per company)</th><th>Companies publishing a price</th></tr></thead><tbody>{rows}</tbody></table>'+STATNOTE
TILE_LBL={"wind":"Wind mitigation","four":"4-point","roof":"Roof certification","bundle":"4-point + wind bundle"}
def stat_tiles(byfirm,note=True):
    t="".join(f'<div class="tile"><div class="t-lbl">{TILE_LBL[k]}</div><div class="t-med">{money(s["med"])}<span class="sr-only"> median</span></div>'
      f'<div class="t-sub">median &middot; <span class="nw">range {money(s["lo"])}&ndash;{money(s["hi"])}</span></div><div class="t-sub">{s["n"]} of {s["total"]} publish a price</div></div>' for k,_ in TYPES for s in [stats(byfirm,k)])
    return f'<div class="tiles">{t}</div>'+(STATNOTE if note else "")

# ---------- city table + cards ----------
def flt(i):
    p=lambda t: pr(i,t)["amt"]
    pub=any(p(t) is not None for t in ("wind","four","roof"))
    bundle=p("bundle") is not None or i["bundle"].startswith(("Yes","Included","Wind Mit"))
    return f'data-pub="{int(pub)}" data-bundle="{int(bundle)}" data-lic="{int(i["lic_status"]=="verified")}" data-local="{int(i["base"]=="pbc")}"'
def row(i):
    p=lambda t: pr(i,t)["amt"]
    cell=lambda t,lbl: f'<td class="c-{t} num" data-label="{lbl}" data-v="{"" if p(t) is None else p(t)}">{mark_html(i,t)}</td>'
    lic="" if i["lic_status"]=="note" else f'<span class="badge b-{i["lic_status"]}">{LIC_LABEL[i["lic_status"]]}</span>'
    return (f'<tr {flt(i)}><td class="c-name"><a href="#{e(i["slug"])}">{e(i["name"])}</a> <span class="tag tag-{i["base"]}">{BASE_LABEL[i["base"]]}</span></td>'
      +cell("wind","Wind mitigation")+cell("four","4-point")+cell("roof","Roof cert")+cell("bundle","Bundle")
      +f'<td class="c-lic">{lic or "<a class=small href=#"+e(i["slug"])+">See card</a>"}</td></tr>')
FILTERS=('<div class="filters" hidden><strong>Show only:</strong> <label><input type="checkbox" data-f="pub"> Publishes prices</label> <label><input type="checkbox" data-f="bundle"> Offers a bundle</label> '
     '<label><input type="checkbox" data-f="lic"> License verified</label> <label><input type="checkbox" data-f="local"> Based in Palm Beach County</label> <span class="count" aria-live="polite"></span></div>')
def table(rows):
    return ('<div class="tablewrap"><table class="compare sortable city-table"><thead><tr><th>Inspector</th><th data-sort>Wind mit.</th><th data-sort>4-point</th><th data-sort>Roof cert</th><th data-sort class="c-bundle">Bundle</th><th>FL license</th></tr></thead><tbody>'
     +"".join(row(i) for i in rows)+'</tbody></table>'+LEGEND+'</div>')
def capline(p):
    if not p["cap"]: c="no size cap stated"
    else: c=p["cap"] if p["cap"].startswith("homes") else "homes "+p["cap"]
    return c+(f'; {p["note"]}' if p["note"] else '')
def card_price(i,t,lbl):
    p=pr(i,t)
    if p["amt"] is None:
        v=f'<span class="pv muted">{e(i[TXT[t]])}</span>'
    else:
        sub=capline(p) if t!="bundle" else (e(i["bundle"]) if False else capline(p))
        v=f'<span class="pv"><span class="amt">${p["amt"]}</span><span class="capl">{e(sub)}</span></span>'
    return f'<div class="prow"><span class="pl">{lbl}</span>{v}</div>'
PHONE_SVG='<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.57 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'
def nice_date(d): return datetime.date.fromisoformat(d).strftime("%b %-d, %Y")
def dom(u): return urllib.parse.urlparse(u).netloc.removeprefix("www.")
def card(i):
    tel="".join(ch for ch in i["phone"] if ch.isdigit() or ch=="+")
    lic="" if i["lic_status"]=="note" else f'<span class="badge b-{i["lic_status"]}">{LIC_LABEL[i["lic_status"]]}</span>'
    book=f'<a class="btn btn-book" href="{e(i["booking"])}" rel="nofollow noopener" target="_blank">Book online</a>' if i.get("booking") else ''
    bundle_row=card_price(i,"bundle","Bundle") if pr(i,"bundle")["amt"] is None else f'<div class="prow"><span class="pl">Bundle</span><span class="pv"><span class="amt">${pr(i,"bundle")["amt"]}</span><span class="capl">{e(i["bundle"])}</span></span></div>'
    return f'''<article class="card insp" id="{e(i["slug"])}" {flt(i)}><div class="insp-head"><h3><a href="{e(i["website"])}" rel="nofollow noopener" target="_blank">{e(i["name"])}</a></h3><div class="badges"><span class="tag tag-{i["base"]}">{BASE_LABEL[i["base"]]}</span>{lic}</div></div>
<div class="actions"><a class="btn btn-phone" href="tel:{e(tel)}">{PHONE_SVG}<span>{e(i["phone"])}</span></a>{book}</div>
<div class="prices">{card_price(i,"wind","Wind mitigation")}{card_price(i,"four","4-point")}{card_price(i,"roof","Roof cert")}{bundle_row}</div>
<details class="more"><summary>Details</summary><dl class="meta"><dt>License</dt><dd>{e(i["license"])}</dd><dt>Area</dt><dd>{e(i["service_area"])}</dd><dt>Based</dt><dd>{e(i["base_note"])}</dd></dl></details>
<p class="src"><a href="{e(i["source"])}" rel="nofollow noopener" target="_blank">{e(dom(i["source"]))} &#8599;</a> &middot; checked <time datetime="{e(i["checked"])}">{nice_date(i["checked"])}</time> &middot; <a href="{e(i["phone_src"])}" rel="nofollow noopener" target="_blank">phone source</a></p>
<p class="fix small">Is this your business? <a href="mailto:{CORRECTIONS}?subject={urllib.parse.quote("Fix my listing: "+i["name"])}">Fix your listing</a>.</p></article>'''

# ---------- Quote request ----------
FORM_ACTION="https://formsubmit.co/265503c53f1018daa54443a7cbfc6097"  # alias for listings@, from activation email
CONSENT=("When you send this, we share your request (name, contact details, city, ZIP and what you need) with up to 3 inspectors listed on this site who serve your area, so they can contact you with a quote. "
         "We don't sell your information. Inspectors set their own prices; we don't guarantee a reply or a price.")
def cta(pre,city=None):
    q=f'?city={city["slug"]}' if city else ''
    where=f' in {e(city["name"])}' if city else ''
    return (f'<aside class="cta" aria-label="Request quotes"><div><strong>Want quotes without calling around?</strong> '
            f'<span>Tell us what you need{where} and we\'ll pass it to up to 3 local inspectors.</span></div>'
            f'<a class="btn btn-book" href="{pre}request/index.html{q}">Request quotes</a></aside>')
# ---------- Home ----------
which='''<table class="which"><thead><tr><th>Your situation</th><th>Report usually asked for</th></tr></thead><tbody>
<tr><td>Home more than 20 years old, applying to Citizens</td><td>4-point</td></tr>
<tr><td>Shingle roof over 25 years, or tile/metal roof over 50 years (Citizens)</td><td>Roof certification (roof inspection form)</td></tr>
<tr><td>You want wind-premium discounts</td><td>Wind mitigation (OIR-B1-1802)</td></tr>
<tr><td>Buying an older home</td><td>Often a 4-point + wind mitigation bundle</td></tr></tbody></table>
<p class="muted small">Thresholds are Citizens' published rules (checked 2026-10-21). Other insurers set their own. Ask your agent. <a href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">Full comparison</a>.</p>'''
city_links="".join(f'<li><a href="cities/{c["slug"]}.html">{e(c["name"])}</a> ({sum(c["slug"] in i["cities"] for i in INS)} listed)</li>' for c in cities)
chips="".join(f'<a class="chip" href="cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in cities)
LIC_FIRMS=sum(any(i["lic_status"]=="verified" for i in r) for r in FIRMS.values())
layout("index.html","Wind Mitigation & 4-Point Inspectors | PBC Inspections",
"Compare Palm Beach County wind mitigation (OIR-B1-1802), 4-point and roof certification inspectors: published prices, size caps, phone, booking and Florida license checks.",
f'''<section class="hero"><h1>Compare Palm Beach County home insurance inspectors</h1>
<p class="lead">Wind mitigation, 4-point and roof certification: published prices, phone and booking, and a license check for each inspector.</p>
<nav class="chips" aria-label="Cities">{chips}</nav><p class="which-link"><a class="chip chip-alt" href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">Which report do I need? &rarr;</a></p>
<ul class="trust"><li>{len(FIRMS)} companies</li><li>{len(cities)} cities</li><li>Prices sourced and dated</li><li>Licenses checked on DBPR</li></ul></section>
{cta('')}
<section><h2>What inspections cost in Palm Beach County</h2>{stat_tiles(FIRMS,False)}<p class="small">Each company counted once; checked {nice_date(CHECKED)}. <a href="prices/index.html">Prices by city and how we counted &rarr;</a></p></section>
<section><h2>Which report do you need?</h2>{which}</section>
<section><h2>Browse by city</h2>{city_grid("cities/")}</section>
<section><h2>Guides</h2>{guide_list(G)}</section>
<!-- QUOTE-WIDGET-HOOK: future insurance-quote widget goes here. Hidden from public view; no widget, partner or affiliate link is connected yet. -->
<section id="list" class="card prose"><h2>List your inspection business</h2><p>Do you do wind mitigation, 4-point, or roof certification inspections in Palm Beach County? Self-serve listings are coming soon. Until then, email your business name, website, service area, pricing page and Florida license number to <a href="mailto:{CONTACT}">{CONTACT}</a>. Listings are free. Already listed and something's wrong? Email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p></section>''',[],[{"@context":"https://schema.org","@type":"WebSite","name":"PBC Inspections","alternateName":"pbcinspections.com","url":BASE_URL+"/"}])

# ---------- Prices ----------
city_rows=""
for c in cities:
    recs=[i for i in INS if c["slug"] in i["cities"]]; byf={}
    for i in recs: byf.setdefault(i["firm"],[]).append(i)
    cells="".join(f'<td data-label="{lbl}"><div class="rng"><span class="nw">{money(s["lo"])}&ndash;{money(s["hi"])}</span><span class="rsub">median {money(s["med"])} &middot; {s["n"]} of {s["total"]}</span></div></td>' if s["n"] else f'<td data-label="{lbl}">—</td>' for t,lbl in TYPES for s in [stats(byf,t)])
    city_rows+=f'<tr><td data-label="City"><a href="../cities/{c["slug"]}.html">{e(c["name"])}</a></td>{cells}</tr>'
layout("prices/index.html","Palm Beach County Wind Mitigation, 4-Point & Roof Cert Prices, 2026",
"Published 2026 prices for wind mitigation, 4-point, roof certification and bundles from Palm Beach County inspectors: ranges, medians and how we counted.",
f'''<h1>Palm Beach County wind mitigation, 4-point &amp; roof cert prices, 2026</h1>
<p>These figures come only from prices inspectors publish on their own websites, checked {ago(CHECKED)}. They are "starting at" or listed prices, not quotes.</p>
<h2>County-wide</h2>{stat_tiles(FIRMS)}
<h2>By city</h2><div class="tablewrap"><table class="compare stack"><thead><tr><th>City</th>{"".join(f"<th>{l}</th>" for _,l in TYPES)}</tr></thead><tbody>{city_rows}</tbody></table></div>
<h2>How we calculated this</h2><ul class="prose">
<li><strong>One company, one vote.</strong> {len(FIRMS)} companies appear across our city pages, many on several pages. County-wide medians and company counts count each company once; the county price range uses every published listing price, including per-city prices.</li>
<li><strong>Per-city prices.</strong> Sun Inspections publishes a different price for each city. For the county-wide figures we use the median of its city prices. On the by-city table we use the price that company publishes for that city.</li>
<li><strong>Which number.</strong> We use the stand-alone price the inspector lists, or its lowest "from" price. Where one company shows two figures for the same service on different pages (Accurate Building Inspections lists wind mitigation at $150 on its package page and $125 on its wind mitigation page), we use the figure on the page cited as the listing's source and note the other.</li>
<li><strong>Size caps differ.</strong> Some prices cover homes up to 2,000, 2,500 or 3,000 sq ft; others state no cap. Larger, older or more distant homes often cost more. Each listing shows the cap.</li>
<li><strong>Not counted:</strong> companies that publish no price for that service, and reports included "free" with a full home inspection (TruView, InspectionNow), because there is no stand-alone price.</li>
<li>"Companies publishing a price" = companies with a published price for that service / all listed companies.</li></ul>''',[("Prices","prices/index.html")])

# ---------- City pages ----------
WBDR=("Palm Beach County's Building Division says all of unincorporated Palm Beach County is within the wind-borne debris region, and its product-approval guidance notes that all of Palm Beach County is classified a wind-borne debris region. "
      "That is the zone where the building code requires protected openings, one of the features a wind mitigation report records. Ask your city's building department to confirm for your address.")
WBDR_SRC=[("Palm Beach County PZB, Wind Speeds","https://discover.pbc.gov/pzb/Maps/Wind-Speeds.aspx"),("Palm Beach County PBO-118 (product approval)","https://discover.pbc.gov/pzb/building/PDF/ProductApproval/PBO-118.pdf")]
def intro(c):
    h=c["housing"]
    age=2026-h["median_year"]; pct=h["pct_pre1980"]
    p1=(f'{c["name"]} has roughly {round(h["units"],-3):,} housing units. The median home was built in {h["median_year"]}, and {pct}% were built before 1980 ({h["release"]} estimates). ')
    if pct>=40:
        p1+=(f'With {pct}% of homes now over 45 years old, a 4-point inspection is a near-certain ask for owners applying to Citizens, which requires one for homes over 20 years old. '
             f'Citizens also asks for a roof inspection once a shingle roof passes 25 years or a tile or metal roof passes 50; roof age, not house age, decides that one.')
    elif pct<=20:
        p1+=(f'Only {pct}% of homes predate 1980, so the stock here is newer than most of the county. Even so, the median home is {age} years old, over Citizens\' 20-year 4-point threshold; '
             f'the inspection that can actually lower your premium is a wind mitigation report documenting the home\'s wind-resistant features.')
    else:
        p1+=(f'The median home is {age} years old, past the 20-year age at which Citizens requires a 4-point inspection, so most owners here should expect that ask; '
             f'a wind mitigation report is the inspection that can lower the premium.')
    srcs=[(f'U.S. Census Bureau {h["release"]}, tables B25034/B25035, via Census Reporter',h["url"])]+WBDR_SRC
    return (f'<div class="prose intro"><p>{e(p1)}</p><details class="disc"><summary>Wind-borne debris region &amp; sources</summary><p>{e(WBDR)}</p><p class="small muted">Sources: '+"; ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a>' for n,u in srcs)+' (checked 2026-10-21).</p></details></div>')
HOWCHECK=('<details class="disc"><summary>How we check</summary><p>Listed in no particular order. None are paid placements. Licenses were checked on the Florida DBPR license search (<a href="https://www.myfloridalicense.com/wl11.asp" rel="nofollow noopener" target="_blank">myfloridalicense.com</a>). '
  '"Not verified" means we could not match the business to a license record, not that it is unlicensed. Prices are copied from each inspector\'s own site on the date shown. Always confirm price and license before you book.</p></details>')
for c in cities:
    rows=[i for i in INS if c["slug"] in i["cities"]]
    il={"@context":"https://schema.org","@type":"ItemList","name":f'Wind mitigation and 4-point inspectors serving {c["name"]}, FL',"numberOfItems":len(rows),
        "itemListElement":[{"@type":"ListItem","position":n+1,"item":{"@type":"LocalBusiness","name":i["name"],"url":i["website"],"telephone":i["phone"]}} for n,i in enumerate(rows)]}
    layout(f'cities/{c["slug"]}.html',f'{c["name"]} Wind Mitigation & 4-Point Inspectors ({len(rows)} compared)',
    f'{len(rows)} inspectors serving {c["name"]}, FL: published wind mitigation, 4-point and roof certification prices, size caps, phone and Florida license checks.',
    f'''<h1>{e(c["name"])} wind mitigation, 4-point &amp; roof certification inspectors</h1>{intro(c)}
<section class="listing"><h2>{len(rows)} inspectors serving {e(c["name"])}</h2><div class="prose">{HOWCHECK}</div>{cta("../",c)}
{FILTERS}
{table(rows)}
<h2 class="details-h">Details</h2><div class="cards">{"".join(card(i) for i in rows)}</div>
<p class="fix">Listed here and something is wrong or out of date? <a href="mailto:{CORRECTIONS}?subject={urllib.parse.quote("Fix a listing on the "+c["name"]+" page")}">Fix your listing</a> at {CORRECTIONS}. Not sure which report you need? Read the <a href="../{G}4-point-vs-wind-mitigation-vs-roof-certification.html">guide</a>.</p></section>''',
    [("Cities","cities/index.html"),(c["name"],f'cities/{c["slug"]}.html')],[il])

# ---------- Cities index ----------
layout("cities/index.html","Palm Beach County Cities: Wind Mitigation & 4-Point Inspectors | PBC Inspections",
"Browse wind mitigation, 4-point and roof certification inspectors by Palm Beach County city.",
f'''<h1>Cities</h1><p class="lead">Pick a city to compare inspectors, published prices and license checks. Median home age from Census ACS 2024; median wind mitigation price counts each company once.</p>{city_grid()}
<p class="muted soon">Coming soon: Riviera Beach, Royal Palm Beach, Greenacres, Lantana, North Palm Beach, Tequesta.</p>''',[("Cities","cities/index.html")])

# ---------- Guides ----------
def faq(qs): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def guide(slug,title,desc,body,qs):
    t=dict(GUIDES)[slug]
    faqhtml="<h2>FAQ</h2>"+"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q,a in qs)
    layout(f"{G}{slug}.html",title,desc,f'<article class="prose"><h1>{e(t)}</h1><p class="notice"><strong>Not insurance advice.</strong> General information only. Your insurer or agent decides what it needs.</p>{body}{cta("../")}{faqhtml}</article>',
      [("Guides","guides/index.html"),(t,f"{G}{slug}.html")],[faq(qs)])
SRC_CIT='<li>Citizens Property Insurance, Inspections: <a href="https://www.citizensfla.com/web/public/inspections">citizensfla.com/web/public/inspections</a> (checked 2026-10-21)</li>'
SRC_OIR='<li>Florida OIR, Wind Mitigation Resources: <a href="https://floir.gov/consumers/wind-mitigation-resources/">floir.gov</a> (checked 2026-10-21)</li>'
SRC_DFS='<li>Florida DFS, Mitigation Notices, Inspections and Forms: <a href="https://www.myfloridacfo.com/division/consumers/storm/mitigation-notices-inspections-and-forms">myfloridacfo.com</a> (checked 2026-10-21)</li>'
onevisit=", ".join(f'<a href="../cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in cities)
guide("4-point-vs-wind-mitigation-vs-roof-certification","4-Point vs. Wind Mitigation vs. Roof Certification: Which One Your Florida Insurer Wants",
"What a 4-point inspection, a wind mitigation report (OIR-B1-1802), and a roof certification are, and when Florida insurers like Citizens ask for each.",
f'''<table><thead><tr><th></th><th>4-point</th><th>Wind mitigation</th><th>Roof certification</th></tr></thead><tbody>
<tr><td>What it covers</td><td>Roof, electrical, plumbing, HVAC: age, type, condition</td><td>Wind-resistant features: roof covering, deck attachment, roof-to-wall connection, roof shape, secondary water resistance, opening protection</td><td>Roof condition and remaining useful life</td></tr>
<tr><td>Why insurers want it</td><td>To decide if they'll insure an older home</td><td>Can qualify you for <em>discounts</em> on the wind part of your premium</td><td>To decide if they'll insure a home with an older roof</td></tr>
<tr><td>Typical trigger (Citizens)</td><td>Home more than 20 years old</td><td>Optional. You order it to get discounts</td><td>Shingle-type roof older than 25 years, or tile/metal roof older than 50 years</td></tr>
<tr><td>Official form</td><td>Insurer's 4-point form (Citizens publishes one)</td><td>OIR-B1-1802 (Rev. 04/26), required for inspections on or after April 1, 2026</td><td>Insurer's roof inspection form (Citizens publishes one)</td></tr></tbody></table>
<h2>4-point inspection</h2><p>Citizens Property Insurance says it "requires a four-point inspection for all property owner, dwelling and mobile home applications for properties more than 20 years old." A Florida-licensed inspector reports the age, type, and condition of the electrical, plumbing, HVAC, and roof. Citizens says serious hazards should be fixed before you apply. Private insurers set their own age cutoffs.</p>
<h2>Wind mitigation (OIR-B1-1802)</h2><p>The Uniform Mitigation Verification Inspection Form, OIR-B1-1802, is adopted under Rule 69O-170.0155, F.A.C. and section 627.0629, Florida Statutes. OIR revised it effective April 1, 2026 (Rev. 04/26); see <a href="oir-b1-1802-rev-04-26-changes.html">what changed</a>. According to OIR, a completed form "is valid for up to five (5) years provided no material changes are made to the structure or inaccuracies are found on the form."</p>
<h2>Roof certification</h2><p>Citizens says roofs older than 25 years (soft, such as shingle) or 50 years (hard, such as tile, slate, clay, concrete, or metal) need documentation showing at least five years of remaining useful life. A Florida-licensed inspector completes Citizens' Roof Inspection Form. Other insurers may use different ages and forms.</p>
<h2>Can I get them in one visit?</h2><p>Often, yes. Many Palm Beach County inspectors sell a 4-point + wind mitigation bundle. See listings for {onevisit}.</p>
<h2>Sources</h2><ul>{SRC_CIT}{SRC_OIR}<li>OIR-B1-1802 (Rev. 04/26) form PDF: <a href="https://www.floir.gov/docs-sf/property-casualty-libraries/product-review/all-forms/form-oir-1802-adopted-version-(no-watermark).pdf">floir.gov</a></li>{SRC_DFS}</ul>''',
[("When does Citizens require a 4-point inspection?","Citizens says it requires a four-point inspection for property owner, dwelling and mobile home applications for properties more than 20 years old. Other insurers set their own rules."),
 ("Is a wind mitigation inspection required?","No. It is optional, but documented wind-resistant features can qualify you for premium discounts."),
 ("Can one inspector do both a 4-point and a wind mitigation?","Yes. Many Palm Beach County inspectors offer both in one visit, often as a bundle.")])

guide("oir-b1-1802-rev-04-26-changes","OIR-B1-1802 Rev. 04/26: What Changed on Florida's Wind Mitigation Form",
"The revised Uniform Mitigation Verification Inspection Form (OIR-B1-1802 Rev. 04/26) took effect April 1, 2026. What's new, and whether an older form still counts.",
'''<p>Florida's Office of Insurance Regulation (OIR) updated the Uniform Mitigation Verification Inspection Form, OIR-B1-1802, effective <strong>April 1, 2026</strong>. OIR says the update follows a June 2024 Residential Wind-Loss Mitigation Study by Applied Research Associates, done under section 627.0629, Florida Statutes. Inspections on or after April 1, 2026 must use the new form, Rev. 04/26.</p>
<h2>What's new</h2><ul>
<li><strong>Region:</strong> a new section for the home's design wind-speed region (Citizens).</li>
<li><strong>Roof slope:</strong> homes with more than one slope must be indicated (Citizens).</li>
<li><strong>FORTIFIED Home certificates:</strong> FORTIFIED Roof, Silver and Gold certificates can validate some features and replace some photos (Citizens).</li>
<li><strong>Updated categories</strong> for building code, roof covering, roof deck attachment, roof-to-wall attachment, secondary water resistance and opening protection (Citizens).</li>
<li><strong>More documentation:</strong> the Florida DFS says the new form "is more comprehensive with additional categories and specifies the documentation that must be used to verify entries." Citizens' guide says attributes 2-9 need at least one photo unless other compliance documentation is provided.</li></ul>
<h2>Does it change my discount?</h2><p>Citizens told agents on March 19, 2026 that the changes and new features "will not result in any difference to the credits available and applied at this time." Other insurers may differ.</p>
<h2>Is my old form still good?</h2><p>Citizens says it will keep accepting the previous version, OIR-B1-1802 (Rev. 01/12), if it was completed within five years before April 1, 2026 and no changes have been made to the structure.</p>
<h2>Sources</h2><ul>'''+SRC_OIR+SRC_DFS+'''<li>Citizens, "Uniform Mitigation Verification Inspection Form Changes" (03.19.26): <a href="https://www.citizensfla.com/-/20260319-uniform-mitigation-verification-inspection-form-changes">citizensfla.com</a></li>
<li>Citizens Wind Loss Mitigation Guide (Rev. 04/26): <a href="https://training.citizensfla.com/lms/courses/core/CIS_Resources/Job_Aids/PolicyCenter/Wind_Loss_Mitigation_Guide_Rev0426.pdf">PDF</a></li></ul>''',
[("When did the new OIR-B1-1802 take effect?","April 1, 2026. Inspections on or after that date must use OIR-B1-1802 (Rev. 04/26)."),
 ("Will the new form change my Citizens discount?","Citizens said in March 2026 that the changes will not result in any difference to the credits available and applied at this time."),
 ("Is my 2012-version wind mitigation form still valid?","Citizens says it accepts a Rev. 01/12 form completed within five years before April 1, 2026 if the structure has not changed.")])

guide("how-long-inspection-reports-are-valid","How Long Is a Wind Mitigation, 4-Point or Roof Inspection Valid in Florida?",
"Wind mitigation reports last up to five years; Citizens wants 4-point reports dated within 12 months. What official sources say about each report's shelf life.",
'''<table><thead><tr><th>Report</th><th>How long it's accepted</th><th>Source</th></tr></thead><tbody>
<tr><td>Wind mitigation (OIR-B1-1802)</td><td>Up to 5 years, if no material changes to the structure and no inaccuracies on the form</td><td>Florida OIR; Florida DFS</td></tr>
<tr><td>4-point</td><td>Citizens: dated within 12 months before a new-business application (shorter for some lender-placed and prior-sinkhole cases)</td><td>Citizens</td></tr>
<tr><td>Roof inspection / roof certification</td><td>We did not find a separate published age limit from Citizens. Insurers generally want a recent report; ask your agent</td><td>Citizens (checked)</td></tr></tbody></table>
<h2>Wind mitigation: up to five years</h2><p>OIR: the form "is valid for up to five (5) years provided no material changes are made to the structure or inaccuracies are found on the form." The DFS says the same. If you replace the roof or add impact windows or shutters, a new inspection can record the new features.</p>
<h2>4-point: 12 months for Citizens</h2><p>Citizens' support center: "The four-point inspection report must be dated within the last 12 months prior to the new-business application submission date." Exceptions: lender-placed coverage in effect within 45 days of the effective date needs an inspection within 10 days before it; risks with a prior sinkhole claim need one within 90 days. Private insurers set their own rules.</p>
<h2>Roof certification</h2><p>Citizens requires roof documentation for shingle roofs over 25 years and tile/metal roofs over 50 years, showing at least five years of remaining useful life. Citizens also accepts a 4-point form in place of the Roof Inspection Form if it includes photos of each side of the roof and is signed by a verifiable Florida-licensed professional, subject to the same 12-month 4-point rule.</p>
<h2>Sources</h2><ul>'''+SRC_OIR+SRC_DFS+SRC_CIT+'''<li>Citizens, "What is the acceptable age of a four-point inspection report?" (updated 05/20/2026): <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/3251/">securesupport.citizensfla.com</a></li>
<li>Citizens, "Can an agent submit the Citizens Four-Point Inspection form to meet the roof condition requirements?": <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/2868/">securesupport.citizensfla.com</a></li></ul>''',
[("How long is a Florida wind mitigation report valid?","Up to five years, if there are no material changes to the structure and no inaccuracies on the form, according to the Florida Office of Insurance Regulation."),
 ("How old can a 4-point inspection be for Citizens?","Citizens says it must be dated within the last 12 months before the new-business application submission date, with shorter windows in some cases."),
 ("How long is a roof certification good for?","We did not find a separate published age limit from Citizens. Ask your agent what your insurer accepts.")])

guide("look-up-inspector-license-dbpr","How to Look Up a Florida Home Inspector's License on DBPR",
"Step-by-step: check a Florida home inspector's or contractor's license on the DBPR license search before you book a wind mitigation or 4-point inspection.",
'''<p>Florida home inspectors are licensed by the Department of Business and Professional Regulation (DBPR). Contractors, building code inspectors, engineers and architects can also sign some insurance forms. Citizens says a form may not be accepted if the professional's Florida license "is not active or cannot be verified."</p>
<h2>Steps</h2><ol>
<li>Go to the DBPR license search: <a href="https://www.myfloridalicense.com/wl11.asp">myfloridalicense.com/wl11.asp</a>.</li>
<li>Choose <strong>Search by License Number</strong> if the inspector gives you one (home inspector numbers start with <strong>HI</strong>, for example HI12345). Otherwise choose <strong>Search by Name</strong> and enter the inspector's last and first name. Company names often don't return results, because home inspector licenses are issued to people.</li>
<li>Check the <strong>License Type</strong> (e.g., Home Inspector, Certified General/Building/Residential Contractor) and the <strong>Status</strong>: you want "Current, Active".</li>
<li>Check the name matches the person coming to your home, and look at the expiration date.</li></ol>
<h2>What our listings show</h2><p>Each listing has a badge: <strong>Verified</strong> (we matched a named inspector or the license number shown on the site to an active DBPR record), <strong>See note</strong> (partial match; details in the card) or <strong>Not verified</strong> (we could not match a record; this does not mean the business is unlicensed).</p>
<h2>Sources</h2><ul><li>Florida DBPR license search: <a href="https://www.myfloridalicense.com/wl11.asp">myfloridalicense.com</a> (used 2026-10-21)</li>'''+SRC_CIT+'''</ul>''',
[("Where do I check a Florida home inspector's license?","On the Florida DBPR license search at myfloridalicense.com. Search by license number (home inspector licenses start with HI) or by the inspector's name."),
 ("What status should the license show?","Current, Active."),
 ("Who can sign a Florida wind mitigation form?","Florida allows licensed home inspectors, building code inspectors, general, building or residential contractors, professional engineers and architects, among others listed on the form.")])

guide("my-safe-florida-home-vs-private-wind-mitigation","My Safe Florida Home Free Inspection vs. a Private Wind Mitigation",
"The My Safe Florida Home free inspection includes the same OIR-B1-1802 wind mitigation form you'd otherwise pay for. What Florida law and the program say, and which route to choose.",
'''<p class="notice"><strong>Short answer:</strong> the free My Safe Florida Home (MSFH) initial inspection produces the same Uniform Mitigation Verification Inspection Form (OIR-B1-1802) you would otherwise pay a private inspector for, plus recommended upgrades, cost estimates and estimated premium-discount information. The program tells homeowners to share the report with their insurer.</p>
<h2>What the sources say</h2><ul>
<li><strong>Florida Statutes s. 215.5586(1)</strong> (2026 text) says program inspections are "to determine what insurance premium discounts may be available and what improvements ... are needed," and that the initial inspection must include, at a minimum, "a home inspection and report," "a range of cost estimates," and "information regarding estimated premium discounts, correlated to the current mitigation features and the recommended mitigation improvements." It requires program inspectors to be licensed building inspectors, contractors, engineers, architects, or home inspectors with at least 3 hours of hurricane mitigation training covering "compliance with the uniform mitigation verification form."</li>
<li><strong>Florida Statutes s. 627.711(2)</strong> (2026 text) says "an insurer shall accept as valid a uniform mitigation verification form signed by" listed authorized mitigation inspectors: a home inspector with that 3-hour training, a certified building code inspector, a general, building or residential contractor, a professional engineer, or a professional architect. It does not name the MSFH program; what makes a form acceptable is the signer's qualification, and s. 215.5586 requires program inspectors to hold those same license types.</li>
<li><strong>MSFH program materials:</strong> the program's Homeowners Guide lists "Form OIR-B1-1802 (Uniform Mitigation Verification Inspection Form)" as an attachment to every Initial Inspection Report and every Final Inspection Report. Its support center says to "share this report with your insurance company" to "make sure you get all the insurance discounts you currently qualify for." The program's home page says the report gives you "the opportunity to share your report with your insurance carrier."</li></ul>
<p>We found no source that contradicts these. Section 627.711 also lets insurers accept forms from others they consider qualified, and a private form signed by a qualified inspector is equally valid.</p>
<p><strong>Status checked 2026-10-21:</strong> the program's website says free wind mitigation inspections and grants of up to $10,000 are available. You create an account, complete a Prioritization Questionnaire, and are placed in an inspection group (1-5); you can apply when your group's window opens. Funding is set by the Legislature, so check <a href="https://mysafeflhome.com/">mysafeflhome.com</a>.</p>
<table><thead><tr><th></th><th>My Safe Florida Home inspection</th><th>Private wind mitigation</th></tr></thead><tbody>
<tr><td>Cost</td><td>Free to eligible homeowners</td><td>You pay (see <a href="../prices/index.html">local prices</a>)</td></tr>
<tr><td>OIR-B1-1802 form?</td><td>Yes, attached to the Initial Inspection Report</td><td>Yes</td></tr>
<tr><td>Also included</td><td>Recommended upgrades, cost estimates, estimated premium discounts</td><td>Varies by inspector</td></tr>
<tr><td>Who inspects</td><td>An inspector from a program wind certification entity</td><td>A qualified inspector you choose</td></tr>
<tr><td>Timing</td><td>Depends on your inspection group and program funding</td><td>Usually within days</td></tr>
<tr><td>Leads to grants?</td><td>Yes. Grants require the program's inspection</td><td>No</td></tr></tbody></table>
<h2>Which should you choose?</h2><ul>
<li><strong>If you qualify and can wait,</strong> the MSFH inspection gets you the same OIR-B1-1802 for free, plus upgrade advice and grant eligibility.</li>
<li><strong>If your insurer or a home closing needs the form soon,</strong> or your group's window isn't open, a private inspection is faster. Ask your agent about deadlines.</li>
<li>Either way, send the signed form to your agent or insurer and keep a copy. OIR says a completed form is valid for up to five years if the structure doesn't materially change.</li></ul>
<h2>Sources</h2><ul>
<li>Florida Statutes s. 215.5586 (2026), My Safe Florida Home Program: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0200-0299/0215/Sections/0215.5586.html">leg.state.fl.us</a> (checked 2026-10-21)</li>
<li>Florida Statutes s. 627.711 (2026), uniform mitigation verification inspection form: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0600-0699/0627/Sections/0627.711.html">leg.state.fl.us</a> (checked 2026-10-21)</li>
<li>MSFH Homeowners Guide, Hurricane Mitigation Inspections: <a href="https://msfh-program.helpjuice.com/en_US/MSFH-Homeowners-Guide-2024-2025/hurricane-mitigation-inspections">msfh-program.helpjuice.com</a></li>
<li>MSFH Support Center, "How do I get discounts on homeowner's insurance using my inspection reports?": <a href="https://support.mysafeflhome.com/en/support/solutions/articles/156000370516-how-do-i-get-discounts-on-homeowner-s-insurance-using-my-inspection-reports-">support.mysafeflhome.com</a></li>
<li>MSFH Support Center, Program Terms Glossary: <a href="https://support.mysafeflhome.com/en/support/solutions/articles/156000372633-program-terms-glossary">support.mysafeflhome.com</a></li>
<li>My Safe Florida Home: <a href="https://mysafeflhome.com/">mysafeflhome.com</a> (checked 2026-10-21)</li>'''+SRC_OIR+'''</ul>''',
[("Does the My Safe Florida Home inspection include the wind mitigation form?","Yes. The program's Homeowners Guide lists Form OIR-B1-1802 (Uniform Mitigation Verification Inspection Form) as an attachment to every Initial Inspection Report."),
 ("Must my insurer accept a form signed by a program inspector?","Florida Statutes s. 627.711 says an insurer shall accept as valid a uniform mitigation verification form signed by listed authorized inspectors, and s. 215.5586 requires program inspectors to hold those same license types and training."),
 ("Is My Safe Florida Home accepting applications?","When we checked on 2026-10-21, the program's site asked homeowners to create an account and complete a Prioritization Questionnaire to be placed in an inspection group. Funding depends on the Legislature; check mysafeflhome.com.")])
layout("guides/index.html","Guides: Florida Wind Mitigation, 4-Point & Roof Inspections | PBC Inspections","Plain-English guides to Florida insurance inspections.",
 f'<h1>Guides</h1>{guide_list()}',[("Guides","guides/index.html")])

opts="".join(f'<option value="{e(c["name"])}" data-slug="{c["slug"]}">{e(c["name"])}</option>' for c in cities)
layout("request/index.html","Request Inspection Quotes in Palm Beach County | PBC Inspections",
"Request quotes for a wind mitigation, 4-point or roof certification inspection from local Palm Beach County inspectors.",
f'''<div class="prose"><h1>Request quotes from local inspectors</h1>
<p class="lead">Tell us what you need. We'll pass your request to up to 3 inspectors listed on this site who serve your area.</p></div>
<form class="qform card" action="{FORM_ACTION}" method="POST">
<input type="hidden" name="_subject" value="Quote request: (city not chosen)" id="f-subject">
<input type="hidden" name="_next" value="{BASE_URL}/thanks.html">
<input type="hidden" name="_captcha" value="true">
<input type="hidden" name="_template" value="table">
<div class="hp" aria-hidden="true"><label for="f-honey">Leave this empty</label><input type="text" name="_honey" id="f-honey" tabindex="-1" autocomplete="off"></div>
<div class="fgrid">
<div class="field"><label for="f-name">Name</label><input id="f-name" name="name" type="text" autocomplete="name" required></div>
<div class="field"><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required></div>
<div class="field"><label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
<div class="field"><label for="f-city">City</label><select id="f-city" name="city" required><option value="">Choose a city</option>{opts}<option value="Other">Other Palm Beach County city</option></select></div>
<div class="field"><label for="f-zip">ZIP code</label><input id="f-zip" name="zip" type="text" inputmode="numeric" autocomplete="postal-code" pattern="[0-9]{{5}}" maxlength="5" required aria-describedby="f-zip-h"><span class="hint" id="f-zip-h">5 digits</span></div>
<div class="field"><label for="f-time">Timeframe</label><select id="f-time" name="timeframe" required><option value="">Choose one</option><option>As soon as possible</option><option>Within 2 weeks</option><option>Within a month</option><option>Just comparing prices</option></select></div>
</div>
<fieldset class="field"><legend>Inspections needed</legend>
<label class="chk"><input type="checkbox" name="inspections" value="Wind mitigation"> Wind mitigation</label>
<label class="chk"><input type="checkbox" name="inspections" value="4-point"> 4-point</label>
<label class="chk"><input type="checkbox" name="inspections" value="Roof certification"> Roof certification</label>
<label class="chk"><input type="checkbox" name="inspections" value="Not sure"> Not sure</label></fieldset>
<div class="field"><label for="f-notes">Notes <span class="opt">(optional)</span></label><textarea id="f-notes" name="notes" rows="4" placeholder="Year built, roof type, insurer deadline, anything else"></textarea></div>
<p class="consent small">{CONSENT} See our <a href="../about.html#privacy">privacy note</a>.</p>
<button class="btn btn-book" type="submit">Send request</button>
</form>
<p class="small muted prose">Prefer to call? Every inspector's phone number is on the <a href="../cities/index.html">city pages</a>.</p>''',[("Request quotes","request/index.html")])
layout("thanks.html","Request Received | PBC Inspections","Your inspection quote request was sent.",
'''<div class="prose"><h1>Thanks, your request was sent</h1><p class="lead">We'll pass it to up to 3 local inspectors who serve your area. They'll contact you directly by phone or email.</p>
<p>In the meantime you can compare <a href="prices/index.html">published prices</a> or read <a href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">which report you need</a>.</p></div>''',[])
# ---------- About ----------
layout("about.html",f"About, Listing Criteria & Disclosures | {SITE}","About this directory, listing and removal criteria, the no-advice disclaimer, and the referral-fee disclosure.",
f'''<article class="prose"><h1>About &amp; disclaimer</h1><p>{LONG} is an independent directory of Palm Beach County, Florida inspectors who do wind mitigation, 4-point, and roof certification reports. It is owned by Leonard Ponce.</p>
<h2>How listings work</h2><p>Each listing comes from the inspector's own public website. Each one shows a source link and the date we checked it. If an inspector doesn't publish a price, we show "call for price". Listings are not endorsements.</p>
<h2>Who we include</h2><ul><li>The business offers wind mitigation, 4-point, or roof certification inspections.</li><li>Its own website says it serves the city it is listed under (or all of Palm Beach County or Florida).</li><li>It has a working public website we can cite.</li><li>Listing is free. Nobody pays to be included or to be ranked; listings appear in no particular order.</li></ul>
<h2>Removal and corrections</h2><ul><li>We remove a listing if the business asks us to, if its website stops working, or if it stops offering these inspections.</li><li>We correct prices, phone numbers, service areas or license details when the business or a reader shows us a public source. Email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</li><li>"Local (PBC-based)" means the business states a Palm Beach County address on its site. "Address not stated" means we did not find one.</li></ul>
<h2>Licenses</h2><p>Where shown, license types and numbers come from the Florida DBPR license search on the date listed. "Not verified" means we could not confirm a license from official sources, not that the business is unlicensed. <a href="guides/look-up-inspector-license-dbpr.html">Check one yourself</a>.</p>
<h2>Affiliate &amp; referral disclosure</h2><p class="notice">Right now we have <strong>no paid relationships</strong> with any inspector, insurer, insurance agency, or lead-generation company. No listing is paid for, and nothing on this site is an affiliate link. In the future the site may earn referral fees, for example from an insurance-quote tool or from featured listings. If that happens we will update this page first, name the type of relationship, and clearly label any paid or affiliate link or placement where it appears. Payment will never change the prices or license information we show.</p>
<h2>Not insurance advice</h2><p>Nothing here is a recommendation to buy, change, or cancel an insurance policy. We do not sell insurance and we are not licensed as an insurance agent. Whether an inspection earns a discount, and how much, depends on your insurer's filed rates and on what the inspector verifies. Talk to a licensed insurance agent or your insurer before you make coverage decisions.</p>
<h2 id="privacy">Privacy</h2><p>If you use our <a href="request/index.html">quote request form</a>, what you enter (name, phone, email, city, ZIP, inspections needed, timeframe and notes) is sent to us by email through FormSubmit (formsubmit.co), a third-party form service. We use it only to pass your request to up to 3 inspectors listed on this site who serve your area. We don't sell your information. To have a request deleted, email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>. The site sets no cookies and runs no ad trackers. We count visits with GoatCounter, a privacy-friendly analytics service that uses no cookies and does not collect personal data; it records things like the page viewed, the referring site, browser and screen size, and approximate country, and we also count clicks on phone, booking and inspector-website links and quote form submissions (as totals, without any details you type). Its font is loaded from Google Fonts.</p>
<h2>Contact</h2><p>Listing requests: <a href="mailto:{CONTACT}">{CONTACT}</a>. Corrections: <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p></article>''',[("About","about.html")])

# ---------- static ----------
open(f"{OUT}/style.css","w").write(open(f"{ROOT}/src/style.css").read())
open(f"{OUT}/favicon.svg","w").write(_svg+"\n")
open(f"{OUT}/site.js","w").write(open(f"{ROOT}/src/site.js").read())
open(f"{OUT}/.nojekyll","w").write("")
open(f"{OUT}/CNAME","w").write("pbcinspections.com\n")
open(f"{OUT}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f'  <url><loc>{url(p)}</loc><lastmod>{CHECKED}</lastmod></url>\n' for p in pages if p!="thanks.html")+"</urlset>\n")
open(f"{OUT}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
keys=["slug","name","firm","cities","base","base_note","phone","phone_src","email","booking","wind_mit","four_point","roof_cert","bundle","lic_status","license","service_area","website","source","checked"]
with open(f"{ROOT}/data/inspectors.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader()
    for i in INS: w.writerow({**i,"cities":";".join(i["cities"])})
print("built",len(pages),"pages ->",OUT)
