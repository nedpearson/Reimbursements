#!/usr/bin/env python3
"""
Pull the ACTUAL bill emails/attachments behind every ledger line that currently has no
document (mortgage payment notices, 'Gmail sweep' utility/pool/PODS/construction/FACTS
lines, AT&T Business) into  <House Bills>/_sources/<Category>/  and register each one in
config.json 'line_sources' so categorize/build_portal show it as that line's exhibit.

Usage:  set GMAIL_APP_PASSWORD=xxxx ; python fetch_gmail_sources.py [--dry]
Never prints or stores the password. IMAP read-only.
"""
import os, sys, re, json, imaplib, email, email.header, datetime as dt, html
HERE=os.path.dirname(os.path.abspath(__file__))
CFG_P=os.path.join(HERE,'config.json'); CFG=json.load(open(CFG_P,encoding='utf-8'))
LEDGER=json.load(open(os.path.join(HERE,'output','ledger.json'),encoding='utf-8'))
BILLS=CFG['last_folder']; SRC=os.path.join(BILLS,'_sources')
USER=CFG.get('user_email','nedpearson@gmail.com')
PW=os.environ.get('GMAIL_APP_PASSWORD','').replace(' ','')
DRY='--dry' in sys.argv
if not PW and not DRY: sys.exit('GMAIL_APP_PASSWORD not set')

# vendor -> (gmail search terms, subject/from hints)
RULES={
 'Assurance Financial': ['FROM "assurance"','SUBJECT "payment"'],
 'Entergy (Electric)':  ['FROM "entergy"'],
 'Atmos (Gas)':         ['FROM "atmos"'],
 'AT&T Internet':       ['FROM "att.com"','SUBJECT "bill"'],
 'AT&T Business (Pearsons Luggage)': ['FROM "att.com"','SUBJECT "bill"'],
 'BR Water':            ['OR FROM "brwater" FROM "speedpay"'],
 'Pool (Fernando)':     ['OR FROM "fernando" SUBJECT "Invoice"'],
 'PODS (Storage)':      ['FROM "pods"'],
 "De Roman's Construction": ['OR SUBJECT "roman" SUBJECT "invoice"'],
 "St Luke's School (FACTS)": ['OR FROM "facts" FROM "factsmgt"'],
}
WANT=[r for r in LEDGER if r.get('her_share') and (str(r.get('file','')).startswith('(') or not r.get('file'))]
print('lines needing a document:',len(WANT))

def dec(s):
    if not s: return ''
    out=[]
    for b,enc in email.header.decode_header(s):
        out.append(b.decode(enc or 'utf-8','ignore') if isinstance(b,bytes) else b)
    return ''.join(out)
def safe(s): return re.sub(r'[^A-Za-z0-9._-]+','_',s)[:80]

def html_to_pdf(htmltext, out):
    """Render the email body to a PDF via Chromium/Edge headless (keeps it a real document)."""
    import subprocess, tempfile
    tmp=out+'.html'
    open(tmp,'w',encoding='utf-8').write(htmltext)
    for exe in [r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']:
        if os.path.exists(exe):
            subprocess.run([exe,'--headless=new','--disable-gpu','--no-pdf-header-footer',
                            '--print-to-pdf='+out,'file:///'+tmp.replace('\\','/')],
                           capture_output=True,timeout=90)
            if os.path.exists(out): os.remove(tmp); return True
    return False

def body_html(msg):
    htmlp=None; txt=None
    for part in msg.walk():
        ct=part.get_content_type()
        if part.get('Content-Disposition','').startswith('attachment'): continue
        try: payload=part.get_payload(decode=True)
        except Exception: payload=None
        if not payload: continue
        cs=part.get_content_charset() or 'utf-8'
        if ct=='text/html' and htmlp is None: htmlp=payload.decode(cs,'ignore')
        elif ct=='text/plain' and txt is None: txt=payload.decode(cs,'ignore')
    if htmlp: return htmlp
    if txt: return '<pre style="font:12px/1.4 monospace;white-space:pre-wrap">'+html.escape(txt)+'</pre>'
    return None

def save_msg(msg, folder, stem):
    """Save attachments (PDF/images) if any, else render the body. Returns rel path or None."""
    os.makedirs(folder,exist_ok=True)
    hdr=('<div style="font:11px Arial;color:#555;border-bottom:1px solid #999;margin-bottom:8px">'
         f'<b>From:</b> {html.escape(dec(msg.get("From")))} &nbsp; <b>Date:</b> {html.escape(msg.get("Date",""))}<br>'
         f'<b>Subject:</b> {html.escape(dec(msg.get("Subject")))}</div>')
    for part in msg.walk():
        fn=part.get_filename()
        if fn and fn.lower().endswith(('.pdf','.jpg','.jpeg','.png')):
            p=os.path.join(folder,safe(stem)+'_'+safe(dec(fn)))
            if not DRY: open(p,'wb').write(part.get_payload(decode=True))
            return os.path.relpath(p,BILLS)
    b=body_html(msg)
    if not b: return None
    p=os.path.join(folder,safe(stem)+'.pdf')
    if DRY or html_to_pdf(hdr+b,p): return os.path.relpath(p,BILLS)
    p=os.path.join(folder,safe(stem)+'.html')
    open(p,'w',encoding='utf-8').write(hdr+b); return os.path.relpath(p,BILLS)

def money_in(text, amt):
    s1='%.2f'%amt; s2='{:,.2f}'.format(amt)
    return s1 in text or s2 in text

M=None
if not DRY:
    M=imaplib.IMAP4_SSL('imap.gmail.com'); M.login(USER,PW); M.select('"[Gmail]/All Mail"',readonly=True)

cache={}
def search(vendor, d):
    """Return list of (uid, msg) near date d for vendor; cached per vendor+month."""
    key=(vendor,d[:7])
    if key in cache: return cache[key]
    terms=RULES.get(vendor)
    if not terms or M is None: cache[key]=[]; return []
    dd=dt.date.fromisoformat(d)
    since=(dd-dt.timedelta(days=45)).strftime('%d-%b-%Y'); before=(dd+dt.timedelta(days=40)).strftime('%d-%b-%Y')
    q='(%s SINCE %s BEFORE %s)'%(' '.join(terms),since,before)
    typ,data=M.uid('search',None,q)
    uids=(data[0] or b'').split()
    out=[]
    for u in uids[-60:]:
        typ,md=M.uid('fetch',u,'(RFC822)')
        if typ!='OK' or not md or not md[0]: continue
        out.append((u.decode(),email.message_from_bytes(md[0][1])))
    cache[key]=out; return out

added=[]; missing=[]
for r in WANT:
    v=r['vendor']; d=r.get('date') or ''; a=float(r['amount']); cat=r['category']
    if not d: missing.append(r); continue
    hits=search(v,d)
    best=None
    for u,msg in hits:
        b=body_html(msg) or ''
        text=re.sub('<[^>]+>',' ',b)
        has_att=any(p.get_filename() for p in msg.walk())
        target=a if r.get('flat_share') is None else None
        if target is None or money_in(text,target) or has_att:
            try: md=email.utils.parsedate_to_datetime(msg.get('Date')).date()
            except Exception: md=dt.date.fromisoformat(d)
            score=abs((md-dt.date.fromisoformat(d)).days)+(0 if (target and money_in(text,target)) else 20)
            if best is None or score<best[0]: best=(score,u,msg)
    if not best: missing.append(r); continue
    _,u,msg=best
    stem=f"{d}_{safe(v)}_{a:.2f}"
    rel=save_msg(msg, os.path.join(SRC,safe(cat)), stem)
    if rel:
        added.append(dict(vendor=v,date=d,amount=a,file=rel.replace('\\','/'),ref=r.get('ref'),gmail_uid=u))
        print('OK ',r.get('ref'),d,v,a,'->',rel)
    else: missing.append(r)

print('\nattached:',len(added),' still missing:',len(missing))
for r in missing: print('MISSING',r.get('ref'),r.get('date'),r['vendor'],r['amount'])
if not DRY and added:
    ls=CFG.get('line_sources',[])
    have={(x['vendor'],x['date'],round(float(x['amount']),2)) for x in ls}
    for x in added:
        k=(x['vendor'],x['date'],round(x['amount'],2))
        if k not in have: ls.append({k2:x[k2] for k2 in ('vendor','date','amount','file')}); have.add(k)
    CFG['line_sources']=ls
    json.dump(CFG,open(CFG_P,'w',encoding='utf-8'),indent=2,ensure_ascii=False)
    print('config.json line_sources now',len(ls))
if M: M.logout()
