let currentQuestionKey = null;

const chatroomName = window.chatroomName || '';
const wsPath = `/ws/chatroom/${chatroomName}`;
const chatSocket = new WebSocket('ws://' + window.location.host + wsPath);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    renderBotMessage(data);
};

function renderBotMessage(data) {
    const chat = document.getElementById('chat_messages');

    // Показать анкету, если есть
    if (data.profile) {
        const profDiv = document.createElement('div');
        profDiv.className = 'chat-message left';
        let profileHtml = `
            <div class="bubble profile-bubble" style="background:#232a36; color:#fff; border:2px solid #ffc107;">
                <b>Ваша анкета:</b><br>
                <table style="width:100%; margin-top:8px;">
                    <tr><td>Возраст:</td><td>${data.profile.age ?? '-'}</td></tr>
                    <tr><td>Пол:</td><td>${data.profile.gender ?? '-'}</td></tr>
                    <tr><td>Страна:</td><td>${data.profile.country ?? '-'}</td></tr>
                    <tr><td>Роль:</td><td>${data.profile.role ?? '-'}</td></tr>
                    <tr><td>Свободен с:</td><td>${formatTime(data.profile.available_from)}</td></tr>
                    <tr><td>О себе:</td><td>${data.profile.bio ?? '-'}</td></tr>
                    <tr><td>MMR:</td><td>${data.profile.MMR ?? '-'}</td></tr>
                </table>
        `;
        if (data.buttons) {
            profileHtml += '<div class="bot-btn-group" style="margin-top:16px;">';
            data.buttons.forEach(btn => {
                profileHtml += `<button class="bot-btn" onclick="sendChoice('${btn.value}')">${btn.text}</button>`;
            });
            profileHtml += '</div>';
        }
        profileHtml += '</div>';
        profDiv.innerHTML = `
            <div class="avatar">
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="Bot" width="40" height="40">
            </div>
            ${profileHtml}
            <div class="meta"><span class="nickname">Бот</span></div>
        `;
        chat.appendChild(profDiv);
    } else if (data.message) {
        // Сообщение от бота (если нет анкеты)
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message left';
        let bubbleHtml = `<div class="bubble">${data.message}`;
        if (data.buttons) {
            bubbleHtml += '<div class="bot-btn-group">';
            data.buttons.forEach(btn => {
                bubbleHtml += `<button class="bot-btn" onclick="sendChoice('${btn.value}')">${btn.text}</button>`;
            });
            bubbleHtml += '</div>';
        }
        bubbleHtml += '</div>';
        msgDiv.innerHTML = `
            <div class="avatar">
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="Bot" width="40" height="40">
            </div>
            ${bubbleHtml}
            <div class="meta"><span class="nickname">Бот</span></div>
        `;
        chat.appendChild(msgDiv);
        chat.scrollTop = chat.scrollHeight;
    }

    // Управление видимостью поля для ввода
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    if (userInput && sendBtn) {
        if (data.buttons && !data.profile) {
            userInput.style.display = 'none';
            sendBtn.style.display = 'none';
        } else {
            userInput.style.display = '';
            sendBtn.style.display = '';
        }
    }
    // Сохраняем ключ вопроса
    if (data.question_key) {
        currentQuestionKey = data.question_key;
    }
}

window.sendChoice = function(choice) {
    if (!currentQuestionKey) return;
    chatSocket.send(JSON.stringify({ question_key: currentQuestionKey, answer: choice }));
    renderUserMessage(choice);
};


function formatTime(timeStr) {
    if (!timeStr) return '-';
    const parts = timeStr.split(':');
    if (parts.length >= 2) {
        return `${parts[0]}:${parts[1]}`;
    }
    return timeStr;
}

document.addEventListener('DOMContentLoaded', function() {
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.onclick = function() {
            const input = document.getElementById('user-input');
            const text = input.value;
            if (text.trim() !== '' && currentQuestionKey) {
                chatSocket.send(JSON.stringify({ question_key: currentQuestionKey, answer: text }));
                renderUserMessage(text);
                input.value = '';
            }
        };
    }
});

function renderUserMessage(text) {
    const chat = document.getElementById('chat_messages');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'user-msg';
    msgDiv.textContent = text;
    chat.appendChild(msgDiv);
    chat.scrollTop = chat.scrollHeight;
} 