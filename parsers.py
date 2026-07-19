"""
Reimbursement bill parsers.
Vendor-specific extraction of (statement_date, current-period amount) from
utility bills, invoices, receipts and Venmo statements.
Handles normal PDFs, image/scanned PDFs (OCR), JPG/PNG, and AT&T-style
HTML-saved-as-PDF files.
"""
import os, re, base64, tempfile, datetime as _dt

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

MONTHS = {m:i for i,m in enumerate(
    ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'],1)}

# ---------- low level helpers ----------
def _lines_from_pdf(path):
    d = fitz.open(path)
    return [l.strip() for pg in d for l in pg.get_text().splitlines() if l.strip()]

def _looks_like_html_pdf(path):
    with open(path,'rb') as f:
        head=f.read(200)
    return b'<!' in head[:5] or b'<html' in head.lower() or b'HTML' in head[:20]

def _decode_html_embedded_pdf(path):
    raw=open(path,encoding='utf-8',errors='ignore').read()
    m=re.search(r'base64String\s*=\s*"([A-Za-z0-9+/=\\\r\n]+)"',raw) or \
      re.search(r'data:application/pdf;base64,([A-Za-z0-9+/=]+)',raw)
    if not m: return None
    b64=re.sub(r'[^A-Za-z0-9+/=]','',m.group(1))
    data=base64.b64decode(b64+'='*(-len(b64)%4))
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.pdf')
    tmp.write(data); tmp.close(); return tmp.name

def _ocr_lines(path, dpi=200, pages=1):
    import pytesseract  # optional
    from PIL import Image
    out=[]
    if path.lower().endswith(('.png','.jpg','.jpeg')):
        out=pytesseract.image_to_string(Image.open(path)).splitlines()
    else:
        d=fitz.open(path)
        for pi in range(min(pages,len(d))):
            pix=d[pi].get_pixmap(dpi=dpi)
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.png'); tmp.write(pix.tobytes('png')); tmp.close()
            out+=pytesseract.image_to_string(Image.open(tmp.name)).splitlines()
    return [l.strip() for l in out if l.strip()]

def _ocr_lines_cli(path, dpi=200, pages=1):
    """OCR using tesseract CLI (no pytesseract dependency)."""
    import subprocess
    imgs=[]
    if path.lower().endswith(('.png','.jpg','.jpeg')):
        imgs=[path]
    else:
        d=fitz.open(path)
        for pi in range(min(pages,len(d))):
            pix=d[pi].get_pixmap(dpi=dpi)
            t=tempfile.NamedTemporaryFile(delete=False,suffix='.png'); t.write(pix.tobytes('png')); t.close(); imgs.append(t.name)
    out=[]
    for im in imgs:
        try:
            r=subprocess.run(['tesseract',im,'-'],capture_output=True,text=True,timeout=60)
            out+=r.stdout.splitlines()
        except Exception: pass
    return [l.strip() for l in out if l.strip()]

def money(s):
    m=re.search(r'([\d,]+\.\d{2})', s or '')
    return float(m.group(1).replace(',','')) if m else None

def _merge_split_money(lines):
    """Entergy renders '$' / '483' / '24' on separate lines. Rejoin."""
    M=[]; i=0
    while i<len(lines):
        if lines[i]=='$' and i+2<len(lines) and re.fullmatch(r'[-]?\d{1,4}',lines[i+1]) and re.fullmatch(r'\d{2}',lines[i+2]):
            M.append(f"${lines[i+1]}.{lines[i+2]}"); i+=3
        else: M.append(lines[i]); i+=1
    return M

def norm_date(s):
    """Return YYYY-MM-DD from many formats, else ''. """
    if not s: return ''
    s=s.strip()
    for fmt in ('%m/%d/%Y','%m/%d/%y','%d %b %Y','%b %d, %Y','%B %d, %Y'):
        try: return _dt.datetime.strptime(s,fmt).strftime('%Y-%m-%d')
        except Exception: pass
    m=re.search(r'([A-Z]{3})\s+(\d{2})\s+(\d{4})',s)  # 'MAY 05 2025'
    if m and m.group(1).title()[:3].lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}"
    return ''

# ---------- vendor detection ----------
def detect_vendor(path, text):
    t=text.lower(); fn=os.path.basename(path).lower()
    if 'atmos' in t or 'atmos' in fn: return 'atmos'
    if 'entergy' in t or 'entergy' in fn: return 'entergy'
    if ('water' in t and 'baton rouge' in t) or 'br water' in fn or 'fairway dr w' in t: return 'brwater'
    if 'pods' in fn or ('order #' in t and 'pods' in t): return 'pods'
    if 'fernando' in t or 'fernando' in fn or ('weekly pool cleaning' in t): return 'pool'
    if "st luke" in t or 'facts' in fn: return 'facts'
    if 'studyville' in t or 'studyville' in fn: return 'studyville'
    if 'venmo' in t or 'venmo' in fn:
        if 'lions' in fn or 'lawncare' in t: return 'venmo_lions'
        if 'lindsey' in fn: return 'venmo_lindsey'
        if 'eli' in fn: return 'venmo_eli'
        return 'venmo'
    if 'pearsons luggage' in t or '2825' in fn: return 'att_business'
    if 'at&t' in t or 'att' in fn or 'attbill' in fn: return 'att_internet'
    if 'zelle' in t or 'cleaning' in fn: return 'cleaning'
    return 'unknown'
