#!/usr/bin/env python3
"""Zero-dependency static generator. Output -> docs/ (GitHub Pages: main /docs)."""
import json, csv, os, html, datetime, statistics, shutil, re, posixpath, urllib.parse
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,"docs")
SITE="PBC Inspections"; LONG="PBC Inspections"
BASE_URL=os.environ.get("BASE_URL","https://pbcinspections.com").rstrip("/")
CONTACT="listings@pbcinspections.com"      # Porkbun email forwarding
CORRECTIONS="corrections@pbcinspections.com"
# Quote form: off by default. QUOTE_FORM=1 re-enables a form that goes ONLY to PBC Inspections (no sharing with inspectors).
QUOTE_FORM=os.environ.get("QUOTE_FORM","0")=="1"
# Affiliate links: off. When AFFILIATE_LINKS=1, use aff_link() for any paid link; pages that contain one get AFF_NOTE at the top.
AFFILIATE_LINKS=os.environ.get("AFFILIATE_LINKS","0")=="1"
EFFECTIVE="2026-10-21"
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
pages=[]; NOINDEX=set()
G="guides/"
GUIDE_LINE={"find-permit-records-palm-beach-county":"Where to look up roof and window permits and product approvals for your wind mitigation.",
 "4-point-vs-wind-mitigation-vs-roof-certification":"What each report covers and when Citizens asks for it.",
 "oir-b1-1802-rev-04-26-changes":"What's new on the wind mitigation form effective April 1, 2026.",
 "how-long-inspection-reports-are-valid":"Wind mitigation reports last up to five years; Citizens wants 4-point reports within 12 months.",
 "look-up-inspector-license-dbpr":"Check an inspector's Florida license yourself on the DBPR search.",
 "my-safe-florida-home-vs-private-wind-mitigation":"The free program inspection includes the OIR-B1-1802 form; when a private one is faster.",
 "wind-mitigation-discount-how-much-you-save":"What OIR's discount table shows, and why the credit applies only to the hurricane-wind premium.",
 "florida-roof-age-insurance-rules":"The 15-year and 5-years-of-life rules in s. 627.7011, how roof age is counted, and Citizens' rules.",
 "4-point-inspection-common-problems":"100-amp minimum, aluminum wiring, polybutylene and the other items Citizens' form flags.",
 "oir-b1-1802-wind-mitigation-form-explained":"All nine questions on the Rev. 04/26 form, what they ask and what the inspector documents."}
def fmt_tel(t,orig):
    d=re.sub(r"\D","",t or "")
    if len(d)==11 and d[0]=="1": d=d[1:]
    return f"({d[:3]}) {d[3:6]}-{d[6:]}" if len(d)==10 else orig

def guide_list(pre="",more=False):
    gl=[(s,t) for h in HOME_GUIDES for s,t in GUIDES if s==h] if more else GUIDES
    items="".join(f'<a class="gitem" href="{pre}{s}.html"><span class="g-t">{e(t)}</span><span class="g-d">{e(GUIDE_LINE[s])}</span><span class="g-c">Checked {nice_date(CHECKED)}</span></a>' for s,t in gl)
    if more: items+=f'<a class="gitem g-more" href="{pre}index.html"><span class="g-t">All {len(GUIDES)} guides</span><span class="g-d">Discounts, roof age rules, the wind mitigation form, report validity and license checks, in one place.</span><span class="g-c">Browse guides <span aria-hidden="true">&rarr;</span></span></a>'
    return '<div class="glist">'+items+'</div>'
def city_stat(c):
    recs=[i for i in INS if c["slug"] in i["cities"]]; byf={}
    for i in recs: byf.setdefault(i["firm"],[]).append(i)
    return len(recs),stats(byf,"wind")
FEATURED=["boca-raton","west-palm-beach","delray-beach","boynton-beach","jupiter","wellington","palm-beach-gardens","lake-worth-beach"]
FEAT=[c for c in cities if c["slug"] in FEATURED]
REGIONS=[("North","North county"),("Central","Central county"),("South","South county"),("Glades","The Glades")]
ALLCHIP=lambda pre: f'<a class="chip chip-all" href="{pre}cities/index.html">All {len(cities)} city pages <span aria-hidden="true">&rarr;</span></a>'
def city_grid(pre="",subset=None):
    out=""
    for c in (subset if subset is not None else cities):
        n,w=city_stat(c); h=c["housing"]
        out+=(f'<a class="ccard" href="{pre}{c["slug"]}.html"><span class="c-n">{e(c["name"])}</span><span class="c-k">{n} inspectors</span>'
              f'<span class="c-s">Median wind mit. <b>{money(w["med"])}</b></span>'+(f'<span class="c-s">{e(c["towns"])}</span>' if "group" in c else f'<span class="c-s">Median home built <b>{h["median_year"]}</b></span>')+'</a>')
    return f'<div class="cgrid">{out}</div>'
GUIDES=[("4-point-vs-wind-mitigation-vs-roof-certification","4-point vs. wind mitigation vs. roof certification"),
 ("oir-b1-1802-rev-04-26-changes","What changed on the OIR-B1-1802 (Rev. 04/26) wind mitigation form"),
 ("how-long-inspection-reports-are-valid","How long a wind mitigation, 4-point or roof report stays valid"),
 ("look-up-inspector-license-dbpr","How to look up a Florida inspector's license on DBPR"),
 ("my-safe-florida-home-vs-private-wind-mitigation","My Safe Florida Home inspection vs. a private wind mitigation"),
 ("wind-mitigation-discount-how-much-you-save","How much a wind mitigation inspection saves"),
 ("florida-roof-age-insurance-rules","Florida roof age rules for home insurance"),
 ("4-point-inspection-common-problems","Common 4-point inspection problems and fixes"),
 ("oir-b1-1802-wind-mitigation-form-explained","The wind mitigation form, question by question"),
 ("find-permit-records-palm-beach-county","How to find your roof and window permits in Palm Beach County")]
HOME_GUIDES=["wind-mitigation-discount-how-much-you-save","4-point-vs-wind-mitigation-vs-roof-certification","florida-roof-age-insurance-rules","4-point-inspection-common-problems","oir-b1-1802-wind-mitigation-form-explained"]
RELATED={"find-permit-records-palm-beach-county":["oir-b1-1802-wind-mitigation-form-explained","florida-roof-age-insurance-rules","wind-mitigation-discount-how-much-you-save","how-long-inspection-reports-are-valid","4-point-vs-wind-mitigation-vs-roof-certification"],
 "4-point-vs-wind-mitigation-vs-roof-certification":["4-point-inspection-common-problems","florida-roof-age-insurance-rules","wind-mitigation-discount-how-much-you-save","how-long-inspection-reports-are-valid","look-up-inspector-license-dbpr"],
 "oir-b1-1802-rev-04-26-changes":["oir-b1-1802-wind-mitigation-form-explained","wind-mitigation-discount-how-much-you-save","how-long-inspection-reports-are-valid","my-safe-florida-home-vs-private-wind-mitigation","look-up-inspector-license-dbpr"],
 "how-long-inspection-reports-are-valid":["4-point-vs-wind-mitigation-vs-roof-certification","oir-b1-1802-wind-mitigation-form-explained","florida-roof-age-insurance-rules","find-permit-records-palm-beach-county","wind-mitigation-discount-how-much-you-save"],
 "look-up-inspector-license-dbpr":["4-point-vs-wind-mitigation-vs-roof-certification","oir-b1-1802-wind-mitigation-form-explained","4-point-inspection-common-problems","how-long-inspection-reports-are-valid","my-safe-florida-home-vs-private-wind-mitigation"],
 "my-safe-florida-home-vs-private-wind-mitigation":["wind-mitigation-discount-how-much-you-save","oir-b1-1802-wind-mitigation-form-explained","oir-b1-1802-rev-04-26-changes","how-long-inspection-reports-are-valid","look-up-inspector-license-dbpr"],
 "wind-mitigation-discount-how-much-you-save":["oir-b1-1802-wind-mitigation-form-explained","my-safe-florida-home-vs-private-wind-mitigation","oir-b1-1802-rev-04-26-changes","how-long-inspection-reports-are-valid","find-permit-records-palm-beach-county"],
 "florida-roof-age-insurance-rules":["4-point-vs-wind-mitigation-vs-roof-certification","4-point-inspection-common-problems","how-long-inspection-reports-are-valid","wind-mitigation-discount-how-much-you-save","find-permit-records-palm-beach-county"],
 "4-point-inspection-common-problems":["4-point-vs-wind-mitigation-vs-roof-certification","florida-roof-age-insurance-rules","how-long-inspection-reports-are-valid","look-up-inspector-license-dbpr","wind-mitigation-discount-how-much-you-save"],
 "oir-b1-1802-wind-mitigation-form-explained":["oir-b1-1802-rev-04-26-changes","wind-mitigation-discount-how-much-you-save","how-long-inspection-reports-are-valid","my-safe-florida-home-vs-private-wind-mitigation","find-permit-records-palm-beach-county"]}
BASE_LABEL={"pbc":"Local (PBC-based)","bd":"Serves area from Broward/Miami-Dade","other":"Based elsewhere in Florida","unknown":"Address not stated"}
LIC_LABEL={"verified":"Verified","not_verified":"Not found on DBPR","none_shown":"No license # on site","note":"See note"}
TYPES=[("wind","Wind mitigation"),("four","4-point"),("roof","Roof certification"),("bundle","4-point + wind bundle")]
TXT={"wind":"wind_mit","four":"four_point","roof":"roof_cert","bundle":"bundle"}

def url(path): return f"{BASE_URL}/{path}".replace("index.html","")
def ld(obj): return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False)+'</script>'
def ago(d): return f'<time class="ago" datetime="{e(d)}">{e(d)}</time>'

# Social image: GitHub MCP can only push text, so og-image.png must be uploaded another way.
# og:image tags are on by default now that docs/og-image.png is in the repo; set OG_IMAGE_PUBLISHED=0 to disable.
OG_IMAGE_PUBLISHED=os.environ.get("OG_IMAGE_PUBLISHED","1")=="1"
def og_image_tags():
    if not OG_IMAGE_PUBLISHED: return '<meta name="twitter:card" content="summary">'
    u=f"{BASE_URL}/og-image.png"
    return (f'<meta property="og:image" content="{u}"><meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            f'<meta property="og:image:alt" content="PBC Inspections: Palm Beach County inspection prices, 2026"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{u}">')
def layout(path,title,desc,body,crumbs,extra_ld=(),noindex=False):
    if AFFILIATE_LINKS and 'rel="sponsored' in body: body=AFF_NOTE.replace("{pre}","../"*path.count("/"))+body
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
<title>{e(title)}</title>{'<meta name="robots" content="noindex">' if noindex else ""}<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:site_name" content="PBC Inspections"><meta property="og:locale" content="en_US"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="{"article" if path.startswith("guides/") and not path.endswith("index.html") else "website"}"><meta property="og:url" content="{canon}">{og_image_tags()}<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap"><link rel="icon" href="{pre}favicon.svg" type="image/svg+xml"><link rel="icon" type="image/png" sizes="32x32" href="{FAV_PNG}"><link rel="apple-touch-icon" href="{TOUCH_PNG}"><meta name="theme-color" content="#0b3d4f"><link rel="stylesheet" href="{pre}style.css?v={ASSET_V}">{ld(bc)}{"".join(ld(x) for x in extra_ld)}</head><body>
<a class="skip" href="#main">Skip to content</a><header><div class="wrap"><a class="brand" href="{pre}index.html" aria-label="PBC Inspections, home"{' aria-current="page"' if path=="index.html" else ""}>{LOGO}<span>{LONG}</span></a><nav>{nav}</nav></div></header>
<main class="wrap" id="main" tabindex="-1">{crumb_html}{body}</main>
<footer><div class="wrap"><p>Informational directory only, not insurance advice. Listings and prices are copied from inspectors' own websites on the date shown and may have changed; always confirm with the inspector. <a href="{pre}about.html">About &amp; listing criteria</a>. Corrections: <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p><p>&copy; {datetime.date.today().year} {LONG} &middot; Owner: Leonard Ponce &middot; <a href="{pre}terms.html">Terms &amp; disclaimer</a> &middot; <a href="{pre}privacy.html">Privacy</a> &middot; <a href="{pre}about.html#accessibility">Accessibility</a></p></div></footer>
<script src="{pre}site.js?v={ASSET_V}" defer></script>
<script data-goatcounter="https://pbcinspections.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script></body></html>'''
    doc=canon_links(doc,path)
    doc=re.sub(r"(?<![\"=\d-])2026-10-21(?![\"\d])","Oct 21, 2026",doc)
    fp=os.path.join(OUT,path); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w").write(doc); pages.append(path)
    if noindex: NOINDEX.add(path)
def canon_links(doc,path):
    base=posixpath.dirname(path)
    def fix(m):
        attr,u=m.group(1),m.group(2)
        if re.match(r"^(?:[a-z]+:|#|/)",u): return m.group(0)
        frag=""
        if "#" in u: u,frag=u.split("#",1); frag="#"+frag
        if "?" in u: u,q=u.split("?",1); frag="?"+q+frag
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
      f'<div class="t-sub">median</div><div class="t-sub"><span class="nw">range {money(s["lo"])}&ndash;{money(s["hi"])}</span></div><div class="t-sub">{s["n"]} of {s["total"]} publish a price</div></div>' for k,_ in TYPES for s in [stats(byfirm,k)])
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
<div class="actions"><a class="btn btn-phone" href="tel:{e(tel)}">{PHONE_SVG}<span>{e(fmt_tel(tel,i["phone"]))}</span></a>{book}</div>
<div class="prices">{card_price(i,"wind","Wind mitigation")}{card_price(i,"four","4-point")}{card_price(i,"roof","Roof cert")}{bundle_row}</div>
<details class="more"><summary>Details</summary><dl class="meta"><dt>License</dt><dd>{e(i["license"])}</dd><dt>Area</dt><dd>{e(i["service_area"])}</dd><dt>Based</dt><dd>{e(i["base_note"])}</dd></dl></details>
<p class="src"><a href="{e(i["source"])}" rel="nofollow noopener" target="_blank">{e(dom(i["source"]))} &#8599;</a> &middot; checked <time datetime="{e(i["checked"])}">{nice_date(i["checked"])}</time> &middot; <a href="{e(i["phone_src"])}" rel="nofollow noopener" target="_blank">phone source</a></p>
<p class="fix small">Is this your business? <a href="mailto:{CORRECTIONS}?subject={urllib.parse.quote("Fix my listing: "+i["name"])}">Fix your listing</a>.</p></article>'''

# ---------- Affiliate (build-ready, off) ----------
AFF_NOTE=('<p class="notice aff-note"><strong>Disclosure:</strong> this page contains affiliate links, marked "(affiliate link)". '
          'If you click one and buy, PBC Inspections may earn a commission at no extra cost to you. It never changes the prices or license information we show. '
          '<a href="{pre}about.html#affiliate-referral-disclosure">How we make money</a>.</p>')
def aff_link(href,text):
    if not AFFILIATE_LINKS: raise RuntimeError("aff_link used while AFFILIATE_LINKS is off")
    return f'<a href="{e(href)}" rel="sponsored nofollow noopener" target="_blank">{e(text)}</a> <span class="small muted">(affiliate link)</span>'
# ---------- Quote request ----------
FORM_ACTION="https://formsubmit.co/265503c53f1018daa54443a7cbfc6097"  # alias for listings@, from activation email
CONSENT=("Your request goes only to PBC Inspections (Leonard Ponce) by email, through the FormSubmit form service. We don't pass it to inspectors, insurers or anyone else, and we don't sell your information. "
         "We don't sell insurance or work for any insurer, and inspectors don't pay us. We'll use your details only to reply to you.")
def cta(pre,city=None):
    q=f'?city={city["slug"]}' if city else ''
    where=f' in {e(city["name"])}' if city else ''
    if QUOTE_FORM:
        return (f'<aside class="cta" aria-label="Ask a question"><div><strong>Not sure who to call?</strong> '
                f'<span>Send us what you need{where}; it goes only to us, not to inspectors.</span></div>'
                f'<a class="btn btn-book" href="{pre}request/index.html{q}">Contact us</a></aside>')
    if city:
        return (f'<aside class="cta" aria-label="Contact inspectors"><div><strong>Ready to book?</strong> '
                f'<span>Call or book with an inspector directly. Every listing above has a phone number, website and published prices.</span></div>'
                f'<a class="btn btn-book" href="#inspectors">Back to the list</a></aside>')
    return (f'<aside class="cta" aria-label="Find an inspector"><div><strong>Ready to book?</strong> '
            f'<span>Compare inspectors in your city and contact them directly. Each listing has a phone number, website and published prices.</span></div>'
            f'<a class="btn btn-book" href="{pre}cities/index.html">Find an inspector</a></aside>')
# ---------- Home ----------
which='''<table class="which"><thead><tr><th>Your situation</th><th>Report usually asked for</th></tr></thead><tbody>
<tr><td>Home more than 20 years old, applying to Citizens</td><td>4-point</td></tr>
<tr><td>Shingle roof over 25 years, or tile/metal roof over 50 years (Citizens)</td><td>Roof certification (roof inspection form)</td></tr>
<tr><td>You want wind-premium discounts</td><td>Wind mitigation (OIR-B1-1802)</td></tr>
<tr><td>Buying an older home</td><td>Often a 4-point + wind mitigation bundle</td></tr></tbody></table>
<p class="muted small">Thresholds are Citizens' published rules (checked Oct 21, 2026). Other insurers set their own. Ask your agent. <a href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">Full comparison</a>.</p>'''
city_links="".join(f'<li><a href="cities/{c["slug"]}.html">{e(c["name"])}</a> ({sum(c["slug"] in i["cities"] for i in INS)} listed)</li>' for c in cities)
chips="".join(f'<a class="chip" href="cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in FEAT)+ALLCHIP("")
LIC_FIRMS=sum(any(i["lic_status"]=="verified" for i in r) for r in FIRMS.values())
layout("index.html","Wind Mitigation & 4-Point Inspectors | PBC Inspections",
"Compare Palm Beach County wind mitigation (OIR-B1-1802), 4-point and roof certification inspectors: published prices, size caps, phone, booking and Florida license checks.",
f'''<section class="hero"><h1>Compare Palm Beach County home insurance inspectors</h1>
<p class="lead">Wind mitigation, 4-point and roof certification: published prices, phone and booking, and a license check for each inspector.</p>
<p class="hero-actions"><a class="btn btn-book" href="cities/index.html">Find an inspector</a><a class="arrow-link" href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">Which report do I need? <span aria-hidden="true">&rarr;</span></a></p>
<nav class="chips" aria-label="Cities">{chips}</nav>
<ul class="trust"><li>{len(FIRMS)} companies</li><li>{len(cities)} city pages</li><li>Prices sourced and dated</li><li>Licenses checked on DBPR</li></ul></section>
<section><h2>What inspections cost in Palm Beach County</h2>{stat_tiles(FIRMS,False)}<p class="small">Each company counted once; checked {nice_date(CHECKED)}. <a href="prices/index.html">Prices by city and how we counted &rarr;</a></p></section>
<section><h2>Which report do you need?</h2>{which}</section>
<section><h2>Browse by city</h2>{city_grid("cities/",FEAT)}<p class="small"><a class="arrow-link" href="cities/index.html">All {len(cities)} city pages, by region <span aria-hidden="true">&rarr;</span></a></p></section>
<section><h2>Guides</h2>{guide_list(G,more=True)}</section>
<!-- QUOTE-WIDGET-HOOK: future insurance-quote widget goes here. Hidden from public view; no widget, partner or affiliate link is connected yet. -->
<section id="list" class="card prose"><h2>List your inspection business</h2><p>Do you do wind mitigation, 4-point, or roof certification inspections in Palm Beach County? To be listed, email your business name, website, service area, pricing page and Florida license number to <a href="mailto:{CONTACT}">{CONTACT}</a>. Listings are free. Already listed and something's wrong? Email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p></section>''',[],[{"@context":"https://schema.org","@type":"WebSite","name":"PBC Inspections","alternateName":"pbcinspections.com","url":BASE_URL+"/"}])

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
CITY_INTRO={
"riviera-beach":"Riviera Beach's housing is split between two eras. The median home dates to 1981, and nearly half of the roughly 18,000 units (48%) were built before 1980, yet 30% went up in 2000 or later. That split matters when you shop for coverage. An older house here will almost certainly need a 4-point inspection for Citizens, which asks for one on any home over 20 years old. A newer one may be able to show its wind-resistant features on a wind mitigation report and earn a discount.",
"royal-palm-beach":"Royal Palm Beach is mostly single-family houses (65% of about 14,700 homes), and 82% of occupied homes are lived in by their owners. It is also young by county standards: just 16% of homes predate 1980, 38% were built in 2000 or later, and the median home dates to 1990. Even so, that median house is 36 years old, well past the 20-year mark at which Citizens asks for a 4-point inspection. For most owners here, the report most likely to lower the premium is the wind mitigation form.",
"greenacres":"Only about a third of Greenacres' roughly 17,500 homes (31%) are detached single-family houses; most are attached homes or units in multi-unit buildings, and very few (5%) sit in buildings of 20 or more units. The median home was built in 1987, and 21% predate 1980. At 39 years old, that median home is past Citizens' 20-year 4-point threshold, so plan on a 4-point if you apply there. A wind mitigation report is the one that can bring the premium down.",
"lantana":"Lantana's housing is old. The median home was built in 1975, and 56% of its roughly 6,000 homes went up before 1980. Nearly half of occupied homes (47%) are rented, so landlords insuring an older rental may be asked for the same reports as owners. With homes this age, expect Citizens to want a 4-point inspection, since it requires one for homes over 20 years old. Check the roof's age as well: Citizens asks for a roof inspection once a shingle roof passes 25 years, or a tile or metal roof passes 50.",
"north-palm-beach":"North Palm Beach has some of the oldest housing in the north county. The median home was built in 1972, and almost three in four (73%) of its roughly 8,400 units predate 1980. Condos are a big part of the picture: 45% of homes are in buildings with 20 or more units. If you own one, ask your agent which reports a condo unit policy needs before you book anything. If you own a house, a 4-point inspection is close to a given for Citizens applicants, and a roof inspection follows once a shingle roof passes 25 years, or tile or metal passes 50.",
"tequesta":"Tequesta is small, with about 3,400 homes, and settled: 80% of occupied homes are owner-occupied. Most of the housing is from before 1980 (59%), and the median home was built in 1977. That age puts nearly every house past the 20-year line at which Citizens requires a 4-point inspection. Roof age is a separate test: Citizens asks for a roof inspection once a shingle roof is over 25 years old, or a tile or metal roof is over 50.",
"juno-beach":"Most of Juno Beach's roughly 3,700 homes are condos: 55% are in buildings with 20 or more units, and only 11% are detached houses. Condo owners should ask their agent which inspection reports a unit policy needs before paying for one. The housing is newer than in North Palm Beach or Tequesta. The median home was built in 1989, only 27% predate 1980, and 28% were built in 2000 or later. That median is still 37 years old, past the 20-year age at which Citizens asks for a 4-point inspection.",
"lake-park":"Lake Park is a compact town of about 3,400 homes, and more than half of occupied homes (53%) are rented. The housing is old: the median home dates to 1977, and 57% were built before 1980. Whether you own or rent out a home here, a Citizens application will almost certainly need a 4-point inspection, since Citizens requires one for homes over 20 years old. If the roof is an older shingle roof (over 25 years) or tile or metal (over 50), expect a roof inspection too.",
"palm-beach":"The Town of Palm Beach has about 10,500 homes. Most are condos and apartments (60% are in buildings with 20 or more units), and 84% of occupied homes are owner-occupied. It is also among the oldest housing stock in the county: the median home was built in 1970, and 70% predate 1980. Condo owners should check with their agent about what a unit policy needs. For houses, a 4-point inspection is a near-certain ask from Citizens, and older roofs bring a roof inspection as well.",
"palm-springs":"In the Village of Palm Springs, just under half of occupied homes (48%) are owner-occupied, and only 30% of its roughly 10,000 homes are detached single-family houses. The rest are attached homes, apartments and condos, with 28% of homes in buildings of 20 or more units. The median home was built in 1978, and 56% predate 1980. With homes that age, expect Citizens to ask for a 4-point inspection (it requires one for homes over 20 years old), plus a roof inspection if a shingle roof is over 25 or a tile or metal roof is over 50.",
"highland-beach":"Highland Beach is almost entirely large condo buildings. Of its roughly 4,600 homes, 83% are in buildings with 20 or more units, only 8% are detached houses, and 93% of occupied homes are owner-occupied. For most residents, the first question is what your condo unit policy needs, so ask your agent before booking an inspection. The median home was built in 1983, and 39% predate 1980. For the houses here, that age is past the 20-year mark at which Citizens asks for a 4-point inspection.",
}
GLADES_INTRO="Belle Glade, Pahokee and South Bay are the three cities along the southeastern shore of Lake Okeechobee, about 35 miles west of West Palm Beach, according to Palm Beach County's Glades Region Master Plan. Much of the housing is old, and mobile homes are common. Belle Glade has about 6,340 homes, median built 1979, 51% before 1980 and 13% mobile homes. Pahokee has about 1,780, median built 1970, 56% before 1980 and 24% mobile homes. South Bay has about 940, median built 1974, 68% before 1980 and 13% mobile homes. If you own a mobile home, ask your insurer which inspection forms it accepts before booking. For site-built houses, most are past the 20-year age at which Citizens requires a 4-point inspection."

def _sentences(name,h):
    """Housing facts for one place, ordered by what stands out there (ACS 5-year tables B25024/B25034/B25003)."""
    age=2026-h["median_year"]; v=sum(map(ord,name))%3; units=f'{round(h["units"],-2):,}'
    lead=[f'{name} has about {units} housing units, and the median one was built in {h["median_year"]}.',
          f'The median home in {name} was built in {h["median_year"]}, out of about {units} housing units.',
          f'Of {name}\'s roughly {units} homes, the median was built in {h["median_year"]}.'][v]
    rent=100-h["pct_owner"]; facts=[]
    if h["pct_20plus"]>=40: facts.append((h["pct_20plus"],f'{h["pct_20plus"]}% of homes are in buildings with 20 or more units, so many owners here live in condos; ask your agent which inspection reports a condo unit policy needs before you book one.'))
    if h["pct_mobile"]>=10: facts.append((h["pct_mobile"]+30,f'About {h["pct_mobile"]}% of homes are mobile homes; ask your insurer which inspection forms it accepts for a manufactured home before booking.'))
    if h["pct_2000plus"]>=30: facts.append((h["pct_2000plus"],f'{h["pct_2000plus"]}% of the housing was built in 2000 or later.'))
    if h["pct_detached"]>=60: facts.append((h["pct_detached"],f'Most homes ({h["pct_detached"]}%) are single-family detached houses, where the owner usually orders the wind mitigation report for the whole house.'))
    elif h["pct_detached"]<35 and h["pct_20plus"]<40: facts.append((50-h["pct_detached"],f'Only {h["pct_detached"]}% are single-family detached houses; most homes are attached or in multi-unit buildings.'))
    if rent>=45: facts.append((rent,f'{rent}% of occupied homes are rented; a landlord policy on an older rental can ask for the same reports.'))
    if h["pct_owner"]>=80 and h["pct_20plus"]<40: facts.append((h["pct_owner"]-30,f'{h["pct_owner"]}% of occupied homes are owner-occupied.'))
    facts.sort(key=lambda x:-x[0])
    if h["pct_pre1980"]>=50:
        agep=[f'{h["pct_pre1980"]}% of homes were built before 1980. With most of the stock more than 45 years old, expect Citizens to ask for a 4-point inspection (it requires one for homes over 20 years old), and check the roof\'s age too: Citizens asks for a roof inspection once a shingle roof passes 25 years or a tile or metal roof passes 50.',
              f'More than half the homes ({h["pct_pre1980"]}%) predate 1980, well past the 20-year age at which Citizens requires a 4-point inspection. Roof age matters separately: Citizens asks for a roof inspection once shingles pass 25 years, or tile or metal passes 50.',
              f'With {h["pct_pre1980"]}% of homes built before 1980, a 4-point inspection is a near-certain ask for Citizens applicants (it requires one for homes over 20 years old); a roof inspection follows if a shingle roof is over 25 years old, or tile or metal over 50.'][v]
    elif h["pct_pre1980"]<=20:
        agep=f'Only {h["pct_pre1980"]}% of homes predate 1980. Even so, the median home is {age} years old, past Citizens\' 20-year 4-point threshold; the inspection most likely to lower your premium is a wind mitigation report.'
    else:
        agep=[f'{h["pct_pre1980"]}% were built before 1980, and the median home is {age} years old, past the 20-year age at which Citizens requires a 4-point inspection; a wind mitigation report is the one that can lower the premium.',
              f'At {age} years, the median home is past the 20-year mark at which Citizens requires a 4-point inspection ({h["pct_pre1980"]}% were built before 1980). The report that can lower the premium is a wind mitigation inspection.',
              f'The median home is {age} years old and {h["pct_pre1980"]}% predate 1980, so most owners applying to Citizens should expect a 4-point request (it requires one for homes over 20); a wind mitigation report is the one that can lower the premium.'][v]
    return [lead]+[f for _,f in facts[:2]]+[agep]
def intro(c):
    h=c["housing"]
    if "group" in c:
        towns=c["group"]
        p1=GLADES_INTRO; _unused=(f'{c["towns"]} are the three cities along the southeastern shore of Lake Okeechobee, about 35 miles west of West Palm Beach, according to Palm Beach County\'s Glades Region Master Plan. '
            +" ".join(f'{t["name"]}: about {round(t["housing"]["units"],-1):,} homes, median built {t["housing"]["median_year"]}, {t["housing"]["pct_pre1980"]}% before 1980, {t["housing"]["pct_mobile"]}% mobile homes.' for t in towns)
            +' With most homes more than 45 years old, expect Citizens to ask for a 4-point inspection (it requires one for homes over 20 years old).')
        srcs=[(f'U.S. Census Bureau ACS 2024 5-year, tables B25034/B25035/B25024, via Census Reporter: {t["name"]}',t["housing"]["url"]) for t in towns]+[("Palm Beach County, Glades Region Master Plan","https://discover.pbcgov.org/HED/Pages/Glades-Region-Master-Plan.aspx")]+WBDR_SRC
        return (f'<div class="prose intro"><p>{e(p1)}</p><details class="disc"><summary>Wind-borne debris region &amp; sources</summary><p>{e(WBDR)}</p><p class="small muted">Sources: '+"; ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a>' for n,u in srcs)+' (checked Oct 21, 2026).</p></details></div>')
    if "pct_20plus" in h:
        p1=CITY_INTRO.get(c["slug"]) or " ".join(_sentences(c["name"],h))
        srcs=[('U.S. Census Bureau ACS 2024 5-year, tables B25034/B25035/B25024/B25003, via Census Reporter',h["url"])]+WBDR_SRC
        return (f'<div class="prose intro"><p>{e(p1)}</p><details class="disc"><summary>Wind-borne debris region &amp; sources</summary><p>{e(WBDR)}</p><p class="small muted">Sources: '+"; ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a>' for n,u in srcs)+' (checked Oct 21, 2026).</p></details></div>')
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
    return (f'<div class="prose intro"><p>{e(p1)}</p><details class="disc"><summary>Wind-borne debris region &amp; sources</summary><p>{e(WBDR)}</p><p class="small muted">Sources: '+"; ".join(f'<a href="{e(u)}" rel="noopener" target="_blank">{e(n)}</a>' for n,u in srcs)+' (checked Oct 21, 2026).</p></details></div>')
def also_note(c):
    if not c.get("also"): return ""
    t=c["also"]; lst=t[0] if len(t)==1 else ", ".join(t[:-1])+" and "+t[-1]
    return f'<p class="also small muted prose">Also the nearest page for {e(lst)}, which {"has no page of its own" if len(t)==1 else "have no pages of their own"}. Confirm the inspector serves your address.</p>'
GLADES_NOTE=('<p class="small">Only companies that name a Glades city on their own site, or say they work statewide, are listed. '
  'Several coastal companies say they cover all of Palm Beach County but list no Glades town, so they are left off; you can still ask them. '
  'Ask any inspector whether a travel fee applies out here.</p>')
HOWCHECK=('<details class="disc"><summary>How we check</summary><p>Listed in no particular order. None are paid placements. Licenses were checked on the Florida DBPR license search (<a href="https://www.myfloridalicense.com/wl11.asp" rel="nofollow noopener" target="_blank">myfloridalicense.com</a>). '
  '"Not found on DBPR" means our search on the date shown found no matching license; "No license # on site" means the business publishes no name or number we could search. Neither means the business is unlicensed (engineers and architects, for example, are licensed outside DBPR). Prices are copied from each inspector\'s own site on the date shown. Always confirm price and license before you book.</p></details>')
for c in cities:
    rows=[i for i in INS if c["slug"] in i["cities"]]
    il={"@context":"https://schema.org","@type":"ItemList","name":f'Wind mitigation and 4-point inspectors serving {c["name"]}, FL',"numberOfItems":len(rows),
        "itemListElement":[{"@type":"ListItem","position":n+1,"item":{"@type":"LocalBusiness","name":i["name"],"url":i["website"],"telephone":i["phone"]}} for n,i in enumerate(rows)]}
    layout(f'cities/{c["slug"]}.html',f'{c["name"]} Wind Mitigation & 4-Point Inspectors ({len(rows)} compared)',
    f'{len(rows)} inspectors serving {c["name"]}, FL: published wind mitigation, 4-point and roof certification prices, size caps, phone and Florida license checks.',
    f'''<h1>{e(c["name"])} wind mitigation, 4-point &amp; roof certification inspectors</h1><p class="qprompt">Contact inspectors directly: each listing below has a phone number, website and published prices. <a href="#inspectors">Jump to the list <span aria-hidden="true">&rarr;</span></a></p>{intro(c)}{also_note(c)}
<section class="listing" id="inspectors"><h2>{len(rows)} inspectors serving {e(c["name"])}</h2><div class="prose">{GLADES_NOTE if "group" in c else ""}{HOWCHECK}</div>
{FILTERS}
{table(rows)}
<h2 class="details-h">Details</h2><div class="cards">{"".join(card(i) for i in rows)}</div>{cta("../",c)}
<p class="fix">Listed here and something is wrong or out of date? <a href="mailto:{CORRECTIONS}?subject={urllib.parse.quote("Fix a listing on the "+c["name"]+" page")}">Fix your listing</a> at {CORRECTIONS}. Not sure which report you need? Read the <a href="../{G}4-point-vs-wind-mitigation-vs-roof-certification.html">guide</a>.</p></section>''',
    [("Cities","cities/index.html"),(c["name"],f'cities/{c["slug"]}.html')],[il])

# ---------- Cities index ----------
layout("cities/index.html","Palm Beach County Cities: Wind Mitigation & 4-Point Inspectors | PBC Inspections",
"Browse wind mitigation, 4-point and roof certification inspectors by Palm Beach County city.",
f'''<h1>Cities</h1><p class="lead">Pick a city to compare inspectors, published prices and license checks. Grouped by region; smaller towns are listed below with their nearest page. Median home age from Census ACS 2024; median wind mitigation price counts each company once.</p>{"".join(f'<section class="region" id="{r.lower()}"><h2>{lbl}</h2>{city_grid("",[c for c in cities if c["region"]==r])}</section>' for r,lbl in REGIONS)}
<section id="smaller-towns"><h2>Smaller towns</h2><p class="prose">These towns don't have their own page yet. Each links to the nearest city page. Not every inspector there serves every town, so confirm your address when you call.</p>
<ul class="towns">{"".join(f'<li>{e(t)} <span class="muted">&rarr;</span> <a href="{c["slug"]}.html">{e(c["name"])}</a></li>' for c in cities for t in c.get("also",[]))}</ul></section>''',[("Cities","cities/index.html")])

# ---------- Guides ----------
def faq(qs): return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def slugify(x): return re.sub(r"[^a-z0-9]+","-",re.sub(r"<[^>]+>","",html.unescape(x)).lower()).strip("-")
def add_ids(h): return re.sub(r"<h2>(.*?)</h2>",lambda m:f'<h2 id="{slugify(m.group(1))}">{m.group(1)}</h2>',h)
def cmp_tables(h):
    def fix(m):
        t=m.group(0); n=len(re.findall(r"<th[ >]",t.split("</thead>")[0]))
        t=t.replace("<table>",'<div class="tablewrap"><table class="cmp"><colgroup><col class="c-lbl">'+'<col>'*(n-1)+'</colgroup>',1)+"</div>"
        t=t.replace("<th></th>",'<td class="corner"></td>',1)
        return re.sub(r"<tr><td>(.*?)</td>",r'<tr><th scope="row">\1</th>',t)
    return re.sub(r"<table><thead><tr><th></th>.*?</table>",fix,h,flags=re.S)
def side(pre,toc=(),current=None):
    out=""
    if toc: out+='<nav class="side-box toc" aria-label="On this page"><p class="side-h">On this page</p><ul>'+"".join(f'<li><a href="#{i}">{t}</a></li>' for i,t in toc)+'</ul></nav>'
    out+=('<div class="side-box"><p class="side-h">Find an inspector</p><div class="chips chips-sm">'+"".join(f'<a class="chip" href="{pre}cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in FEAT)+ALLCHIP(pre)+'</div>'
          f'<p class="small"><a class="arrow-link" href="{pre}prices/index.html">Or compare prices <span aria-hidden="true">&rarr;</span></a></p></div>')
    rel=[(s,t) for r in RELATED.get(current,[]) for s,t in GUIDES if s==r] or [(s,t) for s,t in GUIDES if s!=current][:5]
    out+='<div class="side-box"><p class="side-h">Related guides</p><ul>'+"".join(f'<li><a href="{pre}{G}{s}.html">{e(t)}</a></li>' for s,t in rel)+'</ul></div>'
    return f'<aside class="side" aria-label="More">{out}</aside>'
def with_aside(article,aside): return f'<div class="with-aside">{article}{aside}</div>'
def guide(slug,title,desc,body,qs):
    t=dict(GUIDES)[slug]
    content,_,sources=body.partition("<h2>Sources</h2>")
    content=cmp_tables(add_ids(content))
    faqhtml='<h2 id="faq">FAQ</h2>'+"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q,a in qs)
    srchtml=('<h2 id="sources">Sources</h2>'+sources) if sources else ""
    toc=[(m.group(1),re.sub(r"<[^>]+>","",m.group(2))) for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>',content+faqhtml+srchtml)]
    head=(f'<h1>{e(t)}</h1><p class="dateline">Checked <time datetime="{CHECKED}">{nice_date(CHECKED)}</time></p>'
         f'<p class="notice"><strong>Not insurance advice.</strong> General information only. Your insurer or agent decides what it needs.</p>')
    aside=side("../",toc if len(toc)>=4 else (),slug)
    m=re.search(r'<div class="tablewrap"><table class="cmp">.*?</table></div>',content,flags=re.S)
    if m:
        # comparison table breaks out to full width; the sidebar sits beside the text that follows it
        body=(f'<article class="guide-wide"><div class="prose">{head}{content[:m.start()]}</div><div class="cmp-wide">{m.group(0)}</div>'
              +with_aside(f'<div class="prose">{content[m.end():]}{faqhtml}{cta("../")}{srchtml}</div>',aside)+'</article>')
    else:
        body=with_aside(f'<article class="prose">{head}{content}{faqhtml}{cta("../")}{srchtml}</article>',aside)
    layout(f"{G}{slug}.html",title,desc,body,
      [("Guides","guides/index.html"),(t,f"{G}{slug}.html")],[faq(qs),{"@context":"https://schema.org","@type":"Article","headline":title,"description":desc,"url":url(f"{G}{slug}.html"),"mainEntityOfPage":url(f"{G}{slug}.html"),"dateModified":CHECKED,"inLanguage":"en-US","author":{"@type":"Organization","name":"PBC Inspections","url":BASE_URL+"/"},"publisher":{"@type":"Organization","name":"PBC Inspections","url":BASE_URL+"/"}}])
SRC_CIT='<li>Citizens Property Insurance, Inspections: <a href="https://www.citizensfla.com/web/public/inspections">citizensfla.com/web/public/inspections</a> (checked Oct 21, 2026)</li>'
SRC_OIR='<li>Florida OIR, Wind Mitigation Resources: <a href="https://floir.gov/consumers/wind-mitigation-resources/">floir.gov</a> (checked Oct 21, 2026)</li>'
SRC_DFS='<li>Florida DFS, Mitigation Notices, Inspections and Forms: <a href="https://www.myfloridacfo.com/division/consumers/storm/mitigation-notices-inspections-and-forms">myfloridacfo.com</a> (checked Oct 21, 2026)</li>'
onevisit='<span class="chips chips-sm">'+"".join(f'<a class="chip" href="../cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in FEAT)+ALLCHIP("../")+'</span>'
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
<h2>Can I get them in one visit?</h2><p>Often, yes. Many Palm Beach County inspectors sell a 4-point + wind mitigation bundle. See listings by city:</p><p>{onevisit}</p>
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
<h2>What our listings show</h2><p>Each listing has a badge: <strong>Verified</strong> (we matched a named inspector or the license number shown on the site to an active DBPR record), <strong>See note</strong> (partial match; details in the card) <strong>Not found on DBPR</strong> (our search found no matching record) or <strong>No license # on site</strong> (nothing published to search). Neither means the business is unlicensed.</p>
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
<p><strong>Status checked Oct 21, 2026:</strong> the program's website says free wind mitigation inspections and grants of up to $10,000 are available. You create an account, complete a Prioritization Questionnaire, and are placed in an inspection group (1-5); you can apply when your group's window opens. Funding is set by the Legislature, so check <a href="https://mysafeflhome.com/">mysafeflhome.com</a>.</p>
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
<li>Florida Statutes s. 215.5586 (2026), My Safe Florida Home Program: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0200-0299/0215/Sections/0215.5586.html">leg.state.fl.us</a> (checked Oct 21, 2026)</li>
<li>Florida Statutes s. 627.711 (2026), uniform mitigation verification inspection form: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0600-0699/0627/Sections/0627.711.html">leg.state.fl.us</a> (checked Oct 21, 2026)</li>
<li>My Safe Florida Home, Homeowner's Guide (PDF, updated 7/21/25), "Initial Inspection Reports" and "Final Inspection Reports": <a href="https://mysafeflhome.com/wp-content/uploads/2025/07/MSFH-Homeowners-Guide-Clean-Copy-Updated-72125.pdf">mysafeflhome.com</a> (checked Oct 21, 2026)</li>
<li>MSFH Support Center, "Where do I find the results from my Initial Inspection Report?": <a href="https://support.mysafeflhome.com/en/support/solutions/articles/156000024192-where-do-i-find-the-results-from-my-initial-inspection-report-">support.mysafeflhome.com</a></li>
<li>MSFH Support Center, "How do I get discounts on homeowner's insurance using my inspection reports?": <a href="https://support.mysafeflhome.com/en/support/solutions/articles/156000370516-how-do-i-get-discounts-on-homeowner-s-insurance-using-my-inspection-reports-">support.mysafeflhome.com</a></li>
<li>MSFH Support Center, Program Terms Glossary: <a href="https://support.mysafeflhome.com/en/support/solutions/articles/156000372633-program-terms-glossary">support.mysafeflhome.com</a></li>
<li>My Safe Florida Home: <a href="https://mysafeflhome.com/">mysafeflhome.com</a> (checked Oct 21, 2026)</li>'''+SRC_OIR+'''</ul>''',
[("Does the My Safe Florida Home inspection include the wind mitigation form?","Yes. The program's Homeowners Guide lists Form OIR-B1-1802 (Uniform Mitigation Verification Inspection Form) as an attachment to every Initial Inspection Report."),
 ("Must my insurer accept a form signed by a program inspector?","Florida Statutes s. 627.711 says an insurer shall accept as valid a uniform mitigation verification form signed by listed authorized inspectors, and s. 215.5586 requires program inspectors to hold those same license types and training."),
 ("Is My Safe Florida Home accepting applications?","When we checked on 2026-10-21, the program's site asked homeowners to create an account and complete a Prioritization Questionnaire to be placed in an inspection group. Funding depends on the Legislature; check mysafeflhome.com.")])
SRC_7011='<li>Florida Statutes s. 627.7011 (2026), homeowners\' policies; offer of replacement cost coverage and law and ordinance coverage, subsection (5) roof age: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0600-0699/0627/Sections/0627.7011.html">leg.state.fl.us</a> (checked Oct 21, 2026)</li>'
SRC_0629='<li>Florida Statutes s. 627.0629 (2026), residential property insurance; rate filings: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0600-0699/0627/Sections/0627.0629.html">leg.state.fl.us</a> (checked Oct 21, 2026)</li>'
SRC_1802='<li>Florida OIR, Uniform Mitigation Verification Inspection Form OIR-B1-1802 (Rev. 04/26): <a href="https://www.floir.gov/docs-sf/property-casualty-libraries/product-review/all-forms/form-oir-1802-adopted-version-(no-watermark).pdf">floir.gov (PDF)</a> (checked Oct 21, 2026)</li>'
SRC_WLM='<li>Citizens Wind Loss Mitigation Guide (Rev. 04/26): <a href="https://training.citizensfla.com/lms/courses/core/CIS_Resources/Job_Aids/PolicyCenter/Wind_Loss_Mitigation_Guide_Rev0426.pdf">PDF</a> (checked Oct 21, 2026)</li>'
SRC_4PT='<li>Citizens sample 4-Point Inspection Form (Insp4pt 03 25): <a href="https://www.citizensfla.com/documents/20702/48575/4-Point+Inspection+Form.pdf/e8c41965-f225-37fc-b451-4d360ee30b77?t=1743432185731">citizensfla.com (PDF)</a> (checked Oct 21, 2026)</li>'

guide("wind-mitigation-discount-how-much-you-save","How Much Does a Wind Mitigation Inspection Save in Florida?",
"Florida law requires insurers to give wind mitigation discounts. What OIR's official discount table and notice show, which features count most, and why your number depends on your insurer.",
'''<p class="notice"><strong>Short answer:</strong> it depends on your home and your insurer, and there is no single statewide number. Florida law requires every residential property insurer to offer discounts for wind-resistant features. The credits come off the <em>hurricane-wind</em> part of your premium, not the whole bill. OIR's official credit table (form OIR-B1-1699) shows credits ranging from 0% for a home with no qualifying features to as high as 88%.</p>
<h2>What the law requires</h2><p>Florida Statutes s. 627.0629(1) says a residential property rate filing "must include actuarially reasonable discounts, credits, or other rate differentials, or appropriate reductions in deductibles" for homes with features "demonstrated to reduce the amount of loss in a windstorm." The listed features include roof strength, roof covering performance, roof-to-wall strength and opening protection. Since October 1, 2023, each insurer must also describe its hurricane mitigation discounts on its website.</p>
<p>To get the discounts, your insurer needs proof of the features, usually the Uniform Mitigation Verification Inspection Form (OIR-B1-1802) signed by a qualified inspector. OIR says the form is valid for up to five years if the structure doesn't change. See <a href="oir-b1-1802-wind-mitigation-form-explained.html">the form, question by question</a>.</p>
<h2>The discount applies to the hurricane-wind premium only</h2><p>OIR's standard notice to policyholders (form OIR-B1-1655) explains that your premium has two parts: one for hurricane-force wind and one for everything else, such as fire. It says the mitigation "discounts apply only to the hurricane-wind portion of your policy." The same notice says discounts "are not calculated cumulatively. The total discount is not the sum of the individual discounts." Your insurer fills in your own maximum.</p>
<p>The notice also says homes built under the 2001 Florida Building Code or later "are eligible for a minimum 68% discount on the hurricane-wind portion" of the premium. OIR lists this notice as revised February 2010, with updates pending, so ask your insurer for its current figures.</p>
<h2>What OIR's credit table shows</h2><p>OIR's form OIR-B1-1699, "Windstorm Mitigation Discounts; Single Family Residences," shows the range of wind premium credits for existing homes. OIR lists it as effective October 2006, with updates pending. A few rows for a home that does not meet the 2001 code for roof covering, with the weakest deck nailing (6d nails at 6"/12") and a 2% hurricane deductible in terrain B, show how features stack up:</p>
<table><thead><tr><th></th><th>Roof shape</th><th>Roof-to-wall</th><th>Opening protection</th><th>Credit</th></tr></thead><tbody>
<tr><td>Nothing qualifying</td><td>Other (e.g., gable)</td><td>Toe nails</td><td>None</td><td>0%</td></tr>
<tr><td>Hip roof only</td><td>Hip</td><td>Toe nails</td><td>None</td><td>47%</td></tr>
<tr><td>Clips only</td><td>Other</td><td>Clips</td><td>None</td><td>35%</td></tr>
<tr><td>Clips + hurricane protection</td><td>Other</td><td>Clips</td><td>Hurricane, windows or all</td><td>50%</td></tr>
<tr><td>Hip + clips + hurricane protection + SWR</td><td>Hip</td><td>Clips</td><td>Hurricane, windows or all</td><td>74%</td></tr></tbody></table>
<p class="small muted">Percentages are OIR-B1-1699 values rounded to whole numbers. SWR = secondary water resistance. The highest value in the table, 88%, is for a reinforced concrete roof deck. Insurers file their own discount factors with OIR, so your actual credit can differ.</p>
<h2>What this means in dollars</h2><p>A credit percentage only turns into dollars once you know your hurricane-wind premium. OIR's notice asks the insurer to show both your hurricane-wind premium and your total premium, so check your declarations page or ask your agent for the hurricane portion. Then compare the cost of an inspection (see <a href="../prices/index.html">local prices</a>) with what the credits could take off that portion.</p>
<h2>Which features matter</h2><ul>
<li><strong>Roof shape:</strong> a hip roof qualifies when other roof shapes make up no more than 10% of the total roof perimeter (OIR-B1-1802, question 7).</li>
<li><strong>Roof-to-wall attachment:</strong> clips, single wraps or double wraps rate better than toe nails (question 6).</li>
<li><strong>Opening protection:</strong> credit is based on the <em>weakest</em> protected opening. Citizens' guide says opening protection credit is granted "based on the weakest form" of protection (question 9).</li>
<li><strong>Roof deck attachment and secondary water resistance:</strong> stronger nailing and a sealed roof deck add credit (questions 5 and 8).</li></ul>
<h2>If you're with Citizens</h2><p>Citizens told agents on March 19, 2026, that the new Rev. 04/26 form "will not result in any difference to the credits available and applied at this time." Its Wind Loss Mitigation Guide says mitigation credits will not be granted if the form is completed by an unqualified or unlicensed inspector. See <a href="oir-b1-1802-rev-04-26-changes.html">what changed on the Rev. 04/26 form</a>.</p>
<h2>Sources</h2><ul>'''+SRC_0629+'''<li>Florida OIR, Notice of Premium Discounts for Hurricane Loss Mitigation, OIR-B1-1655 (Rev. 02/10): <a href="https://floir.gov/docs-sf/default-source/property-and-casualty/oir-b1-1655.pdf">floir.gov (PDF)</a> (checked Oct 21, 2026)</li>
<li>Florida OIR, Windstorm Mitigation Discounts; Single Family Residences, OIR-B1-1699: <a href="https://floir.gov/docs-sf/property-casualty-libraries/product-review/all-forms/oir-b1-1699.xls">floir.gov (XLS)</a> (checked Oct 21, 2026)</li>'''+SRC_OIR+SRC_1802+SRC_WLM+'''<li>Citizens, "Uniform Mitigation Verification Inspection Form Changes" (03.19.26): <a href="https://www.citizensfla.com/-/20260319-uniform-mitigation-verification-inspection-form-changes">citizensfla.com</a></li></ul>''',
[("How much does a wind mitigation inspection save in Florida?","It depends on your home's features and your insurer. Discounts apply only to the hurricane-wind portion of the premium. OIR's official credit table ranges from 0% to 88%, and insurers file their own factors."),
 ("Are wind mitigation discounts required in Florida?","Yes. Florida Statutes s. 627.0629 requires residential property rate filings to include actuarially reasonable discounts or credits for wind-loss-reducing features."),
 ("Do wind mitigation discounts add up?","No. OIR's notice to policyholders says discounts are not cumulative; the total discount is not the sum of the individual discounts.")])

guide("florida-roof-age-insurance-rules","Florida Roof Age Rules for Home Insurance: What s. 627.7011 Says",
"Florida law limits when an insurer can refuse a policy because of roof age: not under 15 years, and not if an inspection shows 5 years of life left. How roof age is counted, and Citizens' rules.",
'''<p>Florida law limits how an insurer can use your roof's age. The rule is in Florida Statutes s. 627.7011(5) and applies to homeowners' policies issued or renewed on or after July 1, 2022.</p>
<table><thead><tr><th></th><th>What the law says</th></tr></thead><tbody>
<tr><td>Roof under 15 years old</td><td>An insurer may not refuse to issue or renew a homeowner's policy "solely because of the age of the roof."</td></tr>
<tr><td>Roof 15 years or older</td><td>Before requiring a roof replacement, the insurer must let you get a roof inspection by an authorized inspector, at your expense.</td></tr>
<tr><td>Inspection shows 5+ years of life</td><td>The insurer may not refuse to issue or renew solely because of roof age.</td></tr>
<tr><td>Who can inspect</td><td>An authorized inspector approved by the insurer: a licensed home inspector, certified building code inspector, general, building, residential or roofing contractor, engineer, architect, or anyone else the insurer recognizes as qualified.</td></tr></tbody></table>
<h2>How roof age is counted</h2><p>Section 627.7011(5)(d) says roof age is calculated from "the last date on which 100 percent of the roof's surface area was built or replaced" under the building code in effect at the time. If the roof was replaced in stages that eventually covered 100% of the surface, age runs from the first partial replacement. Keep your roofing permit and final inspection records; they show the date. See <a href="find-permit-records-palm-beach-county.html">how to find your permits in Palm Beach County</a>.</p>
<h2>What the rule does not do</h2><ul>
<li>It covers only roof <em>age</em>. Subsection (6) says the section does not limit an insurer's ability to reject or nonrenew for not meeting underwriting criteria "or for other lawful reasons."</li>
<li>It does not apply to mobile home policies, or to policies that are not considered homeowners' policies (s. 627.7011(6)).</li>
</ul>
<h2>Citizens' roof rules</h2><p>Citizens asks for roof documentation once a shingle roof is more than 25 years old, or a tile or metal roof is more than 50, and wants it to show at least five years of remaining useful life. Citizens also accepts a 4-point form in place of its Roof Inspection Form if it includes photos of each roof slope and is signed by a verifiable Florida-licensed professional. See <a href="4-point-vs-wind-mitigation-vs-roof-certification.html">which report your insurer wants</a> and <a href="how-long-inspection-reports-are-valid.html">how long each report is valid</a>.</p>
<h2>What to do if your insurer cites roof age</h2><ol>
<li>Find your roof's age from the permit date, not the house's age.</li>
<li>If the roof is 15 or more years old, ask the insurer which authorized inspectors it accepts, and book a roof inspection. Our <a href="../cities/index.html">city pages</a> list roof certification prices where inspectors publish them.</li>
<li>If the report shows 5 or more years of remaining life, send it to the insurer and point to s. 627.7011(5)(c).</li></ol>
<h2>Sources</h2><ul>'''+SRC_7011+SRC_CIT+'''<li>Citizens, "Can an agent submit the Citizens Four-Point Inspection form to meet the roof condition requirements?": <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/2868/">securesupport.citizensfla.com</a></li></ul>''',
[("Can a Florida insurer deny coverage because of roof age?","Not solely because of age if the roof is less than 15 years old. For older roofs, the insurer must allow an inspection, and may not refuse solely because of age if the inspection shows at least 5 years of useful life left (Florida Statutes s. 627.7011(5))."),
 ("How is roof age calculated in Florida?","From the last date on which 100% of the roof's surface was built or replaced under the building code in effect at the time, per s. 627.7011(5)(d)."),
 ("Does the roof age law apply to mobile homes?","No. Section 627.7011(6) says the section does not apply to mobile home policies.")])

guide("4-point-inspection-common-problems","Common 4-Point Inspection Problems and How to Fix Them",
"What the Citizens 4-point form flags in the electrical, plumbing, HVAC and roof sections: 100-amp minimum, aluminum and knob-and-tube wiring, polybutylene pipes, and the fixes Citizens accepts.",
'''<p>A 4-point inspection records the condition of four systems: roof, electrical, plumbing and HVAC. Citizens' sample form says underwriting uses it "to determine insurability," and that agents "may not submit applications for properties with electrical, heating or plumbing systems not in good working order or with existing hazards/deficiencies." These are the items that most often hold up an application, based on Citizens' published form and FAQs. Private insurers set their own rules, so ask your agent.</p>
<table><thead><tr><th></th><th>What Citizens says</th><th>Accepted fix</th></tr></thead><tbody>
<tr><td>Electrical service under 100 amps</td><td>"All new-business applications must meet a minimum requirement of 100 amps."</td><td>Upgrade the service to at least 100 amps</td></tr>
<tr><td>Single-strand aluminum branch wiring</td><td>Not acceptable unless remediated; multi-strand aluminum is acceptable</td><td>Complete copper rewire, or all aluminum-to-copper connections repaired with the COPALUM crimp or AlumiConn connector method, documented and certified by a licensed electrician</td></tr>
<tr><td>Polybutylene pipes</td><td>New-business homes over 20 years old with polybutylene are not insurable by Citizens</td><td>Re-pipe; the form records whether the home is completely or partially re-piped and the pipe types</td></tr>
<tr><td>Electrical hazards</td><td>The form lists hazards such as double taps, scorching, exposed or loose wiring, over fusing and improper grounding</td><td>Repair before applying; the form's comments must describe updates and who did them</td></tr></tbody></table>
<h2>Electrical</h2><p>The electrical section asks for the main panel type (breaker or fuse), total amps, whether the amperage is sufficient, the panel's brand, model and age, and the wiring types. It flags cloth wiring, active knob and tube, and branch-circuit aluminum. Hazards listed on the form include blowing fuses, tripping breakers, empty sockets, loose wiring, improper grounding, corrosion, over fusing, double taps, exposed or unsafe wiring, improper breaker size and scorching. Photos are required of the open main panel with its interior door label and of the box with the panel cover off.</p>
<p>Citizens' public FAQs don't name panel brands. The form records the brand and model, so if you have an older panel, ask your agent whether your insurer accepts it before you book.</p>
<p>Aluminum wiring: Citizens says it accepts only a full copper rewire, COPALUM crimp repairs or AlumiConn connector repairs, and that "Leviton products cannot be accepted" for this remediation.</p>
<h2>Plumbing</h2><p>The plumbing section asks whether the water heater has a temperature and pressure relief valve, whether there are active or prior leaks, and the condition of fixtures and appliance connections (dishwasher, refrigerator, washing machine, water heater, toilets, sinks, showers and tubs, the main shut-off valve). It records pipe types, including polybutylene and galvanized, and whether the home is original, partially re-piped or completely re-piped. Fix leaks and water damage before the inspection.</p>
<h2>HVAC</h2><p>The HVAC section asks whether the heating and cooling systems are in good working order, the date of last service, and the system's age. It asks whether a wood-burning stove or central gas fireplace is present and was professionally installed, whether a space heater is the primary heat source, and whether the air handler, condensate line or drain pan shows blockage or leaks. Photos of the equipment's dated manufacturer's plate are required.</p>
<h2>Roof</h2><p>The roof section records covering material, age, remaining useful life, permit and update dates, and signs of damage or leaks: cracking, cupping or curling, granule loss, exposed asphalt or felt, missing or loose tabs or tiles, soft decking and hail damage. With photos of each slope, Citizens says this section can take the place of its Roof Inspection Form. See <a href="florida-roof-age-insurance-rules.html">Florida's roof age rules</a>.</p>
<h2>Before you book</h2><ul><li>Have repair invoices, permits and electrician certifications ready; the inspector must describe updates in the comments.</li>
<li>Citizens wants the 4-point dated within 12 months before the application (<a href="how-long-inspection-reports-are-valid.html">details</a>).</li>
<li>Compare <a href="../prices/index.html">4-point prices</a> or find an inspector on the <a href="../cities/index.html">city pages</a>.</li></ul>
<h2>Sources</h2><ul>'''+SRC_4PT+'''<li>Citizens, "What is the minimum amp requirement for a home's electrical systems?" (updated 08/25/2026): <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/2865/">securesupport.citizensfla.com</a></li>
<li>Citizens, "Is aluminum branch wiring acceptable?" (updated 04/16/2026): <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/1550/">securesupport.citizensfla.com</a></li>
<li>Citizens, "Will Citizens insure dwellings with polybutylene pipes?" (updated 01/26/2026): <a href="https://securesupport.citizensfla.com/app/answers/detail/a_id/1713/">securesupport.citizensfla.com</a></li>'''+SRC_CIT+'''</ul>''',
[("What is the minimum electrical service for Citizens?","Citizens says all new-business applications must meet a minimum requirement of 100 amps."),
 ("Will Citizens insure a home with polybutylene pipes?","Citizens says new-business homes over 20 years old with polybutylene piping are not insurable. Homes 20 years old or newer may be eligible if there are no leaks, unrepaired water damage, disrepair or hazards."),
 ("How do I fix aluminum wiring for a 4-point?","Citizens accepts a complete copper rewire, or all aluminum-to-copper connections repaired with the COPALUM crimp or AlumiConn connector method, documented and certified by a licensed electrician.")])

guide("oir-b1-1802-wind-mitigation-form-explained","The Florida Wind Mitigation Form (OIR-B1-1802), Question by Question",
"A plain-English walk through the nine questions on Florida's Uniform Mitigation Verification Inspection Form (Rev. 04/26): what each one asks, the answer choices, and what the inspector must document.",
'''<p>The Uniform Mitigation Verification Inspection Form, OIR-B1-1802, is the wind mitigation report. Since April 1, 2026, inspections must use Rev. 04/26 (see <a href="oir-b1-1802-rev-04-26-changes.html">what changed</a>). The form says at least one photo or document must accompany it to validate each attribute marked in questions 2 through 9. A FORTIFIED Home Roof, Silver or Gold certificate can validate questions 4 to 6, 8 and 9. The form is valid for up to five years if the structure has no material changes and the form has no inaccuracies.</p>
<table><thead><tr><th></th><th>What it asks</th><th>Answer choices (summary)</th></tr></thead><tbody>
<tr><td>1. Building code</td><td>Which code was in force when the home's permit was applied for</td><td>A: FBC 2001/2004; B: FBC 2007 or later; C: SFBC-94 (HVHZ only); D: unknown</td></tr>
<tr><td>2. Region</td><td>Design wind speed (ASCE 7-22)</td><td>HVHZ; Region 1 (140 mph or more); Region 2 (130-139); Region 3 (under 130)</td></tr>
<tr><td>3. Roof slope</td><td>Slope of at least two-thirds of the main roof</td><td>6:12 or steeper; less than 6:12</td></tr>
<tr><td>4. Roof covering</td><td>Each covering type, with permit date or product approval number and install year</td><td>Shingle, tile, synthetic tile, metal, built-up, membrane, other</td></tr>
<tr><td>5. Roof deck attachment</td><td>The weakest deck fastening</td><td>A-C by nail size and spacing; D: reinforced concrete; E: spray foam; F-H: other, unknown, no attic access</td></tr>
<tr><td>6. Roof-to-wall attachment</td><td>The weakest roof-to-wall connection</td><td>Toenails, clips, single wraps, double wraps, structural; or other, unknown, no attic access, not installed as intended</td></tr>
<tr><td>7. Roof geometry</td><td>Roof shape</td><td>Hip; flat (5+ unit buildings); other</td></tr>
<tr><td>8. Secondary water resistance</td><td>A sealed roof deck under the covering</td><td>Sealed roof deck; none; unknown</td></tr>
<tr><td>9. Opening protection</td><td>The weakest protection on windows, doors, skylights and garage doors</td><td>Levels A, B, C, N, X and sub-options by opening type</td></tr></tbody></table>
<h2>1. Building code</h2><p>The form asks which Florida Building Code was in force when the original permit was applied for. For homes built in 2002 or 2003, the inspector needs a permit application dated after 3/1/2002 to choose FBC 2001/2004; for 2007 or 2008, after 12/8/2006 to choose FBC 2007. Citizens' guide says FBC discounts are not applied when "unknown" is selected.</p>
<h2>2. Region and 3. Roof slope</h2><p>Both are new on Rev. 04/26. Region uses the ASCE 7-22 design wind speed. Slope records whether the main roof is at least 6:12. Citizens says slope does not affect credits but must be accurate.</p>
<h2>4. Roof covering</h2><p>For each covering, the inspector lists the permit application date or FBC/Miami-Dade product approval number and the year installed, or marks that no information was available. This is how a newer roof gets credit for meeting the code.</p>
<h2>5. Roof deck attachment</h2><p>This records how the plywood or OSB is nailed to the trusses, by the <em>weakest</em> area found. A is staples or 6d nails at 6" on the edges and 12" in the field; B is 8d nails at 12" in the field; C is 8d nails at 6" in the field (or dimensional lumber decking). D is a reinforced concrete deck. The inspector usually checks this from the attic, so "no attic access" is its own answer.</p>
<h2>6. Roof-to-wall attachment</h2><p>This is how the roof framing is tied to the walls, again the weakest connection found, ignoring hip and valley jacks within five feet of a corner. Toenails are nails driven at an angle. Clips are metal connectors that don't wrap over the truss. Single and double wraps are straps that wrap over it, with minimum nail counts for each. There is also an answer for connections "not installed as intended."</p>
<h2>7. Roof geometry</h2><p>A hip roof qualifies only if other roof shapes make up no more than 10% of the total roof perimeter; the inspector records both lengths. Porch and carport roofs attached only to the fascia or wall aren't counted.</p>
<h2>8. Secondary water resistance</h2><p>A sealed roof deck is a layer that helps keep water out if the shingles or tiles blow off: fully adhered membrane, taped deck seams, a qualifying double layer of underlayment, or spray foam. The form says standard underlayment or hot-mopped felt does not qualify.</p>
<h2>9. Opening protection</h2><p>The inspector rates every opening (windows, entry and garage doors, skylights, glass block) and the answer is the weakest one. Level A is verified impact protection tested to the 9-lb large missile standard; B is the 4-8-lb standard; C is verified plywood or OSB meeting the 2007 code; N covers products that look like A or B but can't be verified; X is no protection. The form says buildings with openings that need replacement "do not qualify for wind mitigation rate differentials, regardless of the presence/absence of other features." Keep product approval labels and permits; they are how protection gets verified.</p>
<h2>After the inspection</h2><p>Check that the inspector initialed each page and signed the form, then send it with its photos to your agent. Florida Statutes s. 627.711 lists who can sign. To see what the answers can be worth, read <a href="wind-mitigation-discount-how-much-you-save.html">how much a wind mitigation inspection saves</a>, and compare <a href="../prices/index.html">wind mitigation prices</a>.</p>
<h2>Sources</h2><ul>'''+SRC_1802+SRC_WLM+SRC_OIR+'''<li>Florida Statutes s. 627.711 (2026), uniform mitigation verification inspection form: <a href="https://www.leg.state.fl.us/statutes/index.cfm?App_mode=Display_Statute&amp;URL=0600-0699/0627/Sections/0627.711.html">leg.state.fl.us</a> (checked Oct 21, 2026)</li></ul>''',
[("How many questions are on the Florida wind mitigation form?","The OIR-B1-1802 (Rev. 04/26) has nine questions: building code, region, roof slope, roof covering, roof deck attachment, roof-to-wall attachment, roof geometry, secondary water resistance and opening protection."),
 ("Why does the wind mitigation form ask for the weakest connection?","Questions 5, 6 and 9 rate the home by the weakest roof deck attachment, roof-to-wall connection and opening protection found, so one weak area sets the answer."),
 ("Does a damaged window affect the wind mitigation form?","Yes. The form says buildings with openings that need replacement do not qualify for wind mitigation rate differentials, regardless of other features.")])

guide("find-permit-records-palm-beach-county","How to Find Your Roof and Window Permits in Palm Beach County",
"Your roof permit date and window product approval numbers drive wind mitigation credits and roof-age rules. Where to look them up in Palm Beach County: ePZB for unincorporated areas, your city's building department, and floridabuilding.org.",
'''<p class="notice"><strong>Short answer:</strong> permits are kept by whoever issued them. For unincorporated Palm Beach County that is the county's Planning, Zoning &amp; Building Department (PZB), searchable on its ePZB portal. Inside one of the county's 39 cities, towns and villages, it is that municipality's building department. Window and shutter approval numbers can be checked for free on the Florida Building Commission's site.</p>
<h2>Why permits matter for your inspection</h2><ul>
<li><strong>Roof covering (wind mitigation question 4):</strong> for each roof covering, the OIR-B1-1802 form asks for the permit application date or the FBC or Miami-Dade product approval number, and the year installed. This is how a newer roof gets credit for meeting the code.</li>
<li><strong>Building code (question 1):</strong> for homes built in 2002 or 2003, the inspector needs a permit application dated after 3/1/2002 to choose FBC 2001/2004; for 2007 or 2008, one dated after 12/8/2006 to choose FBC 2007. Citizens' guide says building code discounts are not applied when "unknown" is selected.</li>
<li><strong>Opening protection (question 9):</strong> the form's top answers require the protection on every opening to be verified, so product approval labels and permits for impact windows, doors and shutters matter.</li>
<li><strong>Roof age:</strong> Florida Statutes s. 627.7011(5)(d) counts roof age from the last date on which 100% of the roof's surface was built or replaced. Your roofing permit is one record that can show that date. See <a href="florida-roof-age-insurance-rules.html">Florida's roof age rules</a>.</li></ul>
<h2>Step 1: Find out who issued your permits</h2><p>If your address is inside a city, town or village, that municipality issued your permits. If it is in unincorporated Palm Beach County (your mailing city is not always your municipality), the county did. PZB's own help page points to the Property Appraiser's Office (PAPA) to check whether a property is in an incorporated or unincorporated area; search your address at <a href="https://pbcpao.gov/index.htm">pbcpao.gov</a>.</p>
<h2>Step 2: Unincorporated county, use ePZB</h2><ul>
<li>Open the county's <a href="https://www.pbcgov.org/ePZB.Admin.WebSPA/#/Container/Permits_Inspections">ePZB Permits &amp; Inspections search</a>. PZB's Building FAQ says you can search online by address to see whether a property has open or inactive permits, or call the Records Department at 561-233-5160.</li>
<li>With a permit number, the ePZB Building Portal FAQ says to enter it, click "View Inspections" and open the "Inspection History" tab to see each inspection and its result.</li>
<li>PZB also sells a certified open-permit search for unincorporated properties: $63, or $94 for rush, with results in 7 to 10 business days (3 for rush). It covers only open permits, and PZB says its searches do not include properties in municipalities (except areas annexed from the county). PZB also says the public can run an open-permit search on ePZB by registering for an account.</li>
<li>PZB's Building FAQ says an inactive permit from after about 1992 with no newer permit for the same work generally must be reactivated, and one from before 1992 needs a general inspection. The Building Division help desk is 561-233-5108.</li></ul>
<h2>Step 3: Inside a city, use its building department</h2><p>PAPA keeps a list of the <a href="https://pbcpao.gov/muni-permit-departments.htm">permit departments for all 39 municipalities</a>. Permit pages for the cities on our site (from PAPA's list; we updated three links where the city's address had changed):</p>
<table><thead><tr><th>City</th><th>City permit page</th></tr></thead><tbody><tr><td><a href="../cities/boca-raton.html">Boca Raton</a></td><td><a href="https://www.myboca.us/1415/Permits">myboca.us</a></td></tr><tr><td><a href="../cities/boynton-beach.html">Boynton Beach</a></td><td><a href="https://www.boynton-beach.org/202/Building-Division">boynton-beach.org</a></td></tr><tr><td><a href="../cities/delray-beach.html">Delray Beach</a></td><td><a href="https://www.delraybeachfl.gov/government/city-departments/development-services/building/building-permit-applications">delraybeachfl.gov</a></td></tr><tr><td><a href="../cities/greenacres.html">Greenacres</a></td><td><a href="https://www.greenacresfl.gov/378/Building-Permits">greenacresfl.gov</a></td></tr><tr><td><a href="../cities/jupiter.html">Jupiter</a></td><td><a href="https://www.jupiter.fl.us/2524/Online-Permitting">jupiter.fl.us</a></td></tr><tr><td><a href="../cities/lake-worth-beach.html">Lake Worth Beach</a></td><td><a href="https://lakeworthbeachfl.gov/community-sustainability/building">lakeworthbeachfl.gov</a></td></tr><tr><td><a href="../cities/palm-beach-gardens.html">Palm Beach Gardens</a></td><td><a href="https://www.pbgfl.gov/636/Applications-and-Forms">pbgfl.gov</a></td></tr><tr><td><a href="../cities/riviera-beach.html">Riviera Beach</a></td><td><a href="https://www.rivierabch.com/government/development/building">rivierabch.com</a></td></tr><tr><td><a href="../cities/royal-palm-beach.html">Royal Palm Beach</a></td><td><a href="https://www.royalpalmbeachfl.gov/620/Forms-Permits-and-Applications">royalpalmbeachfl.gov</a></td></tr><tr><td><a href="../cities/wellington.html">Wellington</a></td><td><a href="https://www.wellingtonfl.gov/252/Building-Permits">wellingtonfl.gov</a></td></tr><tr><td><a href="../cities/west-palm-beach.html">West Palm Beach</a></td><td><a href="https://www.wpb.org/Departments/Development-Services/Building-Division">wpb.org</a></td></tr><tr><td><a href="../cities/the-glades.html">Belle Glade</a></td><td><a href="https://www.belleglade.gov/building">belleglade.gov</a></td></tr></tbody></table>
<p class="small muted">Some cities offer an online permit search; others handle lookups by phone, email or public records request. Check the city's page. City names link to our inspector listings for that city.</p>
<h2>Step 4: Check window and shutter approval numbers</h2><p>Impact windows, doors and shutters sold in Florida carry a state product approval number (an "FL number") or a Miami-Dade approval. You can look up an FL number for free on the Florida Building Commission's <a href="https://www.floridabuilding.org/pr/pr_app_srch.aspx">product approval search</a>; the site says to enter the FL number and the code version (it notes the code version is the 2023 Florida Building Code, effective December 31, 2023; older products may be listed under earlier code versions). Florida Statutes s. 553.842 says a product may not be marketed as hurricane, windstorm or impact protection unless it is approved under that section or s. 553.8425. Keep any labels on the glass or frames until your inspector has photographed them.</p>
<h2>If you can't find a permit</h2><ul>
<li>Ask the permitting office. PZB takes <a href="https://discover.pbc.gov/pzb/pages/records-request.aspx">public records requests</a>, and each city has its own process.</li>
<li>Gather what you have: the roofer's or window installer's invoice, permit card, product labels and closing documents.</li>
<li>Tell your inspector before the visit. The form has answers for "no information provided for compliance" and "unknown," but those can earn less credit than a documented feature; Citizens' guide says building code discounts are not applied when "unknown" is selected for question 1.</li></ul>
<h2>Sources</h2><ul><li>Palm Beach County PZB, I Want To (permit search, public records, incorporated/unincorporated check): <a href="https://discover.pbc.gov/pzb/pages/i-want-to.aspx">discover.pbc.gov</a> (checked Oct 21, 2026)</li>
<li>Palm Beach County PZB, Building FAQ: <a href="https://discover.pbc.gov/pzb/FAQPages/Building.aspx">discover.pbc.gov</a> (checked Oct 21, 2026)</li>
<li>Palm Beach County ePZB Building Portal FAQs (updated 09-23-2026): <a href="https://www.pbcgov.org/iPZB.Building/Docs/EPZB%20Building%20Portal%20FAQs.pdf">pbcgov.org (PDF)</a> (checked Oct 21, 2026)</li>
<li>Palm Beach County PZB, Fine/Lien, Open Permit and Code Enforcement Open Violation Searches: <a href="https://discover.pbc.gov/pzb/administration/Pages/Search-Services-Administration.aspx">discover.pbc.gov</a> (checked Oct 21, 2026)</li>
<li>Palm Beach County Property Appraiser, Municipal Permit Departments: <a href="https://pbcpao.gov/muni-permit-departments.htm">pbcpao.gov</a> (checked Oct 21, 2026)</li>
<li>Florida Building Commission, Product Approval search: <a href="https://www.floridabuilding.org/pr/pr_app_srch.aspx">floridabuilding.org</a> (checked Oct 21, 2026)</li>
<li>Florida Statutes s. 553.842 (2026), product evaluation and approval: <a href="https://flsenate.gov/Laws/Statutes/2026/553.842">flsenate.gov</a> (checked Oct 21, 2026)</li>'''+SRC_1802+SRC_WLM+SRC_7011+'''</ul>''',
[("How do I find my roof permit in Palm Beach County?","If your home is in unincorporated Palm Beach County, search the county's ePZB Permits & Inspections portal. If it is inside a city, town or village, contact that municipality's building department; the Property Appraiser lists all 39."),
 ("Why does my wind mitigation inspector need my permit?","The OIR-B1-1802 form asks for the roof covering's permit application date or product approval number, and for some homes a permit date to prove which building code applied. Documented features can earn more credit than unknown ones."),
 ("How do I check if my impact windows are approved?","Look up the FL product approval number on the Florida Building Commission's free product approval search at floridabuilding.org, or check the Miami-Dade approval if that is what the label shows.")])

layout("guides/index.html","Guides: Florida Wind Mitigation, 4-Point & Roof Inspections | PBC Inspections","Plain-English guides to Florida insurance inspections.",
 f'<h1>Guides</h1>{guide_list()}',[("Guides","guides/index.html")])

opts="".join(f'<option value="{e(c["name"])}" data-slug="{c["slug"]}">{e(c["name"])}</option>' for c in cities)
if QUOTE_FORM:
    layout("request/index.html","Contact PBC Inspections | PBC Inspections",
    "Send PBC Inspections a question about wind mitigation, 4-point or roof certification inspections in Palm Beach County.",
    f'''<div class="prose"><h1>Contact us</h1>
<p class="lead">Tell us what you need. Your message comes only to us; we don't pass it to inspectors. To get a quote, contact inspectors directly from the <a href="../cities/index.html">city pages</a>.</p></div>
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
<p class="consent small">{CONSENT} See our <a href="../privacy.html">privacy policy</a>.</p>
<button class="btn btn-book" type="submit">Send request</button>
<p class="form-alt small muted">Want a quote now? Every inspector's phone number is on the <a href="../cities/index.html">city pages</a>.</p>
</form>''',[("Contact","request/index.html")])
    layout("thanks.html","Message Received | PBC Inspections","Your message was sent.",
    '''<div class="prose"><h1>Thanks, your message was sent</h1><p class="lead">It came only to us. We don't share it with inspectors.</p>
<p>To get a quote, contact an inspector directly from the <a href="cities/index.html">city pages</a>, or compare <a href="prices/index.html">published prices</a>.</p></div>''',[],noindex=True)
else:
    chips="".join(f'<a class="chip" href="../cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in cities)
    layout("request/index.html","Get Inspection Quotes in Palm Beach County | PBC Inspections",
    "How to get a wind mitigation, 4-point or roof certification quote: contact Palm Beach County inspectors directly.",
    f'''<div class="prose"><h1>Get quotes directly from inspectors</h1>
<p class="lead">We don't take quote requests or pass your details to anyone. Contact inspectors directly: every listing has a phone number, website and published prices, with the date we checked them.</p>
<h2>Pick your city</h2></div><div class="chips">{chips}</div>
<div class="prose"><h2>What to tell the inspector</h2><ul><li>Which report you need: wind mitigation, 4-point, roof certification, or a bundle. Ask your insurance agent if you're unsure (<a href="../guides/4-point-vs-wind-mitigation-vs-roof-certification.html">which report do I need?</a>).</li><li>Year built, approximate square footage and roof type.</li><li>Any insurer deadline.</li><li>Ask the price for your home's size, how soon they can come, when you'll get the report, and their Florida license number.</li></ul>
<p class="small muted">Prices on this site are copied from inspectors' own websites and may have changed. See our <a href="../terms.html">terms</a>.</p></div>''',[("Get quotes","request/index.html")])
    layout("thanks.html","Quote Requests Paused | PBC Inspections","Quote requests are paused.",
    '''<div class="prose"><h1>Quote requests are paused</h1><p class="lead">We're not taking quote requests right now. Contact inspectors directly from the <a href="cities/index.html">city pages</a>.</p>
<p>You can also compare <a href="prices/index.html">published prices</a> or read <a href="guides/4-point-vs-wind-mitigation-vs-roof-certification.html">which report you need</a>.</p></div>''',[],noindex=True)
# ---------- About ----------
AFF_ABOUT=("Some links on this site are affiliate links. They are labelled \"(affiliate link)\" where they appear, and pages that contain them say so at the top. "
           "If you use one, we may earn a commission at no extra cost to you. Listings are still free, nobody pays to be included or ranked, and payment never changes the prices or license information we show."
           if AFFILIATE_LINKS else
           "Right now we have <strong>no paid relationships</strong> with any inspector, insurer, insurance agency, or lead-generation company. No listing is paid for, and nothing on this site is an affiliate link. "
           "In the future the site may earn referral fees, for example from an insurance-quote tool or from featured listings. If that happens we will update this page first, name the type of relationship, and clearly label any paid or affiliate link or placement where it appears. Payment will never change the prices or license information we show.")
layout("about.html",f"About, Listing Criteria & Disclosures | {SITE}","About this directory, where listing information comes from, removal and correction policy, and the referral-fee disclosure.",
with_aside(add_ids(f'''<article class="prose about"><h1>About this directory</h1><p>{LONG} is an independent directory of Palm Beach County, Florida inspectors who do wind mitigation, 4-point, and roof certification reports. It is owned by Leonard Ponce.</p>
<h2>How listings work</h2><p>Each listing is built from facts the business publishes on its own public website (services, service area, prices, phone number, address) and from the public Florida DBPR license search. Each one shows a source link and the date we checked it. If an inspector doesn't publish a price, we show "call for price". Listings are factual information, not endorsements, reviews or recommendations.</p>
<h2>Who we include</h2><ul><li>The business offers wind mitigation, 4-point, or roof certification inspections.</li><li>Its own website says it serves the city it is listed under (or all of Palm Beach County or Florida).</li><li>It has a working public website we can cite.</li><li>Listing is free. Nobody pays to be included or to be ranked; listings appear in no particular order.</li></ul>
<h2>Removal and corrections</h2><ul><li>Any listed business can ask us to remove or correct its listing by emailing <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a> from an address or phone number connected to the business. We remove listings on request, usually within 7 days.</li><li>We also remove a listing if its website stops working or it stops offering these inspections.</li><li>We correct prices, phone numbers, service areas or license details when the business or a reader shows us a public source.</li></ul><h2>What the labels mean</h2><dl class="legend-dl">
<dt><span class="tag tag-pbc">Local (PBC-based)</span></dt><dd>The business states a Palm Beach County address on its site.</dd>
<dt><span class="tag tag-bd">Serves area from Broward/Miami-Dade</span></dt><dd>Its stated address is in Broward or Miami-Dade County.</dd>
<dt><span class="tag tag-other">Based elsewhere in Florida</span></dt><dd>Its stated address is elsewhere in Florida.</dd>
<dt><span class="tag tag-unknown">Address not stated</span></dt><dd>We did not find a street address on its site.</dd>
<dt><span class="badge b-verified">Verified</span></dt><dd>We matched a named inspector, or a license number shown on the business's site, to an active license on the Florida DBPR search. Form OIR-B1-1802 can be signed by licensed home inspectors and by certain contractors, building code inspectors, engineers and architects, so the license may be any of those types; the card says which.</dd>
<dt><span class="badge b-not_verified">Not found on DBPR</span></dt><dd>Our DBPR search on the date shown found no matching license. This does not mean the business is unlicensed: engineers and architects are licensed by other boards, and names can differ.</dd>
<dt><span class="badge b-none_shown">No license # on site</span></dt><dd>The business publishes no inspector name or license number we could search.</dd></dl>
<h2>Licenses</h2><p>Where shown, license types and numbers come from the Florida DBPR license search on the date listed. <a href="guides/look-up-inspector-license-dbpr.html">Check one yourself</a>.</p>
<h2 id="affiliate-referral-disclosure">Affiliate &amp; referral disclosure</h2><p class="notice">{AFF_ABOUT}</p>
<h2>Not insurance advice</h2><p>Nothing here is a recommendation to buy, change, or cancel an insurance policy. We do not sell insurance and we are not licensed as an insurance agent. Whether an inspection earns a discount, and how much, depends on your insurer's filed rates and on what the inspector verifies. Talk to a licensed insurance agent or your insurer before you make coverage decisions. Full <a href="terms.html">terms &amp; disclaimer</a>.</p>
<h2>Privacy</h2><p>We set no cookies, run no ad trackers, and don't collect personal information through the site. See our <a href="privacy.html">privacy policy</a>.</p>
<h2 id="accessibility">Accessibility</h2><p>We aim for this site to meet WCAG 2.1 AA: it works with a keyboard and screen readers, supports dark mode and zoom, and we test pages automatically for contrast and structure. If something is hard to use, email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a> and we'll fix it or get you the information another way.</p>
<h2>Contact</h2><p>Listing requests: <a href="mailto:{CONTACT}">{CONTACT}</a>. Corrections and removals: <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p></article>'''),side("",[("how-listings-work","How listings work"),("removal-and-corrections","Removal &amp; corrections"),("what-the-labels-mean","What the labels mean"),("affiliate-referral-disclosure","Disclosure"),("accessibility","Accessibility"),("contact","Contact")])),[("About","about.html")])

# ---------- Privacy ----------
FORM_PRIV=(f'<p>When the form is on, what you enter (name, phone, email, city, ZIP, inspections needed, timeframe and notes) is sent by email to PBC Inspections through <a href="https://formsubmit.co/privacy.html" rel="nofollow noopener" target="_blank">FormSubmit</a>, a third-party form service. It comes only to us. We use it to reply to you and do not share it with inspectors or anyone else.</p>'
           if QUOTE_FORM else
           '<p>Our quote request form is currently switched off, so the site does not collect names, phone numbers or other details through a form. If we turn a form back on, we will update this policy first and describe exactly where your information goes.</p>')
layout("privacy.html",f"Privacy Policy | {SITE}","What PBC Inspections collects (very little), the services the site uses, and how to contact us.",
add_ids(f'''<article class="prose about"><h1>Privacy policy</h1><p class="muted">Effective {EFFECTIVE}. Last updated {EFFECTIVE}.</p>
<p>This policy covers pbcinspections.com, run by Leonard Ponce as {LONG}. The short version: we set no cookies, run no ads or ad trackers, and do not sell or rent anyone's information.</p>
<h2>Analytics</h2><p>We count visits with <a href="https://www.goatcounter.com/help/privacy" rel="nofollow noopener" target="_blank">GoatCounter</a>, a privacy-friendly analytics service that uses no cookies and does not collect personal data. It records things like the page viewed, the referring site, browser, screen size and approximate country. We also count clicks on phone, booking and inspector-website links as totals, without anything you type.</p>
<h2>Forms</h2>{FORM_PRIV}
<h2>Email</h2><p>If you email listings@ or corrections@pbcinspections.com, the message is forwarded by our domain provider, Porkbun, to Leonard Ponce's inbox. We use what you send only to answer you, handle a listing, correction or removal, and keep a record of that request. Ask us and we'll delete your messages unless we need to keep a record of a removal request.</p>
<h2>Hosting and fonts</h2><p>The site is hosted on <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" rel="nofollow noopener" target="_blank">GitHub Pages</a>. Like most web hosts, GitHub may log technical data such as visitors' IP addresses for security and operations. Our font is loaded from <a href="https://policies.google.com/privacy" rel="nofollow noopener" target="_blank">Google Fonts</a>, which receives your IP address and browser details when the font downloads. We don't receive or control those logs.</p>
<h2>Links to other sites</h2><p>Listings link to inspectors' websites, DBPR and other sources. Their own privacy policies apply once you leave our site.</p>
<h2>Selling or sharing data</h2><p>We do not sell, rent or share personal information, and we don't use it for targeted advertising.</p>
<h2>Children</h2><p>This site is meant for adults dealing with home insurance. It is not directed to children under 13, and we do not knowingly collect information from them.</p>
<h2>Your choices</h2><p>To ask what we have about you, or to have it deleted, email <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>.</p>
<h2>Changes</h2><p>If we change how the site handles information, we'll update this page and the date at the top before the change takes effect.</p>
<h2>Contact</h2><p><a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a></p></article>'''),[("Privacy","privacy.html")])

# ---------- Terms ----------
layout("terms.html",f"Terms of Use & Disclaimer | {SITE}","Terms of use and disclaimer for PBC Inspections: informational directory only, not insurance or legal advice.",
add_ids(f'''<article class="prose about"><h1>Terms of use &amp; disclaimer</h1><p class="muted">Effective {EFFECTIVE}.</p>
<p>By using pbcinspections.com (the "site"), run by Leonard Ponce as {LONG}, you agree to these terms.</p>
<h2>Informational only</h2><p>The site is a directory and general information resource. It is not insurance, legal, engineering or financial advice. We are not an insurance agent, inspector or contractor. Whether you need an inspection and what discount it earns depends on your insurer; ask a licensed insurance agent or your insurer.</p>
<h2>No endorsement or warranty of listed businesses</h2><p>Listings are factual information collected from each business's own public website and the Florida DBPR license search. A listing is not an endorsement, recommendation, referral or guarantee of any business, its licensing, insurance, work quality or availability. You choose and hire inspectors yourself, and any agreement is between you and them. Check license status yourself before you hire.</p>
<h2>Prices and accuracy</h2><p>Prices are third-party figures published by each business on the date shown, and they can change at any time. We try to keep everything accurate, but we don't guarantee that any information is complete, current or error-free. Always confirm price, scope and license directly with the inspector.</p>
<h2>Corrections and removals</h2><p>Businesses can request a correction or removal, and anyone can report an error, by emailing <a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a>. See our <a href="about.html#removal-and-corrections">removal and correction policy</a>.</p>
<h2>Third-party links</h2><p>The site links to websites we don't control. We aren't responsible for their content, prices, privacy practices or services.</p>
<h2>Trademarks</h2><p>Business names, logos and trademarks belong to their owners. Their use here identifies the businesses listed and does not imply any affiliation with or endorsement by them. Citizens Property Insurance Corporation, the Florida Office of Insurance Regulation and DBPR are named only as sources; they don't endorse this site.</p>
<h2>Disclosure</h2><p>See our <a href="about.html#affiliate-referral-disclosure">affiliate and referral disclosure</a>.</p>
<h2>Limitation of liability</h2><p>The site is provided "as is" and "as available", without warranties of any kind, express or implied. To the fullest extent the law allows, {LONG} and Leonard Ponce are not liable for any loss or damage arising from your use of the site, your reliance on its information, or your dealings with any listed business.</p>
<h2>Governing law</h2><p>These terms are governed by the laws of the State of Florida. Any dispute will be handled in the state or federal courts located in Palm Beach County, Florida.</p>
<h2>Changes</h2><p>We may update these terms; the effective date above shows the latest version.</p>
<h2>Contact</h2><p><a href="mailto:{CORRECTIONS}">{CORRECTIONS}</a></p></article>'''),[("Terms","terms.html")])

# ---------- static ----------
open(f"{OUT}/style.css","w").write(open(f"{ROOT}/src/style.css").read())
open(f"{OUT}/favicon.svg","w").write(_svg+"\n")
open(f"{OUT}/site.js","w").write(open(f"{ROOT}/src/site.js").read())
open(f"{OUT}/.nojekyll","w").write("")
open(f"{OUT}/CNAME","w").write("pbcinspections.com\n")
open(f"{OUT}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f'  <url><loc>{url(p)}</loc><lastmod>{CHECKED}</lastmod></url>\n' for p in pages if p not in NOINDEX)+"</urlset>\n")
open(f"{OUT}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
keys=["slug","name","firm","cities","base","base_note","phone","phone_src","email","booking","wind_mit","four_point","roof_cert","bundle","lic_status","license","service_area","website","source","checked"]
with open(f"{ROOT}/data/inspectors.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore"); w.writeheader()
    for i in INS: w.writerow({**i,"cities":";".join(i["cities"])})
print("built",len(pages),"pages ->",OUT)
