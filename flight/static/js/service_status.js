
/**
 * POC PHASE 3D: POC Loading States for Microservices
 * Visual service status dashboard showing real-time microservice health and progress
 */

/**
 * Initialize service status display
 */
function updateServiceStatusDisplay() {
    const container = document.getElementById('service-status-container');
    if (!container) return;
    
    const services = [
        { name: 'Backend Service', icon: '🖥️', step: 1, description: 'Reserve Seat & Confirm Booking' },
        { name: 'Payment Service', icon: '💳', step: 2, description: 'Authorize Payment' },
        { name: 'Loyalty Service', icon: '🏆', step: 3, description: 'Award Miles' }
    ];
    
    let statusHtml = `
        <div style="background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 8px; padding: 15px;">
            <h5 style="color: #495057; margin-bottom: 15px;">🔄 Microservice Status Dashboard</h5>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
    `;
    
    services.forEach(service => {
        statusHtml += createServiceStatusCard(service, 'connecting');
    });
    
    statusHtml += `
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 5px; font-size: 12px; color: #1976d2;">
                💡 <strong>POC Demo:</strong> Watch each microservice process in real-time. Services communicate via SAGA orchestration pattern.
            </div>
        </div>
    `;
    
    container.innerHTML = statusHtml;
}

/**
 * Create individual service status card
 */
function createServiceStatusCard(service, status) {
    const statusConfig = {
        'connecting': { color: '#6c757d', bg: '#f8f9fa', text: 'Connecting...', icon: '⏳' },
        'processing': { color: '#ffc107', bg: '#fff3cd', text: 'Processing...', icon: '🔄' },
        'success': { color: '#28a745', bg: '#d4edda', text: 'Completed', icon: '✅' },
        'error': { color: '#dc3545', bg: '#f8d7da', text: 'Failed', icon: '❌' },
        'compensating': { color: '#fd7e14', bg: '#ffeaa7', text: 'Compensating...', icon: '🔄' }
    };
    
    const config = statusConfig[status] || statusConfig['connecting'];
    
    return `
        <div id="service-${service.name.replace(/\s+/g, '-').toLowerCase()}" 
             style="background: ${config.bg}; border: 1px solid ${config.color}; border-radius: 8px; padding: 12px; transition: all 0.3s ease;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 20px; margin-right: 8px;">${service.icon}</span>
                <div style="flex: 1;">
                    <div style="font-weight: bold; color: ${config.color};">${service.name}</div>
                    <div style="font-size: 11px; color: #6c757d;">Step ${service.step}: ${service.description}</div>
                