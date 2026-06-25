/* ============================================================
   SHOPIFY AGENTIC ASSISTANT — Client-Side Logic
   ============================================================ */

const API = {
    send: (sid, msg) => post('/api/send', { session_id: sid, message: msg }),
    sessions: () => get('/api/sessions'),
    loadChat: (sid) => get(`/api/session/${sid}`),
    newChat: () => post('/api/session/new', {}),
    deleteChat: (sid) => del(`/api/session/${sid}`),
    status: () => get('/api/status'),
};

async function get(url) { return (await fetch(url)).json(); }
async function post(url, body) { return (await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json(); }
async function del(url) { return (await fetch(url, { method: 'DELETE' })).json(); }

/* ---------- State ---------- */
let currentSessionId = null;
let activeHistoryItem = null;

/* ---------- DOM ---------- */
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const app = $('#app');
const sidebar = $('#sidebar');
const historyList = $('#history-list');
const messagesEl = $('#messages');
const inputEl = $('#message-input');
const sendBtn = $('#send-btn');
const newChatBtn = $('#new-chat-btn');
const deleteBtn = $('#delete-btn');
const themeToggle = $('#theme-toggle');
const sidebarToggle = $('#sidebar-toggle');
const dbStatusEl = $('#db-status');

/* ============================================================
   THEME
   ============================================================ */
function initTheme() {
    const saved = localStorage.getItem('shopify-agent-theme') || 'dark';
    setTheme(saved);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('shopify-agent-theme', theme);
    // Toggle icon visibility
    $('#theme-icon-moon').classList.toggle('hidden', theme === 'light');
    $('#theme-icon-sun').classList.toggle('hidden', theme === 'dark');
}

themeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
});

/* ============================================================
   SIDEBAR TOGGLE (mobile)
   ============================================================ */
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
});

/* ============================================================
   NEW CHAT
   ============================================================ */
newChatBtn.addEventListener('click', async () => {
    const data = await API.newChat();
    currentSessionId = data.session_id;
    clearMessages();
    showWelcome();
    await loadSessions();
    inputEl.focus();
});

/* ============================================================
   DELETE CHAT
   ============================================================ */
deleteBtn.addEventListener('click', async () => {
    if (!activeHistoryItem) return;
    const sid = activeHistoryItem.dataset.sid;

    // Determine current theme for SweetAlert
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const bg = isDark ? '#343541' : '#FFFFFF';
    const color = isDark ? '#ECECF1' : '#111827';

    const result = await Swal.fire({
        title: 'Delete chat?',
        text: "This action cannot be undone.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#EF4444',
        cancelButtonColor: isDark ? '#565869' : '#9CA3AF',
        confirmButtonText: 'Yes, delete it!',
        background: bg,
        color: color,
        customClass: {
            popup: 'swal-custom-popup'
        }
    });

    if (result.isConfirmed) {
        await API.deleteChat(sid);
        if (currentSessionId === sid) {
            currentSessionId = null;
            clearMessages();
            showWelcome();
        }
        await loadSessions();

        Swal.fire({
            title: 'Deleted!',
            text: 'Your chat has been deleted.',
            icon: 'success',
            background: bg,
            color: color,
            timer: 1500,
            showConfirmButton: false
        });
    }
});

/* ============================================================
   SEND MESSAGE
   ============================================================ */
sendBtn.addEventListener('click', handleSend);
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

inputEl.addEventListener('input', () => {
    // Auto-resize textarea
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
    // Enable/disable send
    sendBtn.disabled = !inputEl.value.trim();
});

async function handleSend() {
    const text = inputEl.value.trim();
    if (!text) return;

    // If no session yet, create one
    if (!currentSessionId) {
        const data = await API.newChat();
        currentSessionId = data.session_id;
    }

    // Remove welcome if present
    removeWelcome();

    // Show user message
    appendMessage('user', text);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    sendBtn.disabled = true;
    setInputLocked(true);

    // Show typing indicator
    const typingEl = showTypingIndicator();

    try {
        const data = await API.send(currentSessionId, text);
        removeTypingIndicator(typingEl);
        appendMessage('agent', data.response);
    } catch (err) {
        removeTypingIndicator(typingEl);
        appendMessage('system', 'Error communicating with the agent. Please try again.');
    }

    setInputLocked(false);
    inputEl.focus();
    await loadSessions();
}

/* ============================================================
   MESSAGES
   ============================================================ */
function clearMessages() {
    messagesEl.innerHTML = '';
}

function showWelcome() {
    if (messagesEl.querySelector('.welcome-message')) return;
    messagesEl.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🛍️</div>
            <h2>Shopify Agentic Assistant</h2>
            <p>How can I help you manage your store today?</p>
        </div>`;
}

function removeWelcome() {
    const w = messagesEl.querySelector('.welcome-message');
    if (w) w.remove();
}

function stripMarkdown(text) {
    if (!text) return text;
    text = text.replace(/\*\*(.+?)\*\*/g, '$1');
    text = text.replace(/__(.+?)__/g, '$1');
    text = text.replace(/(?<!\w)\*(.+?)\*(?!\w)/g, '$1');
    text = text.replace(/(?<!\w)_(.+?)_(?!\w)/g, '$1');
    text = text.replace(/^#{1,6}\s+/gm, '');
    text = text.replace(/^\*\s+/gm, '  •  ');
    return text;
}

function appendMessage(role, text) {
    const clean = stripMarkdown(text);
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    if (role === 'system') {
        row.innerHTML = `<div class="system-text">${escapeHtml(clean)}</div>`;
    } else {
        const isUser = role === 'user';
        const avatarClass = isUser ? 'user-avatar' : 'agent-avatar';
        const avatarText = isUser ? 'U' : 'A';
        const sender = isUser ? 'You' : 'Agent';
        const formattedText = escapeHtml(clean).replace(/\n/g, '<br>');

        if (isUser) {
            row.innerHTML = `
                <div class="msg-content" style="text-align:right">
                    <div class="msg-sender">${sender}</div>
                    <div class="msg-text">${formattedText}</div>
                </div>
                <div class="msg-avatar ${avatarClass}">${avatarText}</div>`;
        } else {
            row.innerHTML = `
                <div class="msg-avatar ${avatarClass}">${avatarText}</div>
                <div class="msg-content">
                    <div class="msg-sender">${sender}</div>
                    <div class="msg-text">${formattedText}</div>
                </div>`;
        }
    }

    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row agent';
    row.id = 'typing-row';
    row.innerHTML = `
        <div class="msg-avatar agent-avatar">A</div>
        <div class="msg-content">
            <div class="msg-sender">Agent</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>`;
    messagesEl.appendChild(row);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return row;
}

function removeTypingIndicator(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function setInputLocked(locked) {
    inputEl.disabled = locked;
    sendBtn.disabled = locked;
}

/* ============================================================
   SESSIONS
   ============================================================ */
async function loadSessions() {
    const data = await API.sessions();
    historyList.innerHTML = '';
    activeHistoryItem = null;

    data.sessions.forEach((s, i) => {
        const item = document.createElement('div');
        item.className = `history-item${i % 2 === 1 ? ' even' : ''}`;
        item.dataset.sid = s.session_id;
        item.innerHTML = `<span class="item-icon">💬</span><span>${escapeHtml(s.title)}</span>`;

        if (s.session_id === currentSessionId) {
            item.classList.add('active');
            activeHistoryItem = item;
        }

        item.addEventListener('click', () => loadChat(s.session_id, item));
        historyList.appendChild(item);
    });
}

async function loadChat(sid, itemEl) {
    currentSessionId = sid;

    // Highlight active
    $$('.history-item.active').forEach(el => el.classList.remove('active'));
    if (itemEl) { itemEl.classList.add('active'); activeHistoryItem = itemEl; }

    const data = await API.loadChat(sid);
    clearMessages();

    if (!data.messages || data.messages.length === 0) {
        showWelcome();
        return;
    }

    const visible = data.messages.filter(m => (m.role === 'user' || m.role === 'assistant') && m.content);
    if (visible.length === 0) {
        showWelcome();
        return;
    }

    visible.forEach(m => {
        const sender = m.role === 'user' ? 'user' : 'agent';
        appendMessage(sender, m.content);
    });
}

/* ============================================================
   DB STATUS
   ============================================================ */
async function loadStatus() {
    try {
        const data = await API.status();
        const dot = dbStatusEl.querySelector('.status-dot');
        const txt = dbStatusEl.querySelector('.status-text');
        if (data.db_connected) {
            dot.classList.remove('offline');
            txt.textContent = 'MongoDB Connected';
        } else {
            dot.classList.add('offline');
            txt.textContent = 'Local Storage';
        }
    } catch (e) {
        // ignore
    }
}

/* ============================================================
   INIT
   ============================================================ */
async function init() {
    initTheme();
    await loadStatus();
    await loadSessions();
    inputEl.focus();
}

init();
