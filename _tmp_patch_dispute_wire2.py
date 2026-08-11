import sys, io

server_path, admin_path, portal_paths = sys.argv[1], sys.argv[2], sys.argv[3:]

# ================================================================== server.py
t = io.open(server_path, encoding='utf-8').read()
orig_t_len = len(t)

old_import = "from werkzeug.security import check_password_hash, generate_password_hash"
new_import = "from werkzeug.security import check_password_hash, generate_password_hash\nfrom werkzeug.utils import secure_filename"
assert t.count(old_import) == 1, "werkzeug import anchor not found once"
t = t.replace(old_import, new_import)

# 1. item_label, derived alongside item_id
old1 = "    item_id = data.get('Item_ID', '')"
new1 = "    item_id = data.get('Item_ID', '')\n    item_label = data.get('Item_Label') or item_id"
assert t.count(old1) == 1, "item_id anchor not found once"
t = t.replace(old1, new1)

# 2. always save an attached proof file, right after the reason line (inserted
#    before the AI/Gemini block so temp_path is available whether or not AI is on)
old2 = "    reason = data.get('Reason') or data.get('Payment_details') or data.get('Description') or data.get('Message') or ''"
new2 = old2 + """

    # Save any attached proof permanently -- independent of whether AI drafting is
    # configured below -- so a viewer's documentation is never silently dropped.
    # Saved under docs/proofs/ so it's reachable at /portal/proofs/<name> (admin
    # login) the same way the other portal documents are served.
    proof_filename = ''
    temp_path = None
    if file and file.filename:
        try:
            _, ext = os.path.splitext(file.filename)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            file.save(tmp.name)
            tmp.close()
            temp_path = tmp.name
            proofs_dir = os.path.join(app.config['DOCS_FOLDER'], 'proofs')
            if not os.path.exists(proofs_dir):
                os.makedirs(proofs_dir)
            import shutil
            safe_name = f"{int(datetime.datetime.now().timestamp())}_{secure_filename(file.filename)}"
            shutil.copy2(temp_path, os.path.join(proofs_dir, safe_name))
            proof_filename = safe_name
        except Exception as e:
            print(f"Failed to save proof file: {e}")"""
assert t.count(old2) == 1, "reason-line anchor not found once"
t = t.replace(old2, new2)

# 3. prompt: use item_label instead of item_id for readability
old3 = '''            prompt = f"The ex-spouse is submitting a form of type '{kind}' for item '{item_id}'. Her message is: '{reason}'. Please analyze this and provide a JSON response with two keys: 'summary' (a concise summary of her claim) and 'draft' (a polite, objective draft response for me to send back acknowledging this)."'''
new3 = '''            prompt = f"The ex-spouse is submitting a form of type '{kind}' for item '{item_label}'. Her message is: '{reason}'. Please analyze this and provide a JSON response with two keys: 'summary' (a concise summary of her claim) and 'draft' (a polite, objective draft response for me to send back acknowledging this)."'''
assert t.count(old3) == 1, "prompt anchor not found once"
t = t.replace(old3, new3)

# 4. stop double-saving/double-reading the upload stream inside the Gemini block --
#    reuse the temp_path already saved above instead
old4 = """            contents = [prompt]
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
                    shutil.copy2(temp.name, perm_path)"""
new4 = """            contents = [prompt]
            if temp_path:
                # Re-upload the already-saved proof copy to Gemini for analysis.
                uploaded = genai.upload_file(temp_path)
                contents.append(uploaded)"""
assert t.count(old4) == 1, "gemini file-block anchor not found once"
t = t.replace(old4, new4)

# 5. disputes.json entry: add item_label, use the permanently-saved proof filename
old5 = '''    dp['items'].append({
        "item": item_id,
        "status": "review",
        "date": dateStr,
        "her_claim": f"{ai_summary} (Raw: {reason})" if ai_summary != reason else reason,
        "response": f"[AI DRAFT] {ai_draft}" if ai_draft else "",
        "proof": file.filename if (file and file.filename) else ""
    })'''
new5 = '''    dp['items'].append({
        "item": item_id,
        "item_label": item_label,
        "status": "review",
        "date": dateStr,
        "her_claim": f"{ai_summary} (Raw: {reason})" if ai_summary != reason else reason,
        "response": f"[AI DRAFT] {ai_draft}" if ai_draft else "",
        "proof": proof_filename
    })'''
assert t.count(old5) == 1, "dp items append anchor not found once"
t = t.replace(old5, new5)

# 6. email subject: use item_label
old6 = '            "_subject": f"New Submission: {kind.upper()} for {item_id}",'
new6 = '            "_subject": f"New Submission: {kind.upper()} for {item_label}",'
assert t.count(old6) == 1, "email subject anchor not found once"
t = t.replace(old6, new6)

# 7. respond with JSON for AJAX (FormData) callers too, not only JSON-body callers
old7 = '''    if request.is_json:
        return jsonify({"success": "true"})
    else:
        next_url = data.get('_next', '/demo/?sent='+str(kind))
        return redirect(next_url)'''
new7 = '''    if request.is_json or data.get('_ajax'):
        return jsonify({"success": "true"})
    else:
        next_url = data.get('_next', '/demo/?sent='+str(kind))
        return redirect(next_url)'''
assert t.count(old7) == 1, "response-mode anchor not found once"
t = t.replace(old7, new7)

io.open(server_path, 'w', encoding='utf-8').write(t)
print(f"server.py: {orig_t_len} -> {len(t)} bytes OK")

# ================================================================== admin.html
a = io.open(admin_path, encoding='utf-8').read()
orig_a_len = len(a)

old_render_row = '''                html += `<tr>
                    <td><strong>${d.item || ''}</strong></td>
                    <td><span class="badge ${badgeClass}">${d.status || 'review'}</span></td>
                    <td>${d.date || ''}</td>
                    <td><div style="font-size:13px; max-width:200px; overflow:hidden; text-overflow:ellipsis;" title="${(d.her_claim||'').replace(/"/g, '&quot;')}">${d.her_claim || ''}</div></td>
                    <td><div style="font-size:13px; max-width:200px; overflow:hidden; text-overflow:ellipsis;" title="${(d.response||'').replace(/"/g, '&quot;')}">${d.response || ''}</div></td>
                    <td>
                        <button class="btn" style="padding: 4px 8px; font-size:12px;" onclick="resolveDispute(${idx})">Respond / Resolve</button>
                    </td>
                </tr>`;'''
new_render_row = '''                html += `<tr>
                    <td><strong>${(d.item_label || d.item || '').replace(/</g,'&lt;')}</strong>${d.proof ? ' &middot; <a href="/portal/proofs/'+encodeURIComponent(d.proof)+'" target="_blank" style="font-size:12px">view proof</a>' : ''}</td>
                    <td><span class="badge ${badgeClass}">${d.status || 'review'}</span></td>
                    <td>${d.date || ''}</td>
                    <td><div style="font-size:13px; max-width:200px; overflow:hidden; text-overflow:ellipsis;" title="${(d.her_claim||'').replace(/"/g, '&quot;')}">${d.her_claim || ''}</div></td>
                    <td><div style="font-size:13px; max-width:200px; overflow:hidden; text-overflow:ellipsis;" title="${(d.response||'').replace(/"/g, '&quot;')}">${d.response || ''}</div></td>
                    <td>
                        <button class="btn" style="padding: 4px 8px; font-size:12px;" onclick="resolveDispute(${idx})">Respond / Resolve</button>
                    </td>
                </tr>`;'''
assert a.count(old_render_row) == 1, "admin.html renderDisputes row anchor not found once"
a = a.replace(old_render_row, new_render_row)

old_dm_item = '''            document.getElementById('dmItem').textContent = 'Item: ' + (d.item || 'Unknown');'''
new_dm_item = '''            document.getElementById('dmItem').textContent = 'Item: ' + (d.item_label || d.item || 'Unknown');'''
assert a.count(old_dm_item) == 1, "admin.html dmItem anchor not found once"
a = a.replace(old_dm_item, new_dm_item)

io.open(admin_path, 'w', encoding='utf-8').write(a)
print(f"admin.html: {orig_a_len} -> {len(a)} bytes OK")

# ================================================================== portal files
HTML_OLD = "  +'<input type=\"hidden\" name=\"Type\" value=\"'+kind+'\">'"
HTML_NEW = "  +'<input type=\"hidden\" name=\"Type\" value=\"'+kind+'\">'\n  +(item?('<input type=\"hidden\" name=\"Item_ID\" value=\"'+esc(item.id)+'\"><input type=\"hidden\" name=\"Item_Label\" value=\"'+esc(ref)+'\">'):'')"

JS_OLD = '''  // ---- dispute on a specific charge → email Ned GitHub Approve/Deny decision links ----
  if(kind==='dispute' && item){
   ev.preventDefault();
   var reason=((f.querySelector('[name="Reason"]')||{}).value)||'';
   var nm=((f.querySelector('[name="Your_name"]')||{}).value)||'';
   var lbl=itemRef(item);
   function issueURL(action){
    var title='[dispute] '+action+' — '+lbl;
    var body='id: '+item.id+'\\nlabel: '+lbl+'\\naction: '+action+'\\n\\nSubmitting this issue will '+(action==='approve'?'REMOVE this charge from the reimbursement.':'KEEP this charge (mark it reviewed).')+' Filed via the portal Dispute button.';
    return 'https://github.com/'+GH_REPO+'/issues/new?labels=dispute&title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body);
   }
   btn.disabled=true; btn.textContent='Sending…'; msg.style.display='none';
   var payload={_subject:'Dispute filed — '+lbl,_template:'table',Charge:lbl,Reason:reason,From:(nm||'(not given)'),
     'APPROVE — remove this charge':issueURL('approve'),'DENY — keep this charge':issueURL('deny'),
     _note:'Open a link, then click the green Submit button on GitHub. Approve auto-removes the charge; the portal updates within ~1 minute.'};
   fetch(FS_AJAX,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(payload)})
    .then(function(r){return r.json();})
    .then(function(j){
      if(String(j.success)==='true'){ f.reset(); msg.className='formmsg ok';
        msg.textContent='✓ Dispute sent to Ned. He’ll review it — if approved, this charge comes off automatically.';
        if(file){ try{var fd=new FormData();fd.append('_subject','Dispute proof — '+lbl);fd.append('_captcha','false');fd.append('Charge',lbl);fd.append('attachment',file);fetch(FS_STD,{method:'POST',body:fd});}catch(e){} }
      } else { msg.className='formmsg err'; msg.textContent='Could not send: '+(j.message||'please try again')+'.'; }
      btn.disabled=false; btn.textContent='Send to Ned';})
    .catch(function(){ msg.className='formmsg err'; msg.textContent='Network problem — please try again.'; btn.disabled=false; btn.textContent='Send to Ned';});
   return;
  }'''

JS_NEW = '''  // ---- dispute on a specific charge → tracked directly in Ned's Admin dashboard ----
  if(kind==='dispute' && item){
   ev.preventDefault();
   var reason=((f.querySelector('[name="Reason"]')||{}).value)||'';
   var nm=((f.querySelector('[name="Your_name"]')||{}).value)||'';
   var lbl=itemRef(item);
   btn.disabled=true; btn.textContent='Sending…'; msg.style.display='none';
   var fd=new FormData();
   fd.append('Type','dispute');
   fd.append('Item_ID', item.id);
   fd.append('Item_Label', lbl);
   fd.append('Reason', reason);
   fd.append('Your_name', nm);
   fd.append('_ajax','1');
   if(file) fd.append('attachment', file);
   fetch('/api/submit',{method:'POST',body:fd})
    .then(function(r){return r.json();})
    .then(function(j){
      if(String(j.success)==='true'){ f.reset(); msg.className='formmsg ok';
        msg.textContent='✓ Dispute filed — it’s now tracked in Ned’s dashboard for review, and he’ll be notified by email. If he accepts it, this charge is credited automatically.';
      } else { msg.className='formmsg err'; msg.textContent='Could not send: '+(j.message||'please try again')+'.'; }
      btn.disabled=false; btn.textContent='Send to Ned';})
    .catch(function(){ msg.className='formmsg err'; msg.textContent='Network problem — please try again.'; btn.disabled=false; btn.textContent='Send to Ned';});
   return;
  }'''

for p in portal_paths:
    pt = io.open(p, encoding='utf-8').read()
    orig_pt_len = len(pt)

    assert pt.count(HTML_OLD) == 1, f"{p}: hidden-Type-input anchor not found once"
    pt = pt.replace(HTML_OLD, HTML_NEW)

    assert pt.count(JS_OLD) == 1, f"{p}: dispute JS anchor not found once"
    pt = pt.replace(JS_OLD, JS_NEW)

    io.open(p, 'w', encoding='utf-8').write(pt)
    print(f"{p}: {orig_pt_len} -> {len(pt)} bytes OK")
