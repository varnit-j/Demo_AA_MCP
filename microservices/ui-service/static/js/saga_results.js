/**
 * SAGA Results Page JS:
 * - Reads initial logs from script#saga-logs-data (JSON array)
 * - Polls /api/saga/logs/<correlation_id>/ every 300ms
 * - Renders logs as plain text (one line per log)
 * - Instantly updates header/status banner from log content — no page reload needed
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

/**
 * Derive the final SAGA status purely from log content.
 * Returns 'completed' | 'failed' | 'in_progress'
 * Uses 3 independent failure signals to detect failure as early as possible:
 *   1. ORCHESTRATOR logs an ERROR (step failed)
 *   2. ORCHESTRATOR logs the COMPENSATION step (compensation triggered = failure decided)
 *   3. Any compensation SUCCESS log arrived (rollback done)
 */
function deriveStatus(logs) {
  if (!Array.isArray(logs) || !logs.length) return 'in_progress';

  // SUCCESS: BookingDone step completed successfully
  const hasSuccess = logs.some(l => l &&
    String(l.step_name || '').toLowerCase() === 'bookingdone' &&
    String(l.log_level || '').toLowerCase() === 'success');
  if (hasSuccess) return 'completed';

  // FAILURE signal 1: ORCHESTRATOR logged a step error
  const hasOrchError = logs.some(l => l &&
    String(l.service || '').toUpperCase() === 'ORCHESTRATOR' &&
    String(l.log_level || '').toLowerCase() === 'error');

  // FAILURE signal 2: ORCHESTRATOR started compensation (step_name === 'COMPENSATION')
  // This appears at the same instant as the error — catches failure one poll earlier
  const hasCompStarted = logs.some(l => l &&
    String(l.service || '').toUpperCase() === 'ORCHESTRATOR' &&
    String(l.step_name || '').toUpperCase() === 'COMPENSATION');

  // FAILURE signal 3: any compensation SUCCESS log — rollback fully done
  const hasCompDone = logs.some(l => l && l.is_compensation &&
    String(l.log_level || '').toLowerCase() === 'success');

  if (hasOrchError || hasCompStarted || hasCompDone) return 'failed';

  return 'in_progress';
}

/** Auto-reveal the logs panel so the user sees details when status resolves */
function revealLogs() {
  const logsDiv = document.getElementById('dynamic-saga-logs-placeholder');
  const button = document.querySelector('.saga-logs-toggle');
  if (logsDiv && !logsDiv.classList.contains('show')) {
    logsDiv.classList.add('show');
    if (button) button.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Technical Details';
  }
}

/** Apply final status to the page banner and cards without a reload */
function applyStatus(status) {
  const header = document.getElementById('saga-page-header');
  const titleEl = document.getElementById('saga-header-title');
  const subtitleEl = document.getElementById('saga-header-subtitle');
  const statusCard = document.getElementById('saga-status-card');
  const whatHappened = document.getElementById('saga-what-happened-text');
  const whatWeDidContent = document.getElementById('saga-what-we-did-content');

  if (!header || !titleEl) return;  // elements not present on this page variant

  // Remove existing colour classes
  header.classList.remove('success', 'error', 'progress');
  if (statusCard) statusCard.classList.remove('success', 'error', 'progress');

  if (status === 'completed') {
    header.classList.add('success');
    if (statusCard) statusCard.classList.add('success');
    titleEl.innerHTML = '<i class="fas fa-check-circle saga-icon"></i> Transaction Successful';
    if (subtitleEl) subtitleEl.textContent = 'Your booking completed successfully. Logs below show each SAGA step.';
    if (whatHappened) whatHappened.textContent = 'Your booking was completed successfully across Backend, Payment, and Loyalty services.';
    if (whatWeDidContent) whatWeDidContent.innerHTML = `
      <p>Your booking succeeded. The system coordinated all services using the SAGA pattern.</p>
      <ul>
        <li><strong>Seat Reserved:</strong> Backend reserved your seat</li>
        <li><strong>Payment Authorized:</strong> Payment service authorized the transaction</li>
        <li><strong>Miles Awarded:</strong> Loyalty service updated your miles balance</li>
        <li><strong>Booking Confirmed:</strong> Backend confirmed and created the ticket</li>
      </ul>`;
  } else if (status === 'failed') {
    header.classList.add('error');
    if (statusCard) statusCard.classList.add('error');
    titleEl.innerHTML = '<i class="fas fa-exclamation-triangle saga-icon"></i> Transaction Failed';
    if (subtitleEl) subtitleEl.textContent = 'Your booking could not be completed. See logs below for details.';
    if (whatHappened) whatHappened.textContent = 'Your booking attempt failed during the transaction process. Your account remains unchanged and no charges were applied.';
    if (whatWeDidContent) whatWeDidContent.innerHTML = `
      <p>Your booking attempt failed during the distributed transaction process. Here's what our system did:</p>
      <ul>
        <li><strong>Automatic Rollback:</strong> All completed steps were automatically reversed</li>
        <li><strong>No Charges:</strong> No payment was processed due to the failure</li>
        <li><strong>Data Consistency:</strong> Your account and loyalty points remain unchanged</li>
        <li><strong>System Recovery:</strong> All services are ready for your next booking attempt</li>
      </ul>`;
  } else {
    header.classList.add('progress');
    if (statusCard) statusCard.classList.add('progress');
    titleEl.innerHTML = '<i class="fas fa-spinner fa-spin saga-icon"></i> Transaction In Progress';
    if (subtitleEl) subtitleEl.textContent = 'Your booking is processing. Logs below will update as each step completes.';
    if (whatHappened) whatHappened.textContent = 'Your booking is in progress. The log stream below shows each microservice step as it completes.';
    if (whatWeDidContent) whatWeDidContent.innerHTML = '<p>Your booking is processing. If a step fails, compensations will automatically run to keep data consistent.</p>';
  }
}

let lastKeys = new Set();
let currentStatus = 'in_progress';
let pollingActive = true;

function render(container, logs) {
  const norm = normalizeLogs(logs);
  if (!norm.length) {
    container.textContent = 'Loading real-time logs...\n(no logs yet)';
    return;
  }
  lastKeys = new Set(norm.map(x => x.key));
  container.textContent = norm.map(x => x.line).join('\n');
  // Auto-scroll to bottom so latest log is always visible
  container.scrollTop = container.scrollHeight;
}

async function pollOnce(correlationId, container) {
  if (!pollingActive) return;
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

    // Derive status from logs — instant, no server roundtrip
    const newStatus = deriveStatus(logs);
    if (newStatus !== currentStatus) {
      currentStatus = newStatus;
      applyStatus(newStatus);
      // Auto-reveal logs so user immediately sees what happened
      if (newStatus === 'failed' || newStatus === 'completed') {
        revealLogs();
      }
    }

    // Stop polling once we reach a terminal state
    if (newStatus === 'completed' || newStatus === 'failed') {
      pollingActive = false;
    }
  } catch (e) {
    // silence polling errors
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const correlationId = getUrlParameter('correlation_id');
  const container = ensureLogsContainer();
  if (!container || !correlationId) return;

  const embedded = parseEmbeddedLogs();
  render(container, embedded);

  // Apply status from embedded logs immediately on page load
  const initialStatus = deriveStatus(embedded);
  if (initialStatus !== 'in_progress') {
    currentStatus = initialStatus;
    applyStatus(initialStatus);
    if (initialStatus === 'completed' || initialStatus === 'failed') {
      pollingActive = false;
      return;  // No need to poll if already terminal
    }
  }

  setInterval(() => pollOnce(correlationId, container), 300);
});