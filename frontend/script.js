const API_URL = "http://localhost:8000";

// DOM Elements
const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const meetingsList = document.getElementById('meetings-list');
const refreshMeetingsBtn = document.getElementById('refresh-meetings');
const openEmailBtn = document.getElementById('open-email-btn');
const closeEmailBtn = document.getElementById('close-email-btn');
const emailModal = document.getElementById('email-modal');
const emailForm = document.getElementById('email-form');

// --- Chat Logic ---

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', role);

    // Formatting newlines to <br> for display
    const formattedText = text.replace(/\n/g, '<br>');

    msgDiv.innerHTML = `<div class="bubble">${formattedText}</div>`;
    chatHistory.appendChild(msgDiv);

    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // 1. User Message
    appendMessage('user', text);
    userInput.value = '';
    userInput.disabled = true;

    // 2. Loading Indicator (Temporary)
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'assistant');
    loadingDiv.innerHTML = `<div class="bubble">Typing...</div>`;
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        // 3. API Call
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        // Remove loading
        chatHistory.removeChild(loadingDiv);

        // 4. Assistant Message
        if (data.response) {
            appendMessage('assistant', data.response);
        } else {
            appendMessage('assistant', "⚠️ Error: No response from agent.");
        }
    } catch (error) {
        chatHistory.removeChild(loadingDiv);
        appendMessage('assistant', `⚠️ Connection Error: ${error.message}`);
    } finally {
        userInput.disabled = false;
        userInput.focus();

        // Auto-refresh meetings if likely updated (e.g., after "schedule")
        if (text.toLowerCase().includes('schedule') || text.toLowerCase().includes('delete')) {
            setTimeout(fetchMeetings, 1000);
        }
    }
}

// Event Listeners for Chat
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// --- Meetings Logic ---

async function fetchMeetings() {
    meetingsList.innerHTML = '<div class="empty-state">Loading...</div>';

    try {
        const response = await fetch(`${API_URL}/meetings`);
        const data = await response.json();

        meetingsList.innerHTML = ''; // Clear

        // data.formatted_text is the string list, but data.meetings is structured list
        // Let's use formatted_text if it's the only thing for now, 
        // or iterate data.meetings if it exists (which we added in backend).
        // The backend returns: {"meetings": [...], "formatted_text": "..."}

        const meetings = data.meetings || [];

        if (meetings.length === 0) {
            meetingsList.innerHTML = '<div class="empty-state">No upcoming meetings.</div>';
        } else {
            meetings.forEach((m, index) => {
                const card = document.createElement('div');
                card.classList.add('meeting-card');
                card.innerHTML = `
                    <div class="meeting-title">${m.title}</div>
                    <div class="meeting-time">📅 ${m.start_time} (${m.duration}m)</div>
                `;
                meetingsList.appendChild(card);
            });
        }

    } catch (error) {
        meetingsList.innerHTML = `<div class="empty-state">Error: ${error.message}</div>`;
    }
}

refreshMeetingsBtn.addEventListener('click', fetchMeetings);

// --- Email Logic ---

openEmailBtn.addEventListener('click', () => {
    emailModal.classList.remove('hidden');
});

closeEmailBtn.addEventListener('click', () => {
    emailModal.classList.add('hidden');
});

emailForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const to = document.getElementById('email-to').value;
    const subject = document.getElementById('email-subject').value;
    const body = document.getElementById('email-body').value;
    const submitBtn = emailForm.querySelector('button[type="submit"]');

    submitBtn.textContent = "Sending...";
    submitBtn.disabled = true;

    try {
        const response = await fetch(`${API_URL}/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ to, subject, body })
        });

        const data = await response.json();

        if (response.ok) {
            alert('✅ Email sent successfully!');
            emailModal.classList.add('hidden');
            emailForm.reset();
        } else {
            alert(`❌ Error: ${data.detail || 'Failed to send'}`);
        }
    } catch (error) {
        alert(`❌ Connection Error: ${error.message}`);
    } finally {
        submitBtn.textContent = "Send Email";
        submitBtn.disabled = false;
    }
});

// Initial Load
fetchMeetings();
