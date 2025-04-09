// Éléments du DOM
const safeDoor = document.getElementById('safeDoor');
const safeHandle = document.getElementById('safeHandle');
const statusIndicator = document.getElementById('statusIndicator');
const safeStatusBadge = document.getElementById('safeStatusBadge');
const lastActivity = document.getElementById('lastActivity');
const logContainer = document.querySelector('.log-container');

// Éléments du modal
const badgeNameModal = new bootstrap.Modal(document.getElementById('badgeNameModal'));
const badgeNameForm = document.getElementById('badgeNameForm');
const badgeUidInput = document.getElementById('badgeUid');
const badgeNameInput = document.getElementById('badgeName');
const saveBadgeNameBtn = document.getElementById('saveBadgeName');

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

// Sauvegarder le nom du badge
async function saveBadgeName(uid, name) {
    try {
        const response = await fetch('/api/badges', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ uid, name })
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'enregistrement du badge');
        }
        
        badgeNameModal.hide();
        badgeNameForm.reset();
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement du badge');
    }
}

// Event listener pour le bouton de sauvegarde
saveBadgeNameBtn.addEventListener('click', () => {
    const uid = badgeUidInput.value;
    const name = badgeNameInput.value;
    
    if (name.trim()) {
        saveBadgeName(uid, name);
    }
});

function connectWebSocket() {
    console.log("Tentative de connexion WebSocket...");  // Debug log
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = function() {
        console.log("Connexion WebSocket établie");  // Debug log
    };

    ws.onmessage = function(event) {
        console.log("Message WebSocket reçu:", event.data);  // Debug log
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'access_log') {
                console.log("Log d'accès reçu:", data);  // Debug log
                updateSafeStatus(data.status);
                addLogEntry(data.message, data.status, data.timestamp);
                
                // Si c'est un nouveau badge, afficher le modal
                if (data.message === "Badge ajouté" && data.badge_uid) {
                    badgeUidInput.value = data.badge_uid;
                    badgeNameModal.show();
                }
            }
        } catch (error) {
            console.error("Erreur lors du traitement du message WebSocket:", error);  // Debug log
        }
    };

    ws.onerror = function(error) {
        console.error("Erreur WebSocket:", error);
    };

    ws.onclose = function() {
        console.log("Connexion WebSocket fermée, tentative de reconnexion dans 5s...");  // Debug log
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