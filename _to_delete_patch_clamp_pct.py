import sys, io

admin_path = sys.argv[1]
a = io.open(admin_path, encoding='utf-8').read()
orig_len = len(a)

# 1. addSplitRow: select existing value on focus (so typing replaces instead of
#    appending to what's already there) and clamp to 0-100 on blur. This is the
#    fix for "changed percentage of storage and it threw an error" -- clicking
#    into the box and typing without clearing the old value first (e.g. "50" ->
#    "150") used to sail past the browser's min/max (those aren't enforced on
#    typed input, only on the spinner arrows) and get rejected by the server.
old_sp_pct = '''                <input class="sp-pct" type="number" min="0" max="100" placeholder="%" value="${pct !== undefined ? pct : ''}" style="width:90px; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);">'''
new_sp_pct = '''                <input class="sp-pct" type="number" min="0" max="100" placeholder="%" value="${pct !== undefined ? pct : ''}" style="width:90px; padding:8px; border-radius:6px; border:1px solid var(--border); background:rgba(255,255,255,0.03); color:var(--text-main);" onfocus="this.select()" onblur="if(this.value!=='')this.value=Math.max(0,Math.min(100,Number(this.value)||0))">'''
assert a.count(old_sp_pct) == 1, "sp-pct input anchor not found once"
a = a.replace(old_sp_pct, new_sp_pct)

# 2. saveSettings(): clamp again right before building the payload, as a backstop,
#    so a stray out-of-range value (e.g. pasted in) can never again produce the
#    generic "Error: Split % for X must be between 0 and 100" toast -- it's just
#    silently clamped to a valid number instead, same as the blur handler does.
old_loop = '''            document.querySelectorAll('#splitPercentRows > div').forEach(row => {
                const cat = row.querySelector('.sp-cat').value.trim();
                const pct = row.querySelector('.sp-pct').value;
                if (cat && pct !== '') split_percent[cat] = Number(pct);
            });'''
new_loop = '''            document.querySelectorAll('#splitPercentRows > div').forEach(row => {
                const cat = row.querySelector('.sp-cat').value.trim();
                const pctRaw = row.querySelector('.sp-pct').value;
                if (cat && pctRaw !== '') split_percent[cat] = Math.max(0, Math.min(100, Number(pctRaw) || 0));
            });'''
assert a.count(old_loop) == 1, "saveSettings split_percent loop anchor not found once"
a = a.replace(old_loop, new_loop)

io.open(admin_path, 'w', encoding='utf-8').write(a)
print(f"admin.html: {orig_len} -> {len(a)} bytes OK")
