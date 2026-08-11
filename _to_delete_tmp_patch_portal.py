import sys, io

path = sys.argv[1]
with io.open(path, encoding='utf-8') as f:
    t = f.read()

orig_len = len(t)

# 1. CSS: add drill-down styles after .sd .close:hover
old_css = """.sd .close{float:right;color:var(--muted);cursor:pointer;font-size:.78rem;font-weight:600}
.sd .close:hover{color:var(--navy)}"""
new_css = """.sd .close{float:right;color:var(--muted);cursor:pointer;font-size:.78rem;font-weight:600}
.sd .close:hover{color:var(--navy)}
.sd tr.catrow{cursor:pointer}
.sd tr.catrow:hover td{background:rgba(127,127,127,.09)}
.sd tr.catrow .chev{display:inline-block;margin-right:6px;font-size:.72rem}
.sd tr.catrow.open .chev{transform:rotate(90deg);color:var(--navy2)}
.sd tr.catdrill{display:none}
.sd tr.catrow.open+tr.catdrill{display:table-row}
.sd tr.catdrill>td{padding:10px 4px 14px}
.sd .subtbl{font-size:.78rem;box-shadow:none}
.sd .subtbl th{font-size:.62rem;padding:7px 10px}
.sd .subtbl td{padding:7px 10px}"""
assert t.count(old_css) == 1, f"CSS anchor not found exactly once in {path}"
t = t.replace(old_css, new_css)

# 2. catRows(): make each category row expandable to show its underlying charges
old_catrows = """ function catRows(showPct){return D.cats.map(function(c){return '<tr><td>'+c.name+'</td><td class="r">'+money(c.billed)+'</td>'+(showPct?'<td class="r">'+c.basis+'</td>':'')+'<td class="r"><b>'+money(c.owed)+'</b></td></tr>';}).join('');}"""
new_catrows = """ function catRows(showPct){return D.cats.map(function(c){
  var items=D.items.filter(function(i){return i.cat===c.name;});
  var colspan=showPct?4:3;
  var head='<tr class="catrow"><td><span class="chev">▶</span> '+c.name+'</td><td class="r">'+money(c.billed)+'</td>'+(showPct?'<td class="r">'+c.basis+'</td>':'')+'<td class="r"><b>'+money(c.owed)+'</b></td></tr>';
  var body='<tr class="catdrill"><td colspan="'+colspan+'"><table class="subtbl"><thead><tr><th>Ref #</th><th>Date</th><th>Vendor</th><th>Description</th><th class="r">Bill amount</th><th class="r">Her share</th><th>Source of truth</th><th></th></tr></thead><tbody>'+groupedRows(items)+'</tbody></table></td></tr>';
  return head+body;
 }).join('');}"""
assert t.count(old_catrows) == 1, f"catRows anchor not found exactly once in {path}"
t = t.replace(old_catrows, new_catrows)

# 3. show(): wire up click-to-expand on the new .catrow rows
old_show = """  cur=k;det.innerHTML='<div class="sd"><span class="close">✕ close</span>'+detail(k)+'</div>';
  strip.querySelectorAll('.stat').forEach(function(s){s.classList.toggle('active',s.getAttribute('data-k')===k);});
  det.querySelector('.close').onclick=function(){show(k);};
  det.scrollIntoView({behavior:'smooth',block:'nearest'});"""
new_show = """  cur=k;det.innerHTML='<div class="sd"><span class="close">✕ close</span>'+detail(k)+'</div>';
  strip.querySelectorAll('.stat').forEach(function(s){s.classList.toggle('active',s.getAttribute('data-k')===k);});
  det.querySelector('.close').onclick=function(){show(k);};
  det.querySelectorAll('.catrow').forEach(function(row){row.onclick=function(){row.classList.toggle('open');};});
  det.scrollIntoView({behavior:'smooth',block:'nearest'});"""
assert t.count(old_show) == 1, f"show() anchor not found exactly once in {path}"
t = t.replace(old_show, new_show)

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(t)

print(f"{path}: {orig_len} -> {len(t)} bytes OK")
