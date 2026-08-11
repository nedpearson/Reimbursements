import sys, io

paths = sys.argv[1:]
assert paths, "pass at least one file path"

HTML_OLD = """  <label for="emlTo">To</label>
  <input type="text" id="emlTo" placeholder="lindsey@email.com, lawyer@firm.com">
  <label>Link to send</label>"""
HTML_NEW = """  <label for="emlTo">To</label>
  <input type="text" id="emlTo" placeholder="lindsey@email.com, lawyer@firm.com">
  <label for="emlAmount">Amount to state in this email</label>
  <input type="text" id="emlAmount" inputmode="decimal" placeholder="e.g. 45000 &mdash; never auto-filled, type the figure for this email">
  <label>Link to send</label>"""

JS_OLD = """function emailBody(link){
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
JS_NEW = """function emailBody(link,statedAmount){
 var addTotal=(typeof ADD!=='undefined'&&ADD&&ADD.grand_total)?ADD.grand_total:0;
 return {
  subj:'Expense Reimbursement — Pearson ('+money(statedAmount)+')',
  body:'The complete expense reimbursement package is here:\\n'+link+'\\n\\n'
   +'Amount due: '+money(statedAmount)+'\\n'
   +(addTotal?('Additional amounts paid on your behalf (vehicle, insurance, health premium, direct payments): '+money(addTotal)+'\\n'):'')
   +'\\nOn that page: every charge by category, each line linked to the actual bill, plus the itemized statement, cover letter, and full proof pack — all viewable in the browser, nothing to download. If you believe any charge is wrong, use the Dispute button on that line and attach your proof.\\n\\nNed'
 };
}
function openEmailModal(){document.getElementById('emlErr').style.display='none';document.getElementById('emlTo').value='';document.getElementById('emlAmount').value='';document.getElementById('emailModal').classList.add('show');document.getElementById('emlTo').focus();}
function closeEmailModal(){document.getElementById('emailModal').classList.remove('show');}
function doSendEmail(){
 var e=document.getElementById('emlErr');
 var to=document.getElementById('emlTo').value.trim();
 if(!to){e.textContent='Enter at least one email address.';e.style.display='block';return;}
 // The amount is never auto-filled from the calculated net due -- you type the figure
 // for this specific email every time, so a full/whole-claim number can never go out
 // by default or by accident.
 var amtRaw=document.getElementById('emlAmount').value.trim().replace(/[^0-9.]/g,'');
 var amt=parseFloat(amtRaw);
 if(!amtRaw||isNaN(amt)||amt<=0){e.textContent='Enter the amount to state in this email.';e.style.display='block';return;}
 e.style.display='none';
 var toClean=to.split(',').map(function(s){return s.trim();}).filter(Boolean).join(',');
 var which=(document.querySelector('input[name="emlLink"]:checked')||{}).value||'login';
 var link=(which==='share'&&EMAILLINKS.share)?EMAILLINKS.share:EMAILLINKS.login;
 var eb=emailBody(link,amt);
 window.location.href='mailto:'+toClean+'?subject='+encodeURIComponent(eb.subj)+'&body='+encodeURIComponent(eb.body);
 closeEmailModal();
}"""

for path in paths:
    t = io.open(path, encoding='utf-8').read()
    orig_len = len(t)

    assert t.count(HTML_OLD) == 1, f"{path}: HTML anchor not found once"
    t = t.replace(HTML_OLD, HTML_NEW)

    assert t.count(JS_OLD) == 1, f"{path}: JS anchor not found once"
    t = t.replace(JS_OLD, JS_NEW)

    io.open(path, 'w', encoding='utf-8').write(t)
    print(f"{path}: {orig_len} -> {len(t)} bytes OK")
