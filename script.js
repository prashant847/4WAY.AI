// ==================== BACKEND CONNECTION ====================
// Use environment variable if available, otherwise use localhost for development
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000/api' 
    : (window.RENDER_API_URL || 'https://traffic-backend-api.onrender.com/api');
let updateInterval = null;
let isProcessing = false;

// ==================== FETCH BACKEND DATA ====================
async function fetchSignalStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/signals`);
        if (!response.ok) throw new Error('Failed to fetch signals');
        const data = await response.json();
        updateSignalsFromBackend(data);
        return data;
    } catch (error) {
        console.error('❌ Error fetching signals:', error);
        return null;
    }
}

async function fetchAnalysis() {
    try {
        const response = await fetch(`${API_BASE_URL}/analysis`);
        if (!response.ok) throw new Error('Failed to fetch analysis');
        const data = await response.json();
        updateAnalysisFromBackend(data);
        return data;
    } catch (error) {
        console.error('❌ Error fetching analysis:', error);
        return null;
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('❌ Error fetching stats:', error);
        return null;
    }
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        updateHealthStatus(data);
        return data;
    } catch (error) {
        console.error('❌ Backend not available:', error);
        updateHealthStatus({ status: 'offline' });
        return null;
    }
}

// ==================== UPDATE UI FROM BACKEND ====================
function updateSignalsFromBackend(data) {
    if (!data || !data.signals) return;
    
    const signals = data.signals;
    const directions = ['North', 'South', 'East', 'West'];
    const dirMap = { 'North': 'north', 'South': 'south', 'East': 'east', 'West': 'west' };
    
    directions.forEach(dir => {
        const signalData = signals[dir];
        if (!signalData) return;
        
        const card = document.querySelector(`.signal-card.${dirMap[dir]}`);
        if (!card) return;
        
        // Update signal state (Green/Yellow/Red)
        const state = signalData.state;
        const indicator = card.querySelector('.signal-indicator');
        
        // Remove all state classes
        indicator.classList.remove('green', 'yellow', 'red');
        
        // Add current state
        if (state === 'GREEN') {
            indicator.classList.add('green');
        } else if (state === 'YELLOW') {
            indicator.classList.add('yellow');
        } else {
            indicator.classList.add('red');
        }
        
        // Update countdown timer
        const timeRemaining = signalData.time_remaining || 0;
        const timingEl = card.querySelector('.timing');
        if (timingEl && timeRemaining > 0) {
            timingEl.textContent = `${Math.floor(timeRemaining)}s`;
            timingEl.style.color = state === 'GREEN' ? '#5FD068' : '#FF6B6B';
        } else {
            timingEl.textContent = '--';
        }
    });
}

function updateAnalysisFromBackend(data) {
    if (!data) return;
    
    // Update priority ranking
    const priorities = data.priority_ranking || [];
    if (priorities.length > 0) {
        const topPriority = priorities[0];
        
        // Update AI decision panel
        const decisionTitle = document.querySelector('.decision-title');
        const decisionSubtitle = document.querySelector('.decision-subtitle');
        
        if (decisionTitle) {
            const action = data.signal_assignment && data.signal_assignment[topPriority.lane_id] === 'GREEN' 
                ? `${topPriority.lane_name} Lane - GREEN Signal` 
                : `${topPriority.lane_name} Lane Priority`;
            decisionTitle.textContent = action;
        }
        
        if (decisionSubtitle) {
            decisionSubtitle.textContent = `Congestion Level: ${topPriority.congestion_level} | Priority Score: ${topPriority.priority_score.toFixed(2)}`;
        }
        
        // Update impact metrics
        const impactValue = document.querySelector('.impact-value');
        if (impactValue && topPriority.priority_score) {
            const reduction = Math.min(95, Math.floor(topPriority.priority_score));
            impactValue.textContent = `${reduction}% congestion priority`;
        }
    }
    
    // Update vehicle counts from analysis
    priorities.forEach(lane => {
        const dirMap = {
            'North': 'north',
            'South': 'south', 
            'East': 'east',
            'West': 'west'
        };
        
        const dir = dirMap[lane.lane_name];
        if (!dir) return;
        
        const card = document.querySelector(`.signal-card.${dir}`);
        if (!card) return;
        
        // Update vehicle count
        const vehicleCountEl = card.querySelector('.vehicles-count');
        if (vehicleCountEl) {
            vehicleCountEl.textContent = lane.total_vehicles || 0;
            
            // Flash effect on update
            vehicleCountEl.style.transition = 'all 0.3s ease';
            vehicleCountEl.style.transform = 'scale(1.15)';
            vehicleCountEl.style.color = '#00ff00';
            setTimeout(() => {
                vehicleCountEl.style.transform = 'scale(1)';
                vehicleCountEl.style.color = '';
            }, 300);
        }
        
        // Update density based on congestion score
        const densityPercent = Math.min(100, Math.floor((lane.congestion_score / 50) * 100));
        const densityValueEl = card.querySelector('.density-value');
        const progressFill = card.querySelector('.progress-fill');
        
        if (densityValueEl) {
            densityValueEl.textContent = `${densityPercent}%`;
            
            if (densityPercent > 80) {
                densityValueEl.style.color = '#FF6B6B';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #FF6B6B 0%, #EE5A6F 100%)';
            } else if (densityPercent > 60) {
                densityValueEl.style.color = '#FFA500';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #FFA500 0%, #FF8C00 100%)';
            } else {
                densityValueEl.style.color = '#5FD068';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #5FD068 0%, #4CAF50 100%)';
            }
        }
        
        if (progressFill) {
            progressFill.style.width = `${densityPercent}%`;
        }
    });
}

function updateHealthStatus(data) {
    const yoloStatus = document.querySelector('.yolo-status');
    if (!yoloStatus) return;
    
    if (data && data.status === 'healthy') {
        yoloStatus.style.background = 'linear-gradient(135deg, #00ff00, #00cc00)';
        yoloStatus.querySelector('span').textContent = 'YOLO LIVE DETECTION';
        yoloStatus.style.boxShadow = '0 2px 10px rgba(0,255,0,0.5)';
    } else {
        yoloStatus.style.background = 'linear-gradient(135deg, #ff6b6b, #ee5a6f)';
        yoloStatus.querySelector('span').textContent = 'BACKEND OFFLINE';
        yoloStatus.style.boxShadow = '0 2px 10px rgba(255,107,107,0.5)';
    }
}

// ==================== PROCESS VIDEOS (Upload to Backend) ====================
async function processVideos() {
    const formData = new FormData();
    
    // Add video files (you can modify this to handle file uploads)
    // For now, we'll let the backend process existing videos
    
    try {
        const response = await fetch(`${API_BASE_URL}/process-videos`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to process videos');
        
        const result = await response.json();
        console.log('✅ Videos processed:', result);
        
        // Update UI with results
        if (result.analysis) {
            updateAnalysisFromBackend(result.analysis);
        }
        if (result.signals) {
            updateSignalsFromBackend(result.signals);
        }
        
        return result;
    } catch (error) {
        console.error('❌ Error processing videos:', error);
        return null;
    }
}

// ==================== LIVE DETECTION CONTROLS ====================
let isLiveDetectionRunning = false;

async function startLiveDetection() {
    try {
        const response = await fetch(`${API_BASE_URL}/start-live-detection`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            isLiveDetectionRunning = true;
            console.log('✅ Live detection started!');
            
            // Update UI
            updateHealthStatus({ status: 'healthy' });
            
            // Start fetching live data
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(fetchLiveData, 1000); // Update every 1 second (optimized)
            
            return true;
        } else {
            console.error('Failed to start detection:', data.message);
            return false;
        }
    } catch (error) {
        console.error('Error starting detection:', error);
        return false;
    }
}

async function stopLiveDetection() {
    try {
        const response = await fetch(`${API_BASE_URL}/stop-live-detection`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            isLiveDetectionRunning = false;
            console.log('⏹️ Live detection stopped');
            
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
            
            return true;
        }
    } catch (error) {
        console.error('Error stopping detection:', error);
        return false;
    }
}

async function fetchLiveData() {
    try {
        const response = await fetch(`${API_BASE_URL}/live-data`);
        
        if (!response.ok) throw new Error('Failed to fetch live data');
        
        const data = await response.json();
        
        if (data.success && data.lanes) {
            updateLiveDataUI(data.lanes);
            // 📊 Update traffic analytics chart
            updateTrafficChart(data);
        }
        
        return data;
    } catch (error) {
        console.error('❌ Error fetching live data:', error);
        return null;
    }
}

function updateLiveDataUI(lanes) {
    const dirMap = {
        'North': 'north',
        'South': 'south',
        'East': 'east',
        'West': 'west'
    };
    
    lanes.forEach(lane => {
        const direction = dirMap[lane.lane_name];
        if (!direction) return;
        
        const card = document.querySelector(`.signal-card.${direction}`);
        if (!card) return;
        
        // Update vehicle count with animation
        const vehicleCountEl = card.querySelector('.vehicles-count');
        if (vehicleCountEl) {
            const newCount = lane.current_vehicles;
            const oldCount = parseInt(vehicleCountEl.textContent) || 0;
            
            if (newCount !== oldCount) {
                vehicleCountEl.textContent = newCount;
                
                // Flash animation
                vehicleCountEl.style.transition = 'all 0.3s ease';
                vehicleCountEl.style.transform = 'scale(1.2)';
                vehicleCountEl.style.color = '#00ff00';
                
                setTimeout(() => {
                    vehicleCountEl.style.transform = 'scale(1)';
                    vehicleCountEl.style.color = '';
                }, 300);
            }
        }
        
        // Update wait time / signal timer
        const timingEl = card.querySelector('.timing');
        if (timingEl) {
            const waitTime = lane.wait_time;
            if (waitTime > 0) {
                timingEl.textContent = `${waitTime}s`;
                timingEl.style.color = lane.signal === 'GREEN' ? '#5FD068' : '#FF6B6B';
            } else {
                timingEl.textContent = '--';
            }
        }
        
        // Update density
        const densityValueEl = card.querySelector('.density-value');
        const progressFill = card.querySelector('.progress-fill');
        
        if (densityValueEl) {
            densityValueEl.textContent = `${lane.density}%`;
            
            // Color based on density
            if (lane.density > 70) {
                densityValueEl.style.color = '#FF6B6B';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #FF6B6B 0%, #EE5A6F 100%)';
            } else if (lane.density > 40) {
                densityValueEl.style.color = '#FFA500';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #FFA500 0%, #FF8C00 100%)';
            } else {
                densityValueEl.style.color = '#5FD068';
                if (progressFill) progressFill.style.background = 'linear-gradient(90deg, #5FD068 0%, #4CAF50 100%)';
            }
        }
        
        if (progressFill) {
            progressFill.style.width = `${lane.density}%`;
        }
        
        // Update signal indicator with emoji
        const indicator = card.querySelector('.signal-indicator');
        const cardHeader = card.querySelector('.card-header h3');
        
        if (indicator) {
            indicator.classList.remove('green', 'yellow', 'red');
            
            let signalEmoji = '🔴';
            if (lane.signal === 'GREEN') {
                indicator.classList.add('green');
                signalEmoji = '🟢';
            } else if (lane.signal === 'YELLOW') {
                indicator.classList.add('yellow');
                signalEmoji = '🟡';
            } else {
                indicator.classList.add('red');
                signalEmoji = '🔴';
            }
            
            // Add emoji next to direction name
            if (cardHeader) {
                const directionName = lane.lane_name.toUpperCase();
                cardHeader.innerHTML = `${signalEmoji} ${directionName}`;
            }
        }
    });
    
    // Update AI Decision Engine based on highest density lane
    const highestDensityLane = lanes.reduce((max, lane) => 
        lane.density > max.density ? lane : max, lanes[0]);
    
    if (highestDensityLane && highestDensityLane.density > 50) {
        const aiDecisionTitle = document.querySelector('.decision-title');
        const aiDecisionSubtitle = document.querySelector('.decision-subtitle');
        const impactValue = document.querySelector('.impact-value');
        const confidenceValue = document.querySelector('.confidence-value');
        const confidenceFill = document.querySelector('.confidence-fill');
        
        if (aiDecisionTitle) {
            const signalAction = highestDensityLane.signal === 'GREEN' ? 'Extending' : 'Prioritizing';
            aiDecisionTitle.textContent = `${signalAction} ${highestDensityLane.lane_name} Signal +${highestDensityLane.wait_time}s`;
        }
        
        if (aiDecisionSubtitle) {
            aiDecisionSubtitle.textContent = `High density detected (${highestDensityLane.density}%) - ${highestDensityLane.current_vehicles} vehicles`;
        }
        
        if (impactValue) {
            const impact = Math.min(95, Math.round(highestDensityLane.density * 0.8));
            impactValue.textContent = `${impact}% congestion handling`;
        }
        
        if (confidenceValue && confidenceFill) {
            const confidence = Math.min(98, 85 + Math.round(highestDensityLane.density * 0.15));
            confidenceValue.textContent = `${confidence}%`;
            confidenceFill.style.width = `${confidence}%`;
        }
    }
}

// ==================== TRAFFIC AREAS MANAGEMENT ====================
const areas = {
    'ghadi-chowk': { name: 'Ghadi Chowk', description: 'Indira Chowk Area' },
    'pandri-chowk': { name: 'Pandri Chowk', description: 'Pandri Area' },
    'auto-stand': { name: 'Auto Stand Chowk', description: 'Station Area' },
    'tele-chowk': { name: 'Tele Chowk', description: 'Telangana Area' }
};

let currentArea = 'ghadi-chowk';

function initAreasManager() {
    const toggleBtn = document.getElementById('areasToggle');
    const closeBtn = document.getElementById('closeAreas');
    const sidebar = document.getElementById('areasSidebar');
    const areaCards = document.querySelectorAll('.area-card');
    
    toggleBtn.addEventListener('click', function() {
        sidebar.classList.toggle('active');
    });
    
    closeBtn.addEventListener('click', function() {
        sidebar.classList.remove('active');
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(e) {
        if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    });
    
    areaCards.forEach(card => {
        card.addEventListener('click', function() {
            const areaId = this.dataset.area;
            selectArea(areaId);
            sidebar.classList.remove('active');
        });
    });
}

function selectArea(areaId) {
    currentArea = areaId;
    const area = areas[areaId];
    
    // Update active state in sidebar
    document.querySelectorAll('.area-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-area="${areaId}"]`).classList.add('active');
    
    // Update header with current location name
    const header = document.querySelector('.header');
    let locationDisplay = header.querySelector('.location-display');
    
    if (!locationDisplay) {
        locationDisplay = document.createElement('div');
        locationDisplay.className = 'location-display';
        header.insertBefore(locationDisplay, header.querySelector('.search-container'));
    }
    
    locationDisplay.innerHTML = `
        <span class="location-name">${area.name}</span>
        <span class="location-arrow"><i class="fas fa-chevron-right"></i></span>
    `;
    
    // Optionally: Update traffic data for this area
    updateTrafficDataForArea(areaId);
}

function updateTrafficDataForArea(areaId) {
    // This function can be extended to update traffic data based on selected area
    console.log('Switched to area:', areas[areaId].name);
}

// Initialize areas manager on page load
document.addEventListener('DOMContentLoaded', function() {
    initAreasManager();
    // Set Ghadi Chowk as default active
    selectArea('ghadi-chowk');
    
    // Connect to Flask backend and start updates
    console.log('🚀 Connecting to Flask backend at', API_BASE_URL);
    startBackendUpdates();
    
    console.log('🚀 Dashboard initialized with Flask backend connection');
});

// ==================== CLOCK UPDATE ====================
function updateDateTime() {
    const now = new Date();
    
    // Format date as DD/MM/YYYY
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    const dateStr = `${day}/${month}/${year}`;
    
    // Format time with AM/PM
    let hours = now.getHours();
    let minutes = String(now.getMinutes()).padStart(2, '0');
    let seconds = String(now.getSeconds()).padStart(2, '0');
    const ampm = hours >= 12 ? 'pm' : 'am';
    hours = hours % 12;
    hours = hours ? hours : 12;
    hours = String(hours).padStart(2, '0');
    const timeStr = `${hours}:${minutes}:${seconds} ${ampm}`;
    
    document.getElementById('date').textContent = dateStr;
    document.getElementById('time').textContent = timeStr;
}

// Update clock every second
setInterval(updateDateTime, 1000);
updateDateTime();

// ==================== EVENT LISTENERS ====================
// Navigation items
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', function() {
        const section = this.dataset.section;
        console.log('🔗 Navigating to section:', section);
        
        // Navigate to respective pages
        if (section === 'vehicles') {
            console.log('→ Going to Ambulance (ambulance.html)');
            window.location.href = 'ambulance.html';
            return;
        } else if (section === 'restrictions') {
            console.log('→ Going to Restrictions (restricted.html)');
            window.location.href = 'restricted.html';
            return;
        } else if (section === 'violations') {
            console.log('→ Going to Violations (violations.html)');
            window.location.href = 'violations.html';
            return;
        } else if (section === 'reports') {
            console.log('→ Going to Reports (reports.html)');
            window.location.href = 'reports.html';
            return;
        } else if (section === 'users') {
            console.log('→ Going to Users (users.html)');
            window.location.href = 'users.html';
            return;
        }
        
        console.log('✓ Already on this page');
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        this.classList.add('active');
    });
});

// Control buttons
document.querySelectorAll('.control-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        const text = this.textContent.trim();
        console.log(`${text} button clicked`);
        
        // Visual feedback
        this.style.transform = 'scale(0.95)';
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 100);
        
        // Handle different control actions
        if (text.includes('Manual')) {
            console.log('🎮 Manual control mode');
            await stopLiveDetection();
        } else if (text.includes('Auto')) {
            console.log('🤖 Starting live detection...');
            
            this.disabled = true;
            this.textContent = '⏳ Starting...';
            
            const started = await startLiveDetection();
            
            if (started) {
                this.textContent = '⏹️ Stop Auto';
                this.style.background = 'linear-gradient(135deg, #FF6B6B, #EE5A6F)';
                this.disabled = false;
                
                // Change button to stop mode
                const originalHTML = this.innerHTML;
                this.dataset.originalHtml = originalHTML;
                this.dataset.mode = 'stop';
            } else {
                this.textContent = '🤖 Auto Mode';
                this.disabled = false;
            }
        } else if (text.includes('Stop')) {
            console.log('⏹️ Stopping auto mode...');
            
            await stopLiveDetection();
            
            this.style.background = 'linear-gradient(135deg, #00CEC9, #0984E3)';
            this.textContent = '🤖 Auto Mode';
            this.dataset.mode = 'start';
            
        } else if (text.includes('Emergency')) {
            console.log('🚨 Emergency override activated!');
            createConfetti();
            
            // Send emergency signal to backend
            try {
                await fetch(`${API_BASE_URL}/emergency`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'activate' })
                });
            } catch (error) {
                console.error('Emergency signal failed:', error);
            }
        } else if (text.includes('Reset')) {
            console.log('🔄 Resetting system...');
            
            try {
                await fetch(`${API_BASE_URL}/reset`, {
                    method: 'POST'
                });
                location.reload();
            } catch (error) {
                console.error('Reset failed:', error);
                location.reload();
            }
        }
    });
});

// Alert items hover effect
document.querySelectorAll('.alert-item').forEach(item => {
    item.addEventListener('click', function() {
        console.log('Alert clicked');
    });
});

// Signal card click handlers
document.querySelectorAll('.signal-card').forEach(card => {
    card.addEventListener('click', function() {
        console.log('Signal card clicked:', this.className);
    });
});

// ==================== MAIN UPDATE LOOP ====================
function startDashboardUpdates() {
    // Start backend updates immediately
    console.log('🚀 Starting real-time backend updates...');
    
    // Initial updates
    fetchSignalStatus();
    fetchAnalysis();
    
    // No dummy simulation - only real backend data
    console.log('✅ Dashboard connected to live backend API');
}

// Start updates when document is ready
document.addEventListener('DOMContentLoaded', startDashboardUpdates);

// ==================== SEARCH FUNCTIONALITY ====================
const searchInput = document.querySelector('.search-container input');
searchInput.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    console.log('Searching for:', searchTerm);
    // Add search functionality here
});

// ==================== RESPONSIVE ADJUSTMENTS ====================
window.addEventListener('resize', function() {
    const width = window.innerWidth;
    
    if (width <= 768) {
        document.querySelector('.traffic-grid').style.gridTemplateColumns = '1fr';
    } else if (width <= 1200) {
        document.querySelector('.traffic-grid').style.gridTemplateColumns = 'repeat(2, 1fr)';
    }
});

// ==================== NOTIFICATION BELL ====================
const notificationBell = document.querySelector('.notification-bell');
notificationBell.addEventListener('click', function() {
    console.log('Notifications opened');
    this.style.color = '#00CEC9';
    setTimeout(() => {
        this.style.color = '#B0B0C0';
    }, 2000);
});

// ==================== USER PROFILE ====================
const userProfile = document.querySelector('.user-profile');
userProfile.addEventListener('click', function() {
    console.log('User profile clicked');
});

// ==================== ACTION BUTTONS ====================
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const icon = this.querySelector('i');
        if (icon.classList.contains('fa-video')) {
            console.log('Video button clicked');
        } else if (icon.classList.contains('fa-cog')) {
            console.log('Settings button clicked');
        }
    });
});

// ==================== CONFETTI ANIMATION FOR SUCCESS ====================
function createConfetti() {
    const confettis = [];
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.style.position = 'fixed';
        confetti.style.width = '10px';
        confetti.style.height = '10px';
        confetti.style.backgroundColor = ['#FF6B6B', '#00CEC9', '#6C5CE7', '#5FD068', '#FFA500'][Math.floor(Math.random() * 5)];
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.top = '-10px';
        confetti.style.borderRadius = '50%';
        confetti.style.zIndex = '9999';
        confetti.style.opacity = '0.8';
        confetti.style.pointerEvents = 'none';
        
        document.body.appendChild(confetti);
        
        const duration = Math.random() * 2000 + 1000;
        const xOffset = (Math.random() - 0.5) * 400;
        
        let top = -10;
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = elapsed / duration;
            
            if (progress < 1) {
                top = -10 + (window.innerHeight + 20) * progress;
                confetti.style.top = top + 'px';
                confetti.style.left = 'calc(' + Math.random() * 100 + '% + ' + xOffset * progress + 'px)';
                confetti.style.opacity = 1 - progress;
                requestAnimationFrame(animate);
            } else {
                confetti.remove();
            }
        };
        
        animate();
    }
}

// Trigger confetti on emergency button click
document.querySelector('.control-btn.emergency').addEventListener('click', function() {
    createConfetti();
});

// ==================== DRAG AND DROP FOR CARDS ====================
let draggedElement = null;

function initDragAndDrop() {
    const container = document.querySelector('.bottom-section');
    const cards = container.querySelectorAll('.ai-engine, .live-violations, .traffic-prediction');
    
    cards.forEach(card => {
        card.setAttribute('draggable', 'true');
        
        card.addEventListener('dragstart', function(e) {
            draggedElement = this;
            setTimeout(() => {
                this.classList.add('dragging');
            }, 0);
        });
        
        card.addEventListener('dragend', function(e) {
            this.classList.remove('dragging');
            draggedElement = null;
        });
    });
    
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
        const afterElement = getDragAfterElement(container, e.clientY);
        if (afterElement == null) {
            container.appendChild(draggedElement);
        } else {
            container.insertBefore(draggedElement, afterElement);
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.ai-engine:not(.dragging), .live-violations:not(.dragging), .traffic-prediction:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Initialize drag and drop
// initDragAndDrop(); // DISABLED

console.log('🚦 Raipur Traffic Twin System - Dashboard Initialized');

// Auto-start live detection on page load - GUARANTEED START
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Page loaded - Starting live detection...');
    console.log('🔧 API Base URL:', API_BASE_URL);
    
    // Immediately start fetching data
    await fetchSignalStatus();
    await fetchAnalysis();
    
    // Start live detection
    setTimeout(async () => {
        try {
            console.log('🎯 Calling start-live-detection API...');
            const started = await startLiveDetection();
            if (started) {
                console.log('✅ Live detection started successfully!');
            } else {
                console.warn('⚠️ Failed to start - trying again...');
                // Retry once
                setTimeout(() => startLiveDetection(), 2000);
            }
        } catch (error) {
            console.error('❌ Error auto-starting detection:', error);
        }
    }, 500);
    
    // Start polling immediately and show in console
    console.log('🔄 Starting data polling every 2 seconds...');
    console.log('📊 Endpoints being polled:');
    console.log('  - /api/live-data (vehicle counts)');
    console.log('  - /api/ai-decisions (AI engine)');
    console.log('  - /api/traffic-prediction (30-min forecast)');
    
    // Also manually start polling for live data
    setInterval(async () => {
        console.log('🔄 Polling cycle started at', new Date().toLocaleTimeString());
        await fetchLiveData();
        await fetchAIDecisions();  // Update AI Engine
        await fetchTrafficPrediction();  // Update Traffic Prediction
        console.log('✅ Polling cycle completed');
    }, 2000); // Every 2 seconds
});

// ==================== AI DECISION ENGINE ====================
async function fetchAIDecisions() {
    try {
        console.log('🤖 Fetching AI decisions from:', `${API_BASE_URL}/ai-decisions`);
        const response = await fetch(`${API_BASE_URL}/ai-decisions`);
        if (!response.ok) throw new Error('Failed to fetch AI decisions');
        
        const data = await response.json();
        console.log('🤖 AI Decision received:', data);
        
        if (data.success && data.decision) {
            console.log('✅ Updating AI Engine UI with:', data.decision);
            updateAIEngineUI(data.decision);
        } else {
            console.warn('⚠️ No decision data in response');
        }
        
        return data;
    } catch (error) {
        console.error('❌ Error fetching AI decisions:', error);
        return null;
    }
}

function updateAIEngineUI(decision) {
    console.log('🎨 Updating AI Engine UI with decision:', decision);
    
    // Update decision title with animation
    const decisionTitle = document.querySelector('.decision-title');
    if (decisionTitle) {
        const newText = decision.action || 'Monitoring traffic conditions';
        console.log('📝 Decision Title:', newText);
        decisionTitle.textContent = newText;
        
        // Flash animation
        decisionTitle.style.transition = 'all 0.3s ease';
        decisionTitle.style.color = '#00ff00';
        setTimeout(() => {
            decisionTitle.style.color = '';
        }, 500);
    } else {
        console.warn('⚠️ .decision-title element not found!');
    }
    
    // Update decision subtitle
    const decisionSubtitle = document.querySelector('.decision-subtitle');
    if (decisionSubtitle) {
        const newSubtitle = decision.reason || 'System ready';
        console.log('📝 Decision Subtitle:', newSubtitle);
        decisionSubtitle.textContent = newSubtitle;
        
        // Flash animation
        decisionSubtitle.style.transition = 'all 0.3s ease';
        decisionSubtitle.style.color = '#00CEC9';
        setTimeout(() => {
            decisionSubtitle.style.color = '';
        }, 500);
    } else {
        console.warn('⚠️ .decision-subtitle element not found!');
    }
    
    // Update priority badge
    const priorityLevel = document.querySelector('.priority-level');
    const priorityBadge = document.querySelector('.priority-badge');
    if (priorityLevel && priorityBadge) {
        const priority = decision.priority_level || 'LOW';
        console.log('🎯 Priority Level:', priority);
        priorityLevel.textContent = priority;
        
        // Color code based on priority
        if (priority === 'CRITICAL') {
            priorityBadge.style.background = 'rgba(255, 71, 87, 0.2)';
            priorityBadge.style.borderLeft = '3px solid #FF4757';
            priorityLevel.style.color = '#FF4757';
        } else if (priority === 'HIGH') {
            priorityBadge.style.background = 'rgba(255, 165, 0, 0.2)';
            priorityBadge.style.borderLeft = '3px solid #FFA500';
            priorityLevel.style.color = '#FFA500';
        } else if (priority === 'MEDIUM') {
            priorityBadge.style.background = 'rgba(0, 206, 201, 0.2)';
            priorityBadge.style.borderLeft = '3px solid #00CEC9';
            priorityLevel.style.color = '#00CEC9';
        } else {
            priorityBadge.style.background = 'rgba(95, 208, 104, 0.2)';
            priorityBadge.style.borderLeft = '3px solid #5FD068';
            priorityLevel.style.color = '#5FD068';
        }
    }
    
    // Update detailed analysis
    const detailedAnalysis = document.querySelector('.detailed-analysis');
    if (detailedAnalysis) {
        const analysis = decision.detailed_analysis || 'No detailed analysis available';
        console.log('📊 Detailed Analysis:', analysis);
        detailedAnalysis.textContent = analysis;
        
        // Animate
        detailedAnalysis.style.transition = 'all 0.3s ease';
        detailedAnalysis.style.opacity = '0.5';
        setTimeout(() => {
            detailedAnalysis.style.opacity = '1';
        }, 200);
    }
    
    // Update impact prediction
    const impactPrediction = document.querySelector('.impact-prediction');
    if (impactPrediction) {
        const impact = decision.impact_prediction || decision.impact || 'No impact data';
        console.log('� Impact Prediction:', impact);
        impactPrediction.textContent = impact;
        
        // Animate
        impactPrediction.style.transition = 'all 0.3s ease';
        impactPrediction.style.transform = 'translateX(-5px)';
        setTimeout(() => {
            impactPrediction.style.transform = 'translateX(0)';
        }, 300);
    }
    
    // Update alternative action
    const alternativeAction = document.querySelector('.alternative-action');
    if (alternativeAction) {
        const alternative = decision.alternative_action || 'No alternative specified';
        console.log('🔄 Alternative Action:', alternative);
        alternativeAction.textContent = alternative;
    }
    
    // Update risk factors
    const riskFactors = document.querySelector('.risk-factors');
    if (riskFactors) {
        const risks = decision.risk_factors || 'No risks identified';
        console.log('⚡ Risk Factors:', risks);
        riskFactors.textContent = risks;
        
        // Highlight if risks present
        if (risks.toLowerCase().includes('critical') || risks.toLowerCase().includes('high')) {
            riskFactors.style.color = '#FF4757';
            riskFactors.style.fontWeight = 'bold';
        } else {
            riskFactors.style.color = '#aaa';
            riskFactors.style.fontWeight = 'normal';
        }
    }
    
    // Update AI confidence with color coding
    const confidenceValue = document.querySelector('.confidence-value');
    const confidenceFill = document.querySelector('.confidence-fill');
    
    if (confidenceValue && confidenceFill) {
        const confidence = decision.confidence || 0;
        console.log('🎯 Confidence:', confidence + '%');
        confidenceValue.textContent = `${confidence}%`;
        confidenceFill.style.width = `${confidence}%`;
        
        // Color based on confidence level
        if (confidence >= 90) {
            confidenceFill.style.background = 'linear-gradient(90deg, #00ff00, #00cc00)';
        } else if (confidence >= 75) {
            confidenceFill.style.background = 'linear-gradient(90deg, #00CEC9, #0984E3)';
        } else if (confidence >= 60) {
            confidenceFill.style.background = 'linear-gradient(90deg, #FFA500, #FF8C00)';
        } else {
            confidenceFill.style.background = 'linear-gradient(90deg, #FF6B6B, #EE5A6F)';
        }
        
        // Animate confidence bar
        confidenceFill.style.transition = 'all 0.5s ease';
        
        // Pulse animation on confidence value
        confidenceValue.style.transition = 'all 0.3s ease';
        confidenceValue.style.transform = 'scale(1.2)';
        confidenceValue.style.color = '#00ff00';
        setTimeout(() => {
            confidenceValue.style.transform = 'scale(1)';
            confidenceValue.style.color = '';
        }, 300);
    } else {
        console.warn('⚠️ .confidence-value or .confidence-fill element not found!');
    }
    
    // Visual feedback with pulsing border effect
    const aiEngine = document.querySelector('.ai-engine');
    if (aiEngine) {
        // Add timestamp to show last update
        let timestampEl = aiEngine.querySelector('.last-update-time');
        if (!timestampEl) {
            timestampEl = document.createElement('div');
            timestampEl.className = 'last-update-time';
            timestampEl.style.cssText = 'position: absolute; top: 5px; right: 10px; font-size: 9px; color: #00ff00; font-weight: bold;';
            aiEngine.style.position = 'relative';
            aiEngine.appendChild(timestampEl);
        }
        const now = new Date();
        timestampEl.textContent = `⏱️ ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        // Pulsing glow effect
        aiEngine.style.border = '2px solid #00ff00';
        aiEngine.style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.6), inset 0 0 10px rgba(0, 255, 0, 0.2)';
        
        setTimeout(() => {
            aiEngine.style.border = '';
            aiEngine.style.boxShadow = '';
        }, 1000);
        
        console.log('✨ AI Engine UI updated with visual effects!');
    } else {
        console.warn('⚠️ .ai-engine element not found!');
    }
}

// ==================== TRAFFIC FLOW PREDICTION ====================
async function fetchTrafficPrediction() {
    try {
        console.log('📈 Fetching traffic prediction from:', `${API_BASE_URL}/traffic-prediction`);
        const response = await fetch(`${API_BASE_URL}/traffic-prediction`);
        if (!response.ok) throw new Error('Failed to fetch traffic prediction');
        
        const data = await response.json();
        console.log('📈 Traffic Prediction received:', data);
        
        if (data.success && data.predictions) {
            console.log('✅ Updating prediction chart with', data.predictions.length, 'data points');
            console.log('📊 Trend:', data.trend, '| Peak Time:', data.peak_time);
            updateTrafficPredictionChart(data.predictions, data.trend);
        } else {
            console.warn('⚠️ No prediction data in response');
        }
        
        return data;
    } catch (error) {
        console.error('❌ Error fetching traffic prediction:', error);
        return null;
    }
}

function updateTrafficPredictionChart(predictions, trend) {
    if (!predictions || predictions.length === 0) {
        console.warn('⚠️ No predictions data to update chart');
        return;
    }
    
    console.log('📊 Updating prediction chart with', predictions.length, 'points');
    
    // Find max value for scaling
    const maxVehicles = Math.max(...predictions.map(p => p.prediction || 0), 100);
    const chartHeight = 60; // SVG height range (20-80 in viewBox)
    
    console.log('📊 Max vehicles for scaling:', maxVehicles);
    
    // Generate SVG points for polyline
    const points = predictions.map((pred, index) => {
        const x = 40 + (index * 40); // Spacing: 40px between points
        const vehicles = pred.prediction || 0;
        
        // Scale vehicles to chart height (invert Y axis - higher value = lower Y)
        const y = 80 - ((vehicles / maxVehicles) * chartHeight);
        
        return `${x},${y}`;
    }).join(' ');
    
    console.log('📊 Generated polyline points:', points);
    
    // Update polyline
    const polyline = document.querySelector('.prediction-chart polyline');
    if (polyline) {
        polyline.setAttribute('points', points);
        
        // Animate stroke with color based on trend
        polyline.style.transition = 'all 0.5s ease';
        if (trend === 'increasing') {
            polyline.setAttribute('stroke', '#FF6B6B');
        } else if (trend === 'decreasing') {
            polyline.setAttribute('stroke', '#5FD068');
        } else {
            polyline.setAttribute('stroke', '#00CEC9');
        }
        console.log('✅ Polyline updated');
    } else {
        console.warn('⚠️ .prediction-chart polyline not found!');
    }
    
    // Update data points (circles)
    const circles = document.querySelectorAll('.prediction-chart circle');
    console.log('🔵 Found', circles.length, 'circles to update');
    predictions.forEach((pred, index) => {
        if (index < circles.length) {
            const x = 40 + (index * 40);
            const vehicles = pred.prediction || 0;
            const y = 80 - ((vehicles / maxVehicles) * chartHeight);
            
            circles[index].setAttribute('cx', x);
            circles[index].setAttribute('cy', y);
            
            // Animate circles
            circles[index].style.transition = 'all 0.5s ease';
            
            // Pulse animation
            circles[index].setAttribute('r', '3.5');
            setTimeout(() => {
                circles[index].setAttribute('r', '2.5');
            }, 300);
        }
    });
    
    // Update X-axis labels (time)
    const xAxisLabels = document.querySelectorAll('.prediction-chart text[y="92"]');
    console.log('⏰ Found', xAxisLabels.length, 'X-axis labels');
    predictions.forEach((pred, index) => {
        if (index < xAxisLabels.length) {
            xAxisLabels[index].textContent = pred.time || '';
        }
    });
    
    // Update Y-axis labels (vehicle count)
    const yAxisLabels = document.querySelectorAll('.prediction-chart text[x="25"]');
    console.log('📊 Found', yAxisLabels.length, 'Y-axis labels');
    if (yAxisLabels.length >= 4) {
        yAxisLabels[0].textContent = Math.round(maxVehicles);  // Top
        yAxisLabels[1].textContent = Math.round(maxVehicles * 0.66);  // Middle-high
        yAxisLabels[2].textContent = Math.round(maxVehicles * 0.33);  // Middle-low
        yAxisLabels[3].textContent = '0';  // Bottom
    }
    
    // Add trend indicator
    const predictionSection = document.querySelector('.traffic-prediction h3');
    if (predictionSection) {
        let trendEmoji = '➡️';
        let trendText = 'STABLE';
        if (trend === 'increasing') {
            trendEmoji = '📈';
            trendText = 'RISING';
        } else if (trend === 'decreasing') {
            trendEmoji = '📉';
            trendText = 'FALLING';
        }
        
        predictionSection.innerHTML = `<i class="fas fa-chart-line"></i> Traffic Flow Prediction (30 min) ${trendEmoji} ${trendText}`;
        console.log('📊 Trend indicator updated:', trendText);
    }
    
    // Visual feedback with timestamp
    const predictionChart = document.querySelector('.traffic-prediction');
    if (predictionChart) {
        // Add timestamp
        let timestampEl = predictionChart.querySelector('.last-update-time');
        if (!timestampEl) {
            timestampEl = document.createElement('div');
            timestampEl.className = 'last-update-time';
            timestampEl.style.cssText = 'position: absolute; top: 5px; right: 10px; font-size: 9px; color: #00CEC9; font-weight: bold;';
            predictionChart.style.position = 'relative';
            predictionChart.appendChild(timestampEl);
        }
        const now = new Date();
        timestampEl.textContent = `⏱️ ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        // Border color based on trend
        predictionChart.style.borderLeft = trend === 'increasing' 
            ? '3px solid #FF6B6B' 
            : trend === 'decreasing' 
            ? '3px solid #5FD068' 
            : '3px solid #00CEC9';
        
        // Pulsing effect
        predictionChart.style.boxShadow = '0 0 20px rgba(0, 206, 201, 0.6)';
        setTimeout(() => {
            predictionChart.style.boxShadow = '';
        }, 1000);
        
        console.log('✨ Prediction chart updated with visual effects!');
    }
}

// ==================== REAL-TIME TRAFFIC ANALYTICS CHART ====================
let trafficChart = null;
let chartData = {
    labels: [],
    datasets: {
        north: [],
        south: [],
        east: [],
        west: []
    }
};

function initTrafficChart() {
    const ctx = document.getElementById('trafficChart');
    if (!ctx) return;

    const config = {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'North',
                    data: [],
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#FF6B6B',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    fill: true
                },
                {
                    label: 'South',
                    data: [],
                    borderColor: '#00CEC9',
                    backgroundColor: 'rgba(0, 206, 201, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00CEC9',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    fill: true
                },
                {
                    label: 'East',
                    data: [],
                    borderColor: '#FFA500',
                    backgroundColor: 'rgba(255, 165, 0, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#FFA500',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    fill: true
                },
                {
                    label: 'West',
                    data: [],
                    borderColor: '#6C5CE7',
                    backgroundColor: 'rgba(108, 92, 231, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#6C5CE7',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#E8E8FF',
                        font: {
                            size: 10,
                            family: 'Orbitron'
                        },
                        padding: 10,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(15, 15, 35, 0.9)',
                    titleColor: '#00CEC9',
                    bodyColor: '#E8E8FF',
                    borderColor: '#00CEC9',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y + ' vehicles';
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#999',
                        font: {
                            size: 9
                        },
                        maxRotation: 0
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#999',
                        font: {
                            size: 9
                        },
                        callback: function(value) {
                            return value;
                        }
                    }
                }
            },
            animation: {
                duration: 750,
                easing: 'easeInOutQuart'
            }
        }
    };

    trafficChart = new Chart(ctx, config);
    console.log('📊 Traffic analytics chart initialized!');
}

function updateTrafficChart(liveData) {
    if (!trafficChart || !liveData || !liveData.lanes) return;

    const currentTime = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });

    // Update labels
    chartData.labels.push(currentTime);
    if (chartData.labels.length > 20) {
        chartData.labels.shift();
    }

    // Update data for each lane
    liveData.lanes.forEach((lane, index) => {
        const vehicleCount = lane.current_vehicles || 0;
        
        if (!chartData.datasets[lane.lane_name.toLowerCase()]) {
            chartData.datasets[lane.lane_name.toLowerCase()] = [];
        }
        
        chartData.datasets[lane.lane_name.toLowerCase()].push(vehicleCount);
        
        if (chartData.datasets[lane.lane_name.toLowerCase()].length > 20) {
            chartData.datasets[lane.lane_name.toLowerCase()].shift();
        }

        // Update chart dataset
        if (trafficChart.data.datasets[index]) {
            trafficChart.data.datasets[index].data = chartData.datasets[lane.lane_name.toLowerCase()];
        }
    });

    trafficChart.data.labels = chartData.labels;
    trafficChart.update('none'); // Smooth update without animation

    // Update statistics
    updateChartStats(liveData);

    console.log('📈 Chart updated with live data');
}

let previousTotalVehicles = 0;

function updateChartStats(liveData) {
    if (!liveData || !liveData.lanes) return;

    // Calculate statistics
    let peakTraffic = 0;
    let totalDensity = 0;
    let totalVehicles = 0;

    liveData.lanes.forEach(lane => {
        const vehicles = lane.current_vehicles || 0;
        totalVehicles += vehicles;
        
        if (vehicles > peakTraffic) {
            peakTraffic = vehicles;
        }
        totalDensity += lane.density || 0;
    });

    const avgCongestion = Math.round(totalDensity / liveData.lanes.length);

    // Determine trend
    let trend = 'Stable';
    let trendColor = '#00CEC9';
    let trendIcon = '➡️';
    
    if (totalVehicles > previousTotalVehicles + 5) {
        trend = 'Rising';
        trendColor = '#FF6B6B';
        trendIcon = '📈';
    } else if (totalVehicles < previousTotalVehicles - 5) {
        trend = 'Falling';
        trendColor = '#5FD068';
        trendIcon = '📉';
    }
    
    previousTotalVehicles = totalVehicles;

    // Update UI with animations
    const peakElement = document.getElementById('peakTraffic');
    const congestionElement = document.getElementById('avgCongestion');
    const totalElement = document.getElementById('totalVehicles');
    const trendElement = document.getElementById('trafficTrend');

    if (peakElement) {
        peakElement.textContent = peakTraffic;
        peakElement.style.animation = 'none';
        setTimeout(() => {
            peakElement.style.animation = 'pulseNumber 0.5s ease';
        }, 10);
    }

    if (congestionElement) {
        congestionElement.textContent = avgCongestion;
        congestionElement.style.animation = 'none';
        setTimeout(() => {
            congestionElement.style.animation = 'pulseNumber 0.5s ease';
        }, 10);
    }

    if (totalElement) {
        totalElement.textContent = totalVehicles;
        totalElement.style.animation = 'none';
        setTimeout(() => {
            totalElement.style.animation = 'pulseNumber 0.5s ease';
        }, 10);
    }

    if (trendElement) {
        trendElement.textContent = `${trendIcon} ${trend}`;
        trendElement.style.color = trendColor;
        trendElement.style.animation = 'none';
        setTimeout(() => {
            trendElement.style.animation = 'pulseNumber 0.5s ease';
        }, 10);
    }
}

// Chart filter buttons functionality
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.chart-filter');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.style.background = 'transparent';
                btn.style.borderColor = '#555';
                btn.style.color = '#999';
            });

            // Add active class to clicked button
            this.classList.add('active');
            
            const chartType = this.getAttribute('data-chart');
            switchChartView(chartType);
        });
    });

    // Initialize chart
    initTrafficChart();
});

function switchChartView(viewType) {
    if (!trafficChart) return;

    switch(viewType) {
        case 'vehicles':
            trafficChart.type = 'line';
            trafficChart.options.plugins.tooltip.callbacks.label = function(context) {
                return context.dataset.label + ': ' + context.parsed.y + ' vehicles';
            };
            trafficChart.data.datasets.forEach(dataset => {
                dataset.fill = true;
                dataset.borderWidth = 2;
                dataset.tension = 0.4;
            });
            trafficChart.options.scales.y.ticks.callback = function(value) {
                return value;
            };
            break;
        
        case 'density':
            trafficChart.type = 'line';
            trafficChart.options.plugins.tooltip.callbacks.label = function(context) {
                return context.dataset.label + ': ' + context.parsed.y + '% density';
            };
            trafficChart.data.datasets.forEach(dataset => {
                dataset.fill = false;
                dataset.borderWidth = 3;
                dataset.tension = 0.3;
            });
            trafficChart.options.scales.y.ticks.callback = function(value) {
                return value + '%';
            };
            break;
        
        case 'flow':
            trafficChart.type = 'bar';
            trafficChart.options.plugins.tooltip.callbacks.label = function(context) {
                return context.dataset.label + ': ' + context.parsed.y + ' flow';
            };
            trafficChart.data.datasets.forEach(dataset => {
                dataset.fill = false;
                dataset.borderWidth = 0;
            });
            trafficChart.options.scales.y.ticks.callback = function(value) {
                return value;
            };
            break;
    }

    trafficChart.update('active');
    console.log('📊 Chart view switched to:', viewType);
}

// ==================== CONTROL BUTTONS FUNCTIONALITY ====================
let currentMode = 'ai'; // 'ai' or 'manual'
let isEmergencyActive = false;
let manualCycleInterval = null; // To hold the interval for manual mode

function handleAiMode() {
    console.log('🤖 AI Mode Activated');
    if (currentMode === 'ai' && !isEmergencyActive) {
        showNotification('AI Mode is already active.', 'info');
        return;
    }
    currentMode = 'ai';
    isEmergencyActive = false;

    // Stop manual mode cycle
    if (manualCycleInterval) {
        clearInterval(manualCycleInterval);
        manualCycleInterval = null;
    }

    // Visual feedback
    const aiModeBtn = document.querySelector('.control-btn.ai-mode');
    const manualModeBtn = document.querySelector('.control-btn.manual-mode');
    aiModeBtn.classList.add('active');
    manualModeBtn.classList.remove('active');

    // Start live detection
    fetch(`${API_BASE_URL}/start-live-detection`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ AI Mode Active - YOLO Detection Running', 'success');
                if (updateInterval) clearInterval(updateInterval);
                updateInterval = setInterval(fetchLiveData, 1000);
            } else {
                showNotification('❌ Failed to start AI mode', 'error');
            }
        })
        .catch(error => {
            console.error('Error starting AI mode:', error);
            showNotification('❌ Error starting AI mode', 'error');
        });
}

function handleManualMode() {
    console.log('👋 Manual Mode Activated');
    if (currentMode === 'manual' && !isEmergencyActive) {
        showNotification('Manual Mode is already active.', 'info');
        return;
    }
    currentMode = 'manual';
    isEmergencyActive = false;

    // Visual feedback
    const manualModeBtn = document.querySelector('.control-btn.manual-mode');
    const aiModeBtn = document.querySelector('.control-btn.ai-mode');
    manualModeBtn.classList.add('active');
    aiModeBtn.classList.remove('active');

    // Stop live detection and polling
    fetch(`${API_BASE_URL}/stop-live-detection`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showNotification('⚙️ Manual Mode Active - Cyclic Traffic Control', 'info');
                if (updateInterval) {
                    clearInterval(updateInterval);
                    updateInterval = null;
                }
                // Start the manual cyclic mode
                startCyclicMode();
            } else {
                showNotification('❌ Failed to switch to manual mode', 'error');
            }
        })
        .catch(error => {
            console.error('Error switching to manual mode:', error);
            showNotification('❌ Error switching to manual mode', 'error');
        });
}

function showEmergencyModal() {
    console.log('🚨 Emergency Button Clicked');
    document.getElementById('emergencyModal').style.display = 'block';
}

function handleDispatch() {
    console.log('🚔 Dispatch Police Alert');
    const notification = document.getElementById('dispatchNotification');
    const message = document.getElementById('dispatchMessage');
    
    let maxVehicles = -1;
    let congestedLane = 'N/A';

    document.querySelectorAll('.signal-card').forEach(card => {
        const vehicleCount = parseInt(card.querySelector('.vehicles-count').textContent) || 0;
        if (vehicleCount > maxVehicles) {
            maxVehicles = vehicleCount;
            const h3 = card.querySelector('h3');
            if(h3) {
                congestedLane = h3.textContent.replace(/[^a-zA-Z]/g, '');
            }
        }
    });

    message.textContent = `High congestion alert! ${maxVehicles} vehicles detected in ${congestedLane} lane. Requesting immediate dispatch for traffic management.`;
    notification.style.display = 'block';
}

function generateReport() {
    console.log('📊 Generating Report');
    generateTrafficReport();
}


document.addEventListener('DOMContentLoaded', function() {
    const aiModeBtn = document.querySelector('.control-btn.ai-mode');
    const manualModeBtn = document.querySelector('.control-btn.manual-mode');
    const emergencyBtn = document.querySelector('.control-btn.emergency');
    const dispatchBtn = document.querySelector('.control-btn.dispatch');
    const reportBtn = document.querySelector('.control-btn.report');

    if(aiModeBtn) aiModeBtn.addEventListener('click', handleAiMode);
    if(manualModeBtn) manualModeBtn.addEventListener('click', handleManualMode);
    if(emergencyBtn) emergencyBtn.addEventListener('click', showEmergencyModal);
    if(dispatchBtn) dispatchBtn.addEventListener('click', handleDispatch);
    if(reportBtn) reportBtn.addEventListener('click', generateReport);

    // Set AI mode as default active
    if(aiModeBtn) aiModeBtn.classList.add('active');
});

// Emergency Lane Selection
function selectEmergencyLane(laneId) {
    console.log(`🚨 Emergency: Lane ${laneId} selected for GREEN`);
    isEmergencyActive = true;
    
    // Close modal
    closeEmergencyModal();
    
    // Set selected lane to GREEN, all others to RED
    const laneNames = ['North', 'South', 'East', 'West'];
    const dirMap = { 0: 'north', 1: 'south', 2: 'east', 3: 'west' };
    
    laneNames.forEach((name, index) => {
        const card = document.querySelector(`.signal-card.${dirMap[index]}`);
        if (!card) return;
        
        const indicator = card.querySelector('.signal-indicator');
        indicator.classList.remove('green', 'yellow', 'red');
        
        if (index === laneId) {
            indicator.classList.add('green');
            card.querySelector('.timing').textContent = '∞';
            card.querySelector('.timing').style.color = '#5FD068';
        } else {
            indicator.classList.add('red');
            card.querySelector('.timing').textContent = '∞';
            card.querySelector('.timing').style.color = '#FF6B6B';
        }
    });
    
    showNotification(`🚨 EMERGENCY: ${laneNames[laneId]} Lane is GREEN`, 'warning');
}

function closeEmergencyModal() {
    document.getElementById('emergencyModal').style.display = 'none';
}

// Dispatch Police Alert
function showDispatchAlert() {
    const notification = document.getElementById('dispatchNotification');
    const message = document.getElementById('dispatchMessage');
    
    // Get highest traffic lane
    const lanes = document.querySelectorAll('.signal-card');
    let maxVehicles = 0;
    let maxLane = 'Unknown';
    
    lanes.forEach(lane => {
        const countEl = lane.querySelector('.vehicles-count');
        if (countEl) {
            const count = parseInt(countEl.textContent) || 0;
            if (count > maxVehicles) {
                maxVehicles = count;
                const laneClass = Array.from(lane.classList).find(c => ['north', 'south', 'east', 'west'].includes(c));
                maxLane = laneClass ? laneClass.toUpperCase() : 'Unknown';
            }
        }
    });
    
    message.textContent = `Heavy traffic detected on ${maxLane} lane (${maxVehicles} vehicles). Immediate police presence required for traffic management and congestion control.`;
    
    notification.style.display = 'block';
}

// Close dispatch notification
function closeDispatchNotification() {
    document.getElementById('dispatchNotification').style.display = 'none';
}

// Cyclic Traffic Light Mode (Indian Style)
function startCyclicMode() {
    if (manualCycleInterval) {
        clearInterval(manualCycleInterval);
    }

    const lanes = ['north', 'south', 'east', 'west'];
    const totalDuration = 30; // seconds for green light
    let currentLaneIndex = 0;
    let timeRemaining = totalDuration;

    const updateSignalDisplay = () => {
        lanes.forEach((lane, index) => {
            const card = document.querySelector(`.signal-card.${lane}`);
            if (!card) return;

            const indicator = card.querySelector('.signal-indicator');
            const timer = card.querySelector('.timing');
            const cardHeader = card.querySelector('h3');

            indicator.classList.remove('green', 'yellow', 'red');

            if (index === currentLaneIndex) {
                indicator.classList.add('green');
                timer.textContent = `${timeRemaining}s`;
                timer.style.color = '#5FD068';
                if(cardHeader) cardHeader.innerHTML = `🟢 ${lane.toUpperCase()}`;
            } else {
                indicator.classList.add('red');
                timer.textContent = `0s`;
                timer.style.color = '#FF6B6B';
                if(cardHeader) cardHeader.innerHTML = `🔴 ${lane.toUpperCase()}`;
            }
        });
    };

    manualCycleInterval = setInterval(() => {
        if (currentMode !== 'manual' || isEmergencyActive) {
            clearInterval(manualCycleInterval);
            return;
        }

        timeRemaining--;
        
        if (timeRemaining < 0) {
            currentLaneIndex = (currentLaneIndex + 1) % lanes.length;
            timeRemaining = totalDuration;
        }
        updateSignalDisplay();
    }, 1000);

    updateSignalDisplay(); // Initial call
}

// Generate Professional Traffic Report
async function generateTrafficReport() {
    try {
        showNotification('📊 Generating Professional Report...', 'info');
        
        // Fetch latest data
        const liveData = await fetch(`${API_BASE_URL}/live-data`).then(r => r.json());
        const aiDecisions = await fetch(`${API_BASE_URL}/ai-decisions`).then(r => r.json());
        
        // Create report HTML
        const reportWindow = window.open('', '_blank');
        reportWindow.document.write(generateReportHTML(liveData, aiDecisions));
        reportWindow.document.close();
        
        showNotification('✅ Report Generated Successfully', 'success');
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('❌ Failed to generate report', 'error');
    }
}

function generateReportHTML(liveData, aiData) {
    const currentDate = new Date().toLocaleDateString('en-IN');
    const currentTime = new Date().toLocaleTimeString('en-IN');
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Traffic Management Report - ${currentDate}</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 40px;
            background: #fff;
            color: #333;
        }
        .header {
            text-align: center;
            border-bottom: 3px solid #00CEC9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #0F0F23;
            margin: 0;
        }
        .header p {
            color: #666;
            margin: 5px 0;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .section h2 {
            color: #00CEC9;
            border-bottom: 2px solid #00CEC9;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }
        th {
            background: #00CEC9;
            color: white;
        }
        .ai-insight {
            background: #f0f9ff;
            padding: 15px;
            border-left: 4px solid #00CEC9;
            margin: 15px 0;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            color: #666;
        }
        @media print {
            .no-print { display: none; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚦 TRAFFIC MANAGEMENT SYSTEM</h1>
        <p>Intelligent Traffic Control & Analysis Report</p>
        <p><strong>Date:</strong> ${currentDate} | <strong>Time:</strong> ${currentTime}</p>
        <p><strong>Location:</strong> Raipur Smart Traffic Junction</p>
    </div>

    <div class="section">
        <h2>📊 Executive Summary</h2>
        <p><strong>Total Vehicles Monitored:</strong> ${liveData?.lanes?.reduce((sum, lane) => sum + (lane.current_vehicles || 0), 0) || 0}</p>
        <p><strong>Average Congestion:</strong> ${liveData?.lanes ? Math.round(liveData.lanes.reduce((sum, lane) => sum + (lane.density || 0), 0) / liveData.lanes.length) : 0}%</p>
        <p><strong>AI Model Status:</strong> Active (YOLO v8)</p>
        <p><strong>Detection Accuracy:</strong> 92%</p>
    </div>

    <div class="section">
        <h2>🚗 Lane-wise Traffic Data</h2>
        <table>
            <thead>
                <tr>
                    <th>Lane</th>
                    <th>Current Vehicles</th>
                    <th>Density (%)</th>
                    <th>Signal Status</th>
                    <th>Wait Time (s)</th>
                </tr>
            </thead>
            <tbody>
                ${liveData?.lanes?.map(lane => `
                    <tr>
                        <td><strong>${lane.lane_name}</strong></td>
                        <td>${lane.current_vehicles || 0}</td>
                        <td>${lane.density || 0}%</td>
                        <td style="color: ${lane.signal === 'GREEN' ? '#5FD068' : '#FF6B6B'}">${lane.signal || 'RED'}</td>
                        <td>${lane.wait_time || 0}s</td>
                    </tr>
                `).join('') || '<tr><td colspan="5">No data available</td></tr>'}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🤖 AI-Powered Insights</h2>
        <div class="ai-insight">
            <h3>${aiData?.action || 'AI Analysis'}</h3>
            <p><strong>Recommendation:</strong> ${aiData?.reason || 'N/A'}</p>
            <p><strong>Detailed Analysis:</strong> ${aiData?.detailed_analysis || 'N/A'}</p>
            <p><strong>Impact Prediction:</strong> ${aiData?.impact_prediction || 'N/A'}</p>
            <p><strong>Confidence Score:</strong> ${aiData?.confidence || 0}%</p>
            <p><strong>Priority Level:</strong> ${aiData?.priority_level || 'MEDIUM'}</p>
        </div>
    </div>

    <div class="section">
        <h2>⚡ Recommendations</h2>
        <ul>
            <li><strong>Primary Action:</strong> ${aiData?.action || 'Monitor traffic flow'}</li>
            <li><strong>Alternative:</strong> ${aiData?.alternative_action || 'Continue current signal timing'}</li>
            <li><strong>Risk Factors:</strong> ${aiData?.risk_factors || 'None identified'}</li>
        </ul>
    </div>

    <div class="footer">
        <p><strong>Generated by:</strong> Raipur AI Traffic Management System</p>
        <p>Powered by YOLO v8 | Gemini AI | Real-time Vehicle Detection</p>
        <p style="margin-top: 10px;">
            <button onclick="window.print()" class="no-print" style="padding: 10px 20px; background: #00CEC9; color: white; border: none; border-radius: 5px; cursor: pointer;">Print Report</button>
            <button onclick="window.close()" class="no-print" style="padding: 10px 20px; background: #FF6B6B; color: white; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">Close</button>
        </p>
    </div>
</body>
</html>
    `;
}

// Notification System
function showNotification(message, type = 'info') {
    const colors = {
        success: '#5FD068',
        error: '#FF6B6B',
        warning: '#FFA500',
        info: '#00CEC9'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        z-index: 10001;
        font-size: 12px;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}












