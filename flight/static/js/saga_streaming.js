
/**
 * POC PHASE 3C: Real-time Service Updates Streaming
 * Handles live microservice monitoring and log streaming for SAGA transactions
 */

/**
 * Start real-time log polling with service status tracking
 */
function startRealTimeLogPolling(correlationId, container) {
    console.log('[POC_STREAMING] Starting real-time polling for correlation:', correlationId);
    
    let pollCount = 0;
    let lastLogCount = 0;
    const maxPolls = 30; // Poll for 30 seconds
    
    // Initialize service status display
    updateServiceStatusDisplay();
    
    const pollInterval = setInterval(() => {
        pollCount++;
        console.log(`[POC_STREAMING] Poll ${pollCount}/${maxPolls} for correlation: ${correlationId}`);
        
        // Update streaming status
        updateStreamingStatus(`⚡ Live polling... (${pollCount}/${maxPolls})`);
        
        // Fetch latest logs
        fetch(`/api/saga/logs/${correlationId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.logs && data.logs.length > lastLogCount) {
                    console.log(`[POC_STREAMING] New logs detected: ${data.logs.length} (was ${lastLogCount})`);
                    lastLogCount = data.logs.length;
                    displayStreamingLogs(data.logs, correlationId);
                    updateServiceStatusFromLogs(data.logs);
                    
                    // Check if SAGA is complete
                    const isComplete = data.logs.some(log => 
                        log.message.includes('SAGA completed') || 
                        log.message.includes('SAGA failed') ||
                        log.message.includes('compensation completed')
                    );
                    
                    if (isComplete) {
                        console.log('[POC_STREAMING] SAGA transaction completed, stopping polling');
                        clearInterval(pollInterval);
                        updateStreamingStatus('✅ SAGA transaction completed');
                    }
                } else if (pollCount === 1) {
                    // No logs yet on first poll, show demo logs for immediate feedback
                    displayDemoStreamingLogs(correlationId);
                }
            })
            .catch(error => {
                console.error(`[POC_STREAMING] Poll ${pollCount} error:`, error);
                if (pollCount === 1) {
                    // First poll failed, show demo logs
                    displayDemoStreamingLogs(correlationId);
                }
            });
        
        // Stop polling after max attempts
        if (pollCount >= maxPolls) {
            console.log('[POC_STREAMING] Max polls reached, stopping');
            clearInterval(pollInterval);
            updateStreamingStatus('⏰ Polling completed');
        }
    }, 1000); // Poll every 1 second
}

/**
 * Update streaming status message
 */
function updateStreamingStatus(message) {
    const statusElement = document.getElementById('streaming-status');
    if (statusElement) {
        statusElement.innerHTML = message;
    }
}

/**
 * Display streaming logs with real-time updates
 */
function displayStreamingLogs(logs, correlationId) {
    const container = document.getElementById('live-logs-container');
    if (!container) return;
    
    let logHtml = `<div style="color: #28a745; margin-bottom: 10px;">📊 Live SAGA Logs (${logs.length} entries)</div>`;
    
    logs.forEach(log => {
        const timestamp = new Date(log.timestamp).toLocaleTimeString();
        const serviceColor = getServiceColor(