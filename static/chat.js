let messageCount = 0;

// Theme toggle
const themeToggle = document.getElementById('theme-toggle');
const savedTheme = localStorage.getItem('theme') || 'light';
if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    themeToggle.textContent = '☀️';
}

themeToggle?.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    themeToggle.textContent = isDark ? '☀️' : '🌙';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
});

// Get current time
function getTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

// Show typing indicator
function showTyping() {
    document.getElementById('typing').style.display = 'flex';
    scrollToBottom();
}

function hideTyping() {
    document.getElementById('typing').style.display = 'none';
}

// Add message to chat
function addMessage(text, sender) {
    const chatbox = document.getElementById('chatbox');
    
    // Remove welcome message after first interaction
    if (messageCount === 0) {
        const welcome = chatbox.querySelector('.welcome-message');
        if (welcome) welcome.remove();
    }
    messageCount++;
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg ${sender}`;
    msgDiv.innerHTML = text + `<span class="msg-time">${getTime()}</span>`;
    chatbox.appendChild(msgDiv);
    scrollToBottom();
}

function scrollToBottom() {
    const chatbox = document.getElementById('chatbox');
    chatbox.scrollTop = chatbox.scrollHeight;
}

// Send message
async function send() {
    const input = document.getElementById('user-input');
    const msg = input.value.trim();
    if (!msg) return;
    
    addMessage(msg, 'user');
    input.value = '';
    
    showTyping();
    
    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        
        hideTyping();
        
        if (!res.ok) throw new Error('Server error');
        
        const data = await res.json();
        addMessage(data.reply, 'bot');
        
    } catch (err) {
        hideTyping();
        addMessage('⚠️ Sorry, I encountered an error. Please try again.', 'bot');
    }
}

// Quick reply function
function sendQuickReply(text) {
    const input = document.getElementById('user-input');
    input.value = text;
    send();
}

// Voice input (no TTS output)
const voiceBtn = document.getElementById('voice');
voiceBtn?.addEventListener('click', () => {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        alert('❌ Voice input not supported in this browser.\n\nPlease use Chrome, Edge, or Safari.');
        return;
    }
    
    try {
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        voiceBtn.style.background = '#ef4444';
        voiceBtn.textContent = '⏺️';
        voiceBtn.disabled = true;
        
        recognition.onstart = () => {
            console.log('Voice recognition started');
        };
        
        recognition.onresult = (e) => {
            const transcript = e.results[0][0].transcript;
            document.getElementById('user-input').value = transcript;
            voiceBtn.style.background = '';
            voiceBtn.textContent = '🎤';
            voiceBtn.disabled = false;
            send();
        };
        
        recognition.onend = () => {
            voiceBtn.style.background = '';
            voiceBtn.textContent = '🎤';
            voiceBtn.disabled = false;
        };
        
        recognition.onerror = (e) => {
            voiceBtn.style.background = '';
            voiceBtn.textContent = '🎤';
            voiceBtn.disabled = false;
            
            let errorMsg = 'Voice input failed';
            if (e.error === 'not-allowed') {
                errorMsg = '❌ Microphone access denied.\n\nPlease allow microphone permission in browser settings.';
            } else if (e.error === 'no-speech') {
                errorMsg = '🔇 No speech detected. Please try again.';
            } else if (e.error === 'network') {
                errorMsg = '🌐 Network error. Check your internet connection.';
            } else if (e.error === 'aborted') {
                errorMsg = 'Voice input cancelled.';
            }
            
            console.error('Speech recognition error:', e.error);
            alert(errorMsg);
        };
        
        recognition.start();
    } catch (err) {
        voiceBtn.style.background = '';
        voiceBtn.textContent = '🎤';
        voiceBtn.disabled = false;
        console.error('Voice recognition error:', err);
        alert('❌ Voice input initialization failed. Please try again.');
    }
});

// Send button
document.getElementById('send')?.addEventListener('click', send);

// Enter key
document.getElementById('user-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') send();
});
