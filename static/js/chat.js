document.addEventListener('DOMContentLoaded', () => {
    const roomId = window.location.pathname.split('/').pop();
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const fileInput = document.getElementById('file-input');
    const chatMessages = document.getElementById('chat-messages');
    const imagePreview = document.getElementById('image-preview');
    const currentUsername = document.getElementById('current-username').value;

    let lastMessageId = 0;
    let isConnected = false;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;
    const RECONNECT_DELAY = 2000;

    // Initialize websocket for real-time updates
    function initializeWebSocket() {
        const messagesEndpoint = `/api/messages/${roomId}`;

        // First load existing messages
        fetchMessages();

        // Set up polling for new messages (as an alternative to SSE)
        startMessagePolling();
    }

    // Fetch all messages from the server
    async function fetchMessages() {
        try {
            const response = await fetch(`/api/messages/${roomId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch messages');
            }

            const messages = await response.json();

            // Clear the messages container first if this is initial load
            if (lastMessageId === 0) {
                chatMessages.innerHTML = '';
            }

            // Display only new messages
            messages.forEach(message => {
                if (message.id > lastMessageId) {
                    displayMessage(message);
                    lastMessageId = Math.max(lastMessageId, message.id);
                }
            });

            // Scroll to the bottom
            scrollToBottom();

            isConnected = true;
            reconnectAttempts = 0;

        } catch (error) {
            console.error('Error fetching messages:', error);
            isConnected = false;

            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                setTimeout(fetchMessages, RECONNECT_DELAY);
            }
        }
    }

    // Poll for new messages every few seconds
    function startMessagePolling() {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                fetchMessages();
            }
        }, 3000); // Poll every 3 seconds when tab is visible
    }

    // Handle visibility change to optimize polling
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            fetchMessages(); // Immediately fetch when returning to tab
        }
    });

    // Display a message in the chat
    function displayMessage(message) {
        // Check if message already exists
        if (document.getElementById(`message-${message.id}`)) {
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.id = `message-${message.id}`;
        messageDiv.className = 'message';

        // Add class for own messages
        if (message.sender === currentUsername) {
            messageDiv.classList.add('message-self');
        }

        // Create message header with sender and time
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';

        const senderSpan = document.createElement('span');
        senderSpan.className = 'message-sender';
        senderSpan.textContent = message.sender;

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = message.timestamp;

        headerDiv.appendChild(senderSpan);
        headerDiv.appendChild(timeSpan);
        messageDiv.appendChild(headerDiv);

        // Handle different message types
        if (message.message_type === 'image' && message.image_url) {
            const messageContent = document.createElement('div');
            messageContent.className = 'message-image';

            const img = document.createElement('img');
            img.src = message.image_url;
            img.alt = 'Shared image';
            img.addEventListener('click', () => {
                window.open(message.image_url, '_blank');
            });

            messageContent.appendChild(img);
            messageDiv.appendChild(messageContent);
        } else if (message.text) {
            const messageContent = document.createElement('div');
            messageContent.className = 'message-text';
            messageContent.textContent = message.text;
            messageDiv.appendChild(messageContent);
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Scroll chat to bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Handle file input change
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) {
            imagePreview.innerHTML = '';
            return;
        }

        // Show file type icon and name
        imagePreview.innerHTML = '';

        if (file.type.startsWith('image/')) {
            // Create preview for images
            const img = document.createElement('img');
            img.className = 'preview-image';
            img.file = file;

            const reader = new FileReader();
            reader.onload = (e) => { img.src = e.target.result; };
            reader.readAsDataURL(file);

            const fileInfo = document.createElement('div');
            fileInfo.textContent = `Selected: ${file.name}`;

            imagePreview.appendChild(img);
            imagePreview.appendChild(fileInfo);
        } else {
            // For other file types, just show file name
            const fileIcon = document.createElement('i');
            fileIcon.className = 'bi bi-file-earmark';

            const fileInfo = document.createElement('div');
            fileInfo.textContent = `Selected: ${file.name}`;

            imagePreview.appendChild(fileIcon);
            imagePreview.appendChild(fileInfo);
        }
    });

    // Handle form submission
    messageForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const messageText = messageInput.value.trim();
        const file = fileInput.files[0];

        if (!messageText && !file) {
            return; // Nothing to send
        }

        // Clear input fields
        messageInput.value = '';

        try {
            const formData = new FormData();
            if (messageText) {
                formData.append('message', messageText);
            }
            if (file) {
                formData.append('image', file);
                fileInput.value = '';
                imagePreview.innerHTML = '';
            }

            const response = await fetch(`/api/messages/${roomId}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const message = await response.json();
            displayMessage(message);

            // Focus back on input after sending
            messageInput.focus();

        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        }
    });

    // Initialize the chat
    initializeWebSocket();

    // Focus on message input on page load
    messageInput.focus();
});