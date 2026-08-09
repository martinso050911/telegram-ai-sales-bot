document.addEventListener('DOMContentLoaded', () => {
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const openChatBtn = document.getElementById('open-chat-btn');
    const chatCloseBtn = document.getElementById('chat-close-btn');
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');

    // Generate or retrieve persistent web session ID
    let sessionId = localStorage.getItem('web_chat_session_id');
    if (!sessionId) {
        sessionId = 'web_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
        localStorage.setItem('web_chat_session_id', sessionId);
    }

    function toggleChat() {
        chatWindow.classList.toggle('hidden');
        const isHidden = chatWindow.classList.contains('hidden');
        document.querySelector('.icon-open').classList.toggle('hidden', !isHidden);
        document.querySelector('.icon-close').classList.toggle('hidden', isHidden);
        if (!isHidden) {
            chatInput.focus();
        }
    }

    if (chatToggleBtn) chatToggleBtn.addEventListener('click', toggleChat);
    if (openChatBtn) openChatBtn.addEventListener('click', () => {
        if (chatWindow.classList.contains('hidden')) toggleChat();
    });
    if (chatCloseBtn) chatCloseBtn.addEventListener('click', toggleChat);

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // Append user message
        appendMessage(text, 'user-msg');
        chatInput.value = '';
        chatInput.disabled = true;
        chatSendBtn.disabled = true;

        // Typing indicator
        const typingMsg = appendMessage('Печатает... ⏳', 'bot-msg');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text
                })
            });

            const data = await response.json();
            typingMsg.remove();

            if (response.ok && data.response) {
                appendMessage(data.response, 'bot-msg');
            } else {
                appendMessage('Извините, произошла ошибка. Попробуйте еще раз.', 'bot-msg');
            }
        } catch (err) {
            console.error('Chat error:', err);
            typingMsg.remove();
            appendMessage('Ошибка подключения к AI-сервису.', 'bot-msg');
        } finally {
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    }

    function appendMessage(text, className) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${className}`;
        msgDiv.innerText = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    if (chatSendBtn) chatSendBtn.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }
});
