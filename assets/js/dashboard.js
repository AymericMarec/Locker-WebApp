// Simulation de l'état du coffre-fort
let isSafeOpen = false;
const safeDoor = document.getElementById('safeDoor');
const safeHandle = document.getElementById('safeHandle');
const statusIndicator = document.getElementById('statusIndicator');
const safeStatusBadge = document.getElementById('safeStatusBadge');
const lastActivity = document.getElementById('lastActivity');
const activityList = document.getElementById('activityList');

function updateSafeStatus() {
    const time = new Date().toLocaleTimeString();
    const date = new Date().toLocaleDateString();
    
    isSafeOpen = !isSafeOpen;
    safeDoor.classList.toggle('open');
    statusIndicator.classList.toggle('locked');
    
    if (isSafeOpen) {
        safeStatusBadge.textContent = 'OUVERT';
        safeStatusBadge.classList.remove('closed');
        safeStatusBadge.classList.add('open');
        safeHandle.innerHTML = '<i class="bi bi-unlock"></i>';
    } else {
        safeStatusBadge.textContent = 'FERMÉ';
        safeStatusBadge.classList.remove('open');
        safeStatusBadge.classList.add('closed');
        safeHandle.innerHTML = '<i class="bi bi-lock"></i>';
    }
    
    lastActivity.textContent = `${date} ${time}`;
    
    // Ajouter une entrée au journal
    const entry = document.createElement('li');
    entry.className = 'activity-item';
    entry.innerHTML = `
        <div class="activity-time">${time}</div>
        <div class="activity-message">${isSafeOpen ? 'Ouverture' : 'Fermeture'} du coffre-fort</div>
    `;
    activityList.insertBefore(entry, activityList.firstChild);
}

// Simuler les changements d'état (à remplacer par les événements réels)
setInterval(updateSafeStatus, 10000); 