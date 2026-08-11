import sys, io

paths = sys.argv[1:]
assert paths, "pass at least one file path"

CSS_OLD = ".emailbtn:hover{background:#f0fbf4}"
CSS_NEW = CSS_OLD + """
.emlmodal{display:none;position:fixed;inset:0;background:rgba(10,14,30,.55);z-index:9999;align-items:center;justify-content:center;padding:20px}
.emlmodal.show{display:flex}
.emlbox{background:#fff;color:#1c2340;border-radius:14px;padding:26px 28px;max-width:460px;width:100%;box-shadow:0 24px 60px rgba(0,0,0,.35)}
.emlbox h3{font-family:'Source Serif 4',Georgia,serif;font-size:1.2rem;margin-bottom:6px;color:var(--navy)}
.emlbox p.sub{font-size:.85rem;color:var(--muted);margin-bottom:16px}
.emlbox label{display:block;font-size:.78rem;font-weight:700;color:var(--navy2);margin:14px 0 5px;text-transform:uppercase;letter-spacing:.04em}
.emlbox input[type=text]{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:8px;font-size:.92rem;box-sizing:border-box}
.emlbox .radiorow{display:flex;flex-direction:column;gap:8px;font-size:.86rem}
.emlbox .radiorow label{display:flex;align-items:center;gap:8px;font-weight:500;text-transform:none;letter-spacing:0;color:#2b3444;margin:0}
.emlbtns{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}
.emlbtns button{padding:10px 18px;border-radius:9px;border:none;font-weight:700;cursor:pointer;font-size:.88rem}
.emlcancel{background:#eef1f7;color:#42506b}
.emlsend{background:var(--green);color:#fff}
.emlerr{color:#b3261e;font-size:.8rem;margin-top:6px;display:none}"""

ANCHOR_OLD = '<a id="emailbtn" class="emailbtn" href="#">&#9993;&nbsp;Email this out</a>'
ANCHOR_NEW = '<a id="emailbtn" class="emailbtn" href="#" onclick="openEmailModal();return false;">&#9993;&nbsp;Email this out</a>'

FOOTER_OLD = '<footer>Prepared from source documents &middot; Reimbursement Manager</footer></div>'
FOOTER_NEW = FOOTER_OLD + """
<div class="emlmodal" id="emailModal">
 <div class="emlbox">
  <h3>Email this out</h3>
  <p class="sub">Send the reimbursement package link to whoever needs it &mdash; separate multiple addresses with a comma.</p>
  <label for="emlTo">To</label>
  <input type="text" id="emlTo" placeholder="lindsey@email.com, lawyer@firm.com">
  <label>Link to send</label>
  <div class="radiorow">
   <label><input type="radio" name="emlLink" value="login" checked> Portal login (recommended &mdash; they sign in with the account you created)</label>
   <label id="emlShareOpt" style="display:none"><input type="radio" name="emlLink" value="share"> No-login share link</label>
  </div>
  <div class="emlerr" id="emlErr"></div>
  <div class="emlbtns">
   <button class="emlcancel" type="button" onclick="closeEmailModal()">Cancel</button>
   <button class="emlsend" type="button" onclick="doSendEmail()">Open in my email app</button>
  </div>
 </div>
</div>"""

JS_OLD = """(function(){
 var link='https://nedpearson.github.io/Reimbursements/';
 var addTotal=(typeof ADD!=='undefined'&&ADD&&ADD.grand_total)?ADD.grand_total:0;
 var paidT=(typeof SETTLED!=='undefined'&&SETTLED&&SETTLED.paid_total)?SETTLED.paid_total:0;
 var due=paidT?Math.max(0,Math.round((D.net-paidT)*100)/100):D.net;
 var subj='Expense Reimbursement — Pearson ('+money(due)+')';
 var body='The complete expense reimbursement package is here:\\n'+link+'\\n\\n'
  +((due!==D.net)?('Balance still due: '+money(due)+'  (original '+money(D.net)+' less '+money(paidT)+' already paid)\\n'):('Net amount due: '+money(D.net)+'\\n'))
  +(addTotal?('Additional amounts paid on your behalf (vehicle, insurance, health premium, direct payments): '+money(addTotal)+'\\n'):'')
  +'\\nOn that page: every charge by category, each line linked to the actual bill, plus the itemized statement, cover letter, and full proof pack — all viewable in the browser, nothing to download. If you believe any charge is wrong, use the Dispute button on that line and attach your proof.\\n\\nNed';
 var el=document.getElementById('emailbtn');
 if(el) el.href='mailto:?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(body);
})();"""

JS_NEW = """var EMAILLINKS={login:location.origin+'/login',share:''};
(function(){ // best-effort: pick up the no-login share link if we're logged in as admin (fails silently otherwise)
 fetch('/api/config').then(function(r){return r.ok?r.json():null;}).then(function(cfg){
   if(cfg&&cfg.share_token){ EMAILLINKS.share=location.origin+'/share/'+cfg.share_token+'/';
     var opt=document.getElementById('emlShareOpt'); if(opt) opt.style.display='flex'; }
 }).catch(function(){});
})();
function emailBody(link){
 var addTotal=(typeof ADD!=='undefined'&&ADD&&ADD.grand_total)?ADD.grand_total:0;
 var paidT=(typeof SETTLED!=='undefined'&&SETTLED&&SETTLED.paid_total)?SETTLED.paid_total:0;
 var due=paidT?Math.max(0,Math.round((D.net-paidT)*100)/100):D.net;
 return {
  subj:'Expense Reimbursement — Pearson ('+money(due)+')',
  body:'The complete expense reimbursement package is here:\\n'+link+'\\n\\n'
   +((due!==D.net)?('Balance still due: '+money(due)+'  (original '+money(D.net)+' less '+money(paidT)+' already paid)\\n'):('Net amount due: '+money(D.net)+'\\n'))
   +(addTotal?('Additional amounts paid on your behalf (vehicle, insurance, health premium, direct payments): '+money(addTotal)+'\\n'):'')
   +'\\nOn that page: every charge by category, each line linked to the actual bill, plus the itemized statement, cover letter, and full proof pack — all viewable in the browser, nothing to download. If you believe any charge is wrong, use the Dispute button on that line and attach your proof.\\n\\nNed'
 };
}
function openEmailModal(){document.getElementById('emlErr').style.display='none';document.getElementById('emlTo').value='';document.getElementById('emailModal').classList.add('show');document.getElementById('emlTo').focus();}
function closeEmailModal(){document.getElementById('emailModal').classList.remove('show');}
function doSendEmail(){
 var to=document.getElementById('emlTo').value.trim();
 if(!to){var e=document.getElementById('emlErr');e.textContent='Enter at least one email address.';e.style.display='block';return;}
 var toClean=to.split(',').map(function(s){return s.trim();}).filter(Boolean).join(',');
 var which=(document.querySelector('input[name="emlLink"]:checked')||{}).value||'login';
 var link=(which==='share'&&EMAILLINKS.share)?EMAILLINKS.share:EMAILLINKS.login;
 var eb=emailBody(link);
 window.location.href='mailto:'+toClean+'?subject='+encodeURIComponent(eb.subj)+'&body='+encodeURIComponent(eb.body);
 closeEmailModal();
}"""

for path in paths:
    t = io.open(path, encoding='utf-8').read()
    orig_len = len(t)

    assert t.count(CSS_OLD) == 1, f"{path}: CSS anchor not found once"
    t = t.replace(CSS_OLD, CSS_NEW)

    assert t.count(ANCHOR_OLD) == 1, f"{path}: anchor not found once"
    t = t.replace(ANCHOR_OLD, ANCHOR_NEW)

    assert t.count(FOOTER_OLD) == 1, f"{path}: footer anchor not found once"
    t = t.replace(FOOTER_OLD, FOOTER_NEW)

    assert t.count(JS_OLD) == 1, f"{path}: JS anchor not found once"
    t = t.replace(JS_OLD, JS_NEW)

    io.open(path, 'w', encoding='utf-8').write(t)
    print(f"{path}: {orig_len} -> {len(t)} bytes OK")
