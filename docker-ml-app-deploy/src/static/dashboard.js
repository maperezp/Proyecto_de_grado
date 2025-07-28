// Dashboard JavaScript functionality
let selectedDevice = null;
let selectedPeriod = null;
let currentPredictions = null;

// Inicializar la aplicación
$(document).ready(function() {
    loadDevices();
    loadModels();
    initializeDateTimes();
    updatePredictButton();
    
    // Cargar todas las predicciones al inicio de la aplicación
    loadDatabasePredictions();
    
    // Actualizar estadísticas del dashboard al inicio
    updateDashboardStats();
    
    // Agregar evento para cargar datos de la base de datos cuando se activa la pestaña de predicciones
    $('button[data-bs-target="#predictions"]').on('shown.bs.tab', function() {
        // Cargar datos de la base de datos cuando se abre la pestaña de predicciones
        loadDatabasePredictions();
    });
});

function initializeDateTimes() {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    
    $('#endDateTime').val(formatDateTimeLocal(now));
    $('#startDateTime').val(formatDateTimeLocal(oneHourAgo));
}

function formatDateTimeLocal(date) {
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - (offset * 60 * 1000));
    return localDate.toISOString().slice(0, 16);
}

function loadDevices() {
    $('#devicesList').html('<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div><p>Loading devices...</p></div>');
    
    $.get('/api/devices')
        .done(function(data) {
            displayDevices(data.devices);
            updateConnectionStatus('online', data.connected ? 'Connected' : 'Demo Mode');
            if (data.demo_mode) {
                showDemoNotification();
            }
        })
        .fail(function(xhr) {
            $('#devicesList').html('<div class="alert alert-danger">Failed to load devices. <button class="btn btn-sm btn-outline-danger" onclick="loadDevices()">Retry</button></div>');
            updateConnectionStatus('offline', 'Connection Error');
            console.error('Error loading devices:', xhr);
        });
}

function showDemoNotification() {
    if (!$('#demoAlert').length) {
        const alert = $(`
            <div id="demoAlert" class="alert alert-info alert-dismissible fade show" role="alert">
                <strong>Demo Mode:</strong> Could not connect to PCH-Cloud. Using demo data.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
        $('.container-fluid').prepend(alert);
    }
}

function loadModels() {
    $.get('/api/models')
        .done(function(data) {
            const select = $('#modelSelect');
            select.empty();
            data.models.forEach(model => {
                select.append(`<option value="${model}">${model}</option>`);
            });
            if (data.models.length > 0) {
                select.val(data.models[0]);
                updateStatusModel(data.models[0]);
            }
            updatePredictButton();
            
            // Listener para cambios en el modelo
            select.off('change').on('change', function() {
                updateStatusModel($(this).val());
                updatePredictButton();
            });
        });
}

function displayDevices(devices) {
    const container = $('#devicesList');
    container.empty();

    if (devices.length === 0) {
        container.html('<div class="alert alert-info">No devices found</div>');
        return;
    }

    devices.forEach(device => {
        const deviceCard = $(`
            <div class="device-card" onclick="selectDevice('${device.id}', '${device.name || device.id}', event)">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="status-indicator status-online"></span>
                        <strong>${device.name || device.id}</strong>
                    </div>
                    <small class="text-muted">${device.type || 'Sensor'}</small>
                </div>
                <small class="text-muted">ID: ${device.id}</small>
            </div>
        `);
        container.append(deviceCard);
    });
}

function selectDevice(deviceId, deviceName, event) {
    selectedDevice = {
        id: deviceId,
        name: deviceName
    };
    
    // Actualizar UI
    $('.device-card').removeClass('active');
    $(event.currentTarget).addClass('active');
    
    // Actualizar estado
    updateStatusDevice(deviceName);
    updatePredictButton();
    
    // Cargar canales disponibles para este dispositivo
    loadDeviceChannels(deviceId);
    
    // Limpiar resultados anteriores
    clearResults();
}

function loadDeviceChannels(deviceId) {
    $.ajax({
        url: `/api/channels/${deviceId}`,
        method: 'GET',
        success: function(channelData) {
            updateChannelSelector(channelData);
        },
        error: function(xhr) {
            console.error('Error loading device channels:', xhr);
            // En caso de error, usar configuración por defecto
            updateChannelSelector({
                channels: [1, 2, 3],
                max_channels: 3,
                default_channel: 1
            });
        }
    });
}

function updateChannelSelector(channelData) {
    const channelSelect = $('#channelSelect');
    channelSelect.empty();
    
    // Agregar opciones de canal
    channelData.channels.forEach(channel => {
        const option = $(`<option value="${channel}">Canal ${channel}</option>`);
        channelSelect.append(option);
    });
    
    // Seleccionar el canal por defecto
    channelSelect.val(channelData.default_channel);
    
    // Mostrar información si hay algún mensaje
    if (channelData.message) {
        console.log('Channel info:', channelData.message);
    }
}

function setPeriod(periodType) {
    const now = new Date();
    let periodText = '';
    
    selectedPeriod = { period_type: periodType };
    
    // Limpiar selecciones de botones
    $('.btn-group-vertical .btn').removeClass('btn-secondary').addClass('btn-outline-secondary');
    
    if (periodType === 'last_minute') {
        periodText = 'Last Minute';
        $(event.target).removeClass('btn-outline-secondary').addClass('btn-secondary');
    } else if (periodType === 'last_hour') {
        periodText = 'Last Hour';
        $(event.target).removeClass('btn-outline-secondary').addClass('btn-secondary');
    } else if (periodType === 'last_24h') {
        periodText = 'Last 24 Hours';
        $(event.target).removeClass('btn-outline-secondary').addClass('btn-secondary');
    } else if (periodType === 'custom') {
        const startTime = $('#startDateTime').val();
        const endTime = $('#endDateTime').val();
        
        if (!startTime || !endTime) {
            alert('Please select both start and end dates');
            return;
        }
        
        if (startTime >= endTime) {
            alert('End time must be after start time');
            return;
        }
        
        selectedPeriod.start_time = new Date(startTime).toISOString();
        selectedPeriod.end_time = new Date(endTime).toISOString();
        
        periodText = `Custom: ${new Date(startTime).toLocaleString()} to ${new Date(endTime).toLocaleString()}`;
    }
    
    $('#selectedPeriod').show();
    $('#periodText').text(periodText);
    updateStatusPeriod(periodText);
    updatePredictButton();
    
    // Limpiar resultados anteriores
    clearResults();
}

function performPrediction() {
    if (!selectedDevice || !selectedPeriod) {
        alert('Please select a device and time period first');
        return;
    }
    
    const modelName = $('#modelSelect').val();
    if (!modelName) {
        alert('Please select a prediction model');
        return;
    }
    
    // Mostrar estado de carga
    $('#predictionStatus').show();
    $('#predictButton').prop('disabled', true);
    
    const requestData = {
        device_id: selectedDevice.id,
        model_name: modelName,
        period: selectedPeriod,
        channel: 1
    };
    
    $.ajax({
        url: '/api/predict/period',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(requestData),
        success: function(data) {
            currentPredictions = data;
            displayPredictionResults(data);
            $('#predictionStatus').hide();
            $('#predictButton').prop('disabled', false);
            
            // Mostrar indicador de actualización en la tabla
            $('#predictionsTableBody').html('<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm"></div> Updating table with new predictions...</td></tr>');
            $('#predictionsTable').show();
            
            // Actualizar inmediatamente la tabla de la base de datos mostrando todas las predicciones
            // Reducido el tiempo de espera para actualización más rápida
            setTimeout(function() {
                loadDatabasePredictions(false); // No preservar tarjetas, mostrar todas las predicciones
                showNotification('Nueva predicción guardada y tabla actualizada', 'success');
                
                // Scroll automático hacia arriba para mostrar la nueva predicción
                setTimeout(function() {
                    $('#predictionsTable').get(0).scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 200);
            }, 200); // Reducido a 200ms para una actualización más rápida
        },
        error: function(xhr) {
            console.error('Prediction error:', xhr);
            alert('Error performing predictions: ' + (xhr.responseJSON?.detail || 'Unknown error'));
            $('#predictionStatus').hide();
            $('#predictButton').prop('disabled', false);
        }
    });
}

function displayPredictionResults(data) {
    // Cambiar a la pestaña de predicciones automáticamente
    const predictionsTab = new bootstrap.Tab(document.getElementById('predictions-tab'));
    predictionsTab.show();
    
    // Mostrar resumen del período
    displayPeriodSummary(data.summary);
    
    // Mostrar información de grabaciones
    displayRecordingsInfo(data);
    
    // NO mostrar tabla de predicciones aquí - se actualizará con todas las predicciones después
    // displayPredictionsTable(data.predictions); // Comentado para evitar mostrar solo las nuevas
    
    // Mostrar probabilidades promedio del período actual
    displayProbabilities(data.predictions);
}

function displayPeriodSummary(summary) {
    let html = '';
    
    if (summary.total_recordings === 0) {
        html = '<p class="mb-0">No recordings found for the selected period</p>';
    } else {
        html = '<p class="mb-0">Prediction results ready - check probabilities below</p>';
    }
    
    $('#periodSummary').html(html);
}

function displayRecordingsInfo(data) {
    const html = `
        <strong>Device:</strong> ${selectedDevice.name}<br>
        <strong>Period:</strong> ${selectedPeriod.period_type}<br>
        <strong>Model:</strong> ${data.model_used}<br>
        <small class="text-muted">Last updated: ${new Date().toLocaleString()}</small>
    `;
    $('#recordingsInfo').html(html);
}

function displayPredictionsTable(predictions) {
    const tbody = $('#predictionsTableBody');
    tbody.empty();
    
    // Si no hay predicciones, mostrar mensaje informativo
    if (!predictions || predictions.length === 0) {
        tbody.html(`
            <tr>
                <td colspan="8" class="text-center text-muted">
                    <div class="py-4">
                        <i class="fas fa-info-circle fa-2x mb-2"></i>
                        <h5>No hay predicciones disponibles</h5>
                        <p class="mb-0">Selecciona un dispositivo y período de tiempo, luego presiona "Realizar Predicción" para generar nuevas predicciones.</p>
                    </div>
                </td>
            </tr>
        `);
        return;
    }
    
    predictions.forEach((pred, index) => {
        const timestamp = new Date(pred.timestamp).toLocaleString();
        const success = pred.success;
        const deviceId = pred.device_id || 'Unknown';
        const deviceName = pred.device_name || deviceId;
        
        let predictionText = '';
        let confidenceText = '';
        let probabilitiesText = '';
        let modelText = pred.model_name || 'Unknown';
        
        if (success && pred.prediction) {
            predictionText = pred.prediction.prediction || 'Unknown';
            if (pred.prediction.probabilities) {
                const maxProb = Math.max(...Object.values(pred.prediction.probabilities));
                confidenceText = `${(maxProb * 100).toFixed(1)}%`;
                
                // Mostrar las top 3 probabilidades
                const sortedProbs = Object.entries(pred.prediction.probabilities)
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3);
                
                probabilitiesText = sortedProbs.map(([className, prob]) => 
                    `<small class="d-block">${className}: ${(prob * 100).toFixed(1)}%</small>`
                ).join('');
            }
        } else {
            predictionText = '<span class="text-danger">Error</span>';
            confidenceText = '-';
            probabilitiesText = '-';
        }
        
        // Verificar si los datos están disponibles para el botón del ojo
        const isDataAvailable = success && pred.recording_id;
        const eyeButton = isDataAvailable ? 
            `<button class="btn btn-sm btn-outline-primary me-1" onclick="viewRecordingDetails('${pred.recording_id}', '${deviceId}')" title="View Details">
                <i class="fas fa-eye"></i>
            </button>` : 
            `<button class="btn btn-sm btn-outline-secondary me-1" disabled title="Data not available">
                <i class="fas fa-eye opacity-50"></i>
            </button>`;
        
        const row = $(`
            <tr class="${success ? 'prediction-row' : 'table-warning'}" 
                data-prediction-index="${index}" 
                data-recording-id="${pred.recording_id}"
                data-prediction-id="${pred.id}"
                style="cursor: pointer;">
                <td>${timestamp}</td>
                <td><small class="text-muted">${deviceName}</small></td>
                <td><small>${pred.recording_id}</small></td>
                <td>${predictionText}</td>
                <td>${confidenceText}</td>
                <td>${probabilitiesText}</td>
                <td><small>${modelText}</small></td>
                <td>
                    ${eyeButton}
                    <button class="btn btn-sm btn-outline-danger" onclick="deletePrediction(${pred.id}, event)" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `);
        
        // Agregar evento de clic para seleccionar fila
        row.on('click', function(e) {
            if (!$(e.target).closest('button').length) {
                selectPredictionRow(index, pred);
            }
        });
        
        tbody.append(row);
    });
    
    $('#predictionsTable').show();
}

function displayProbabilities(predictions) {
    if (!predictions || predictions.length === 0) {
        $('#probabilitiesInCard').hide();
        return;
    }
    
    // Verificar que las predicciones tengan probabilidades
    const validPredictions = predictions.filter(pred => pred.prediction && pred.prediction.probabilities);
    if (validPredictions.length === 0) {
        $('#probabilitiesInCard').hide();
        return;
    }
    
    // Calcular probabilidades promedio por clase
    const classTotals = {};
    const classNames = Object.keys(validPredictions[0].prediction.probabilities);
    
    // Inicializar contadores
    classNames.forEach(className => {
        classTotals[className] = 0;
    });
    
    // Sumar todas las probabilidades
    validPredictions.forEach(prediction => {
        Object.entries(prediction.prediction.probabilities).forEach(([className, probability]) => {
            classTotals[className] += probability;
        });
    });
    
    // Calcular promedios
    const averageProbabilities = {};
    classNames.forEach(className => {
        averageProbabilities[className] = classTotals[className] / validPredictions.length;
    });
    
    // Usar la función centralizada para mostrar probabilidades
    displayProbabilitiesInCard(averageProbabilities, `Average from ${validPredictions.length} predictions`);
}

// Función para eliminar una predicción
function deletePrediction(predictionId, event) {
    // Prevenir que se active el clic de la fila
    event.stopPropagation();
    
    if (!confirm('¿Está seguro de que desea eliminar esta predicción?')) {
        return;
    }
    
    $.ajax({
        url: `/api/predictions/${predictionId}`,
        method: 'DELETE',
        success: function(response) {
            console.log('Prediction deleted:', response);
            // Recargar la tabla de predicciones
            loadDatabasePredictions(false);
            // Mostrar mensaje de éxito
            showNotification('Predicción eliminada exitosamente', 'success');
        },
        error: function(xhr) {
            console.error('Error deleting prediction:', xhr);
            showNotification('Error al eliminar la predicción', 'error');
        }
    });
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const alertType = type === 'error' ? 'danger' : type;
    const alert = $(`
        <div class="alert alert-${alertType} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 1050; min-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(alert);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        alert.alert('close');
    }, 3000);
}

// Función mejorada para ver detalles de grabación
function viewRecordingDetails(recordingId, deviceId) {
    if (!selectedDevice && !deviceId) {
        showNotification('Device information not available', 'error');
        return;
    }
    
    const currentDeviceId = deviceId || selectedDevice.id;
    
    // Mostrar información de la grabación seleccionada
    $('#selectedRecordingInfo').text(`Recording ID: ${recordingId} (Device: ${currentDeviceId})`);
    $('#recordingDetails').show();
    
    // Mostrar loading en los gráficos
    $('#timePlot').html('<div class="text-center p-4"><div class="spinner-border"></div><p>Loading time plot...</p></div>');
    $('#fftPlot').html('<div class="text-center p-4"><div class="spinner-border"></div><p>Loading FFT plot...</p></div>');
    
    $.get(`/api/plot/${currentDeviceId}/${recordingId}`)
        .done(function(data) {
            if (data.time_plot) {
                Plotly.newPlot('timePlot', data.time_plot.data, data.time_plot.layout);
            } else {
                $('#timePlot').html('<div class="alert alert-warning">No time plot data available</div>');
            }
            
            if (data.fft_plot) {
                Plotly.newPlot('fftPlot', data.fft_plot.data, data.fft_plot.layout);
            } else {
                $('#fftPlot').html('<div class="alert alert-warning">No FFT plot data available</div>');
            }
            
            if (data.error) {
                showNotification(`Warning: ${data.error}`, 'warning');
            }
        })
        .fail(function(xhr) {
            $('#timePlot').html('<div class="alert alert-danger">Failed to load time plot data</div>');
            $('#fftPlot').html('<div class="alert alert-danger">Failed to load FFT plot data</div>');
            
            if (xhr.status === 404) {
                showNotification('Recording data not found or no longer available', 'error');
            } else {
                showNotification('Failed to load plot data', 'error');
            }
        });
}

function updateStatusDevice(deviceName) {
    $('#statusDevice').removeClass('bg-secondary bg-success').addClass('bg-success').text(deviceName);
}

function updateStatusPeriod(periodText) {
    $('#statusPeriod').removeClass('bg-secondary bg-success').addClass('bg-success').text(periodText);
}

function updateStatusModel(modelName) {
    $('#statusModel').removeClass('bg-secondary bg-success').addClass('bg-success').text(modelName);
}

function updatePredictButton() {
    const hasDevice = selectedDevice !== null;
    const hasPeriod = selectedPeriod !== null;
    const hasModel = $('#modelSelect').val() !== '';
    
    $('#predictButton').prop('disabled', !(hasDevice && hasPeriod && hasModel));
}

function clearResults() {
    currentPredictions = null;
    updateProbabilitiesOnly();
    $('#recordingsInfo').html('<p class="mb-0">No data available</p>');
    // NO ocultar la tabla - mantenerla visible con todas las predicciones
    // $('#predictionsTable').hide(); // Comentado para mantener tabla siempre visible
    $('#recordingDetails').hide();
    
    // También limpiar datos de señal
    clearSignalData();
}

function clearSignalData() {
    $('#signalCharts').hide();
    $('#noSignalData').show();
    $('#timeSignalPlot').empty();
    $('#fftSignalPlot').empty();
    $('#signalStats').empty();
}

// Función para cargar datos de señal del período
function loadSignalData() {
    if (!selectedDevice || !selectedPeriod) {
        alert('Please select a device and time period first');
        return;
    }
    
    const channel = $('#channelSelect').val();
    
    // Mostrar estado de carga
    $('#signalLoading').show();
    $('#signalCharts').hide();
    $('#noSignalData').hide();
    $('#loadSignalBtn').prop('disabled', true);
    
    // Primero obtener las grabaciones del período
    $.ajax({
        url: `/api/recordings/${selectedDevice.id}/period`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(selectedPeriod),
        success: function(recordingsData) {
            if (recordingsData.recordings && recordingsData.recordings.length > 0) {
                // Tomar la primera grabación como ejemplo
                const firstRecording = recordingsData.recordings[0];
                loadSignalPlots(selectedDevice.id, firstRecording.id, channel, recordingsData);
            } else {
                $('#signalLoading').hide();
                $('#noSignalData').html('<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> No recordings found for the selected period</div>').show();
                $('#loadSignalBtn').prop('disabled', false);
            }
        },
        error: function(xhr) {
            console.error('Error loading recordings:', xhr);
            $('#signalLoading').hide();
            $('#noSignalData').html('<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> Error loading recordings data</div>').show();
            $('#loadSignalBtn').prop('disabled', false);
        }
    });
}

function loadSignalPlots(deviceId, recordingId, channel, recordingsData) {
    // Cargar datos de la señal
    $.ajax({
        url: `/api/signal/period/${deviceId}`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            period: selectedPeriod,
            channel: parseInt(channel)
        }),
        success: function(signalData) {
            if (signalData.error) {
                $('#signalLoading').hide();
                $('#noSignalData').html(`<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> ${signalData.error}</div>`).show();
                if (signalData.debug_info) {
                    console.log('Debug info:', signalData.debug_info);
                }
            } else {
                displaySignalCharts(signalData, recordingsData);
                $('#signalLoading').hide();
                $('#signalCharts').show();
            }
            $('#loadSignalBtn').prop('disabled', false);
        },
        error: function(xhr) {
            console.error('Error loading signal data:', xhr);
            let errorMsg = 'Error loading signal data';
            if (xhr.responseJSON && xhr.responseJSON.detail) {
                errorMsg += ': ' + xhr.responseJSON.detail;
            }
            $('#signalLoading').hide();
            $('#noSignalData').html(`<div class="alert alert-danger"><i class="fas fa-exclamation-circle"></i> ${errorMsg}</div>`).show();
            $('#loadSignalBtn').prop('disabled', false);
        }
    });
}

function displaySignalCharts(signalData, recordingsData) {
    // Actualizar información del período
    if (signalData.debug_info) {
        const debugInfo = signalData.debug_info;
        $('#signalTimeInfo').text(`${debugInfo.total_recordings} recordings found, ${debugInfo.valid_recordings} used | Channel ${$('#channelSelect').val()} | ${selectedPeriod.period_type} | ${signalData.total_samples} samples`);
    } else {
        $('#signalTimeInfo').text(`${recordingsData.count} recordings found | Channel ${$('#channelSelect').val()} | ${selectedPeriod.period_type}`);
    }
    
    // Mostrar gráfico de tiempo
    if (signalData.time_plot && signalData.time_plot.data) {
        Plotly.newPlot('timeSignalPlot', signalData.time_plot.data, signalData.time_plot.layout, {responsive: true});
    } else {
        $('#timeSignalPlot').html('<div class="alert alert-warning">No se pudieron generar gráficos de tiempo</div>');
    }
    
    // Mostrar gráfico de FFT
    if (signalData.fft_plot && signalData.fft_plot.data) {
        Plotly.newPlot('fftSignalPlot', signalData.fft_plot.data, signalData.fft_plot.layout, {responsive: true});
    } else {
        $('#fftSignalPlot').html('<div class="alert alert-warning">No se pudieron generar gráficos de FFT</div>');
    }
    
    // Mostrar estadísticas
    if (signalData.stats) {
        displaySignalStats(signalData.stats);
    } else {
        $('#signalStats').html('<div class="col-12"><div class="alert alert-info">No hay estadísticas disponibles</div></div>');
    }
}

function displaySignalStats(stats) {
    const html = `
        <div class="col-md-3">
            <div class="text-center">
                <h6><i class="fas fa-chart-line"></i> RMS</h6>
                <strong>${stats.rms ? stats.rms.toFixed(4) : 'N/A'}</strong>
            </div>
        </div>
        <div class="col-md-3">
            <div class="text-center">
                <h6><i class="fas fa-arrows-alt-v"></i> Peak</h6>
                <strong>${stats.peak ? stats.peak.toFixed(4) : 'N/A'}</strong>
            </div>
        </div>
        <div class="col-md-3">
            <div class="text-center">
                <h6><i class="fas fa-wave-square"></i> Frequency</h6>
                <strong>${stats.sampling_rate ? (stats.sampling_rate/1000).toFixed(1) + ' kHz' : 'N/A'}</strong>
            </div>
        </div>
        <div class="col-md-3">
            <div class="text-center">
                <h6><i class="fas fa-clock"></i> Duration</h6>
                <strong>${stats.duration ? (stats.duration*1000).toFixed(1) + ' ms' : 'N/A'}</strong>
            </div>
        </div>
    `;
    
    $('#signalStats').html(html);
}

// Variables para el manejo de predicciones de la base de datos
let databasePredictions = [];
let selectedPredictionIndex = null;

// Función para cargar predicciones desde la base de datos
function loadDatabasePredictions(preserveCurrentCards = false) {
    // Mostrar indicador de carga
    $('#predictionsTableBody').html('<tr><td colspan="8" class="text-center"><div class="spinner-border spinner-border-sm"></div> Loading predictions from database...</td></tr>');
    $('#predictionsTable').show();
    
    // SIEMPRE cargar TODAS las predicciones sin filtrar por device_id
    let url = '/api/predictions/all';
    
    $.get(url)
        .done(function(data) {
            databasePredictions = data.predictions;
            displayPredictionsTable(databasePredictions);
            
            // Actualizar estadísticas del dashboard
            updateDashboardStats(data.predictions);
            
            // Solo actualizar tarjetas si no preservamos las actuales
            if (!preserveCurrentCards) {
                updateCardsFromDatabase(data.predictions);
            }
            
            console.log(`Loaded ${data.predictions.length} predictions from database (showing ALL predictions)`);
        })
        .fail(function(xhr) {
            $('#predictionsTableBody').html('<tr><td colspan="8" class="text-center text-danger">Failed to load predictions from database</td></tr>');
            console.error('Error loading database predictions:', xhr);
        });
}

// Función para refrescar predicciones de la base de datos
function refreshDatabasePredictions() {
    if (databasePredictions.length > 0 || $('#predictionsTable').is(':visible')) {
        loadDatabasePredictions(false); // No preservar tarjetas en refresh manual
    }
}

// Función para seleccionar una fila de predicción
function selectPredictionRow(index, prediction) {
    // Remover selección anterior
    $('.prediction-row').removeClass('table-info');
    
    // Seleccionar nueva fila
    $(`.prediction-row[data-prediction-index="${index}"]`).addClass('table-info');
    
    selectedPredictionIndex = index;
    
    // Actualizar tarjetas con la predicción seleccionada
    updateCardsFromSelectedPrediction(prediction);
}

// Función para actualizar las tarjetas con datos de la base de datos
function updateCardsFromDatabase(predictions) {
    if (!predictions || predictions.length === 0) {
        updateProbabilitiesOnly('No predictions found in database');
        $('#recordingsInfo').html('<p class="mb-0">No data available</p>');
        return;
    }
    
    // Encontrar rango de fechas
    const timestamps = predictions.map(p => new Date(p.timestamp));
    const oldestDate = new Date(Math.min(...timestamps));
    const newestDate = new Date(Math.max(...timestamps));
    
    // Calcular estadísticas básicas
    const totalPredictions = predictions.length;
    const successfulPredictions = predictions.filter(p => p.success).length;
    
    // Actualizar solo el mensaje de probabilidades
    updateProbabilitiesOnly('Database predictions loaded - check probabilities below');
    
    // Actualizar Recordings Info con información de rango de fechas
    const recordingsHtml = `
        <p><strong>Data Range:</strong></p>
        <p class="mb-1"><small><i class="fas fa-clock"></i> From: ${oldestDate.toLocaleString()}</small></p>
        <p class="mb-1"><small><i class="fas fa-clock"></i> To: ${newestDate.toLocaleString()}</small></p>
        <p class="mb-0"><small><i class="fas fa-database"></i> Success Rate: ${((successfulPredictions/totalPredictions)*100).toFixed(1)}%</small></p>
    `;
    $('#recordingsInfo').html(recordingsHtml);
    
    // Calcular y mostrar probabilidades promedio
    displayProbabilities(predictions.filter(p => p.success));
}

// Función para actualizar las tarjetas con una predicción seleccionada
function updateCardsFromSelectedPrediction(prediction) {
    if (!prediction || !prediction.success) {
        updateProbabilitiesOnly('Selected prediction has no valid data');
        $('#recordingsInfo').html('<p class="mb-0">No data available for selected prediction</p>');
        return;
    }
    
    // Actualizar solo el mensaje de probabilidades
    updateProbabilitiesOnly('Selected prediction probabilities');
    
    // Actualizar Recordings Info con información de la predicción seleccionada
    const timestamp = new Date(prediction.timestamp);
    const recordingsHtml = `
        <p><strong>Selected Prediction:</strong></p>
        <p class="mb-1"><small><i class="fas fa-tag"></i> Recording: ${prediction.recording_id}</small></p>
        <p class="mb-1"><small><i class="fas fa-satellite-dish"></i> Channel: ${prediction.channel || 1}</small></p>
        <p class="mb-1"><small><i class="fas fa-microchip"></i> Device: ${prediction.device_id || 'Unknown'}</small></p>
        <p class="mb-1"><small><i class="fas fa-cog"></i> Model: ${prediction.model_name || 'Unknown'}</small></p>
        <p class="mb-0"><small><i class="fas fa-calendar"></i> Created: ${new Date(prediction.created_at || prediction.timestamp).toLocaleString()}</small></p>
    `;
    $('#recordingsInfo').html(recordingsHtml);
    
    // Mostrar probabilidades de la predicción seleccionada
    if (prediction.prediction && prediction.prediction.probabilities) {
        displayProbabilitiesInCard(prediction.prediction.probabilities, 'Selected prediction');
    }
}

// Función auxiliar para mostrar probabilidades en la tarjeta
function displayProbabilitiesInCard(probabilities, title) {
    // Encontrar la clase ganadora
    const sortedClasses = Object.entries(probabilities)
        .sort((a, b) => b[1] - a[1]);
    
    const winnerClass = sortedClasses[0];
    const winnerName = winnerClass[0];
    const winnerPercentage = (winnerClass[1] * 100).toFixed(1);
    
    // Generar HTML con clase ganadora y barras de probabilidades
    let html = `
        <div class="text-center mb-3">
            <div class="prediction-badge">${winnerName}</div>
            <div class="top-prediction">${winnerPercentage}%</div>
        </div>
        <small class="text-muted d-block text-center mb-2">${title}</small>
    `;
    
    // Mostrar todas las probabilidades con barras
    sortedClasses.forEach(([className, probability]) => {
        const percentage = (probability * 100).toFixed(1);
        html += `
            <div class="mb-2">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="probability-label">${className}</span>
                    <span class="probability-percentage">${percentage}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${probability > 0.5 ? 'bg-warning' : 'bg-light'}" 
                         style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    });
    
    $('#probabilitiesCardContent').html(html);
    $('#probabilitiesInCard').show();
}

// Función para actualizar las estadísticas del dashboard
function updateDashboardStats(predictions = null) {
    // Si no se pasan predicciones, usar las de la base de datos global
    const allPredictions = predictions || databasePredictions || [];
    
    // Calcular estadísticas
    const totalPredictions = allPredictions.length;
    const successfulPredictions = allPredictions.filter(p => p.success).length;
    
    // Obtener dispositivos únicos
    const uniqueDevices = [...new Set(allPredictions.map(p => p.device_id))].length;
    
    // Obtener modelos únicos
    const uniqueModels = [...new Set(allPredictions.map(p => p.model_name))].length;
    
    // Actualizar los elementos del panel
    $('#totalPredictionsCount').text(totalPredictions);
    $('#successfulPredictionsCount').text(successfulPredictions);
    $('#uniqueDevicesCount').text(uniqueDevices);
    $('#uniqueModelsCount').text(uniqueModels);
}

// Función para actualizar solo las probabilidades en el card
function updateProbabilitiesOnly(message = null) {
    if (message) {
        $('#periodSummary').html(`<p class="mb-0">${message}</p>`);
    } else {
        $('#periodSummary').html('<p class="mb-0">Configure device and period, then perform prediction to see probabilities</p>');
    }
    $('#probabilitiesInCard').hide();
}

function updateConnectionStatus(status, text) {
    const indicator = $('#connectionStatus');
    const textElement = $('#connectionText');
    
    indicator.removeClass('status-online status-offline status-warning');
    indicator.addClass(`status-${status}`);
    textElement.text(text);
}
