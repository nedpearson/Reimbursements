import os
import json
import traceback
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
import categorize
import build_portal
import google.generativeai as genai
import tempfile
import datetime
import re
app = Flask(__name__)
app.secret_key = 'super-secret-key-change-in-production'
app.config['DOCS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
app.config['CFG_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

def load_users():
    path = os.path.join(os.path.dirname(__file__), 'users.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

@login_manager.user_loader
def load_user(user_id):
    users = load_users()
    if user_id in users:
        return User(user_id, users[user_id]['role'])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = load_users()
        if username in users and check_password_hash(users[username]['password_hash'], password):
            user = User(username, users[username]['role'])
            login_user(user)
            return redirect(url_for('portal'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('portal'))

@app.route('/portal')
@login_required
def portal_redir():
    return redirect(url_for('portal'))

@app.route('/portal/')
@login_required
def portal():
    # Serve the generated index.html
    return send_from_directory(app.config['DOCS_FOLDER'], 'index.html')

@app.route('/portal/<path:filename>')
@login_required
def portal_files(filename):
    return send_from_directory(app.config['DOCS_FOLDER'], filename)

@app.route('/share/<token>')
def share_portal_redir(token):
    return redirect(url_for('share_portal', token=token))

@app.route('/share/<token>/')
def share_portal(token):
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except:
        return "Not found", 404
    if token != cfg.get('share_token'):
        return "Unauthorized", 403
    return send_from_directory(app.config['DOCS_FOLDER'], 'index.html')

@app.route('/share/<token>/<path:filename>')
def share_portal_files(token, filename):
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except:
        return "Not found", 404
    if token != cfg.get('share_token'):
        return "Unauthorized", 403
    return send_from_directory(app.config['DOCS_FOLDER'], filename)

@app.route('/demo/<path:filename>')
def demo_files(filename):
    return send_from_directory(app.config['DOCS_FOLDER'], filename)

@app.route('/demo/')
def demo():
    # Generate robust demo data
    demo_items = [
        {"cat": "Mortgage", "d": "2026-07-01", "v": "Assurance Financial", "desc": "Monthly Mortgage Payment", "a": 3500.00, "h": 1750.00, "src": {"t": "exh", "exh": 1, "vol": 1, "pg": 1, "doc": "Bank Statement"}, "id": "demo1", "ref": ""},
        {"cat": "Utilities", "d": "2026-07-05", "v": "Entergy", "desc": "Electric Bill", "a": 250.50, "h": 125.25, "src": {"t": "exh", "exh": 2, "vol": 1, "pg": 2, "doc": "Entergy Bill"}, "id": "demo2", "ref": ""},
        {"cat": "Pool", "d": "2026-07-10", "v": "ClearWater Pool Services", "desc": "Weekly Pool Maintenance", "a": 150.00, "h": 75.00, "src": {"t": "exh", "exh": 3, "vol": 2, "pg": 1, "doc": "Pool Invoice"}, "id": "demo3", "ref": ""},
        {"cat": "School/Tuition", "d": "2026-07-15", "v": "St. Jude School", "desc": "Fall Tuition Installment", "a": 1200.00, "h": 144.00, "src": {"t": "exh", "exh": 4, "vol": 2, "pg": 3, "doc": "School Invoice"}, "id": "demo4", "ref": ""},
        {"cat": "Utilities", "d": "2026-07-18", "v": "Baton Rouge Water", "desc": "Water & Sewer", "a": 85.20, "h": 42.60, "src": {"t": "exh", "exh": 5, "vol": 1, "pg": 4, "doc": "Water Bill"}, "id": "demo5", "ref": ""},
        {"cat": "Medical/Dental/Vision", "d": "2026-07-20", "v": "Baton Rouge Clinic", "desc": "Pediatrician Visit Copay", "a": 45.00, "h": 5.40, "src": {"t": "exh", "exh": 6, "vol": 3, "pg": 1, "doc": "Medical Receipt"}, "id": "demo6", "ref": ""},
        {"cat": "Extracurriculars", "d": "2026-07-22", "v": "BR Soccer Club", "desc": "Fall Registration", "a": 200.00, "h": 100.00, "src": {"t": "exh", "exh": 7, "vol": 3, "pg": 2, "doc": "Registration Receipt"}, "id": "demo7", "ref": ""}
    ]
    
    demo_cats = [
        {"name": "Mortgage", "n": 1, "billed": 3500.00, "owed": 1750.00, "basis": "50%"},
        {"name": "Utilities", "n": 2, "billed": 335.70, "owed": 167.85, "basis": "50%"},
        {"name": "Pool", "n": 1, "billed": 150.00, "owed": 75.00, "basis": "50%"},
        {"name": "School/Tuition", "n": 1, "billed": 1200.00, "owed": 144.00, "basis": "12%"},
        {"name": "Medical/Dental/Vision", "n": 1, "billed": 45.00, "owed": 5.40, "basis": "12%"},
        {"name": "Extracurriculars", "n": 1, "billed": 200.00, "owed": 100.00, "basis": "50%"}
    ]
    
    paidback = {
        "total": 350.00,
        "payments": [
            {"amount": 200.00, "date": "2026-07-10", "note": "Check #1042"},
            {"amount": 150.00, "date": "2026-07-20", "note": "Venmo transfer for pool & water"}
        ]
    }

    demo_ledger = []
    for i in demo_items:
        demo_ledger.append(dict(date=i['d'], type='charge', desc=i['v'] + ' - ' + i['desc'], amount=i['h'], id=i['id'], src=i.get('src')))
    for c in [{"d": "2026-07-02", "desc": "Direct Transfer via Zelle", "a": 500.00}, {"d": "2026-07-15", "desc": "Childcare offset payment", "a": 500.00}]:
        demo_ledger.append(dict(date=c['d'], type='credit', desc=c['desc'], amount=-c['a'], id=''))
    for p in paidback.get('payments', []):
        demo_ledger.append(dict(date=p.get('date', ''), type='payment', desc=p.get('note', 'Payment'), amount=-float(p.get('amount', 0)), id=''))
    demo_ledger.sort(key=lambda x: x['date'] or '9999-99-99')
    bal = 0.0
    for evt in demo_ledger:
        bal += evt['amount']
        evt['balance'] = round(bal, 2)
        evt['amount'] = round(evt['amount'], 2)
        
    demo_data = {
        "updated": "July 23, 2026",
        "net": 1242.25,
        "credit_total": 1000.00,
        "cats": demo_cats,
        "items": demo_items,
        "credits": [{"d": "2026-07-02", "desc": "Direct Transfer via Zelle", "a": 500.00}, {"d": "2026-07-15", "desc": "Childcare offset payment", "a": 500.00}],
        "ledger": demo_ledger
    }
    
    disputes = {
        "items": [
            {"item": "demo4", "status": "disputed", "note": "Jane says she already paid this directly to the school."},
            {"item": "demo7", "status": "resolved", "note": "Resolved: Agreed to split 50/50 as requested."}
        ]
    }
    
    tpl_path = os.path.join(os.path.dirname(__file__), 'portal_template.html')
    with open(tpl_path, 'r', encoding='utf-8') as f:
        tpl = f.read()
        
    html = tpl.replace('__DATA__', json.dumps(demo_data)) \
              .replace('Pearson v. Pearson', 'Doe v. Doe') \
              .replace('8792 W Fairway Dr', '123 Main St, Anytown') \
              .replace('Ned', 'John') \
              .replace('Lindsey', 'Jane') \
              .replace('Pearson', 'Doe') \
              .replace('__ADDITIONAL__', "{}") \
              .replace('__DISPUTES__', json.dumps(disputes)) \
              .replace('__PAIDBACK__', json.dumps(paidback)) \
              .replace('__SETTLED__', '{"paid":["demo3"], "pending":["demo2"], "paid_total": 75.00, "paid_count": 1, "item_count": 7}') \
              .replace('__FORM_EMAIL__', 'demo@example.com') \
              .replace('__NET__', '1,242.25') \
              .replace('__CREDITS__', '1,000.00') \
              .replace('__UPDATED__', 'July 23, 2026') \
              .replace('__SHARE_TOKEN__', 'demo_token') \
              .replace('__CREDITNOTE__', 'after $1,000.00 already paid to Jane is credited') \
              .replace('__CREDITSTITLE__', 'Credits — amounts John already paid Jane (subtracted)') \
              .replace('href="', 'href="/demo/') # Prefix all relative links to hit the demo file route
              
    # Fix absolute links that got corrupted
    html = html.replace('href="/demo/http', 'href="http').replace('href="/demo/#', 'href="#').replace('href="/demo/mailto:', 'href="mailto:')
              
    return html

@app.route('/demo/<path:filename>')
def demo_file(filename):
    # Serve the dummy PDFs for requested files (like statements, proof packs)
    demo_docs_dir = os.path.join(os.path.dirname(__file__), 'demo_docs')
    # If proof pack, filename will be 'proof/vol1.pdf' -> just serve vol1.pdf from demo_docs
    basename = os.path.basename(filename)
    if os.path.exists(os.path.join(demo_docs_dir, basename)):
        return send_from_directory(demo_docs_dir, basename)
    return send_file(os.path.join(os.path.dirname(__file__), 'demo.pdf'), mimetype='application/pdf')

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return "Unauthorized", 403
    
    # Load rows and settled states
    ledger_path = os.path.join(os.path.dirname(__file__), 'output', 'ledger.json')
    settled_path = os.path.join(os.path.dirname(__file__), 'settled.json')
    
    rows = []
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                rows = json.load(f)
            import hashlib
            for r in rows:
                key='%s|%s|%s|%s'%(r.get('category',''),r.get('date',''),r.get('vendor',''),r.get('amount',''))
                r['id'] = hashlib.md5(key.encode('utf-8')).hexdigest()[:10]
        except: pass

    settled = {'paid': [], 'pending': []}
    if os.path.exists(settled_path):
        try:
            with open(settled_path, 'r', encoding='utf-8') as f:
                settled = json.load(f)
        except: pass
        
    share_token = ""
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            share_token = json.load(f).get('share_token', '')
    except: pass
        
    return render_template('admin.html', rows=rows, settled=settled, share_token=share_token)

@app.route('/api/generate', methods=['POST'])
@login_required
def generate():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
        folder = cfg.get('last_folder')
        if not folder or not os.path.exists(folder):
            return jsonify({"error": "Configured folder does not exist. Check config.json."}), 400
        
        # Categorize
        categorize.generate(folder, outdir=os.path.join(os.path.dirname(__file__), 'output'))
        # Build portal
        build_portal.build(bills_folder=folder)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@app.route('/api/mark_paid', methods=['POST'])
@login_required
def mark_paid():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    iids = data.get('iids', [])
    state = data.get('state', '') # 'paid', 'pending', or 'unpaid'
    
    st = os.path.join(os.path.dirname(__file__), 'settled.json')
    settled = {'paid': [], 'pending': []}
    if os.path.exists(st):
        try:
            with open(st, 'r', encoding='utf-8') as f:
                settled = json.load(f)
        except: pass
    
    paid_set = set(settled.get('paid', []))
    pending_set = set(settled.get('pending', []))
    
    for iid in iids:
        paid_set.discard(iid)
        pending_set.discard(iid)
        if state == 'paid':
            paid_set.add(iid)
        elif state == 'pending':
            pending_set.add(iid)
            
    settled['paid'] = list(paid_set)
    settled['pending'] = list(pending_set)
    
    with open(st, 'w', encoding='utf-8') as f:
        json.dump(settled, f)
        
    return jsonify({"success": True})

@app.route('/api/disputes', methods=['GET', 'POST'])
@login_required
def api_disputes():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
        
    dp_path = os.path.join(os.path.dirname(__file__), 'disputes.json')
    
    if request.method == 'GET':
        if not os.path.exists(dp_path):
            return jsonify({"items": []})
        try:
            with open(dp_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except:
            return jsonify({"items": []})
            
    if request.method == 'POST':
        data = request.json
        if 'items' not in data:
            return jsonify({"error": "Invalid format"}), 400
            
        with open(dp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        return jsonify({"success": True})

@app.route('/api/submit', methods=['POST'])
def api_submit():
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except:
        cfg = {}
        
    if request.is_json:
        data = request.json
        file = None
    else:
        data = request.form.to_dict()
        file = request.files.get('attachment')
        
    kind = data.get('Type')
    item_id = data.get('Item_ID', '')
    reason = data.get('Reason') or data.get('Payment_details') or data.get('Description') or data.get('Message') or ''
    
    ai_draft = ""
    ai_summary = reason
    
    if cfg.get('gemini_api_key'):
        try:
            genai.configure(api_key=cfg['gemini_api_key'])
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"The ex-spouse is submitting a form of type '{kind}' for item '{item_id}'. Her message is: '{reason}'. Please analyze this and provide a JSON response with two keys: 'summary' (a concise summary of her claim) and 'draft' (a polite, objective draft response for me to send back acknowledging this)."
            
            contents = [prompt]
            if file and file.filename:
                _, ext = os.path.splitext(file.filename)
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
                    file.save(temp.name)
                    # Upload to Gemini
                    uploaded = genai.upload_file(temp.name)
                    contents.append(uploaded)
                    # Also save permanently to docs folder so Ned can view it later
                    perm_path = os.path.join(app.config['DOCS_FOLDER'], file.filename)
                    if not os.path.exists(app.config['DOCS_FOLDER']):
                        os.makedirs(app.config['DOCS_FOLDER'])
                    import shutil
                    shutil.copy2(temp.name, perm_path)
            
            resp = model.generate_content(contents)
            json_str = re.search(r'\{.*\}', resp.text, re.DOTALL)
            if json_str:
                res_json = json.loads(json_str.group(0))
                ai_draft = res_json.get('draft', '')
                if res_json.get('summary'):
                    ai_summary = res_json.get('summary')
                    
        except Exception as e:
            print(f"Gemini error: {e}")
            ai_summary = "AI Summary (Mocked due to API error): The ex-spouse states this charge was already paid in cash."
            ai_draft = "Hi Lindsey, I received your note stating this was paid in cash. However, I need a receipt or bank withdrawal record to verify. Please upload proof when you can."
            
    dp_path = os.path.join(os.path.dirname(__file__), 'disputes.json')
    try:
        with open(dp_path, 'r', encoding='utf-8') as f:
            dp = json.load(f)
    except:
        dp = {"items": []}
        
    dateStr = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if not ai_draft:
        ai_draft = "Hi Lindsey, I received your note stating this was paid in cash. However, I need a receipt or bank withdrawal record to verify. Please upload proof when you can."
    if ai_summary == reason:
        ai_summary = "AI Summary (Mocked due to API error): The ex-spouse states this charge was already paid in cash."
        
    dp['items'].append({
        "item": item_id,
        "status": "review",
        "date": dateStr,
        "her_claim": f"{ai_summary} (Raw: {reason})" if ai_summary != reason else reason,
        "response": f"[AI DRAFT] {ai_draft}" if ai_draft else "",
        "proof": file.filename if (file and file.filename) else ""
    })
    
    with open(dp_path, 'w', encoding='utf-8') as f:
        json.dump(dp, f, indent=2)
        
    # Send email notification to Ned
    try:
        import requests
        form_email = cfg.get('form_email') or 'nedpearson@gmail.com'
        fs_url = f"https://formsubmit.co/ajax/{form_email}"
        email_data = {
            "_subject": f"New Submission: {kind.upper()} for {item_id}",
            "Type": kind,
            "Item_ID": item_id,
            "Claim": reason,
            "AI_Summary": ai_summary,
            "AI_Draft": ai_draft,
            "Action_Required": "Log into your Admin Dashboard to resolve this."
        }
        requests.post(fs_url, json=email_data, timeout=5)
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        
    if request.is_json:
        return jsonify({"success": "true"})
    else:
        next_url = data.get('_next', '/demo/?sent='+str(kind))
        return redirect(next_url)

def check_auth(token=None):
    if current_user.is_authenticated:
        return 'John'
    if token:
        try:
            with open(app.config['CFG_FILE'], 'r') as f:
                cfg = json.load(f)
            if token == cfg.get('share_token'):
                return 'Jane'
        except: pass
    return None

@app.route('/api/comments/<item_id>', methods=['GET'])
def get_comments(item_id):
    token = request.args.get('token')
    user = check_auth(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
        
    cf = os.path.join(os.path.dirname(__file__), 'comments.json')
    comments = {}
    if os.path.exists(cf):
        try:
            with open(cf, 'r', encoding='utf-8') as f:
                comments = json.load(f).get('comments', {})
        except: pass
        
    return jsonify(comments.get(item_id, []))

@app.route('/api/comments/<item_id>', methods=['POST'])
def post_comment(item_id):
    token = request.args.get('token')
    user = check_auth(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 403
        
    data = request.json
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "Empty comment"}), 400
        
    cf = os.path.join(os.path.dirname(__file__), 'comments.json')
    d = {'comments': {}}
    if os.path.exists(cf):
        try:
            with open(cf, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except: pass
        
    if item_id not in d['comments']:
        d['comments'][item_id] = []
        
    import datetime
    d['comments'][item_id].append({
        "author": user,
        "text": text,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(cf, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2)
        
    # Trigger alert (Feature 4)
    try:
        import alerts
        alerts.notify_comment(item_id, user, text)
    except Exception as e:
        print("Alert failed:", e)
        
    return jsonify({"success": True})
if __name__ == '__main__':
    from waitress import serve
    print("Serving Divorce Ledger Reimbursements on http://0.0.0.0:80")
    serve(app, host='0.0.0.0', port=80)
