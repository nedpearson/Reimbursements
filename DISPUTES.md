# Disputes — how Approve / Deny works (GitHub-native, no external backend)

When someone clicks **Dispute** on a charge in the portal, you get an email (via FormSubmit)
with two links: **APPROVE — remove this charge** and **DENY — keep this charge**.

- Clicking a link opens a **pre-filled GitHub issue** on this repo (you're already logged in).
- Click the green **Submit new issue** button.
- The **Dispute decision** GitHub Action (`.github/workflows/dispute-decision.yml`) then updates
  `docs/overrides.json`: Approve removes the charge (portal + every total recompute automatically,
  ~1 min later); Deny keeps it and marks it "reviewed — dispute declined". The Action closes the
  issue with a confirmation comment.

Security: the Action only runs for issues opened by **you** (the repo owner). The public dispute
form cannot trigger a removal — a stranger opening a look-alike issue is ignored.

## One-time setup (2 things)

1. **Let the Action write.** Repo **Settings -> Actions -> General -> Workflow permissions ->**
   select **"Read and write permissions"** -> Save. (Needed so the Action can commit the change
   and close the issue.)
2. **Activate the dispute email.** The first dispute triggers a one-time "Confirm your email"
   message from FormSubmit to nedpearson@gmail.com — click it once. To do it now: open the portal,
   click **Dispute** on any charge, send a test, then click the confirm email.

## Test it
Dispute any charge -> open your email -> click **APPROVE** -> Submit the GitHub issue -> within a
minute the charge is gone from https://nedpearson.github.io/Reimbursements/ and the net drops by
that charge's share. Undo by disputing again and clicking **DENY** (or edit `docs/overrides.json`).

## Notes
- Nothing to host, no tokens, no database. Everything lives in this repo.
- Permanent record: each approved/denied charge is also honored by `build_portal.py`, so a future
  "Publish to Web.bat" rebuild keeps removed charges out of the PDFs too.
- The `dispute-api/` folder is an unused alternate (a Vercel version). You can ignore or delete it.
