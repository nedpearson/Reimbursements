// GET /api/decide?t=<signed token>  — Ned clicks Approve or Deny from the email.
// Verifies the token, then commits the decision to docs/overrides.json on GitHub.
const { verify, html, esc, readOverrides, writeOverrides } = require('./_lib');

module.exports = async (req, res) => {
  try {
    const secret = process.env.SIGN_SECRET;
    const repo = process.env.GH_REPO;         // "owner/repo"
    const token = process.env.GH_TOKEN;       // fine-grained PAT, contents:read+write
    const portal = process.env.PORTAL_URL || 'https://nedpearson.github.io/Reimbursements/';
    if (!secret || !repo || !token)
      return html(res, 500, 'Not configured', 'The server is missing GH_REPO / GH_TOKEN / SIGN_SECRET.');

    const t = (req.query && req.query.t) || new URL(req.url, 'http://x').searchParams.get('t');
    const p = verify(t, secret);
    if (!p || !p.id || !p.action)
      return html(res, 400, 'Invalid link',
        'This approve/deny link could not be verified. It may have been altered or is malformed.');

    const { data, sha } = await readOverrides(repo, token);
    const now = new Date().toISOString();

    // one decision per charge id — clear any prior decision, then apply the new one
    data.removed = data.removed.filter((x) => x.id !== p.id);
    data.denied = data.denied.filter((x) => x.id !== p.id);

    if (p.action === 'approve') {
      data.removed.push({ id: p.id, label: p.label || '', date: p.date || '', reason: 'dispute upheld', ts: now });
    } else {
      data.denied.push({ id: p.id, label: p.label || '', date: p.date || '', note: 'reviewed — charge stands', ts: now });
    }

    await writeOverrides(repo, token, data, sha, 'dispute: ' + p.action + ' — ' + (p.label || p.id));

    if (p.action === 'approve')
      return html(res, 200, 'Charge removed ✓',
        '<b>' + esc(p.label) + '</b> has been removed from the reimbursement. ' +
        'The live portal and its totals update within about a minute.<br><br>' +
        '<a href="' + esc(portal) + '" style="color:#1e3a63">Open the portal &rarr;</a>');

    return html(res, 200, 'Charge kept ✓',
      '<b>' + esc(p.label) + '</b> stays on the reimbursement and is now marked <i>reviewed — dispute declined</i>. ' +
      'Nothing was removed.<br><br>' +
      '<a href="' + esc(portal) + '" style="color:#1e3a63">Open the portal &rarr;</a>');
  } catch (e) {
    return html(res, 500, 'Something went wrong',
      'The decision could not be saved. You can retry the link. Detail: ' + esc(e.message || e));
  }
};
