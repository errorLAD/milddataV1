// AI Business Assistant AJAX logic
document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('ai-chat-box');
    const inputForm = document.getElementById('ai-chat-form');
    const queryInput = document.getElementById('ai-query-input');

    if (!inputForm) return;

    inputForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = queryInput.value.trim();
        if (!text) return;

        // Append user bubble
        appendMessage('user', text);
        queryInput.value = '';

        // Show typing indicator
        const typingId = appendTypingIndicator();

        // Send AJAX query
        fetch('/ai-assistant/api/ask/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({ 'query': text })
        })
        .then(res => res.json())
        .then(data => {
            removeTypingIndicator(typingId);
            if (data.answer) {
                appendMessage('bot', formatMarkdown(data.answer));
            } else if (data.error) {
                appendMessage('bot', '⚠️ ' + data.error);
            }
        })
        .catch(err => {
            removeTypingIndicator(typingId);
            appendMessage('bot', '⚠️ Error contacting AI Assistant server.');
        });
    });

    function appendMessage(sender, htmlText) {
        const div = document.createElement('div');
        div.style.marginBottom = '0.75rem';
        div.style.display = 'flex';
        div.style.justifyContent = sender === 'user' ? 'flex-end' : 'flex-start';

        const bubble = document.createElement('div');
        bubble.style.maxWidth = '85%';
        bubble.style.padding = '0.6rem 0.85rem';
        bubble.style.borderRadius = '10px';
        bubble.style.fontSize = '0.74rem';
        bubble.style.lineHeight = '1.45';

        if (sender === 'user') {
            bubble.style.background = 'var(--brand)';
            bubble.style.color = '#FFFFFF';
        } else {
            bubble.style.background = 'var(--surface-alt)';
            bubble.style.border = '1px solid var(--border)';
            bubble.style.color = 'var(--text-primary)';
        }

        bubble.innerHTML = htmlText;
        div.appendChild(bubble);
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function appendTypingIndicator() {
        const id = 'typing-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.style.marginBottom = '0.75rem';
        div.innerHTML = `<div style="font-size: 0.68rem; color: var(--text-tertiary);">🤖 Analyzing fleet database...</div>`;
        chatContainer.appendChild(div);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function formatMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
});

function sendQuickQuery(queryText) {
    const input = document.getElementById('ai-query-input');
    const form = document.getElementById('ai-chat-form');
    if (input && form) {
        input.value = queryText;
        form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
}
