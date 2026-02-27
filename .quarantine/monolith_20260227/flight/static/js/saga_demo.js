
/**
 * SAGA Demo JavaScript - Dynamic Log Display and Real-time Updates
 * Handles checkbox selection and shows appropriate logs with visual feedback
 */

// SAGA Step Configuration with logos and details
const SAGA_STEPS = {
    'reserveseat': {
        name: 'Reserve Seat',
        icon: '💺',
        service: 'Backend Service',
        description: 'Reserve seat on the selected flight',
        step_number: 1
    },
    'authorizepayment': {
        name: 'Authorize Payment',
        icon: '💳',
        service: 'Payment Service', 
        description: 'Authorize payment for the booking',
        step_number: 2
    },
    'awardmiles': {
        name: 'Award Miles',
        icon: '🏆',
        service: 'Loyalty Service',
        description: 'Award loyalty miles to customer',
        step_number: 3
    },
    'confirmbooking': {
        name: 'Confirm Booking',
        icon: '📋',
        service: 'Backend Service',
        description: 'Finalize and confirm the booking',
        step_number: 4
    }
};

// Current selected failure type
let selectedFailureType = null;

/**
 * Initialize SAGA demo functionality
 */
function initializeSagaDemo() {
    console.log('[SAGA DEMO] Initializing dynamic SAGA demo functionality');
    
    // Add event listeners to checkboxes
    const checkboxes = document.querySelectorAll('input[name^="simulate_"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleCheckboxChange);
    });
    
    // Initialize with no failure selected
    updateSagaDemoDisplay(null);
}

/**
 * Handle checkbox change events
 */
function handleCheckboxChange(event) {
    const checkbox = event.target;
    const failureType = extractFailureType(checkbox.name);
    
    console.log(`[SAGA DEMO] Checkbox changed: ${checkbox.name}, checked: ${checkbox.checked}`);
    
    if (checkbox.checked) {
        // Uncheck other checkboxes (only one failure at a time)
        const otherCheckboxes = document.querySelectorAll('input[name^="simulate_"]:not([name="' + checkbox.name + '"])');
        otherCheckboxes.forEach(cb => cb.checked = false);
        
        selectedFailureType = failureType;
        console.log(`[SAGA DEMO] Selected failure type: ${selectedFailureType}`);
    } else {
        selectedFailureType = null;
        console.log('[SAGA DEMO] No failure type selected');
    }
    
    // Update the display
    updateSagaDemoDisplay(selectedFailureType);
    
    // Show real-time preview
    showRealTimePreview(selectedFailureType);
    
    // Update the saga demo mode flag
    updateSagaDemoMode();
}

/**
 * Extract failure type from checkbox name
 */
function extractFailureType(checkboxName) {
    // Convert "simulate_reserveseat_fail" to "reserveseat"
    return checkboxName.replace('simulate_', '').replace('_fail', '');
}

/**
 * Update SAGA demo display based on selected failure type
 */
function updateSagaDemoDisplay(failureType) {
    console.log(`[SAGA DEMO] Updating display for failure type: ${failureType}`);
    
    // Create or update the dynamic logs container
    createDynamicLogsContainer();
    
    // Generate and display logs based on failure type
    if (failureType) {
        displayFailureScenarioLogs(failureType);
        showStepsProgress(failureType);
    } else {
        displaySuccessScenarioLogs();
        showStepsProgress(null);
    }
}

/**
 * Create dynamic logs container if it doesn't exist
 */
function createDynamicLogsContainer() {
    let container = document.getElementById('dynamic-saga-logs');
    if (!container) {
        container = document.createElement('div');
        container.id = 'dynamic-saga-logs';
        container.style.cssText = `
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        `;
        
        // Insert after SAGA demo section
        const demoSection = document.querySelector('.saga-demo-section');
        if (demoSection) {
            demoSection.parentNode.insertBefore(container, demoSection.nextSibling);
        }
    }
    return container;
}

/**
 * Display logs for failure scenario
 */
function displayFailureScenarioLogs(failureType) {
    const container = document.getElementById('dynamic-saga-logs');
    const failedStep = SAGA_STEPS[failureType];
    
    if (!failedStep) {
        console.error(`[SAGA DEMO] Unknown failure type: ${failureType}`);
        return;
    }
    
    const currentTime = new Date();
    let logs = [];
    
    // Add header
    logs.push(`<div style="background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-weight: bold;">
        📊 SAGA Transaction Simulation - Failure at ${failedStep.name}
    </div>`);
    
    // Generate logs for successful steps
    for (let i = 1; i < failedStep.step_number; i++) {
        const step = Object.values(SAGA_STEPS).find(s => s.step_number === i);
        if (step) {
            const stepTime = new Date(currentTime.getTime() + (i * 1000));
            logs.push(createLogEntry(stepTime, step.service, 'INFO', `${step.icon} ${step.name} initiated`));
            logs.push(createLogEntry(new Date(stepTime.getTime() + 500), step.service, 'SUCCESS', `✅ ${step.name} completed successfully`));
        }
    }
    
    // Add failed step
    const failTime = new Date(currentTime.getTime() + (failedStep.step_number * 1000));
    logs.push(createLogEntry(failTime, failedStep.service, 'INFO', `${failedStep.icon} ${failedStep.name} initiated`));
    logs.push(createLogEntry(new Date(failTime.getTime() + 500), failedStep.service, 'ERROR', `❌ Simulated failure in ${failedStep.name}`));
    
    container.innerHTML = logs.join('');
}

/**
 * Display logs for success scenario
 */
function displaySuccessScenarioLogs() {
    const container = document.getElementById('dynamic-saga-logs');
    const currentTime = new Date();
    let logs = [];
    
    // Add header
    logs.push(`<div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-weight: bold;">
        ✅ SAGA Transaction Simulation - All Steps Successful
    </div>`);
    
    // Generate logs for all successful steps
    Object.values(SAGA_STEPS).forEach(step => {
        const stepTime = new Date(currentTime.getTime() + (step.step_number * 1000));
        logs.push(createLogEntry(stepTime, step.service, 'INFO', `${step.icon} ${step.name} initiated`));
        logs.push(createLogEntry(new Date(stepTime.getTime() + 500), step.service, 'SUCCESS', `✅ ${step.name} completed successfully`));
    });
    
    container.innerHTML = logs.join('');
}

/**
 * Create a log entry HTML
 */
function createLogEntry(timestamp, service, level, message) {
    const timeStr = timestamp.toLocaleTimeString();
    const levelColor = {
        'INFO': '#17a2b8',
        'SUCCESS': '#28a745',
        'ERROR': '#dc3545',
        'WARNING': '#ffc107'
    }[level] || '#6c757d';
    
    return `<div style="margin-bottom: 5px; padding: 3px 0; border-bottom: 1px solid #eee;">
        <span style="color: #6c757d; margin-right: 10px;">[${timeStr}]</span>
        <span style="color: ${levelColor}; font-weight: bold; margin-right: 10px;">[${service}]</span>
        <span>${message}</span>
    </div>`;
}

/**
 * Show steps progress with visual indicators
 */
function showStepsProgress(failureType) {
    let progressContainer = document.getElementById('saga-steps-progress');
    if (!progressContainer) {
        progressContainer = document.createElement('div');
        progressContainer.id = 'saga-steps-progress';
        progressContainer.style.cssText = `
            background: #ffffff;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        `;
        
        const logsContainer = document.getElementById('dynamic-saga-logs');
        if (logsContainer) {
            logsContainer.parentNode.insertBefore(progressContainer, logsContainer.nextSibling);
        }
    }
    
    let stepsHtml = '<h5 style="color: #495057; margin-bottom: 15px;">📊 SAGA Transaction Steps</h5>';
    
    Object.values(SAGA_STEPS).forEach(step => {
        let status = 'pending';
        let statusIcon = '⏳';
        let statusColor = '#6c757d';
        
        if (failureType) {
            const failedStep = SAGA_STEPS[failureType];
            if (step.step_number < failedStep.step_number) {
                status = 'completed';
                statusIcon = '✅';
                statusColor = '#28a745';
            } else if (step.step_number === failedStep.step_number) {
                status = 'failed';
                statusIcon = '❌';
                statusColor = '#dc3545';
            }
        } else {
            status = 'completed';
            statusIcon = '✅';
            statusColor = '#28a745';
        }
        
        stepsHtml += `
            <div style="display: flex; align-items: center; margin-bottom: 10px; padding: 8px; border-radius: 5px; background: ${status === 'failed' ? '#f8d7da' : status === 'completed' ? '#d4edda' : '#f8f9fa'};">
                <span style="font-size: 20px; margin-right: 10px;">${step.icon}</span>
                <div style="flex: 1;">
                    <strong style="color: ${statusColor};">${step.name}</strong>
                    <br><small style="color: #6c757d;">${step.description}</small>
                </div>
                <span style="font-size: 18px; color: ${statusColor};">${statusIcon}</span>
            </div>
        `;
    });
    
    progressContainer.innerHTML = stepsHtml;
}

/**
 * Update saga demo mode flag
 */
function updateSagaDemoMode() {
    const checkboxes = document.querySelectorAll('input[name^="simulate_"]');
    const sagaDemoInput = document.getElementById('sagaDemoMode');
    let anyChecked = false;
    
    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            anyChecked = true;
        }
    });
    
    if (sagaDemoInput) {
        sagaDemoInput.value = anyChecked ? 'true' : 'false';
        console.log('[SAGA DEMO] Demo mode set to:', sagaDemoInput.value);
    }
}

/**
 * Show real-time preview of selected failure scenario
 */
function showRealTimePreview(failureType) {
    let previewContainer = document.getElementById('saga-real-time-preview');
    if (!previewContainer) {
        previewContainer = document.createElement('div');
        previewContainer.id = 'saga-real-time-preview';
        previewContainer.style.cssText = `
            background: #e3f2fd;
            border: 2px solid #2196f3;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            font-size: 13px;
        `;
        
        const demoSection = document.querySelector('.saga-demo-section');
        if (demoSection) {
            demoSection.appendChild(previewContainer);
        }
    }
    
    if (failureType) {
        const failedStep = SAGA_STEPS[failureType];
        previewContainer.innerHTML = `
            <div style="color: #1976d2; font-weight: bold; margin-bottom: 10px;">
                🔮 Preview: ${failedStep.name} Failure
            </div>
            <div style="margin-top: 10px; padding: 8px; background: #fff3e0; border-radius: 4px; color: #f57c00;">
                💡 Will fail at step ${failedStep.step_number} and compensate ${failedStep.step_number - 1} step(s)
            </div>
        `;
    } else {
        previewContainer.innerHTML = `
            <div style="color: #4caf50; font-weight: bold;">
                ✅ Success Scenario - All steps will complete
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SAGA DEMO] DOM loaded, initializing SAGA demo');
    initializeSagaDemo();
});