// WiFi Configuration JavaScript
let selectedNetwork = null;
let currentStatus = null;

$(document).ready(function() {
    // Load initial WiFi status
    loadWiFiStatus();
    
    // Setup event listeners
    setupEventListeners();
    
    // Auto-refresh status every 30 seconds
    setInterval(loadWiFiStatus, 30000);
});

function setupEventListeners() {
    // Scan networks button
    $('#scanBtn').on('click', scanNetworks);
    
    // WiFi form submission
    $('#wifiForm').on('submit', connectToNetwork);
    
    // Clear form button
    $('#clearBtn').on('click', clearForm);
    
    // Toggle password visibility
    $('#togglePassword').on('click', togglePasswordVisibility);
}

function loadWiFiStatus() {
    $.ajax({
        url: '/api/wifi/status',
        method: 'GET',
        success: function(response) {
            if (response.success && response.status) {
                // Check if the status has an error field
                if (response.status.status === 'error') {
                    displayCurrentStatus({
                        connected: false,
                        error: response.status.message || 'WiFi status check failed'
                    });
                } else {
                    displayCurrentStatus(response.status);
                    currentStatus = response.status;
                }
            } else {
                displayCurrentStatus({
                    connected: false,
                    error: 'WiFi service unavailable'
                });
            }
        },
        error: function(xhr) {
            console.error('Error loading WiFi status:', xhr);
            let errorMessage = 'Unable to check WiFi status';
            
            if (xhr.status === 0) {
                errorMessage = 'Connection failed - service may be unavailable';
            } else if (xhr.status === 404) {
                errorMessage = 'WiFi service not found';
            } else if (xhr.status === 500) {
                errorMessage = 'WiFi service error';
            } else if (xhr.responseJSON && xhr.responseJSON.detail) {
                errorMessage = xhr.responseJSON.detail;
            }
            
            displayCurrentStatus({
                connected: false,
                error: errorMessage
            });
        }
    });
}

function displayCurrentStatus(status) {
    const statusContainer = $('#currentStatus');
    
    if (status && status.connected) {
        const statusHtml = `
            <div class="d-flex align-items-center">
                <span class="status-indicator status-connected"></span>
                <div>
                    <strong class="text-success">Connected to: ${status.ssid}</strong>
                    ${status.ip_address ? `<br><small class="text-muted">IP Address: ${status.ip_address}</small>` : ''}
                </div>
            </div>
        `;
        statusContainer.html(statusHtml);
    } else {
        const errorText = status && status.error ? status.error : 'No WiFi connection';
        const statusHtml = `
            <div class="d-flex align-items-center">
                <span class="status-indicator status-disconnected"></span>
                <div>
                    <strong class="text-danger">${errorText}</strong>
                    <br><small class="text-info"><i class="fas fa-info-circle me-1"></i>Use the form below to connect to a WiFi network</small>
                </div>
            </div>
        `;
        statusContainer.html(statusHtml);
    }
}

function scanNetworks() {
    const scanBtn = $('#scanBtn');
    const originalText = scanBtn.html();
    
    // Show loading state
    scanBtn.prop('disabled', true);
    scanBtn.html('<i class="fas fa-spinner fa-spin me-2"></i>Scanning...');
    
    $('#networksList').html(`
        <div class="text-center p-4">
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <p class="text-muted">Scanning for WiFi networks...</p>
        </div>
    `);
    
    $.ajax({
        url: '/api/wifi/scan',
        method: 'GET',
        success: function(response) {
            if (response.success && response.networks && response.networks.networks) {
                displayNetworks(response.networks.networks);
            } else {
                showError('No networks found or scan failed');
                $('#networksList').html(`
                    <div class="text-center p-4">
                        <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <p class="text-muted">No networks found</p>
                    </div>
                `);
            }
        },
        error: function(xhr) {
            console.error('Error scanning networks:', xhr);
            showError('Failed to scan networks');
            $('#networksList').html(`
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-circle fa-3x text-danger mb-3"></i>
                    <p class="text-muted">Failed to scan networks</p>
                </div>
            `);
        },
        complete: function() {
            // Restore button state
            scanBtn.prop('disabled', false);
            scanBtn.html(originalText);
        }
    });
}

function displayNetworks(networks) {
    const networksList = $('#networksList');
    
    if (!networks || networks.length === 0) {
        networksList.html(`
            <div class="text-center p-4">
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <p class="text-muted">No networks found</p>
            </div>
        `);
        return;
    }
    
    let networksHtml = '';
    
    // Sort networks by signal strength (if available)
    const sortedNetworks = networks.sort((a, b) => {
        const strengthA = parseInt(a.signal) || 0;
        const strengthB = parseInt(b.signal) || 0;
        return strengthB - strengthA;
    });
    
    sortedNetworks.forEach((network, index) => {
        const isSecure = network.security && network.security !== 'Open' && network.security !== 'None';
        const signalStrength = parseInt(network.signal) || 0;
        const isConnected = currentStatus && currentStatus.connected && currentStatus.ssid === network.ssid;
        
        networksHtml += `
            <div class="wifi-card ${isConnected ? 'selected' : ''}" data-ssid="${network.ssid}" data-security="${network.security || 'Open'}">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-wifi me-3 text-primary"></i>
                            <div>
                                <strong>${network.ssid}</strong>
                                ${isConnected ? '<span class="badge bg-success ms-2">Connected</span>' : ''}
                                <br>
                                <small class="text-muted">
                                    <i class="fas fa-${isSecure ? 'lock' : 'lock-open'} me-1"></i>
                                    ${network.security || 'Open'}
                                </small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="signal-strength ${getSignalClass(signalStrength)}">
                            ${getSignalIcon(signalStrength)}
                            <small>${signalStrength}%</small>
                        </div>
                    </div>
                    <div class="col-md-3 text-end">
                        <button class="btn btn-sm btn-outline-primary select-network-btn" 
                                data-ssid="${network.ssid}" 
                                data-security="${network.security || 'Open'}">
                            <i class="fas fa-arrow-right"></i>
                            Select
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    networksList.html(networksHtml);
    
    // Add click handlers for network cards and buttons
    $('.wifi-card').on('click', function() {
        const ssid = $(this).data('ssid');
        const security = $(this).data('security');
        selectNetwork(ssid, security);
    });
    
    $('.select-network-btn').on('click', function(e) {
        e.stopPropagation();
        const ssid = $(this).data('ssid');
        const security = $(this).data('security');
        selectNetwork(ssid, security);
    });
}

function selectNetwork(ssid, security) {
    selectedNetwork = { ssid, security };
    
    // Update UI
    $('.wifi-card').removeClass('selected');
    $(`.wifi-card[data-ssid="${ssid}"]`).addClass('selected');
    
    // Fill form
    $('#ssid').val(ssid);
    
    // Clear password field if network is open
    if (security === 'Open') {
        $('#password').val('');
        $('#password').prop('disabled', true);
    } else {
        $('#password').prop('disabled', false);
        $('#password').focus();
    }
    
    showNotification(`Selected network: ${ssid}`, 'info');
}

function connectToNetwork(e) {
    e.preventDefault();
    
    const ssid = $('#ssid').val().trim();
    const password = $('#password').val();
    
    if (!ssid) {
        showError('Please enter a network name (SSID)');
        return;
    }
    
    const connectBtn = $('#connectBtn');
    const originalText = connectBtn.html();
    
    // Show loading state
    connectBtn.prop('disabled', true);
    connectBtn.html('<i class="fas fa-spinner fa-spin me-2"></i>Connecting...');
    
    // Show modal with connection status
    showConnectionModal(ssid);
    
    $.ajax({
        url: '/api/wifi/connect',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            ssid: ssid,
            password: password
        }),
        success: function(response) {
            if (response.success) {
                updateModalContent('success', `Successfully connected to ${ssid}!`);
                setTimeout(() => {
                    loadWiFiStatus(); // Refresh status
                }, 2000);
            } else {
                updateModalContent('error', 'Failed to connect to network');
            }
        },
        error: function(xhr) {
            console.error('Error connecting to WiFi:', xhr);
            const errorMsg = xhr.responseJSON?.detail || 'Connection failed';
            updateModalContent('error', errorMsg);
        },
        complete: function() {
            // Restore button state
            connectBtn.prop('disabled', false);
            connectBtn.html(originalText);
        }
    });
}

function showConnectionModal(ssid) {
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    $('#modalContent').html(`
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <p>Connecting to <strong>${ssid}</strong>...</p>
        <small class="text-muted">This may take a few moments</small>
    `);
    modal.show();
}

function updateModalContent(type, message) {
    let icon, colorClass;
    
    if (type === 'success') {
        icon = 'fas fa-check-circle';
        colorClass = 'text-success';
    } else {
        icon = 'fas fa-exclamation-circle';
        colorClass = 'text-danger';
    }
    
    $('#modalContent').html(`
        <i class="${icon} fa-3x ${colorClass} mb-3"></i>
        <p>${message}</p>
    `);
}

function clearForm() {
    $('#ssid').val('');
    $('#password').val('');
    $('#password').prop('disabled', false);
    $('.wifi-card').removeClass('selected');
    selectedNetwork = null;
}

function togglePasswordVisibility() {
    const passwordField = $('#password');
    const toggleBtn = $('#togglePassword');
    const icon = toggleBtn.find('i');
    
    if (passwordField.attr('type') === 'password') {
        passwordField.attr('type', 'text');
        icon.removeClass('fa-eye').addClass('fa-eye-slash');
    } else {
        passwordField.attr('type', 'password');
        icon.removeClass('fa-eye-slash').addClass('fa-eye');
    }
}

function getSignalIcon(strength) {
    const level = parseInt(strength) || 0;
    
    if (level >= 75) return '<i class="fas fa-wifi"></i>';
    if (level >= 50) return '<i class="fas fa-wifi"></i>';
    if (level >= 25) return '<i class="fas fa-wifi"></i>';
    return '<i class="fas fa-wifi"></i>';
}

function getSignalClass(strength) {
    const level = parseInt(strength) || 0;
    
    if (level >= 50) return 'signal-strong';
    if (level >= 25) return 'signal-weak';
    return 'signal-very-weak';
}

function showNotification(message, type = 'info') {
    const alertType = type === 'error' ? 'danger' : type;
    const alert = $(`
        <div class="alert alert-${alertType} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 1055; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(alert);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        alert.alert('close');
    }, 4000);
}

function showError(message) {
    showNotification(message, 'error');
}
