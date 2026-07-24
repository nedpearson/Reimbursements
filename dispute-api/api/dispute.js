// POST /api/dispute  — receives a dispute from the portal, emails Ned (via FormSubmit)
// with one-click Approve / Deny buttons that carry a signed token for /api/decide.
const { sign, readBody, cors, json } = require('./_lib');

module.exports = async (req, res) => {
  cors(res);
  if (req.method === 'OPTIONS') { res.statusCode = 204; return res.end(); }
  if (req.method !== 'POST') return json(res, 405, { success: false, message: 'POST only' });

  try {
    const secret = process.env.SIGN_SECRET;
    const notify = process.env.NOTIFY_EMAIL;
    if (!secret || !notify) return json(res, 500, { success: false, message: 'server not configured' });

    const b = await readBody(req);
    const id = (b.id || '').toString().trim();
    const label = (b.label || b.Charge || 'this charge').toString().trim();
    if (!id) return json(res, 400, { success: false, message: 'missing charge id' });

    const base = 'https://' + req.headers.host;
    const mk = (action) => base + '/api/decide?t=' +
      encodeURIComponent(sign({ id: id, label: label, date: b.date || '', action: action, iat: Date.now() }, secret));

    const payload = {
      _subject: 'Dispute filed — ' + label,
      _template: 'table',
      Charge: label,
      Reason: b.reason || b.Reason || '(none given)',
      From: b.name || b.Your_name || '(not given)',
      'APPROVE — remove this charge from the reimbursement': mk('approve'),
      'DENY — keep this charge (marks it reviewed)': mk('deny'),
      _note: 'Click APPROVE to auto-remove the charge, or DENY to keep it. The portal updates within ~1 minute.'
    };

    let emailed = '';
    try {
      const r = await fetch('https://formsubmit.co/ajax/' + encodeURIComponent(notify), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(payload)
      });
      const jr = await r.json().catch(() => ({}));
      emailed = String(jr.success || '');
    } catch (e) { emailed = 'error:' + (e.message || e); }

    return json(res, 200, { success: true, emailed: emailed });
  } catch (e) {
    return json(res, 500, { success: false, message: String(e.message || e) });
  }
};
