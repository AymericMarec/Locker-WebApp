class BadgeScanner {
    constructor() {
        this.isScanning = false;
        this.scanTimer = null;
        this.scanDuration = 10; // Durée du scan en secondes
        this.remainingTime = this.scanDuration;
        
        // États du scanner
        this.idleState = document.getElementById('scannerIdle');
        this.scanningState = document.getElementById('scannerActive');
        this.badgeFoundState = document.getElementById('badgeFound');
        
        // Boutons
        this.startScanBtn = document.getElementById('startScan');
        this.cancelScanBtn = document.getElementById('cancelScan');
        this.saveBadgeBtn = document.getElementById('saveBadge');
        this.cancelBadgeBtn = document.getElementById('cancelBadge');
        
        // Éléments d'affichage
        this.timerDisplay = document.getElementById('scanTimer');
        this.badgeUidDisplay = document.getElementById('badgeUid');
        
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        this.startScanBtn.addEventListener('click', () => this.startScan());
        this.cancelScanBtn.addEventListener('click', () => this.cancelScan());
        this.saveBadgeBtn.addEventListener('click', () => this.saveBadge());
        this.cancelBadgeBtn.addEventListener('click', () => this.resetScanner());

        // Simulation de détection de badge avec la touche 'B'
        document.addEventListener('keypress', (e) => {
            if (e.key.toLowerCase() === 'b' && this.isScanning) {
                this.simulateBadgeDetection();
            }
        });
    }

    showState(state) {
        [this.idleState, this.scanningState, this.badgeFoundState].forEach(el => {
            if (el) el.style.display = 'none';
        });
        if (state) state.style.display = 'block';
    }

    startScan() {
        this.isScanning = true;
        this.remainingTime = this.scanDuration;
        this.showState(this.scanningState);
        this.updateTimer();

        this.scanTimer = setInterval(() => {
            this.remainingTime--;
            this.updateTimer();
            
            if (this.remainingTime <= 0) {
                this.cancelScan();
            }
        }, 1000);
    }

    updateTimer() {
        if (this.timerDisplay) {
            this.timerDisplay.textContent = this.remainingTime;
        }
    }

    cancelScan() {
        this.isScanning = false;
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }
        this.resetScanner();
    }

    simulateBadgeDetection() {
        // Génère un UID aléatoire pour la simulation
        const uid = Math.random().toString(36).substring(2, 15).toUpperCase();
        this.onBadgeDetected(uid);
    }

    onBadgeDetected(uid) {
        this.isScanning = false;
        if (this.scanTimer) {
            clearInterval(this.scanTimer);
            this.scanTimer = null;
        }

        if (this.badgeUidDisplay) {
            this.badgeUidDisplay.textContent = uid;
        }

        this.showState(this.badgeFoundState);
    }

    async saveBadge() {
        const uid = this.badgeUidDisplay.textContent;
        try {
            const response = await fetch('/api/badges', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ uid: uid })
            });

            if (!response.ok) {
                throw new Error('Erreur lors de l\'enregistrement du badge');
            }

            // Recharge la page pour afficher le nouveau badge
            window.location.reload();
        } catch (error) {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de l\'enregistrement du badge');
        }
    }

    resetScanner() {
        this.isScanning = false;
        this.remainingTime = this.scanDuration;
        this.updateTimer();
        this.showState(this.idleState);
    }
}

// Initialisation du scanner
document.addEventListener('DOMContentLoaded', () => {
    const scanner = new BadgeScanner();
}); 