import sys, io

server_path, build_path, admin_path = sys.argv[1], sys.argv[2], sys.argv[3]

# ============================================================== build_portal.py
b = io.open(build_path, encoding='utf-8').read()
orig_b_len = len(b)

old_tpl_load = "    tpl=open(os.path.join(HERE,'portal_template.html'),encoding='utf-8').read()"
new_tpl_load = """    tpl=open(os.path.join(HERE,'portal_template.html'),encoding='utf-8').read()
    # Settings-driven names & case info. Defaults match the original hardcoded text,
    # so this is a no-op until someone changes a value in Admin > Settings. The name
    # swap runs on the raw static template -- before any bill/vendor data is inserted
    # below -- so it can never touch real ledger data, only the document's own copy.
    ned_name=str(cfg.get('ned_name') or 'Ned')
    lindsey_name=str(cfg.get('lindsey_name') or 'Lindsey')
    case_surname=str(cfg.get('case_surname') or 'Pearson')
    tpl=tpl.replace('Ned', ned_name).replace('Lindsey', lindsey_name).replace('Pearson', case_surname)
    property_address=str(cfg.get('property_address') or '8792 W Fairway Dr, Baton Rouge')
    date_range=str(cfg.get('date_range') or 'Aug 2024 – Jul 2026')
    case_number=str(cfg.get('case_number') or 'No. 236951')
    court_name=str(cfg.get('court_name') or 'Family Court, EBR Parish')
    tpl=tpl.replace('8792 W Fairway Dr, Baton Rouge', property_address)
    tpl=tpl.replace('Aug 2024 – Jul 2026', date_range)
    tpl=tpl.replace('No. 236951', case_number)
    tpl=tpl.replace('Family Court, EBR Parish', court_name)"""
assert b.count(old_tpl_load) == 1, "build_portal.py tpl-load anchor not found once"
b = b.replace(old_tpl_load, new_tpl_load)

old_creditnote = """    tpl=tpl.replace('__CREDITNOTE__', ('after $__CREDITS__ already paid to Lindsey is credited' if subtract else 'includes the direct payments/advances Ned made to Lindsey — see the Advances category below'))
    tpl=tpl.replace('__CREDITSTITLE__', ('Credits — amounts Ned already paid Lindsey (subtracted)' if subtract else 'Payments Ned made to Lindsey — settled separate expenses (NOT subtracted)'))"""
new_creditnote = """    tpl=tpl.replace('__CREDITNOTE__', (('after $__CREDITS__ already paid to %s is credited'%lindsey_name) if subtract else ('includes the direct payments/advances %s made to %s — see the Advances category below'%(ned_name,lindsey_name))))
    tpl=tpl.replace('__CREDITSTITLE__', (('Credits — amounts %s already paid %s (subtracted)'%(ned_name,lindsey_name)) if subtract else ('Payments %s made to %s — settled separate expenses (NOT subtracted)'%(ned_name,lindsey_name))))"""
assert b.count(old_creditnote) == 1, "build_portal.py creditnote anchor not found once"
b = b.replace(old_creditnote, new_creditnote)

io.open(build_path, 'w', encoding='utf-8').write(b)
print(f"build_portal.py: {orig_b_len} -> {len(b)} bytes OK")

# ============================================================== server.py
t = io.open(server_path, encoding='utf-8').read()
orig_t_len = len(t)

old_portal_route = """@app.route('/portal/')
@login_required
def portal():
    # Serve the generated index.html
    return send_from_directory(app.config['DOCS_FOLDER'], 'index.html')"""
new_portal_route = """ADMIN_LINK_HTML = '<a href="/admin" style="position:fixed;top:14px;right:14px;z-index:9999;background:#1a1540;color:#fff;padding:8px 16px;border-radius:20px;font:600 13px Inter,Arial,sans-serif;text-decoration:none;box-shadow:0 4px 12px rgba(0,0,0,.35)">\\u2699 Admin</a>'

@app.route('/portal/')
@login_required
def portal():
    # Serve the generated index.html. Admins get a small floating link back to
    # /admin injected on the way out -- nobody else's login (or the public share
    # link) ever sees it, since this only runs for an authenticated admin request.
    path = os.path.join(app.config['DOCS_FOLDER'], 'index.html')
    if current_user.role != 'admin':
        return send_from_directory(app.config['DOCS_FOLDER'], 'index.html')
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('</header>', ADMIN_LINK_HTML + '</header>', 1)
    return html"""
assert t.count(old_portal_route) == 1, "server.py portal-route anchor not found once"
t = t.replace(old_portal_route, new_portal_route)

old_anchor = "@app.route('/api/submit', methods=['POST'])"
new_block = """SETTINGS_KEYS = [
    'ned_name', 'lindsey_name', 'case_surname',
    'property_address', 'date_range', 'case_number', 'court_name',
    'form_email', 'gemini_api_key',
    'split_percent', 'exclude_business',
]

@app.route('/api/config', methods=['GET'])
@login_required
def api_config_get():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    out = {k: cfg.get(k) for k in SETTINGS_KEYS}
    out['share_token'] = cfg.get('share_token', '')
    return jsonify(out)

@app.route('/api/config', methods=['POST'])
@login_required
def api_config_post():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json or {}
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    if 'split_percent' in data:
        sp = data['split_percent']
        if not isinstance(sp, dict):
            return jsonify({"error": "split_percent must be an object"}), 400
        for k, v in sp.items():
            try:
                num = float(v)
            except (TypeError, ValueError):
                return jsonify({"error": f"Split % for {k} must be a number"}), 400
            if num < 0 or num > 100:
                return jsonify({"error": f"Split % for {k} must be between 0 and 100"}), 400
    if 'exclude_business' in data and not isinstance(data['exclude_business'], list):
        return jsonify({"error": "exclude_business must be a list"}), 400
    for k in SETTINGS_KEYS:
        if k in data:
            cfg[k] = data[k]
    with open(app.config['CFG_FILE'], 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
    return jsonify({"success": True})

@app.route('/api/regenerate_share_token', methods=['POST'])
@login_required
def api_regenerate_share_token():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    import secrets
    try:
        with open(app.config['CFG_FILE'], 'r') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    new_token = 't_' + secrets.token_urlsafe(16)
    cfg['share_token'] = new_token
    with open(app.config['CFG_FILE'], 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
    return jsonify({"success": True, "share_token": new_token})

@app.route('/api/submit', methods=['POST'])"""
assert t.count(old_anchor) == 1, "server.py submit-route anchor not found once"
t = t.replace(old_anchor, new_block)

io.open(server_path, 'w', encoding='utf-8').write(t)
print(f"server.py: {orig_t_len} -> {len(t)} bytes OK")

# ============================================================== admin.html
a = io.open(admin_path, encoding='utf-8').read()
orig_a_len = len(a)

old_anchor = "    </div>\n\n    <!-- Add / Reset User Modal -->"
new_settings_section = """
        <div style="margin-top: 40px; margin-bottom: 24px;">
            <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">Settings</h2>
            <p style="color: var(--text-muted);">Notifications, sharing, and the AI key take effect immediately. Case info, names, and split percentages take effect the next time you click <b>Regenerate Portal</b> above \\u2014 run that from your own computer, since that\\u2019s where the bill files live, not this server.</p>
        </div>

        <div class="card" style="padding:24px; margin-bottom:20px;">
            <h3 style="margin-bottom:16px;">Notifications &amp; sharing</h3>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
                <div>
                    <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Dispute notification email</label>
                    <input id="cfgFormEmail" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">
                </div>
            </div>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">No-login share link</label>
            <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
                <span id="cfgShareLink" style="font-family:monospace; font-size:13px; color:#60a5fa;"></span>
                <button class="btn" style="padding:6px 12px; font-size:12px;" onclick="regenShareToken()">Regenerate link</button>
            </div>
            <p style="font-size:12px; color:var(--text-muted); margin-top:6px;">Regenerating immediately invalidates the old link \\u2014 anyone using it loses access until you send the new one.</p>
        </div>

        <div class="card" style="padding:24px; margin-bottom:20px;">
            <h3 style="margin-bottom:16px;">AI dispute drafting</h3>
            <label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Gemini API key (leave blank to keep AI drafting off)</label>
            <input id="cfgGeminiKey" type="password" autocomplete="off" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">
        </div>

        <div class="card" style="padding:24px; margin-bottom:20px;">
            <h3 style="margin-bottom:16px;">Case info &amp; header</h3>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Your name (as shown on the portal)</label><input id="cfgNedName" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Her name (as shown on the portal)</label><input id="cfgLindseyName" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Case surname (e.g. Pearson \\u2192 "Pearson v. Pearson")</label><input id="cfgCaseSurname" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Case number</label><input id="cfgCaseNumber" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Court</label><input id="cfgCourtName" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Property address</label><input id="cfgPropertyAddress" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
                <div><label style="display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px;">Date range shown under the title</label><input id="cfgDateRange" style="width:100%; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);"></div>
            </div>
        </div>

        <div class="card" style="padding:24px; margin-bottom:20px;">
            <h3 style="margin-bottom:6px;">Split percentages by category</h3>
            <p style="font-size:12px; color:var(--text-muted); margin-bottom:16px;">What percentage of each category she owes. Changing these does not re-file past charges \\u2014 it only applies the next time you regenerate.</p>
            <div id="splitPercentRows"></div>
            <button class="btn" style="padding:6px 12px; font-size:12px; margin-top:8px;" onclick="addSplitRow()">+ Add category</button>
        </div>

        <div class="card" style="padding:24px; margin-bottom:20px;">
            <h3 style="margin-bottom:6px;">Excluded vendors</h3>
            <p style="font-size:12px; color:var(--text-muted); margin-bottom:16px;">Charges from any vendor whose name contains this text are never counted toward her share (matched case-insensitively, partial match). Used for your own businesses and anything else that shouldn't be in this claim.</p>
            <div id="excludeBusinessRows"></div>
            <button class="btn" style="padding:6px 12px; font-size:12px; margin-top:8px;" onclick="addExcludeRow()">+ Add vendor</button>
        </div>

        <div style="margin-bottom:60px;">
            <button class="btn btn-success" onclick="saveSettings()">Save Settings</button>
        </div>
    </div>

    <!-- Add / Reset User Modal -->"""
assert a.count(old_anchor) == 1, "admin.html settings-section anchor not found once"
a = a.replace(old_anchor, new_settings_section)

old_js_anchor = "        document.addEventListener('DOMContentLoaded', loadUsers);"
new_js_block = """        document.addEventListener('DOMContentLoaded', loadUsers);

        // ---- Settings ----
        async function loadSettings() {
            try {
                const res = await fetch('/api/config');
                const cfg = await res.json();
                document.getElementById('cfgFormEmail').value = cfg.form_email || '';
                document.getElementById('cfgGeminiKey').value = cfg.gemini_api_key || '';
                document.getElementById('cfgNedName').value = cfg.ned_name || 'Ned';
                document.getElementById('cfgLindseyName').value = cfg.lindsey_name || 'Lindsey';
                document.getElementById('cfgCaseSurname').value = cfg.case_surname || 'Pearson';
                document.getElementById('cfgCaseNumber').value = cfg.case_number || '';
                document.getElementById('cfgCourtName').value = cfg.court_name || '';
                document.getElementById('cfgPropertyAddress').value = cfg.property_address || '';
                document.getElementById('cfgDateRange').value = cfg.date_range || '';
                document.getElementById('cfgShareLink').textContent = cfg.share_token
                    ? ('https://reimbursements.bridgebox.ai/share/' + cfg.share_token + '/') : '(none set)';

                const spRows = document.getElementById('splitPercentRows');
                spRows.innerHTML = '';
                Object.entries(cfg.split_percent || {}).forEach(([cat, pct]) => addSplitRow(cat, pct));

                const exRows = document.getElementById('excludeBusinessRows');
                exRows.innerHTML = '';
                (cfg.exclude_business || []).forEach(v => addExcludeRow(v));
            } catch (e) { console.error(e); }
        }

        function addSplitRow(cat, pct) {
            const row = document.createElement('div');
            row.style.cssText = 'display:flex; gap:8px; margin-bottom:8px; align-items:center;';
            row.innerHTML = `
                <input class="sp-cat" placeholder="Category" value="${cat ? cat.replace(/"/g,'&quot;') : ''}" style="flex:2; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">
                <input class="sp-pct" type="number" min="0" max="100" placeholder="%" value="${pct !== undefined ? pct : ''}" style="width:90px; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">
                <button class="btn" style="padding:6px 10px; font-size:12px; background:#7f1d1d;" onclick="this.parentElement.remove()">Remove</button>
            `;
            document.getElementById('splitPercentRows').appendChild(row);
        }

        function addExcludeRow(vendor) {
            const row = document.createElement('div');
            row.style.cssText = 'display:flex; gap:8px; margin-bottom:8px; align-items:center;';
            row.innerHTML = `
                <input class="ex-vendor" placeholder="Vendor name or fragment" value="${vendor ? String(vendor).replace(/"/g,'&quot;') : ''}" style="flex:1; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">
                <button class="btn" style="padding:6px 10px; font-size:12px; background:#7f1d1d;" onclick="this.parentElement.remove()">Remove</button>
            `;
            document.getElementById('excludeBusinessRows').appendChild(row);
        }

        async function regenShareToken() {
            if (!confirm('Regenerate the share link? The old link stops working immediately.')) return;
            try {
                const res = await fetch('/api/regenerate_share_token', { method: 'POST' });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('cfgShareLink').textContent = 'https://reimbursements.bridgebox.ai/share/' + data.share_token + '/';
                    showToast('Share link regenerated.');
                } else {
                    showToast('Error: ' + (data.error || 'Failed'), true);
                }
            } catch (e) {
                showToast('Error: ' + e.message, true);
            }
        }

        async function saveSettings() {
            const split_percent = {};
            document.querySelectorAll('#splitPercentRows > div').forEach(row => {
                const cat = row.querySelector('.sp-cat').value.trim();
                const pct = row.querySelector('.sp-pct').value;
                if (cat && pct !== '') split_percent[cat] = Number(pct);
            });
            const exclude_business = Array.from(document.querySelectorAll('#excludeBusinessRows .ex-vendor'))
                .map(i => i.value.trim()).filter(Boolean);

            const payload = {
                form_email: document.getElementById('cfgFormEmail').value.trim(),
                gemini_api_key: document.getElementById('cfgGeminiKey').value.trim(),
                ned_name: document.getElementById('cfgNedName').value.trim() || 'Ned',
                lindsey_name: document.getElementById('cfgLindseyName').value.trim() || 'Lindsey',
                case_surname: document.getElementById('cfgCaseSurname').value.trim() || 'Pearson',
                case_number: document.getElementById('cfgCaseNumber').value.trim(),
                court_name: document.getElementById('cfgCourtName').value.trim(),
                property_address: document.getElementById('cfgPropertyAddress').value.trim(),
                date_range: document.getElementById('cfgDateRange').value.trim(),
                split_percent, exclude_business
            };

            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (res.ok) {
                    showToast('Settings saved. Click Regenerate Portal (from your computer) to apply case-info and split % changes.');
                } else {
                    showToast('Error: ' + (data.error || 'Failed'), true);
                }
            } catch (e) {
                showToast('Error: ' + e.message, true);
            }
        }

        document.addEventListener('DOMContentLoaded', loadSettings);"""
assert a.count(old_js_anchor) == 1, "admin.html settings-JS anchor not found once"
a = a.replace(old_js_anchor, new_js_block)

io.open(admin_path, 'w', encoding='utf-8').write(a)
print(f"admin.html: {orig_a_len} -> {len(a)} bytes OK")
