#!/usr/bin/env python3
"""
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
NAVY='#1F3864'; GREEN='#2E7D32'; BG='#F4F6FB'

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
        self.geometry("860x700"); self.minsize(780,620)
        try: self.iconbitmap(os.path.join(HERE,'assets','icon.ico'))
        except Exception: pass
        self.cfg=load_cfg(); self.q=queue.Queue(); self.result=None
        self._build(); self.after(120,self._drain)

    # ---------- UI ----------
    def _build(self):
        hdr=tk.Frame(self,bg=NAVY); hdr.pack(fill='x')
        tk.Label(hdr,text="Reimbursement Manager",bg=NAVY,fg='white',
                 font=('Segoe UI',18,'bold')).pack(anchor='w',padx=18,pady=(12,0))
        tk.Label(hdr,text="Import bills → categorize → generate documents for Lindsey",
                 bg=NAVY,fg='#C9D3EA',font=('Segoe UI',10)).pack(anchor='w',padx=18,pady=(0,12))
        nb=ttk.Notebook(self); nb.pack(fill='both',expand=True,padx=12,pady=10)
        self.tab_run=tk.Frame(nb,bg=BG); self.tab_add=tk.Frame(nb,bg=BG)
        self.tab_set=tk.Frame(nb,bg=BG)
        self.tab_amt=tk.Frame(nb,bg=BG)
        nb.add(self.tab_run,text='  Generate & Export  ')
        nb.add(self.tab_amt,text='  Edit Amounts  ')
        nb.add(self.tab_add,text='  Add / Import  ')
        nb.add(self.tab_set,text='  Settings  ')
        self._build_run(); self._build_amounts(); self._build_add(); self._build_settings()

    def _build_run(self):
        f=self.tab_run
        tk.Label(f,text="Bills folder",bg=BG,fg=NAVY,font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,2))
        fr=tk.Frame(f,bg=BG); fr.pack(fill='x',padx=14)
        self.folder=tk.StringVar(value=self.cfg.get('last_folder') or '')
        tk.Entry(fr,textvariable=self.folder,font=('Segoe UI',10)).pack(side='left',fill='x',expand=True)
        tk.Button(fr,text="Browse…",command=self._browse).pack(side='left',padx=6)
        act=tk.Frame(f,bg=BG); act.pack(fill='x',padx=14,pady=12)
        self.gen_btn=tk.Button(act,text="⚙  Generate All Documents",bg=GREEN,fg='white',
                 font=('Segoe UI',12,'bold'),relief='flat',padx=18,pady=8,command=self._run)
        self.gen_btn.pack(side='left')
        tk.Button(act,text="✉  Email Full Packet",bg=NAVY,fg='white',
                 font=('Segoe UI',12,'bold'),relief='flat',padx=18,pady=8,
                 command=self._email_packet).pack(side='left',padx=(10,0))
        self.net_lbl=tk.Label(act,text="",bg=BG,fg=GREEN,font=('Segoe UI',15,'bold')); self.net_lbl.pack(side='left',padx=16)
        ob=tk.Frame(f,bg=BG); ob.pack(fill='x',padx=14)
        self.buttons={}
        for key,label in [('xlsx','Open Workbook'),('pdf','Open Statement'),('cover','Open Cover Letter'),
                          ('proof','Open Proof Pack'),('print','Open PRINT Package'),('out','Open Output Folder')]:
            b=tk.Button(ob,text=label,state='disabled',
                        command=(lambda k=key: open_path(OUTDIR) if k=='out' else open_path(self._f(k))))
            b.pack(side='left',padx=(0,7)); self.buttons[key]=b
        tk.Label(f,text="Progress",bg=BG,fg=NAVY,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=14,pady=(10,0))
        self.log=tk.Text(f,height=14,font=('Consolas',9),bg='white',relief='solid',bd=1)
        self.log.pack(fill='both',expand=True,padx=14,pady=(2,12))

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
        tk.Entry(cf,textvariable=self.cutoff,width=12,font=('Segoe UI',10)).pack(side='left',padx=6)
        tk.Button(f,text="Save Settings",bg=NAVY,fg='white',relief='flat',padx=12,pady=5,
                  font=('Segoe UI',10,'bold'),command=self._save_settings).grid(row=rr+2,column=0,sticky='w',padx=14,pady=12)

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
        save_cfg(c); messagebox.showinfo("Saved","Settings saved. Re-run Generate to apply.")
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
                    self.net_lbl.config(text="Lindsey owes:  ${:,.2f}".format(payload['net']))
                    self.gen_btn.config(state='normal',text="⚙  Generate All Documents")
                    for k,b in self.buttons.items():
                        b.config(state='normal' if (k=='out' or self._f(k)) else 'disabled')
        except queue.Empty: pass
        self.after(120,self._drain)

if __name__=='__main__':
    App().mainloop()
