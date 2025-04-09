// Éléments du DOM
const safeDoor = document.getElementById('safeDoor');
const safeHandle = document.getElementById('safeHandle');
const statusIndicator = document.getElementById('statusIndicator');
const safeStatusBadge = document.getElementById('safeStatusBadge');
const lastActivity = document.getElementById('lastActivity');
const logContainer = document.querySelector('.log-container');

// Configuration WebSocket
let ws;

// Mettre à jour l'état visuel du coffre-fort
function updateSafeStatus(status) {
    if (status === "authorized") {
        safeStatusBadge.textContent = 'OUVERT';
        safeStatusBadge.classList.remove('closed');
        safeStatusBadge.classList.add('open');
        safeHandle.innerHTML = '<i class="bi bi-unlock"></i>';
        safeDoor.classList.add('open');
        statusIndicator.classList.remove('locked');
    } else {
        safeStatusBadge.textContent = 'FERMÉ';
        safeStatusBadge.classList.remove('open');
        safeStatusBadge.classList.add('closed');
        safeHandle.innerHTML = '<i class="bi bi-lock"></i>';
        safeDoor.classList.remove('open');
        statusIndicator.classList.add('locked');
    }
}

// Charger l'état actuel du coffre-fort et les logs
async function loadCurrentStatus() {
    try {
        const response = await fetch('/api/safe-status');
        const data = await response.json();
        
        // Mettre à jour l'état du coffre-fort
        updateSafeStatus(data.status);
        
        // Effacer les logs existants
        logContainer.innerHTML = '';
        
        // Afficher les logs
        data.logs.forEach(log => {
            addLogEntry(log.message, log.status, log.timestamp, false);
        });
        
        // Mettre à jour la dernière activité
        if (data.logs.length > 0) {
            const lastLog = data.logs[0];
            const lastTime = new Date(lastLog.timestamp).toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            lastActivity.textContent = lastTime;
        }
    } catch (error) {
        console.error('Erreur lors du chargement de l\'état du coffre-fort:', error);
    }
}

function addLogEntry(message, status, timestamp, isNewEntry = true) {
    const entry = document.createElement('div');
    entry.className = `log-entry ${status}`;
    
    const time = new Date(timestamp).toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    entry.innerHTML = `
        <div class="log-time">${time}</div>
        <div class="log-message">${message}</div>
        <i class="bi ${status === 'authorized' ? 'bi-check-circle-fill' : 'bi-x-circle-fill'} log-icon ${status}"></i>
    `;
    
    if (isNewEntry) {
        logContainer.insertBefore(entry, logContainer.firstChild);
        lastActivity.textContent = time;
    } else {
        logContainer.appendChild(entry);
    }
}

function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'access_log') {
            updateSafeStatus(data.status);
            addLogEntry(data.message, data.status, data.timestamp);
        }
    };

    ws.onerror = function(error) {
        console.error('Erreur WebSocket:', error);
    };

    ws.onclose = function() {
        setTimeout(connectWebSocket, 5000);
    };
}

// Initialisation
async function init() {
    await loadCurrentStatus();  // Charger l'état actuel du coffre-fort et les logs
    connectWebSocket();        // Connecter au WebSocket
}

// Démarrer l'application
init(); 
init(); 