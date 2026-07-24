// Shared helpers for the dispute API. Files beginning with "_" are not routes.
const crypto = require('crypto');

const REPO_FILE = 'docs/overrides.json'; // served live by GitHub Pages at /overrides.json

function b64url(buf) {
  return Buffer.from(buf).toString('base64')
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function b64urlToBuf(s) {
  s = String(s).replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  return Buffer.from(s, 'base64');
}

// token = b64url(payloadJSON) + "." + b64url(HMAC-SHA256(secret, payload))
function sign(payloadObj, secret) {
  const p = b64url(JSON.stringify(payloadObj));
  const sig = b64url(crypto.createHmac('sha256', secret).update(p).digest());
  return p + '.' + sig;
}
function verify(token, secret) {
  if (!token || !secret) return null;
  const parts = String(token).split('.');
  if (parts.length !== 2) return null;
  const [p, sig] = parts;
  const exp = b64url(crypto.createHmac('sha256', secret).update(p).digest());
  const a = Buffer.from(sig), b = Buffer.from(exp);
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;
  try { return JSON.parse(b64urlToBuf(p).toString('utf8')); } catch (e) { return null; }
}

function readBody(req) {
  return new Promise((resolve) => {
    // Vercel may have already parsed it.
    if (req.body && typeof req.body === 'object') return resolve(req.body);
    let raw = '';
    req.on('data', (c) => { raw += c; if (raw.length > 1e6) req.destroy(); });
    req.on('end', () => {
      if (!raw) return resolve({});
      const ct = String(req.headers['content-type'] || '');
      try {
        if (ct.indexOf('application/json') >= 0) return resolve(JSON.parse(raw));
        if (ct.indexOf('application/x-www-form-urlencoded') >= 0) {
          const o = {}; new URLSearchParams(raw).forEach((v, k) => { o[k] = v; }); return resolve(o);
        }
        return resolve(JSON.parse(raw)); // best effort
      } catch (e) { resolve({}); }
    });
    req.on('error', () => resolve({}));
  });
}

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}
function json(res, code, obj) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(obj));
}
function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function html(res, code, title, bodyHtml) {
  res.statusCode = code;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.end('<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>' + esc(title) + '</title>' +
    '<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:560px;' +
    'margin:12vh auto;padding:28px 30px;border:1px solid #e3e6ee;border-radius:14px;' +
    'box-shadow:0 8px 30px rgba(20,30,60,.08)">' +
    '<h2 style="margin:0 0 10px;color:#1e3a63;font-size:1.4rem">' + esc(title) + '</h2>' +
    '<div style="color:#333;line-height:1.55;font-size:1rem">' + bodyHtml + '</div></div>');
}

async function readOverrides(repo, token) {
  const url = 'https://api.github.com/repos/' + repo + '/contents/' + REPO_FILE + '?ref=main';
  const r = await fetch(url, {
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'User-Agent': 'dispute-bot' }
  });
  if (r.status === 404) return { data: { removed: [], denied: [] }, sha: null };
  if (!r.ok) throw new Error('GitHub read ' + r.status + ': ' + (await r.text()));
  const j = await r.json();
  let data;
  try { data = JSON.parse(Buffer.from(j.content, 'base64').toString('utf8')); }
  catch (e) { data = { removed: [], denied: [] }; }
  data.removed = data.removed || []; data.denied = data.denied || [];
  return { data, sha: j.sha };
}
async function writeOverrides(repo, token, data, sha, msg) {
  const url = 'https://api.github.com/repos/' + repo + '/contents/' + REPO_FILE;
  const body = {
    message: msg, branch: 'main',
    content: Buffer.from(JSON.stringify(data, null, 1)).toString('base64')
  };
  if (sha) body.sha = sha;
  const r = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json',
      'User-Agent': 'dispute-bot', 'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error('GitHub write ' + r.status + ': ' + (await r.text()));
}

module.exports = { sign, verify, readBody, cors, json, html, esc, readOverrides, writeOverrides };
