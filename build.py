#!/usr/bin/env python3
"""Tiny static generator. No dependencies. Output -> docs/ (GitHub Pages: deploy from /docs)."""
import json, csv, os, html, datetime
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,"docs")
SITE="Palm Beach Inspection Finder"
BASE_URL=os.environ.get("BASE_URL","https://pbcinspections.com")
CONTACT="listings@pbcinspections.com"  # forwarded via Porkbun email forwarding (to be set up)
e=html.escape
data=json.load(open(f"{ROOT}/data/inspectors.json")); cities=json.load(open(f"{ROOT}/data/cities.json"))
pages=[]

def layout(path,title,desc,body):
    depth=path.count("/"); pre="../"*depth
    nav=f'<a href="{pre}index.html">Home</a><a href="{pre}guides/4-point-vs-wind-mitigation-vs-roof-certification.html">Guide</a>' + "".join(f'<a href="{pre}cities/{c["slug"]}.html">{e(c["name"])}</a>' for c in cities) + f'<a href="{pre}about.html">About</a>'
    canon=f"{BASE_URL}/{path}".replace("/index.html","/")
    doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{canon}"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{pre}style.css"></head><body>
<header><div class="wrap"><a class="brand" href="{pre}index.html">{SITE}</a><nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap"><p>Informational directory only, not insurance advice. Listings and prices are copied from inspectors' own websites on the date shown and may have changed; always confirm with the inspector. <a href="{pre}about.html">Disclaimer &amp; disclosures</a>.</p><p>&copy; {datetime.date.today().year} {SITE} &middot; Owner: Leonard Ponce</p></div></footer>
</body></html>'''
    fp=os.path.join(OUT,path); os.makedirs(os.path.dirname(fp),exist_ok=True); open(fp,"w").write(doc); pages.append(path)

guide="guides/4-point-vs-wind-mitigation-vs-roof-certification.html"
# Home
city_links="".join(f'<li><a href="cities/{c["slug"]}.html">{e(c["name"])} inspectors</a> ({sum(c["slug"] in i["cities"] for i in data["inspectors"])} listed)</li>' for c in cities)
layout("index.html",f"{SITE}: Wind Mitigation, 4-Point & Roof Certification Inspectors in Palm Beach County, FL",
"Compare Palm Beach County wind mitigation (OIR-B1-1802), 4-point and roof certification inspectors, with published prices and sources.",
f'''<section class="hero"><h1>Find a wind mitigation, 4-point, or roof certification inspector in Palm Beach County</h1>
<p>A directory of inspectors who do the three reports Florida insurers ask for most. Where an inspector publishes prices, we show them with a link to the source and the date we checked. If they don't publish prices, we say "call for price". We don't make numbers up.</p></section>
<section><h2>Browse by city</h2><ul class="list">{city_links}</ul><p class="muted">More Palm Beach County cities coming soon: Boynton Beach, Jupiter, Wellington.</p></section>
<section><h2>Guides</h2><ul class="list"><li><a href="{guide}">4-point vs. wind mitigation vs. roof certification: which one your insurer wants</a></li></ul></section>
<!-- QUOTE-WIDGET-HOOK: future insurance-quote widget goes here. Hidden from public view; no widget, partner or affiliate link is connected yet. -->
<section id="list" class="card"><h2>List your inspection business</h2><p>Do you do wind mitigation, 4-point, or roof certification inspections in Palm Beach County? Self-serve listings are coming soon. Until then, email your business name, website, service area, pricing page and Florida license number to <a href="mailto:{CONTACT}">{CONTACT}</a>. Listings are free.</p></section>''')

# City pages
def tbl(rows):
    out='<div class="table-scroll"><table class="compare"><thead><tr><th>Inspector</th><th>Wind mitigation</th><th>4-point</th><th>Roof cert</th><th>FL license</th></tr></thead><tbody>'
    for i in rows:
        out+=f'<tr><td>{e(i["name"])}</td><td>{e(i["wind_mit"])}</td><td>{e(i["four_point"])}</td><td>{e(i["roof_cert"])}</td><td>{e(i.get("license","Not verified"))}</td></tr>'
    out+='</tbody></table></div><div class="cards">'
    for i in rows:
        out+=f'''<article class="card insp"><h3><a href="{e(i["website"])}" rel="nofollow noopener" target="_blank">{e(i["name"])}</a></h3>
<p class="muted">{e(i["service_area"])}</p><dl><dt>Wind mitigation</dt><dd>{e(i["wind_mit"])}</dd><dt>4-point</dt><dd>{e(i["four_point"])}</dd><dt>Roof certification</dt><dd>{e(i["roof_cert"])}</dd><dt>Bundle</dt><dd>{e(i["bundle"])}</dd><dt>FL license</dt><dd>{e(i.get("license","Not verified"))}</dd></dl>
<p class="src">Source: <a href="{e(i["source"])}" rel="nofollow noopener" target="_blank">{e(i["source"])}</a>, checked {e(i["checked"])}</p></article>'''
    return out+"</div>"
for c in cities:
    rows=[i for i in data["inspectors"] if c["slug"] in i["cities"]]
    layout(f'cities/{c["slug"]}.html',f'{c["name"]} Wind Mitigation, 4-Point & Roof Certification Inspectors ({len(rows)} compared)',
    f'{len(rows)} inspectors serving {c["name"]}, FL, with published wind mitigation, 4-point and roof certification prices and sources.',
    f'''<h1>{e(c["name"])} wind mitigation, 4-point & roof certification inspectors</h1><p>{e(c["intro"])}</p>
<p class="muted">{len(rows)} inspectors, listed in no particular order. None are paid placements. Prices are "starting at" figures copied from each inspector's site on the date shown. Size, age, and travel can change the final price. Always confirm the price, and check the inspector's Florida license, before you book. License details come from the Florida DBPR license search (<a href="https://www.myfloridalicense.com/wl11.asp" rel="nofollow noopener" target="_blank">myfloridalicense.com</a>), checked 2026-10-21; "not verified" means we could not match the business to a license, not that it is unlicensed.</p>
{tbl(rows)}<p>Not sure which report you need? Read the <a href="../{guide}">guide</a>.</p>''')

# Guide
layout(guide,"4-Point vs. Wind Mitigation vs. Roof Certification: Which One Your Florida Insurer Wants",
"What a 4-point inspection, a wind mitigation report (OIR-B1-1802), and a roof certification are, and when Florida insurers like Citizens ask for each.",
'''<article class="prose"><h1>4-point vs. wind mitigation vs. roof certification: which one your insurer wants</h1>
<p class="notice"><strong>Not insurance advice.</strong> This page is general information. Your insurer or agent decides which inspections it needs. Ask them first.</p>
<table><thead><tr><th></th><th>4-point</th><th>Wind mitigation</th><th>Roof certification</th></tr></thead><tbody>
<tr><td>What it covers</td><td>Roof, electrical, plumbing, HVAC: age, type, condition</td><td>Wind-resistant features: roof covering, deck attachment, roof-to-wall connection, roof shape, secondary water resistance, opening protection</td><td>Roof condition and remaining useful life</td></tr>
<tr><td>Why insurers want it</td><td>To decide if they'll insure an older home</td><td>Can qualify you for <em>discounts</em> on the wind part of your premium</td><td>To decide if they'll insure a home with an older roof</td></tr>
<tr><td>Typical trigger (Citizens)</td><td>Home more than 20 years old</td><td>Optional. You order it to get discounts</td><td>Shingle-type roof older than 25 years, or tile/metal roof older than 50 years</td></tr>
<tr><td>Official form</td><td>Insurer's 4-point form (Citizens publishes one)</td><td>OIR-B1-1802 (Rev. 04/26), required for inspections on or after April 1, 2026</td><td>Insurer's roof inspection form (Citizens publishes one)</td></tr></tbody></table>
<h2>4-point inspection</h2><p>Citizens Property Insurance says it "requires a four-point inspection for all property owner, dwelling and mobile home applications for properties more than 20 years old." A Florida-licensed inspector reports the age, type, and condition of the electrical, plumbing, HVAC, and roof. Citizens says serious hazards should be fixed before you apply. Private insurers set their own age cutoffs.</p>
<h2>Wind mitigation (OIR-B1-1802)</h2><p>The Uniform Mitigation Verification Inspection Form, OIR-B1-1802, is adopted under Rule 69O-170.0155, F.A.C. and section 627.0629, Florida Statutes. Florida OIR revised it effective April 1, 2026 (Rev. 04/26). According to OIR, a completed form "is valid for up to five (5) years provided no material changes are made to the structure or inaccuracies are found on the form." Citizens says wind mitigation inspections document features that may qualify a home for premium discounts.</p>
<h2>Roof certification</h2><p>Citizens says roofs older than 25 years (soft, such as shingle) or 50 years (hard, such as tile, slate, clay, concrete, or metal) need documentation showing at least five years of remaining useful life. A Florida-licensed inspector completes Citizens' Roof Inspection Form. Other insurers may use different ages and forms.</p>
<h2>Can I get them in one visit?</h2><p>Often, yes. Many Palm Beach County inspectors sell a 4-point + wind mitigation bundle. See the <a href="../cities/boca-raton.html">Boca Raton listings</a>.</p>
<h2>Sources</h2><ul><li>Citizens Property Insurance, Inspections: <a href="https://www.citizensfla.com/web/public/inspections">citizensfla.com/web/public/inspections</a> (checked 2026-10-21)</li>
<li>Florida OIR, Wind Mitigation Resources: <a href="https://floir.gov/consumers/wind-mitigation-resources/">floir.gov/consumers/wind-mitigation-resources</a> (checked 2026-10-21)</li>
<li>OIR-B1-1802 (Rev. 04/26) form PDF: <a href="https://www.floir.gov/docs-sf/property-casualty-libraries/product-review/all-forms/form-oir-1802-adopted-version-(no-watermark).pdf">floir.gov</a></li>
<li>Florida DFS, Mitigation Notices, Inspections and Forms: <a href="https://www.myfloridacfo.com/division/consumers/storm/mitigation-notices-inspections-and-forms">myfloridacfo.com</a></li></ul></article>''')

# About
layout("about.html",f"About & Disclaimer | {SITE}","About this directory, the no-advice disclaimer, and the affiliate disclosure.",
f'''<article class="prose"><h1>About &amp; disclaimer</h1><p>{SITE} is an independent directory of Palm Beach County, Florida inspectors who do wind mitigation, 4-point, and roof certification reports. It is owned by Leonard Ponce.</p>
<h2>How listings work</h2><p>Each listing comes from the inspector's own public website. Each one shows a source link and the date we checked it. If an inspector doesn't publish a price, we show "call for price". Listings are not endorsements. Check that an inspector's Florida license is active before you hire them.</p>
<h2>Not insurance, legal, or engineering advice</h2><p>Everything on this site is general information. We are not an insurance agent, insurer, or inspector. Your insurer decides which inspections it accepts and what discounts apply. Ask your agent or insurer.</p>
<h2>Affiliate &amp; referral disclosure</h2><p class="notice">Right now we have <strong>no paid relationships</strong> with any inspector, insurer, insurance agency, or lead-generation company. No listing is paid for, and nothing on this site is an affiliate link. In the future the site may earn referral fees, for example from an insurance-quote tool or from featured listings. If that happens we will update this page first, name the type of relationship, and clearly label any paid or affiliate link or placement where it appears. Payment will never change the prices or license information we show.</p>
<h2>Not insurance advice</h2><p>Nothing here is a recommendation to buy, change, or cancel an insurance policy. We do not sell insurance and we are not licensed as an insurance agent. Whether an inspection earns a discount, and how much, depends on your insurer's filed rates and on what the inspector verifies. Talk to a licensed insurance agent or your insurer before you make coverage decisions.</p>
<h2>Licenses</h2><p>Where shown, license types and numbers come from the Florida Department of Business and Professional Regulation license search on the date listed. "Not verified" means we could not confirm a license from official sources, not that the business is unlicensed. Check <a href="https://www.myfloridalicense.com/wl11.asp">myfloridalicense.com</a> yourself before you hire.</p>
<h2>Corrections &amp; listing requests</h2><p>Email <a href="mailto:{CONTACT}">{CONTACT}</a>. Self-serve listings are coming soon.</p></article>''')

# CSS, sitemap, robots, csv
open(f"{OUT}/style.css","w").write(open(f"{ROOT}/src/style.css").read())
open(f"{OUT}/.nojekyll","w").write("")
open(f"{OUT}/CNAME","w").write("pbcinspections.com\n")
today=data["checked"]
open(f"{OUT}/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+"".join(f'  <url><loc>{BASE_URL}/{p}</loc><lastmod>{today}</lastmod></url>\n'.replace("/index.html","/") for p in pages)+"</urlset>\n")
open(f"{OUT}/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
keys=list(data["inspectors"][0].keys())
with open(f"{ROOT}/data/inspectors.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
    for i in data["inspectors"]: w.writerow({**i,"cities":";".join(i["cities"])})
print("built",len(pages),"pages ->",OUT)
