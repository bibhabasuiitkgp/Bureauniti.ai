$(document).ready(function () {
    const currentUser = 'bibhabasuiitkgp';
    const currentUTCDate = '2025-03-01 08:31:19';

    // Initialize calendar
    $('#calendar').evoCalendar({
        theme: 'Royal Navy',
        todayHighlight: true,
        sidebarDisplayDefault: false,
        format: 'yyyy-mm-dd',
        calendarEvents: []
    });

    // Function to generate event ID
    function generateEventId() {
        return `evt_${currentUser}_${Date.now()}`;
    }

    // Only after initialization, try to load saved events
    loadSavedEvents();

    // Update time
    function updateTime() {
        const now = new Date(currentUTCDate);
        const options = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        };
        const timeString = now.toLocaleString('en-US', options).replace(',', '');
        $('#current-time').text(timeString + ' UTC');
    }

    // Update time initially
    updateTime();

    // Modal Elements
    const modal = document.getElementById('eventModal');
    const closeModal = document.querySelector('.close-modal');
    const eventForm = document.getElementById('eventForm');
    const btnCancel = document.querySelector('.btn-cancel');

    // Show Modal Function
    function showModal() {
        modal.classList.add('show');
        const defaultDate = currentUTCDate.split(' ')[0];
        document.getElementById('eventDate').value = defaultDate;
        document.getElementById('eventDate').min = defaultDate;
        document.getElementById('eventEndDate').min = defaultDate;
    }

    // Hide Modal Function
    function hideModal() {
        modal.classList.remove('show');
        eventForm.reset();
    }

    // Generate Random ID
    function generateEventId() {
        return `evt_${currentUser}_${Date.now()}`;
    }

    // Event Color Map
    const eventTypeColors = {
        event: '#3498db',
        holiday: '#e74c3c',
        birthday: '#2ecc71',
        meeting: '#9b59b6'
    };

    // Modified loadSavedEvents function
    function loadSavedEvents() {
        try {
            const savedEvents = JSON.parse(localStorage.getItem(`calendarEvents_${currentUser}`)) || [];
            if (Array.isArray(savedEvents) && savedEvents.length > 0) {
                savedEvents.forEach(event => {
                    if (event && event.name && event.date) {
                        try {
                            $('#calendar').evoCalendar('addCalendarEvent', {
                                id: event.id || generateEventId(),
                                name: event.name,
                                date: event.date,
                                type: event.type || 'event',
                                description: event.description || '',
                                color: event.color || eventTypeColors[event.type] || '#3498db'
                            });
                        } catch (err) {
                            console.warn('Failed to add event:', event.name, err);
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Error loading saved events:', error);
            localStorage.removeItem(`calendarEvents_${currentUser}`);
        }
    }

    // Load saved events after a short delay
    setTimeout(loadSavedEvents, 100);

    // Event Handlers
    $('#addEventBtn').on('click', showModal);
    closeModal.addEventListener('click', hideModal);
    btnCancel.addEventListener('click', hideModal);
    window.addEventListener('click', (e) => {
        if (e.target === modal) hideModal();
    });

    // Event Type Change Handler
    document.getElementById('eventType').addEventListener('change', function (e) {
        const color = eventTypeColors[e.target.value];
        if (color) {
            document.getElementById('eventColor').value = color;
        }
    });

    // Handle start date change
    document.getElementById('eventDate').addEventListener('change', function (e) {
        const startDate = e.target.value;
        document.getElementById('eventEndDate').min = startDate;

        const endDate = document.getElementById('eventEndDate').value;
        if (endDate && endDate < startDate) {
            document.getElementById('eventEndDate').value = startDate;
        }
    });

    // Form Submit Handler
    // Modified form submit handler
    // Event Form Submit Handler
    $('#eventForm').on('submit', function (e) {
        e.preventDefault();

        const eventData = {
            id: generateEventId(),
            name: $('#eventName').val(),
            date: $('#eventEndDate').val() ?
                [$('#eventDate').val(), $('#eventEndDate').val()] :
                $('#eventDate').val(),
            type: $('#eventType').val(),
            description: $('#eventDescription').val(),
            color: $('#eventColor').val(),
            createdBy: currentUser,
            createdAt: currentUTCDate
        };

        try {
            // Add event to calendar using jQuery plugin method
            $('#calendar').evoCalendar('addCalendarEvent', eventData);

            // Save to localStorage
            const savedEvents = JSON.parse(localStorage.getItem(`calendarEvents_${currentUser}`)) || [];
            savedEvents.push(eventData);
            localStorage.setItem(`calendarEvents_${currentUser}`, JSON.stringify(savedEvents));

            alert(`Event "${eventData.name}" added successfully!`);
            $('#eventModal').modal('hide');
            $('#eventForm')[0].reset();
        } catch (error) {
            console.error('Error adding event:', error);
            alert('Error adding event. Please try again.');
        }
    });

    // Event click handler
    $('#calendar').on('selectEvent', function (event, activeEvent) {
        if (!activeEvent) return;

        const dateInfo = Array.isArray(activeEvent.date)
            ? `From: ${activeEvent.date[0]}\nTo: ${activeEvent.date[1]}`
            : `Date: ${activeEvent.date}`;

        let eventInfo = `Event Details:\n\nName: ${activeEvent.name}\n${dateInfo}`;

        if (activeEvent.description) {
            eventInfo += `\nDescription: ${activeEvent.description}`;
        }
        if (activeEvent.createdBy) {
            eventInfo += `\n\nCreated by: ${activeEvent.createdBy}\nCreated at: ${activeEvent.createdAt}`;
        }

        alert(eventInfo);
    });
});








document.addEventListener('DOMContentLoaded', () => {
    // Get user data from localStorage
    const userData = JSON.parse(localStorage.getItem('userData'));

    if (!userData) {
        // Redirect to login if no user data is found
        window.location.href = '/';
        return;
    }

    // Update profile information with user data
    updateProfileInfo(userData);

    // Calendar initialization
    $('#calendar').evoCalendar({
        theme: 'Default',
        todayHighlight: true,
        sidebarDisplayDefault: false,
        calendarEvents: []
    });

    // Event Modal Handling
    const modal = document.getElementById('eventModal');
    const addEventBtn = document.getElementById('addEventBtn');
    const closeBtn = document.querySelector('.close-modal');
    const cancelBtn = document.querySelector('.btn-cancel');
    const eventForm = document.getElementById('eventForm');

    // Show modal
    addEventBtn.onclick = () => {
        modal.style.display = 'block';
    }

    // Close modal
    closeBtn.onclick = () => {
        modal.style.display = 'none';
    }

    cancelBtn.onclick = () => {
        modal.style.display = 'none';
    }

    // Close on outside click
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }

    // Handle form submission
    eventForm.onsubmit = (e) => {
        e.preventDefault();

        const eventData = {
            name: document.getElementById('eventName').value,
            date: document.getElementById('eventDate').value,
            endDate: document.getElementById('eventEndDate').value || null,
            description: document.getElementById('eventDescription').value,
            type: document.getElementById('eventType').value,
            color: document.getElementById('eventColor').value
        };

        // Add event to calendar
        $('#calendar').evoCalendar('addCalendarEvent', {
            id: Date.now(), // Unique ID
            name: eventData.name,
            date: eventData.date,
            description: eventData.description,
            type: eventData.type,
            color: eventData.color
        });

        // Close modal and reset form
        modal.style.display = 'none';
        eventForm.reset();
    }
});

// Function to update profile information
function updateProfileInfo(userData) {
    // Update profile image with username
    const profileImage = document.querySelector('.profile-image img');
    profileImage.src = `https://api.dicebear.com/6.x/avataaars/svg?seed=${userData.username}`;

    // Update name
    document.querySelector('.profile-header h2').textContent = userData.name;

    // Update designation/title
    document.querySelector('.profile-header .title').textContent = userData.designation;

    // Update email
    document.querySelector('.info-box:nth-child(1) p').textContent = userData.email;

    // Update phone
    document.querySelector('.info-box:nth-child(2) p').textContent = userData.phone;

    // Update work experience
    // document.querySelector('.info-box:nth-child(3) p').textContent = userData.workExperience;

    // Add logout button to social links
    const socialLinks = document.querySelector('.social-links');
    const logoutButton = document.createElement('a');
    logoutButton.href = '#';
    logoutButton.className = 'social-icon logout';
    logoutButton.innerHTML = '<i class="fas fa-sign-out-alt"></i>';
    logoutButton.addEventListener('click', handleLogout);
    socialLinks.appendChild(logoutButton);
}

// Function to handle logout
function handleLogout() {
    localStorage.removeItem('userData');
    window.location.href = '/';
}