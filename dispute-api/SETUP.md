# Dispute one-click Approve/Deny — setup (one time, ~10 min)

When someone clicks **Dispute** on a charge in the portal, you get an email with two buttons:
**APPROVE** (removes the charge from the portal + all totals, automatically) and **DENY**
(keeps it, marks it "reviewed"). This folder is the tiny backend that makes those buttons work.

Everything in code is already done. You only need to (1) deploy this folder, (2) make one
GitHub token, (3) paste 5 settings, (4) put the resulting URL in `config.json` and republish.

---

## 1. Deploy this folder to Vercel

**Option A — dashboard (no terminal):**
1. Go to https://vercel.com → **Add New… → Project**.
2. Import the GitHub repo **nedpearson/Reimbursements**.
3. Set **Root Directory** = `dispute-api`  (click *Edit* next to Root Directory and pick it).
4. Framework preset: **Other**. Leave build/output blank. Click **Deploy**.

**Option B — terminal (from this folder):**
```
cd dispute-api
npx vercel --prod
```

Either way you'll get a URL like `https://pearson-dispute-api.vercel.app`. Keep it.

## 2. Make a GitHub token (so the buttons can update the portal)

1. https://github.com/settings/tokens?type=beta → **Generate new token** (fine-grained).
2. **Resource owner:** your account. **Repository access:** *Only select repositories* → **Reimbursements**.
3. **Permissions → Repository → Contents:** **Read and write**. (Nothing else is needed.)
4. Generate, copy the `github_pat_…` value.

## 3. Set the 5 environment variables in Vercel

Vercel → your project → **Settings → Environment Variables**. Add each (Production):

| Name          | Value                                             |
|---------------|---------------------------------------------------|
| `GH_TOKEN`    | the `github_pat_…` token from step 2              |
| `GH_REPO`     | `nedpearson/Reimbursements`                        |
| `SIGN_SECRET` | `1df9191d87d936dda6304d7e976983394d7b6b714e0164eb60a66e316da87b4d` |
| `NOTIFY_EMAIL`| `nedpearson@gmail.com`                             |
| `PORTAL_URL`  | `https://nedpearson.github.io/Reimbursements/`     |

Then **Deployments → … → Redeploy** so the variables take effect.

> `SIGN_SECRET` is a random value generated just for you. It signs the approve/deny links so
> nobody can forge one. If you ever want to rotate it, replace it here and it just works.

## 4. Point the portal at the API

1. Open `config.json`, set:  `"dispute_api": "https://pearson-dispute-api.vercel.app"`  (your step-1 URL, no trailing slash).
2. Double-click **Publish to Web.bat**. That rebuilds the portal so the Dispute button now
   routes through the API. (Until this step, disputes still email you — just without the buttons.)

## 5. One-time email activation (FormSubmit)

The very first dispute triggers a **"Confirm your email"** message from FormSubmit to
nedpearson@gmail.com. Click it once; after that every dispute email arrives normally. To do it
now: open the portal, click **Dispute** on any charge, send a test — then click the confirm email.

---

## Definition of done / verify

- [ ] Vercel shows the project **Ready**. Visiting `…vercel.app/api/decide` returns a small
      "Invalid link" page (that's correct — it means the function is live).
- [ ] `config.json` has your `dispute_api` URL and you re-ran **Publish to Web.bat**.
- [ ] File a test dispute from the portal → you receive an email with **APPROVE** / **DENY** buttons.
- [ ] Click **APPROVE** → you get a "Charge removed ✓" page → within ~1 min the charge is gone
      from the portal and the net total dropped by that charge's amount.
- [ ] `docs/overrides.json` in the repo now lists the removed charge.

## How it fits together

```
Portal "Dispute" button ──POST──▶ /api/dispute ──emails you (FormSubmit) with signed links
                                                        │
You click APPROVE/DENY in email ──▶ /api/decide ──commits──▶ docs/overrides.json (GitHub)
                                                        │
Portal loads overrides.json on open ──▶ removes the charge + recomputes every total (no rebuild)
Next "Publish to Web.bat" ──▶ build_portal.py also drops it, so the PDFs stay in sync too.
```

Nothing here stores data or needs a database. If the API is ever down, the portal still works and
disputes still email you (they just fall back to a plain message without the one-click buttons).
