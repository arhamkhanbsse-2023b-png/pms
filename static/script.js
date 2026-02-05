document.addEventListener('DOMContentLoaded', () => {
    const parkingGrid = document.getElementById('parkingGrid');
    const slotSelect = document.getElementById('slotSelect');
    const parkForm = document.getElementById('parkForm');
    const messageBox = document.getElementById('messageBox');
    const countAvailable = document.getElementById('countAvailable');
    const countOccupied = document.getElementById('countOccupied');

    let currentData = [];
    let activeMenuId = null; // Track open menu

    // --- FETCH DATA ---
    async function fetchData() {
        try {
            const response = await fetch('/full_status');
            const data = await response.json();

            // Only update DOM if data changed (simple check)
            // Note: with menus, we need to be careful not to re-render if user has a menu open?
            // Actually, if we re-render, the menu disappears. 
            // We can check if activeMenuId exists, if so pause updates?
            // Or just re-render and lose menu (simplest for now).
            if (activeMenuId === null && JSON.stringify(data) !== JSON.stringify(currentData)) {
                currentData = data;
                renderGrid(data);
                updateStats(data);
                updateDropdown(data);
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    // --- RENDER GRID ---
    function renderGrid(data) {
        parkingGrid.innerHTML = '';
        data.forEach((slot, index) => { // Added index for staggered animation delay
            const [id, status, plate, model] = slot;
            // Determine class based on status
            let statusClass = 'available';
            if (status === 'OCCUPIED') statusClass = 'occupied';
            else if (status === 'RESERVED') statusClass = 'reserved';
            else if (status === 'UNAVAILABLE') statusClass = 'unavailable';

            const card = document.createElement('div');
            card.className = `slot-card ${statusClass}`;
            card.style.animationDelay = `${index * 0.05}s`; // Staggered entrance

            card.innerHTML = `
                <div class="slot-header">
                    <span class="slot-id">${id}</span>
                    <div class="menu-container" style="position:relative;">
                        <i class="fa-solid fa-ellipsis-vertical menu-btn" onclick="toggleMenu('${id}', event)"></i>
                        <div class="context-menu" id="menu-${id}">
                            <button onclick="setStatus('${id}', 'AVAILABLE')"><i class="fa-solid fa-check"></i> Available</button>
                            <button onclick="setStatus('${id}', 'RESERVED')"><i class="fa-solid fa-bookmark"></i> Reserve</button>
                            <button onclick="setStatus('${id}', 'UNAVAILABLE')"><i class="fa-solid fa-ban"></i> Unavailable</button>
                        </div>
                    </div>
                </div>
                <div class="icon-area">
                    <i class="fa-solid fa-car"></i>
                </div>
                <!-- Status Badge below icon -->
                <div style="text-align:center; margin-bottom: 0.5rem;">
                    <span class="slot-status-badge">${status}</span>
                </div>

                ${status === 'OCCUPIED' ? `
                    <div class="car-details">
                        <span class="car-plate">${plate || 'Unknown'}</span>
                        <span class="car-model">${model || ''}</span>
                    </div>
                ` : ''}
            `;
            parkingGrid.appendChild(card);
        });
    }

    // --- WINDOW CLICK TO CLOSE MENUS ---
    window.addEventListener('click', (e) => {
        if (!e.target.classList.contains('menu-btn')) {
            closeAllMenus();
        }
    });

    // --- GLOBALS FOR HTML ONCLICK ---
    window.toggleMenu = (id, event) => {
        event.stopPropagation();
        const menu = document.getElementById(`menu-${id}`);
        const isVisible = menu.classList.contains('show');
        closeAllMenus();
        if (!isVisible) {
            menu.classList.add('show');
            activeMenuId = id;
        }
    };

    window.setStatus = async (id, status) => {
        try {
            await fetch('/update_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot_id: id, status: status })
            });
            fetchData(); // Force refresh
        } catch (e) {
            console.error(e);
        }
    };

    function closeAllMenus() {
        document.querySelectorAll('.context-menu').forEach(m => m.classList.remove('show'));
        activeMenuId = null;
    }

    // --- UPDATE STATS ---
    function updateStats(data) {
        const available = data.filter(s => s[1] === 'AVAILABLE').length;
        const occupied = data.filter(s => s[1] === 'OCCUPIED').length;

        countAvailable.textContent = available;
        countOccupied.textContent = occupied;
    }

    // --- UPDATE DROPDOWN ---
    function updateDropdown(data) {
        const currentSelection = slotSelect.value;
        slotSelect.innerHTML = '<option value="" disabled selected>Select Slot</option>';
        data.filter(s => s[1] === 'AVAILABLE').forEach(slot => {
            const option = document.createElement('option');
            option.value = slot[0];
            option.textContent = slot[0];
            slotSelect.appendChild(option);
        });
        if (currentSelection && Array.from(slotSelect.options).some(o => o.value === currentSelection)) {
            slotSelect.value = currentSelection;
        }
    }

    // --- HANDLE FORM SUBMIT ---
    parkForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const plate = document.getElementById('plate').value;
        const model = document.getElementById('model').value;
        const slot = slotSelect.value;

        if (!slot) {
            showMessage('Please select a slot!', 'error');
            return;
        }

        try {
            const response = await fetch('/park', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plate, model, slot })
            });

            if (response.ok) {
                showMessage(`Vehicle ${plate} parked successfully!`, 'success');
                parkForm.reset();
                fetchData();
            } else {
                showMessage('Error parking vehicle', 'error');
            }
        } catch (error) {
            showMessage('Network error', 'error');
        }
    });

    function showMessage(msg, type) {
        messageBox.textContent = msg;
        messageBox.className = type === 'success' ? 'success-msg' : 'error-msg';
        setTimeout(() => {
            messageBox.textContent = '';
            messageBox.className = '';
        }, 3000);
    }

    // Poll every 2 seconds
    fetchData(); // Initial load
    setInterval(fetchData, 2000);
});
