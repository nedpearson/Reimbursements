#!/usr/bin/env python3
r"""
Reimbursement Manager — desktop app.
Add expenses, import bills/Venmo statements, generate & export all documents.
Lives at C:\dev\github\personal\Reimbursements (github.com/nedpearson/Reimbursements).
"""
import os, sys, json, shutil, threading, queue, traceback, subprocess, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,HERE)
CFG_PATH=os.path.join(HERE,'config.json')
OUTDIR=os.path.join(HERE,'output')
NAVY='#1B2E52'; NAVY2='#28457c'; GREEN='#217a43'; BG='#EDF0F6'; CARD='#FFFFFF'; LINE='#DBE0EC'; MUTED='#5b6472'; GOLD='#8a6100'; RED='#9a3324'

def load_cfg(): return json.load(open(CFG_PATH))
def save_cfg(c):
    from safewrite import write_via_temp
    write_via_temp(CFG_PATH,lambda tmp: json.dump(c,open(tmp,'w'),indent=2))
def open_path(p):
    try:
        if sys.platform.startswith('win'): os.startfile(p)
        elif sys.platform=='darwin': subprocess.run(['open',p])
        else: subprocess.run(['xdg-open',p])
    except Exception as e: messagebox.showerror("Open failed",str(e))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reimbursement Manager"); self.configure(bg=BG)
        self.geometry("960x760"); self.minsize(860,660)
        try: self.iconbitmap(os.path.join(HERE,'assets','icon.ico'))
        except Exception: pass
        self._setup_style()
        self.cfg=load_cfg(); self.q=queue.Queue(); self.result=None
        self._build(); self.after(120,self._drain)

    def _setup_style(self):
        # each styling call is best-effort — a theme quirk must never stop the app from opening
        try:
            st=ttk.Style(self)
            try: st.theme_use('clam')
            except Exception: pass
            def _c(*a,**k):
                try: st.configure(*a,**k)
                except Exception: pass
            def _m(*a,**k):
                try: st.map(*a,**k)
                except Exception: pass
            _c('.',font=('Segoe UI',10))
            _c('TNotebook',background=BG,borderwidth=0,tabmargins=(10,8,10,0))
            _c('TNotebook.Tab',font=('Segoe UI',10,'bold'),padding=(18,9),background='#DDE3EF',foreground=NAVY,borderwidth=0)
            _m('TNotebook.Tab',background=[('selected',CARD)],foreground=[('selected',NAVY)])
            _c('Treeview',font=('Segoe UI',9),rowheight=24,fieldbackground=CARD,background=CARD)
            _c('Treeview.Heading',font=('Segoe UI',9,'bold'),background=NAVY,foreground='white')
            _m('Treeview.Heading',background=[('active',NAVY2)])
            _c('TScrollbar',background='#C7CFDE',troughcolor=BG,borderwidth=0,arrowcolor=NAVY)
        except Exception:
            pass

    def _btn(self,parent,text,cmd,kind='ghost',**kw):
        colors={'primary':(NAVY,'white'),'go':(GREEN,'white'),'accent':(NAVY2,'white'),
                'gold':(GOLD,'white'),'ghost':('#E7ECF6',NAVY)}
        bg,fg=colors.get(kind,colors['ghost'])
        b=tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,activebackground=bg,activeforeground=fg,
                    relief='flat',bd=0,font=('Segoe UI',10,'bold'),cursor='hand2',
                    padx=kw.pop('padx',14),pady=kw.pop('pady',7),**kw)
        return b

    # ---------- UI ----------
    def _build(self):
        # gradient header (canvas) for a polished, professional look
        H=78; hdr=tk.Canvas(self,height=H,highlightthickness=0,bd=0); hdr.pack(fill='x')
        def _grad(ev=None):
          try:
            hdr.delete('g'); w=hdr.winfo_width() or 960
            c1=(27,46,82); c2=(41,75,133)
            for x in range(0,w+1):
                t=x/max(1,w); r=int(c1[0]+(c2[0]-c1[0])*t); g=int(c1[1]+(c2[1]-c1[1])*t); b=int(c1[2]+(c2[2]-c1[2])*t)
                hdr.create_line(x,0,x,H,fill='#%02x%02x%02x'%(r,g,b),width=1,tags='g')
            hdr.create_text(20,20,text="Reimbursement Manager",anchor='w',fill='white',font=('Segoe UI',19,'bold'),tags='g')
            hdr.create_text(21,50,text="Import bills  →  categorize  →  generate & publish the shared reimbursement record",
                            anchor='w',fill='#C9D3EA',font=('Segoe UI',10),tags='g')
            hdr.create_text(w-18,26,text="Pearson v. Pearson",anchor='e',fill='#9db0d4',font=('Segoe UI',10,'bold'),tags='g')
            hdr.create_text(w-18,46,text="No. 236951 · EBR Parish",anchor='e',fill='#7f93bd',font=('Segoe UI',8),tags='g')
          except Exception:
            pass
        hdr.bind('<Configure>',_grad); self.after(60,_grad)
        nb=ttk.Notebook(self); nb.pack(fill='both',expand=True,padx=12,pady=10)
        self.tab_run=tk.Frame(nb,bg=BG); self.tab_add=tk.Frame(nb,bg=BG)
        self.tab_set=tk.Frame(nb,bg=BG)
        self.tab_amt=tk.Frame(nb,bg=BG)
        self.tab_paid=tk.Frame(nb,bg=BG)
        self.tab_arch=tk.Frame(nb,bg=BG)
        nb.add(self.tab_run,text='  Generate & Export  ')
        nb.add(self.tab_amt,text='  Edit Amounts  ')
        nb.add(self.tab_paid,text='  Mark Paid  ')
        nb.add(self.tab_add,text='  Add / Import  ')
        nb.add(self.tab_arch,text='  Archive / Backups  ')
        nb.add(self.tab_set,text='  Settings  ')
        self._build_run(); self._build_amounts(); self._build_paid(); self._build_add(); self._build_archive(); self._build_settings()

    def _card(self,parent,**kw):
        c=tk.Frame(parent,bg=CARD,highlightbackground=LINE,highlightthickness=1,bd=0)
        c.pack(fill='x',padx=16,pady=(10,0),**kw); return c
    def _build_run(self):
        f=self.tab_run
        # --- stat dashboard ---
        dash=tk.Frame(f,bg=BG); dash.pack(fill='x',padx=12,pady=(14,2))
        self.stat=[]
        for i,(lab,col) in enumerate([('LINDSEY OWES (NET)',GREEN),('LINE ITEMS',NAVY),('CATEGORIES',NAVY2)]):
            card=tk.Frame(dash,bg=CARD,highlightbackground=LINE,highlightthickness=1)
            card.grid(row=0,column=i,sticky='ew',padx=(0 if i==0 else 8,0))
            dash.columnconfigure(i,weight=1)
            tk.Label(card,text=lab,bg=CARD,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=14,pady=(11,0))
            v=tk.Label(card,text='—',bg=CARD,fg=col,font=('Segoe UI',19,'bold')); v.pack(anchor='w',padx=14,pady=(0,11))
            self.stat.append(v)
        # --- folder + actions ---
        card=self._card(f)
        tk.Label(card,text="BILLS FOLDER",bg=CARD,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=14,pady=(11,3))
        fr=tk.Frame(card,bg=CARD); fr.pack(fill='x',padx=14,pady=(0,12))
        self.folder=tk.StringVar(value=self.cfg.get('last_folder') or '')
        tk.Entry(fr,textvariable=self.folder,font=('Segoe UI',10),relief='solid',bd=1).pack(side='left',fill='x',expand=True,ipady=4)
        self._btn(fr,"Browse…",self._browse,'ghost').pack(side='left',padx=(8,0))
        act=tk.Frame(f,bg=BG); act.pack(fill='x',padx=16,pady=14)
        self.gen_btn=self._btn(act,"⚙  Generate All Documents",self._run,'go',padx=20,pady=10)
        self.gen_btn.configure(font=('Segoe UI',12,'bold')); self.gen_btn.pack(side='left')
        b2=self._btn(act,"✉  Email Full Packet",self._email_packet,'primary',padx=20,pady=10)
        b2.configure(font=('Segoe UI',12,'bold')); b2.pack(side='left',padx=(10,0))
        b3=self._btn(act,"🌐  Publish to Web",self._publish,'accent',padx=20,pady=10)
        b3.configure(font=('Segoe UI',12,'bold')); b3.pack(side='left',padx=(10,0))
        self.net_lbl=tk.Label(act,text="",bg=BG,fg=GREEN,font=('Segoe UI',15,'bold')); self.net_lbl.pack(side='left',padx=16)
        ob=tk.Frame(f,bg=BG); ob.pack(fill='x',padx=16)
        self.buttons={}
        for key,label in [('xlsx','Workbook'),('pdf','Statement'),('cover','Cover Letter'),
                          ('proof','Proof Pack'),('print','PRINT Package'),('out','Output Folder')]:
            b=self._btn(ob,label,(lambda k=key: open_path(OUTDIR) if k=='out' else open_path(self._f(k))),'ghost',padx=11,pady=6)
            b.configure(state='disabled',font=('Segoe UI',9,'bold')); b.pack(side='left',padx=(0,7)); self.buttons[key]=b
        tk.Label(f,text="PROGRESS",bg=BG,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=16,pady=(12,2))
        lf=tk.Frame(f,bg=CARD,highlightbackground=LINE,highlightthickness=1); lf.pack(fill='both',expand=True,padx=16,pady=(0,14))
        self.log=tk.Text(lf,height=12,font=('Consolas',9),bg=CARD,relief='flat',bd=0,fg='#2b3444',padx=10,pady=8)
        self.log.pack(fill='both',expand=True)
    # ---------- Archive / Backups tab ----------
    def _build_archive(self):
        f=self.tab_arch
        tk.Label(f,text="Archive & backups — a safety net if the wrong button is pushed",
                 bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).pack(anchor='w',padx=16,pady=(14,2))
        tk.Label(f,text="A snapshot of your data is saved automatically every time you Generate. "
                 "You can also save one anytime, and restore any snapshot to roll everything back.",
                 bg=BG,fg=MUTED,font=('Segoe UI',9),justify='left',wraplength=880).pack(anchor='w',padx=16)
        bar=tk.Frame(f,bg=BG); bar.pack(fill='x',padx=16,pady=8)
        self._btn(bar,"📦  Save a snapshot now",self._arch_save,'go').pack(side='left')
        self._btn(bar,"↩  Restore selected",self._arch_restore,'accent').pack(side='left',padx=(8,0))
        self._btn(bar,"🗑  Delete selected",self._arch_delete,'ghost').pack(side='left',padx=(8,0))
        self._btn(bar,"↻  Refresh",self._arch_fill,'ghost').pack(side='left',padx=(8,0))
        self._btn(bar,"📂  Open archive folder",self._arch_open,'ghost').pack(side='right')
        cols=('when','net','kind','note')
        tv=ttk.Treeview(f,columns=cols,show='headings',selectmode='browse',height=16)
        for c,w,t in [('when',180,'Saved'),('net',120,'Net at the time'),('kind',80,'Type'),('note',420,'Note')]:
            tv.heading(c,text=t); tv.column(c,width=w,anchor='w')
        sb=ttk.Scrollbar(f,orient='vertical',command=tv.yview); tv.configure(yscroll=sb.set)
        tv.pack(side='left',fill='both',expand=True,padx=(16,0),pady=(2,14)); sb.pack(side='left',fill='y',pady=(2,14))
        self.arch_tv=tv; self._arch_fill()
    def _arch_fill(self):
        try: import backup
        except Exception as e: messagebox.showerror("Archive",str(e)); return
        tv=self.arch_tv
        for i in tv.get_children(): tv.delete(i)
        for s in backup.snapshots():
            net=('${:,.2f}'.format(s['net']) if s.get('net') is not None else '—')
            kind=('auto' if s.get('auto') else 'saved')
            tv.insert('','end',iid=s['id'],values=(s.get('when_human',s['id']),net,kind,s.get('note','')))
    def _arch_save(self):
        try:
            import backup
            note=simpledialog.askstring("Save snapshot","Optional label for this snapshot:",parent=self) or ''
            sid=backup.snapshot(note=note,auto=False)
            self._arch_fill(); messagebox.showinfo("Archive","Snapshot saved:  %s"%sid)
        except Exception as e: messagebox.showerror("Archive",str(e))
    def _arch_restore(self):
        sel=self.arch_tv.selection()
        if not sel: messagebox.showinfo("Restore","Select a snapshot to restore first."); return
        sid=sel[0]
        if not messagebox.askyesno("Restore snapshot",
            "Restore your data to this snapshot?\n\n  %s\n\nYour current data is backed up first, so this is undoable. "
            "After restoring, click Generate (then Publish) to rebuild everything."%sid): return
        try:
            import backup; backup.restore(sid); self._arch_fill()
            messagebox.showinfo("Restored","Restored %s.\n\nNow click Generate (and Publish) to apply it."%sid)
        except Exception as e: messagebox.showerror("Restore",str(e))
    def _arch_delete(self):
        sel=self.arch_tv.selection()
        if not sel: return
        if not messagebox.askyesno("Delete","Delete snapshot %s permanently?"%sel[0]): return
        try:
            import backup; backup.delete(sel[0]); self._arch_fill()
        except Exception as e: messagebox.showerror("Delete",str(e))
    def _arch_open(self):
        d=os.path.join(HERE,'archive'); os.makedirs(d,exist_ok=True); open_path(d)
    def _publish(self):
        p=os.path.join(HERE,'Publish to Web.bat')
        if sys.platform.startswith('win') and os.path.exists(p):
            try: os.startfile(p)
            except Exception as e: messagebox.showerror("Publish",str(e))
        else:
            messagebox.showinfo("Publish","Run 'Publish to Web.bat' in the program folder to update the shared link.")

    # ---------- Edit Amounts tab ----------
    def _build_amounts(self):
        f=self.tab_amt
        tk.Label(f,text="Manual amounts (mortgage, labor, moving, AT&T placeholders...) — select a row and click Edit",
                 bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,4))
        cols=('vendor','category','when','amount','desc')
        self.amt_tree=ttk.Treeview(f,columns=cols,show='headings',height=9)
        for c,w in zip(cols,(170,150,130,90,300)):
            self.amt_tree.heading(c,text=c.title()); self.amt_tree.column(c,width=w,anchor='w')
        self.amt_tree.pack(fill='x',padx=14)
        bf=tk.Frame(f,bg=BG); bf.pack(fill='x',padx=14,pady=6)
        tk.Button(bf,text="Edit Selected…",command=self._amt_edit).pack(side='left')
        tk.Button(bf,text="Delete Selected",command=self._amt_delete).pack(side='left',padx=8)
        tk.Button(bf,text="Reload",command=self._amt_reload).pack(side='left')
        self.amt_status=tk.Label(f,text='',bg=BG,fg=GREEN,font=('Segoe UI',10,'bold')); self.amt_status.pack(anchor='w',padx=14)
        ttk.Separator(f,orient='horizontal').pack(fill='x',padx=14,pady=8)
        tk.Label(f,text='"Additional amounts paid for her" (Yukon / auto insurance / health) live in additional.json.',
                 bg=BG,fg=NAVY,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=14)
        tk.Button(f,text="Open additional.json in Notepad",command=lambda:os.startfile(os.path.join(HERE,'additional.json')) if sys.platform.startswith('win') else open_path(os.path.join(HERE,'additional.json'))).pack(anchor='w',padx=14,pady=4)
        tk.Button(f,text="Open disputes.json in Notepad (Lindsey's disputes & your responses)",command=lambda:os.startfile(os.path.join(HERE,'disputes.json')) if sys.platform.startswith('win') else open_path(os.path.join(HERE,'disputes.json'))).pack(anchor='w',padx=14,pady=4)
        pbf=tk.Frame(f,bg=BG); pbf.pack(anchor='w',padx=14,pady=4)
        tk.Button(pbf,text="✔  Record Paid Back…",bg=GREEN,fg='white',font=('Segoe UI',10,'bold'),
                 relief='flat',padx=14,pady=4,command=self._paidback_dialog).pack(side='left')
        tk.Button(pbf,text="Open paidback.json in Notepad",command=lambda:os.startfile(os.path.join(HERE,'paidback.json')) if sys.platform.startswith('win') else open_path(os.path.join(HERE,'paidback.json'))).pack(side='left',padx=8)
        tk.Label(f,text="After ANY change here: go to Generate & Export and click Generate, then Publish to Web.bat to update the shared link.",
                 bg=BG,fg='#777',font=('Segoe UI',9)).pack(anchor='w',padx=14,pady=(4,10))
        self._amt_reload()

    def _amt_reload(self):
        try: self.cfg=load_cfg()
        except Exception: pass
        for i in self.amt_tree.get_children(): self.amt_tree.delete(i)
        for idx,m in enumerate(self.cfg.get('manual_entries',[])):
            rec=m.get('recurring_monthly')
            when=(rec['start']+' to '+rec['end']) if rec else m.get('date','')
            amt=m.get('amount',0)
            if m.get('amount_schedule'): amt=str(amt)+' (tiered)'
            if m.get('flat_share') is not None: amt=str(m.get('amount'))+' (her: '+str(m.get('flat_share'))+')'
            self.amt_tree.insert('',ated:='end',iid=str(idx),values=(m.get('vendor',''),m.get('category',''),when,amt,(m.get('description','') or '')[:60]))
        self.amt_status.config(text='')

    def _amt_sel(self):
        sel=self.amt_tree.selection()
        if not sel:
            messagebox.showinfo("Select","Click a row first."); return None
        return int(sel[0])

    def _amt_edit(self):
        idx=self._amt_sel()
        if idx is None: return
        m=self.cfg['manual_entries'][idx]
        dlg=tk.Toplevel(self); dlg.title("Edit amount"); dlg.configure(bg=BG); dlg.grab_set()
        fields=[('Amount ($)','amount',str(m.get('amount','')))]
        rec=m.get('recurring_monthly')
        if rec:
            fields+=[('Start (YYYY-MM)','_start',rec.get('start','')),('End (YYYY-MM)','_end',rec.get('end',''))]
        else:
            fields+=[('Date (YYYY-MM-DD)','date',m.get('date',''))]
        if m.get('flat_share') is not None:
            fields+=[('Her flat share ($)','flat_share',str(m.get('flat_share','')))]
        fields+=[('Description','description',m.get('description',''))]
        vars={}
        for i,(lab,key,val) in enumerate(fields):
            tk.Label(dlg,text=lab,bg=BG,font=('Segoe UI',10)).grid(row=i,column=0,sticky='w',padx=12,pady=4)
            v=tk.StringVar(value=val); vars[key]=v
            tk.Entry(dlg,textvariable=v,width=46,font=('Segoe UI',10)).grid(row=i,column=1,padx=12,pady=4)
        if m.get('amount_schedule'):
            tk.Label(dlg,text="Note: this entry has a tiered amount_schedule (edit per-tier in config.json).",
                     bg=BG,fg='#8a6100',font=('Segoe UI',9)).grid(row=len(fields),column=0,columnspan=2,sticky='w',padx=12)
        def save():
            try:
                m['amount']=float(vars['amount'].get())
                if 'flat_share' in vars: m['flat_share']=float(vars['flat_share'].get())
                if rec:
                    rec['start']=vars['_start'].get().strip(); rec['end']=vars['_end'].get().strip()
                elif 'date' in vars: m['date']=vars['date'].get().strip()
                m['description']=vars['description'].get()
            except ValueError:
                messagebox.showerror("Invalid","Amount must be a number."); return
            try: disk=load_cfg()
            except Exception: disk=self.cfg
            disk['manual_entries']=self.cfg['manual_entries']; save_cfg(disk); self.cfg=disk
            dlg.destroy(); self._amt_reload()
            self.amt_status.config(text="Saved. Re-run Generate (and Publish) to apply.")
        tk.Button(dlg,text="Save",bg=GREEN,fg='white',relief='flat',padx=16,pady=5,
                  font=('Segoe UI',10,'bold'),command=save).grid(row=len(fields)+1,column=1,sticky='e',padx=12,pady=10)

    def _amt_delete(self):
        idx=self._amt_sel()
        if idx is None: return
        m=self.cfg['manual_entries'][idx]
        if not messagebox.askyesno("Delete",f"Remove {m.get('vendor')} {m.get('amount')}?"): return
        del self.cfg['manual_entries'][idx]
        try: disk=load_cfg()
        except Exception: disk=self.cfg
        disk['manual_entries']=self.cfg['manual_entries']; save_cfg(disk); self.cfg=disk
        self._amt_reload(); self.amt_status.config(text="Deleted. Re-run Generate (and Publish) to apply.")

    def _build_add(self):
        f=self.tab_add
        tk.Label(f,text="Add a manual expense (no bill document)",bg=BG,fg=NAVY,
                 font=('Segoe UI',11,'bold')).grid(row=0,column=0,columnspan=4,sticky='w',padx=14,pady=(14,6))
        cats=list(self.cfg.get('split_percent',{}).keys())
        labels=['Date (YYYY-MM-DD)','Vendor','Category','Amount ($)','Description']
        self.add_vars={}
        defaults=[datetime.date.today().isoformat(),'','', '', '']
        for i,(lab,d) in enumerate(zip(labels,defaults)):
            tk.Label(f,text=lab,bg=BG,font=('Segoe UI',10)).grid(row=1+i,column=0,sticky='w',padx=14,pady=3)
            if lab=='Category':
                v=tk.StringVar(value=cats[0] if cats else '')
                ttk.Combobox(f,textvariable=v,values=cats,width=28,state='readonly').grid(row=1+i,column=1,sticky='w')
            else:
                v=tk.StringVar(value=d)
                tk.Entry(f,textvariable=v,width=31,font=('Segoe UI',10)).grid(row=1+i,column=1,sticky='w')
            self.add_vars[lab]=v
        tk.Button(f,text="＋ Add Expense",bg=NAVY,fg='white',font=('Segoe UI',10,'bold'),relief='flat',
                  padx=12,pady=5,command=self._add_expense).grid(row=6,column=1,sticky='w',pady=8)
        ttk.Separator(f,orient='horizontal').grid(row=7,column=0,columnspan=4,sticky='ew',padx=14,pady=10)
        tk.Label(f,text="Import documents",bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).grid(row=8,column=0,columnspan=4,sticky='w',padx=14,pady=(0,6))
        tk.Button(f,text="Import bill files (PDF/JPG/PNG)…",command=lambda:self._import_files('') ,padx=8).grid(row=9,column=0,columnspan=2,sticky='w',padx=14,pady=3)
        tk.Button(f,text="Import Venmo statement CSVs…",command=lambda:self._import_files('Venmo Statements'),padx=8).grid(row=10,column=0,columnspan=2,sticky='w',padx=14,pady=3)
        tk.Label(f,text="Files are copied into the bills folder, then auto-categorized on the next Generate.\n"
                 "Email import runs automatically every Monday via Claude Cowork (weekly bill collector).",
                 bg=BG,fg='#777',font=('Segoe UI',9),justify='left').grid(row=11,column=0,columnspan=4,sticky='w',padx=14,pady=8)
        self.add_status=tk.Label(f,text='',bg=BG,fg=GREEN,font=('Segoe UI',10,'bold'))
        self.add_status.grid(row=12,column=0,columnspan=4,sticky='w',padx=14)

    def _build_settings(self):
        f=self.tab_set
        tk.Label(f,text="Percentage Lindsey reimburses (AT&T Business is a flat $100/mo regardless)",
                 bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).grid(row=0,column=0,columnspan=4,sticky='w',padx=14,pady=(14,8))
        self.pct_vars={}
        for i,(cat,val) in enumerate(self.cfg['split_percent'].items()):
            r,c=divmod(i,2)
            cell=tk.Frame(f,bg=BG); cell.grid(row=1+r,column=c,sticky='w',padx=14,pady=3)
            tk.Label(cell,text=cat,bg=BG,width=26,anchor='w',font=('Segoe UI',10)).pack(side='left')
            v=tk.StringVar(value=str(val)); self.pct_vars[cat]=v
            tk.Entry(cell,textvariable=v,width=5,justify='center',font=('Segoe UI',10)).pack(side='left')
            tk.Label(cell,text="%",bg=BG).pack(side='left')
        rr=2+len(self.cfg['split_percent'])//2
        self.sub_credits=tk.BooleanVar(value=bool(self.cfg.get('subtract_payments_to_lindsey',True)))
        tk.Checkbutton(f,text="Subtract money already paid to Lindsey",variable=self.sub_credits,bg=BG,
                       font=('Segoe UI',10)).grid(row=rr,column=0,sticky='w',padx=14,pady=(10,2))
        cf=tk.Frame(f,bg=BG); cf.grid(row=rr+1,column=0,columnspan=2,sticky='w',padx=14,pady=2)
        tk.Label(cf,text="Only count bills on/after:",bg=BG,font=('Segoe UI',10)).pack(side='left')
        self.cutoff=tk.StringVar(value=self.cfg.get('date_cutoff') or '')
        tk.Entry(cf,textvariable=self.cutoff,width=12,font=('Segoe UI',10),relief='solid',bd=1).pack(side='left',padx=6)
        # On-page uploads (FormSubmit) — destination inbox for uploaded files/disputes
        wf=tk.Frame(f,bg=CARD,highlightbackground=LINE,highlightthickness=1)
        wf.grid(row=rr+2,column=0,columnspan=4,sticky='ew',padx=14,pady=(12,4))
        f.columnconfigure(0,weight=1); f.columnconfigure(1,weight=1)
        tk.Label(wf,text="ON-PAGE UPLOADS  —  where uploaded files & disputes are emailed",bg=CARD,fg=MUTED,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=12,pady=(10,2))
        tk.Label(wf,text="Uploads on the shared page are LIVE (no account/key needed). Anything uploaded is emailed to the address below. Change it only if you want a different inbox.",
                 bg=CARD,fg=GREEN,font=('Segoe UI',9),wraplength=820,justify='left').pack(anchor='w',padx=12)
        self.w3f=tk.StringVar(value=self.cfg.get('form_email') or 'nedpearson@gmail.com')
        tk.Entry(wf,textvariable=self.w3f,font=('Consolas',10),relief='solid',bd=1).pack(fill='x',padx=12,pady=(6,12),ipady=4)
        self._btn(f,"💾  Save Settings",self._save_settings,'primary',padx=16,pady=8).grid(row=rr+3,column=0,sticky='w',padx=14,pady=14)

    # ---------- actions ----------
    def _f(self,k): return (self.result or {}).get(k)
    def _browse(self):
        d=filedialog.askdirectory(initialdir=self.folder.get() or os.path.expanduser('~'))
        if d: self.folder.set(d)
    def _email_packet(self):
        try:
            import email_packet
            email_packet.main()
        except Exception as e:
            messagebox.showerror("Email Full Packet", str(e))
    # ---------- Mark Paid tab ----------
    def _build_paid(self):
        f=self.tab_paid
        tk.Label(f,text="Mark each line Paid, Proof-Submitted, or Unpaid — you control this",
                 bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,2))
        tk.Label(f,text="Load your lines, select one or more rows, then click a status. Green = paid (drops off the balance). "
                 "Yellow = Lindsey sent proof, awaiting your OK. Then Generate & Publish.",
                 bg=BG,fg='#555',font=('Segoe UI',9),justify='left',wraplength=800).pack(anchor='w',padx=14)
        bar=tk.Frame(f,bg=BG); bar.pack(fill='x',padx=14,pady=6)
        tk.Button(bar,text="⟳ Load / Refresh lines",command=self._paid_load).pack(side='left')
        tk.Label(bar,text="  Filter:",bg=BG).pack(side='left')
        self.paid_filter=tk.StringVar()
        fe=tk.Entry(bar,textvariable=self.paid_filter,width=26); fe.pack(side='left')
        fe.bind('<KeyRelease>',lambda e:self._paid_fill())
        self.paid_count_lbl=tk.Label(bar,text="",bg=BG,fg=GREEN,font=('Segoe UI',10,'bold')); self.paid_count_lbl.pack(side='right')
        cols=('date','cat','vendor','amount','share','status')
        tv=ttk.Treeview(f,columns=cols,show='headings',selectmode='extended',height=16)
        for c,w,t in [('date',80,'Date'),('cat',150,'Category'),('vendor',150,'Vendor'),('amount',90,'Bill'),('share',90,'Her share'),('status',150,'Status')]:
            tv.heading(c,text=t); tv.column(c,width=w,anchor=('e' if c in('amount','share') else 'w'))
        tv.tag_configure('paid',background='#E7F5EC'); tv.tag_configure('pending',background='#FDF3E3')
        sb=ttk.Scrollbar(f,orient='vertical',command=tv.yview); tv.configure(yscroll=sb.set)
        tv.pack(side='left',fill='both',expand=True,padx=(14,0),pady=(0,12)); sb.pack(side='left',fill='y',pady=(0,12))
        self.paid_tv=tv
        bf=tk.Frame(f,bg=BG); bf.pack(side='left',fill='y',padx=10,pady=8)
        tk.Button(bf,text="✔ Mark PAID",bg=GREEN,fg='white',font=('Segoe UI',10,'bold'),relief='flat',width=20,command=lambda:self._paid_set('paid')).pack(pady=4)
        tk.Button(bf,text="◐ Proof Submitted",bg='#B07A00',fg='white',font=('Segoe UI',10,'bold'),relief='flat',width=20,command=lambda:self._paid_set('pending')).pack(pady=4)
        tk.Button(bf,text="○ Mark Unpaid",width=20,command=lambda:self._paid_set('unpaid')).pack(pady=4)
        tk.Label(bf,text="Tip: hold Ctrl or Shift\nto select several lines.",bg=BG,fg='#777',font=('Segoe UI',9),justify='left').pack(pady=(10,0))
        self._paid_rows=[]; self._paid_state={'paid':set(),'pending':set()}
    def _settled_path(self): return os.path.join(HERE,'settled.json')
    def _paid_loadstate(self):
        try: s=json.load(open(self._settled_path(),encoding='utf-8'))
        except Exception: s={'paid':[],'pending':[]}
        self._paid_state={'paid':set(s.get('paid',[])),'pending':set(s.get('pending',[]))-set(s.get('paid',[]))}
    def _paid_savestate(self):
        s={'_how_to_use':'Per-line paid tracking (managed by the app Mark Paid tab). paid=green/subtracted, pending=yellow/awaiting review. After changes: Generate + Publish.',
           'paid':sorted(self._paid_state['paid']),'pending':sorted(self._paid_state['pending']-self._paid_state['paid'])}
        from safewrite import write_via_temp
        write_via_temp(self._settled_path(),lambda tmp: json.dump(s,open(tmp,'w',encoding='utf-8'),indent=1))
    def _paid_load(self):
        folder=self.folder.get() or self.cfg.get('last_folder')
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Mark Paid","Pick your Bills folder on the Generate tab first."); return
        self.paid_count_lbl.config(text="loading…"); self.update_idletasks()
        try:
            import categorize
            rows=categorize.apply_split(categorize.build(folder))
        except Exception as e:
            messagebox.showerror("Mark Paid","Could not read lines: %s"%e); return
        self._paid_loadstate()
        out=[]
        for r in rows:
            if not (r.get('include') and r.get('in_window',True) and r.get('amount') is not None and r.get('her_share') is not None): continue
            out.append(dict(id=categorize.item_id(r),date=r.get('date') or '',cat=r['category'],vendor=r['vendor'],
                            amount=r['amount'],share=r['her_share']))
        out.sort(key=lambda x:(x['cat'],x['date']))
        self._paid_rows=out; self._paid_fill()
    def _paid_fill(self):
        tv=self.paid_tv
        for iid in tv.get_children(): tv.delete(iid)
        flt=(self.paid_filter.get() or '').lower()
        shown=0
        for r in self._paid_rows:
            if flt and flt not in (r['cat']+' '+r['vendor']+' '+r['date']).lower(): continue
            if r['id'] in self._paid_state['paid']: stat='PAID ✓'; tag='paid'
            elif r['id'] in self._paid_state['pending']: stat='Proof submitted'; tag='pending'
            else: stat=''; tag=''
            tv.insert('','end',iid=r['id'],tags=(tag,),
                      values=(r['date'],r['cat'],r['vendor'][:24],'$%,.2f'%r['amount'],'$%,.2f'%r['share'],stat))
            shown+=1
        paidtot=sum(r['share'] for r in self._paid_rows if r['id'] in self._paid_state['paid'])
        self.paid_count_lbl.config(text="%d paid · $%,.2f settled"%(len(self._paid_state['paid']),paidtot))
    def _paid_set(self,state):
        sel=self.paid_tv.selection()
        if not sel:
            messagebox.showinfo("Mark Paid","Select one or more lines first."); return
        for iid in sel:
            self._paid_state['paid'].discard(iid); self._paid_state['pending'].discard(iid)
            if state=='paid': self._paid_state['paid'].add(iid)
            elif state=='pending': self._paid_state['pending'].add(iid)
        self._paid_savestate(); self._paid_fill()
    def _paidback_dialog(self):
        dlg=tk.Toplevel(self); dlg.title("Record Paid Back"); dlg.configure(bg=BG); dlg.grab_set()
        fields=[("Date (YYYY-MM-DD)",datetime.date.today().isoformat()),
                ("Amount (e.g. 500.00)",""),("Method (Venmo / check / cash / Zelle)",""),
                ("What it covers (e.g. Pool + Utilities Jan-Mar)",""),
                ("Exhibit #s fully covered, comma-separated (optional)",""),("Note (optional)","")]
        ents=[]
        for i,(lab,dv) in enumerate(fields):
            tk.Label(dlg,text=lab,bg=BG,anchor='w').grid(row=i*2,column=0,sticky='w',padx=14,pady=(8 if i==0 else 4,0))
            e=tk.Entry(dlg,width=52); e.insert(0,dv); e.grid(row=i*2+1,column=0,padx=14,sticky='we'); ents.append(e)
        st=tk.Label(dlg,text="Only record money you have actually received (or verified proof of).",bg=BG,fg='#777',font=('Segoe UI',9))
        st.grid(row=98,column=0,padx=14,pady=(8,0),sticky='w')
        def save():
            try: amt=round(float(ents[1].get().replace('$','').replace(',','').strip()),2)
            except ValueError:
                messagebox.showerror("Record Paid Back","Amount must be a number.",parent=dlg); return
            if amt<=0:
                messagebox.showerror("Record Paid Back","Amount must be positive.",parent=dlg); return
            exh=[]
            for tok in ents[4].get().replace(' ','').split(','):
                if tok.isdigit(): exh.append(int(tok))
            p={'date':ents[0].get().strip(),'amount':amt,'method':ents[2].get().strip() or 'payment',
               'covers':ents[3].get().strip(),'exh':exh,'note':ents[5].get().strip()}
            path=os.path.join(HERE,'paidback.json')
            try: data=json.load(open(path,encoding='utf-8'))
            except Exception: data={'payments':[]}
            data.setdefault('payments',[]).append(p)
            from safewrite import write_via_temp
            write_via_temp(path,lambda tmp: json.dump(data,open(tmp,'w',encoding='utf-8'),indent=1))
            dlg.destroy()
            messagebox.showinfo("Record Paid Back","Recorded %s.\n\nNow click Generate, then Publish to Web — the portal balance will drop and the payment will show in the Paid Back section."%('$%,.2f'%amt if False else '$'+format(amt,',.2f')))
        bf=tk.Frame(dlg,bg=BG); bf.grid(row=99,column=0,pady=12)
        tk.Button(bf,text="Save Payment",bg=GREEN,fg='white',relief='flat',padx=16,pady=5,command=save).pack(side='left',padx=6)
        tk.Button(bf,text="Cancel",command=dlg.destroy).pack(side='left',padx=6)
    def _log(self,m): self.log.insert('end',m+"\n"); self.log.see('end')
    def _save_settings(self):
        try: self.cfg=load_cfg()
        except Exception: pass
        c=self.cfg
        for cat,v in self.pct_vars.items():
            try: c['split_percent'][cat]=float(v.get())
            except ValueError: pass
        c['subtract_payments_to_lindsey']=bool(self.sub_credits.get())
        c['date_cutoff']=self.cutoff.get().strip() or None
        if hasattr(self,'w3f'): c['form_email']=self.w3f.get().strip() or 'nedpearson@gmail.com'
        save_cfg(c); messagebox.showinfo("Saved","Settings saved. Re-run Generate, then Publish to apply on the shared page.")
    def _add_expense(self):
        try:
            amt=float(self.add_vars['Amount ($)'].get())
        except ValueError:
            messagebox.showerror("Amount","Enter a valid dollar amount."); return
        e={"vendor":self.add_vars['Vendor'].get() or 'Manual entry',
           "category":self.add_vars['Category'].get(),
           "description":self.add_vars['Description'].get() or 'Manual expense',
           "amount":amt,"date":self.add_vars['Date (YYYY-MM-DD)'].get()}
        try: self.cfg=load_cfg()
        except Exception: pass
        self.cfg.setdefault('manual_entries',[]).append(e); save_cfg(self.cfg)
        self.add_status.config(text=f"Added: {e['vendor']} ${amt:,.2f} ({e['category']}). Re-run Generate.")
    def _import_files(self,subdir):
        folder=self.folder.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Bills folder","Set a valid bills folder on the Generate tab first."); return
        paths=filedialog.askopenfilenames(filetypes=[("Documents","*.pdf *.jpg *.jpeg *.png *.csv"),("All","*.*")])
        if not paths: return
        dest=os.path.join(folder,subdir) if subdir else folder
        os.makedirs(dest,exist_ok=True)
        n=0
        for p in paths:
            try: shutil.copy2(p,os.path.join(dest,os.path.basename(p))); n+=1
            except Exception as ex: messagebox.showwarning("Copy failed",f"{p}\n{ex}")
        self.add_status.config(text=f"Imported {n} file(s) into {'Venmo Statements' if subdir else 'bills folder'}. Re-run Generate.")
    def _run(self):
        folder=self.folder.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Folder not found","Choose a valid bills folder."); return
        try: disk=load_cfg()
        except Exception: disk=self.cfg
        disk['last_folder']=folder; save_cfg(disk); self.cfg=disk
        self.gen_btn.config(state='disabled',text="Working…"); self.net_lbl.config(text="")
        for b in self.buttons.values(): b.config(state='disabled')
        self.log.delete('1.0','end')
        threading.Thread(target=self._work,args=(folder,),daemon=True).start()
    def _work(self,folder):
        try:
            import importlib, categorize, exports
            importlib.reload(categorize)
            res=categorize.generate(folder,outdir=OUTDIR,progress=lambda m:self.q.put(('log',m)))
            outs=exports.export_all(res['rows'],json.load(open(CFG_PATH)),folder,OUTDIR,
                                    progress=lambda m:self.q.put(('log',m)))
            files=dict(res['files']); files.update(outs); files['out']=OUTDIR
            self.q.put(('done',dict(net=res['net'],files=files)))
        except Exception:
            self.q.put(('err',traceback.format_exc()))
    def _drain(self):
        try:
            while True:
                kind,payload=self.q.get_nowait()
                if kind=='log': self._log(payload)
                elif kind=='err':
                    self._log("ERROR:\n"+payload); self.gen_btn.config(state='normal',text="⚙  Generate All Documents")
                elif kind=='done':
                    self.result=payload['files']; self._log("Finished.")
                    self.net_lbl.config(text="")
                    try:
                        rows=payload.get('rows') or []
                        n=sum(1 for r in rows if r.get('include') and r.get('her_share'))
                        cats=len({r['category'] for r in rows if r.get('include') and r.get('her_share')})
                        self.stat[0].config(text="${:,.2f}".format(payload['net']))
                        self.stat[1].config(text=str(n)); self.stat[2].config(text=str(cats))
                    except Exception: pass
                    self.gen_btn.config(state='normal',text="⚙  Generate All Documents")
                    for k,b in self.buttons.items():
                        b.config(state='normal' if (k=='out' or self._f(k)) else 'disabled')
        except queue.Empty: pass
        self.after(120,self._drain)

def _fatal(exc):
    # pythonw shows no console, so a startup crash would just vanish — log it and pop a dialog
    try:
        with open(os.path.join(HERE,'app_error.log'),'w',encoding='utf-8') as fh:
            fh.write(traceback.format_exc())
    except Exception: pass
    try:
        r=tk.Tk(); r.withdraw()
        messagebox.showerror("Reimbursement Manager — startup error",
            "The app hit an error while starting:\n\n%s\n\nDetails saved to app_error.log in the program folder."%exc)
        r.destroy()
    except Exception: pass

if __name__=='__main__':
    try:
        App().mainloop()
    except Exception as e:
        _fatal(e)
