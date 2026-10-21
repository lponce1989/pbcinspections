#!/usr/bin/env python3
"""Refetch every listing's source URL, extract the dollar amounts on the page, and diff them
against the stored snapshot (data/price_snapshots.json). Writes reports/recheck-YYYY-MM-DD.md.
  python3 scripts/recheck.py          # compare and write report
  python3 scripts/recheck.py --init   # (re)write the stored snapshot from the live pages
Zero dependencies. Never edits inspectors.json; a human reviews the report and updates data."""
import json, os, re, sys, html, datetime, gzip, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP=f"{ROOT}/data/price_snapshots.json"
def fetch(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (pbcinspections.com recheck)","Accept-Encoding":"gzip, identity"})
    with urllib.request.urlopen(r,timeout=30) as f: b=f.read(); enc=f.headers.get("Content-Encoding","")
    if b[:2]==b"\x1f\x8b": b=gzip.decompress(b)
    elif enc=="br":  # some hosts send brotli regardless; fall back to curl if present
        import subprocess; b=subprocess.run(["curl","-sL","--compressed","-m","30","-A","Mozilla/5.0",u],capture_output=True).stdout
    return b.decode("utf-8","ignore")
def snippet(t):
    t=re.sub(r"<script.*?</script>|<style.*?</style>","",t,flags=re.S|re.I)
    x=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",t)))
    amounts=sorted(set(re.findall(r"\$\s?\d[\d,]*(?:\.\d\d)?",x)))
    ctx=[x[max(0,m.start()-60):m.end()+20].strip() for m in re.finditer(r"\$\s?\d[\d,]*",x)][:40]
    return {"amounts":[a.replace(" ","") for a in amounts],"context":ctx}
def main():
    data=json.load(open(f"{ROOT}/data/inspectors.json"))
    old=json.load(open(SNAP)) if os.path.exists(SNAP) else {}
    new={}; lines=[]; today=datetime.date.today().isoformat()
    for i in data["inspectors"]:
        u=i["source"]
        try: s=snippet(fetch(u)); s["fetched"]=today
        except Exception as ex:
            lines.append(f"- **{i['name']}** ({u}): FETCH FAILED: {ex}"); new[i["slug"]]=old.get(i["slug"],{}); continue
        new[i["slug"]]=s; o=old.get(i["slug"])
        if not o: lines.append(f"- {i['name']}: no stored snapshot (run --init)"); continue
        a,b=set(o.get("amounts",[])),set(s["amounts"])
        if a!=b: lines.append(f"- **{i['name']}** ({u}): CHANGED. Removed {sorted(a-b) or 'none'}; added {sorted(b-a) or 'none'}")
        else: lines.append(f"- {i['name']}: no change")
    if "--init" in sys.argv:
        json.dump(new,open(SNAP,"w"),indent=1); print("snapshot written",len(new)); return
    os.makedirs(f"{ROOT}/reports",exist_ok=True); p=f"{ROOT}/reports/recheck-{today}.md"
    open(p,"w").write(f"# Price recheck {today}\n\n"+"\n".join(lines)+"\n"); print("report:",p)
if __name__=="__main__": main()
