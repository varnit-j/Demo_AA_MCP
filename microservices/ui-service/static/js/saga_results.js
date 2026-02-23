/**
 * SAGA Results Page JS (compact):
 * - Reads initial logs from script#saga-logs-data (JSON array)
 * - Polls /api/saga/logs/<correlation_id>/ every 1s
 * - Renders logs as plain text (one line per log)
 */

function getUrlParameter(name) {
  name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
  const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
  const results = regex.exec(location.search);
  return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

function ensureLogsContainer() {
  const existing = document.getElementById('dynamic-saga-logs');
  if (existing) return existing;

  const placeholder = document.getElementById('dynamic-saga-logs-placeholder');
  if (!placeholder) return null;

  const container = document.createElement('pre');
  container.id = 'dynamic-saga-logs';
  container.style.cssText =
    'background:#1e1e1e;color:#f8f9fa;border-radius:8px;padding:20px;' +
    "font-family:'Courier New', monospace;font-size:13px;max-height:400px;" +
    'overflow-y:auto;margin:20px 0;border:1px solid #495057;white-space:pre-wrap;';
  placeholder.parentNode.replaceChild(container, placeholder);
  return container;
}

function parseEmbeddedLogs() {
  const el = document.getElementById('saga-logs-data');
  if (!el) return [];
  try {
    const parsed = JSON.parse(el.textContent || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    console.warn('[SAGA RESULT] Failed to parse embedded logs JSON', e);
    return [];
  }
}

function normalizeLogs(logs) {
  if (!Array.isArray(logs)) return [];
  return logs.map((l) => {
    const o = (l && typeof l === 'object') ? l : {};
    const ts = o.timestamp_full || o.timestamp || o.date_local || o.date || '';
    const svc = o.service || 'Unknown';
    const step = o.step_name || '';
    const lvl = (o.log_level || 'info').toString().toUpperCase();
    const msg = (o.message || '').toString();
    return {
      key: ts + '|' + svc + '|' + step + '|' + lvl + '|' + msg,
      line: `[${ts}] [${svc}] [${step}] [${lvl}] ${msg}`
    };
  });
}

let lastKeys = new Set();

function render(container, logs) {
  const norm = normalizeLogs(logs);
  if (!norm.length) {
    container.textContent = 'Loading real-time logs...\n(no logs yet)';
    return;
  }
  lastKeys = new Set(norm.map(x => x.key));
  container.textContent = norm.map(x => x.line).join('\n');
}

async function pollOnce(correlationId, container) {
  try {
    const resp = await fetch(`/api/saga/logs/${encodeURIComponent(correlationId)}/`, { cache: 'no-store' });
    if (!resp.ok) return;
    const data = await resp.json();
    const logs = (data && data.logs) ? data.logs : [];
    const norm = normalizeLogs(logs);
    const keys = new Set(norm.map(x => x.key));
    const changed = keys.size !== lastKeys.size;
    if (changed) render(container, logs);
    lastKeys = keys;
    const hasConfirmSuccess = logs.some(l => l && l.step_name === 'BookingDone' && String(l.log_level || '').toLowerCase() === 'success');
    const hasOrchError = logs.some(l => l && String(l.service || '').toUpperCase() === 'ORCHESTRATOR' && String(l.log_level || '').toLowerCase() === 'error');
    const hasComp = logs.some(l => l && l.is_compensation);
    if (hasConfirmSuccess || hasOrchError || hasComp) window.location.reload(true);
  } catch (e) {
    // silence polling errors
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const correlationId = getUrlParameter('correlation_id');
  const container = ensureLogsContainer();
  if (!container || !correlationId) return;

  render(container, parseEmbeddedLogs());
  setInterval(() => pollOnce(correlationId, container), 1000);
});