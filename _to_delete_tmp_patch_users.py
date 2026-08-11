import sys, io

server_path, admin_path, users_path = sys.argv[1], sys.argv[2], sys.argv[3]

# ---------------------------------------------------------------- server.py
t = io.open(server_path, encoding='utf-8').read()
orig_len = len(t)

old_import = "from werkzeug.security import check_password_hash"
new_import = "from werkzeug.security import check_password_hash, generate_password_hash"
assert t.count(old_import) == 1, "import anchor not found once"
t = t.replace(old_import, new_import)

old_loader = """def load_users():
    path = os.path.join(os.path.dirname(__file__), 'users.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}"""
new_loader = """def load_users():
    path = os.path.join(os.path.dirname(__file__), 'users.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    path = os.path.join(os.path.dirname(__file__), 'users.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

# Roles that can be created or assigned through /api/users. 'admin' is deliberately
# excluded -- there is no code path, via this API, that can ever mint a second admin
# account. Only the account already in users.json as role "admin" can approve/deny
# disputes (enforced in /api/disputes below); every account created here is
# view-and-dispute-only, no matter what a client sends.
ALLOWED_CREATE_ROLES = {'viewer'}"""
assert t.count(old_loader) == 1, "load_users anchor not found once"
t = t.replace(old_loader, new_loader)

old_anchor = "@app.route('/api/submit', methods=['POST'])"
new_block = """@app.route('/api/users', methods=['GET'])
@login_required
def api_users_list():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    users = load_users()
    return jsonify({"users": [{"username": u, "role": d.get('role')} for u, d in users.items()]})

@app.route('/api/users', methods=['POST'])
@login_required
def api_users_create():
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    role = data.get('role') or 'viewer'
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if role not in ALLOWED_CREATE_ROLES:
        return jsonify({"error": "Only view-only accounts can be created here"}), 400
    users = load_users()
    if username in users:
        return jsonify({"error": "That username already exists"}), 400
    users[username] = {"password_hash": generate_password_hash(password), "role": role}
    save_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<username>', methods=['PATCH'])
@login_required
def api_users_update(username):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    users = load_users()
    if username not in users:
        return jsonify({"error": "Not found"}), 404
    if users[username].get('role') == 'admin':
        return jsonify({"error": "The admin account can't be changed here"}), 400
    data = request.json or {}
    if data.get('password'):
        if len(data['password']) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        users[username]['password_hash'] = generate_password_hash(data['password'])
    if data.get('role'):
        if data['role'] not in ALLOWED_CREATE_ROLES:
            return jsonify({"error": "Only the view-only role is allowed here"}), 400
        users[username]['role'] = data['role']
    save_users(users)
    return jsonify({"success": True})

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
def api_users_delete(username):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized"}), 403
    users = load_users()
    if username not in users:
        return jsonify({"error": "Not found"}), 404
    if users[username].get('role') == 'admin':
        return jsonify({"error": "The admin account can't be removed"}), 400
    del users[username]
    save_users(users)
    return jsonify({"success": True})

@app.route('/api/submit', methods=['POST'])"""
assert t.count(old_anchor) == 1, "submit-route anchor not found once"
t = t.replace(old_anchor, new_block)

io.open(server_path, 'w', encoding='utf-8').write(t)
print(f"server.py: {orig_len} -> {len(t)} bytes OK")

# ---------------------------------------------------------------- admin.html
a = io.open(admin_path, encoding='utf-8').read()
orig_a_len = len(a)

old_section = """    </div>

    <!-- Dispute Resolution Modal -->"""
new_section = """
        <div style="margin-top: 40px; display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px;">
            <div>
                <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 8px;">User Accounts</h2>
                <p style="color: var(--text-muted);">Only accounts you create here can sign in. Every account you add is view + dispute only — it can never approve or deny a charge. Only your own admin login can do that.</p>
            </div>
            <div>
                <button class="btn" onclick="openAddUserModal()">+ Add User</button>
            </div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Username / Email</th>
                        <th>Role</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="usersBody">
                    <tr><td colspan="3" style="text-align:center; color:var(--text-muted);">Loading users...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Add / Reset User Modal -->
    <div id="userModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:2000; align-items:center; justify-content:center;">
        <div style="background:#fff; width:440px; max-width:90%; border-radius:12px; padding:24px; box-shadow:0 20px 40px rgba(0,0,0,0.2); color:#1e293b;">
            <h2 style="margin-top:0; margin-bottom:8px;" id="umTitle">Add User</h2>
            <p style="font-size:13px; color:#64748b; margin-bottom:16px;">This account can view the portal and file disputes. It can never approve or deny a charge — only your admin login can.</p>

            <div style="margin-bottom:14px;">
                <label style="display:block; font-size:12px; font-weight:600; margin-bottom:4px;">Username or email</label>
                <input id="umUsername" type="text" style="width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e1;">
            </div>
            <div style="margin-bottom:20px;">
                <label style="display:block; font-size:12px; font-weight:600; margin-bottom:4px;" id="umPwLabel">Password (min 8 characters)</label>
                <input id="umPassword" type="text" style="width:100%; padding:8px; border-radius:6px; border:1px solid #cbd5e1;">
            </div>

            <div style="display:flex; justify-content:flex-end; gap:12px;">
                <button class="btn" style="background:#fff; color:#475569; border:1px solid #cbd5e1;" onclick="closeUserModal()">Cancel</button>
                <button class="btn btn-success" onclick="saveUserModal()">Save</button>
            </div>
        </div>
    </div>

    <!-- Dispute Resolution Modal -->"""
assert a.count(old_section) == 1, "admin.html section anchor not found once"
a = a.replace(old_section, new_section)

old_js_anchor = "        // Load disputes on init\n        document.addEventListener('DOMContentLoaded', loadDisputes);"
new_js_block = """        // Load disputes on init
        document.addEventListener('DOMContentLoaded', loadDisputes);

        // ---- User accounts ----
        let allUsers = [];
        let editingUsername = null;

        async function loadUsers() {
            try {
                const res = await fetch('/api/users');
                const data = await res.json();
                allUsers = data.users || [];
                renderUsers();
            } catch (e) { console.error(e); }
        }

        function renderUsers() {
            const tbody = document.getElementById('usersBody');
            if (!allUsers.length) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">No accounts yet.</td></tr>';
                return;
            }
            let html = '';
            allUsers.forEach(u => {
                const isAdmin = u.role === 'admin';
                html += `<tr>
                    <td><strong>${u.username}</strong></td>
                    <td><span class="badge ${isAdmin ? 'badge-paid' : 'badge-pending'}">${isAdmin ? 'Admin (you)' : 'View only'}</span></td>
                    <td>
                        ${isAdmin ? '<span style="color:var(--text-muted); font-size:13px;">—</span>' : `
                            <button class="btn" style="padding:4px 8px; font-size:12px;" onclick="openResetPassword('${u.username}')">Reset password</button>
                            <button class="btn" style="padding:4px 8px; font-size:12px; background:#7f1d1d;" onclick="deleteUser('${u.username}')">Remove</button>
                        `}
                    </td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }

        function openAddUserModal() {
            editingUsername = null;
            document.getElementById('umTitle').textContent = 'Add User';
            document.getElementById('umPwLabel').textContent = 'Password (min 8 characters)';
            document.getElementById('umUsername').value = '';
            document.getElementById('umUsername').disabled = false;
            document.getElementById('umPassword').value = '';
            document.getElementById('userModal').style.display = 'flex';
        }

        function openResetPassword(username) {
            editingUsername = username;
            document.getElementById('umTitle').textContent = 'Reset password — ' + username;
            document.getElementById('umPwLabel').textContent = 'New password (min 8 characters)';
            document.getElementById('umUsername').value = username;
            document.getElementById('umUsername').disabled = true;
            document.getElementById('umPassword').value = '';
            document.getElementById('userModal').style.display = 'flex';
        }

        function closeUserModal() {
            document.getElementById('userModal').style.display = 'none';
        }

        async function saveUserModal() {
            const username = document.getElementById('umUsername').value.trim();
            const password = document.getElementById('umPassword').value;
            if (!username) { showToast('Enter a username or email.', true); return; }
            if (!password || password.length < 8) { showToast('Password must be at least 8 characters.', true); return; }

            try {
                let res;
                if (editingUsername) {
                    res = await fetch('/api/users/' + encodeURIComponent(editingUsername), {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ password })
                    });
                } else {
                    res = await fetch('/api/users', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, password, role: 'viewer' })
                    });
                }
                const data = await res.json();
                if (res.ok) {
                    showToast(editingUsername ? 'Password updated.' : 'Account created.');
                    closeUserModal();
                    loadUsers();
                } else {
                    showToast('Error: ' + (data.error || 'Failed'), true);
                }
            } catch (e) {
                showToast('Error: ' + e.message, true);
            }
        }

        async function deleteUser(username) {
            if (!confirm('Remove ' + username + '\\'s access? They will no longer be able to log in.')) return;
            try {
                const res = await fetch('/api/users/' + encodeURIComponent(username), { method: 'DELETE' });
                const data = await res.json();
                if (res.ok) {
                    showToast('Account removed.');
                    loadUsers();
                } else {
                    showToast('Error: ' + (data.error || 'Failed'), true);
                }
            } catch (e) {
                showToast('Error: ' + e.message, true);
            }
        }

        document.addEventListener('DOMContentLoaded', loadUsers);"""
assert a.count(old_js_anchor) == 1, "admin.html JS anchor not found once"
a = a.replace(old_js_anchor, new_js_block)

io.open(admin_path, 'w', encoding='utf-8').write(a)
print(f"admin.html: {orig_a_len} -> {len(a)} bytes OK")

# ---------------------------------------------------------------- users.json
users = __import__('json').load(io.open(users_path, encoding='utf-8'))
if 'viewer' in users:
    del users['viewer']
    io.open(users_path, 'w', encoding='utf-8').write(__import__('json').dumps(users, indent=2))
    print("users.json: removed shared 'viewer' account")
else:
    print("users.json: no 'viewer' account present, nothing to remove")
