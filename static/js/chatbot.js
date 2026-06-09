const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');

// Enable sending message with Enter key
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Disable input while sending
    chatInput.disabled = true;
    sendBtn.disabled = true;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (response.ok) {
            // Add bot response
            addMessage(data.response, 'bot');
        } else {
            // Handle error
            addMessage(data.error || 'Sorry, something went wrong. Please try again.', 'bot');
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage('Sorry, I could not connect to the server. Please check your connection and try again.', 'bot');
        console.error('Chat error:', error);
    } finally {
        // Re-enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
}

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Convert markdown-style formatting to HTML
    const formattedText = formatMessage(text);
    contentDiv.innerHTML = formattedText;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
    // Convert **bold** to <strong>
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    // Convert numbered lists
    text = text.replace(/^(\d+)\.\s(.+)$/gm, '<li>$2</li>');
    
    // Convert bullet points
    text = text.replace(/^[-*]\s(.+)$/gm, '<li>$1</li>');
    
    // Wrap lists in ul tags
    if (text.includes('<li>')) {
        text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }
    
    return text;
}

function addTypingIndicator() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = 'typing-indicator';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return 'typing-indicator';
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.clear();
        window.location.href = '/logout';
    }
}

async function clearChat() {
    if (!confirm('Are you sure you want to clear the conversation? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/chat/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Clear the chat messages UI
            const initialMessage = chatMessages.querySelector('.bot-message');
            chatMessages.innerHTML = '';
            
            // Re-add the initial welcome message
            if (initialMessage) {
                chatMessages.appendChild(initialMessage.cloneNode(true));
            } else {
                // Add default welcome message
                const welcomeDiv = document.createElement('div');
                welcomeDiv.className = 'message bot-message';
                welcomeDiv.innerHTML = `
                    <div class="message-content">
                        <p>Hello! 👋 I'm your SmartCare health assistant. I'm here to help you with:</p>
                        <ul>
                            <li>Diet and nutrition advice</li>
                            <li>Fitness and exercise tips</li>
                            <li>Healthy eating habits</li>
                            <li>Weight management guidance</li>
                            <li>General wellness information</li>
                        </ul>
                        <p>How can I help you today?</p>
                    </div>
                `;
                chatMessages.appendChild(welcomeDiv);
            }
            
            chatInput.focus();
        } else {
            alert('Failed to clear chat. Please try again.');
        }
    } catch (error) {
        console.error('Clear chat error:', error);
        alert('Failed to clear chat. Please check your connection.');
    }
}

// Focus input on load
chatInput.focus();
