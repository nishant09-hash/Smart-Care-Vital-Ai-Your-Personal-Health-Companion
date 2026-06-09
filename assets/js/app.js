const createMessage = (text, type) => {
    const item = document.createElement('div');
    item.className = `chat-message ${type}`;
    item.textContent = text;
    return item;
};

document.querySelectorAll('[data-chat-form]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const windowNode = document.querySelector('[data-chat-window]');
        const input = form.querySelector('input[name="message"]');
        const goalSlug = form.querySelector('input[name="goal_slug"]').value;
        const message = input.value.trim();

        if (!message || !windowNode) {
            return;
        }

        windowNode.appendChild(createMessage(message, 'user'));
        input.value = '';

        try {
            const response = await fetch('/chatbot.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal_slug: goalSlug, message }),
            });
            const data = await response.json();
            windowNode.appendChild(createMessage(data.reply || 'Unable to fetch response right now.', 'ai'));
        } catch (error) {
            windowNode.appendChild(createMessage('Network issue. Please try again.', 'ai'));
        }

        windowNode.scrollTop = windowNode.scrollHeight;
    });
});

document.querySelectorAll('[data-goal-form]').forEach((form) => {
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const statusNode = form.querySelector('[data-goal-status]');
        const payload = Object.fromEntries(new FormData(form).entries());

        try {
            const response = await fetch('/save-goal.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            statusNode.textContent = data.message || 'Saved.';
            statusNode.className = response.ok ? 'ms-2 small text-success' : 'ms-2 small text-danger';
        } catch (error) {
            statusNode.textContent = 'Unable to save right now.';
            statusNode.className = 'ms-2 small text-danger';
        }
    });
});
