// ============================================================
// inbox.js — Messaging + Follow + Emoji Picker
// ============================================================

// Variables injected by the template before this file loads:
//   RECEIVER_ID, CURRENT_USER_ID, lastMessageId

// ── EMOJI DATA ──
const EMOJI_DATA = {
    smileys: [
        '😀','😃','😄','😁','😆','😅','🤣','😂','🙂','🙃',
        '😉','😊','😇','🥰','😍','🤩','😘','😗','😚','😙',
        '🥲','😋','😛','😜','🤪','😝','🤑','🤗','🤭','🤫',
        '🤔','🤐','🤨','😐','😑','😶','😏','😒','🙄','😬',
        '😮','😯','😲','😳','🥺','😦','😧','😨','😰','😥',
        '😢','😭','😱','😖','😣','😞','😓','😩','😫','🥱',
        '😤','😡','🤬','😈','👿','💀','☠️','💩','🤡','👹',
        '😺','😸','😹','😻','😼','😽','🙀','😿','😾'
    ],
    gestures: [
        '👋','🤚','🖐️','✋','🖖','👌','🤌','🤏','✌️','🤞',
        '🤟','🤘','🤙','👈','👉','👆','🖕','👇','☝️','👍',
        '👎','✊','👊','🤛','🤜','👏','🙌','👐','🤲','🤝',
        '🙏','✍️','💅','🤳','💪','🦵','🦶','👂','🦻','👃',
        '🫀','🫁','🧠','🦷','🦴','👀','👁️','👅','👄'
    ],
    hearts: [
        '❤️','🧡','💛','💚','💙','💜','🖤','🤍','🤎','💔',
        '❤️‍🔥','❤️‍🩹','❣️','💕','💞','💓','💗','💖','💘','💝',
        '💟','☮️','✝️','☯️','🕉️','🛐','⛎','♈','♉','♊',
        '💋','💌','💍','💎','🫶','🥰'
    ],
    nature: [
        '🐶','🐱','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯',
        '🦁','🐮','🐷','🐸','🐵','🙈','🙉','🙊','🐔','🐧',
        '🐦','🦆','🦅','🦉','🦇','🐺','🐗','🐴','🦄','🐝',
        '🌸','🌺','🌻','🌹','🌷','🌱','🌿','🍀','🍁','🍂',
        '🍃','🌾','🌵','🌴','🌳','🌲','🎋','🎍','☘️','🌊',
        '🌈','⛅','🌤️','🌙','⭐','🌟','💫','⚡','🌪️','🌞'
    ],
    food: [
        '🍎','🍊','🍋','🍇','🍓','🫐','🍈','🍑','🍒','🥭',
        '🍍','🥝','🍅','🥥','🥑','🍆','🥔','🌽','🌶️','🥕',
        '🧄','🧅','🥦','🥬','🥒','🍄','🧀','🥚','🍳','🥞',
        '🧇','🥓','🥩','🍗','🍖','🌭','🍔','🍟','🍕','🫔',
        '🌮','🌯','🥙','🧆','🍜','🍝','🍛','🍲','🍣','🍱',
        '🍤','🍙','🍚','🍘','🍥','🥮','🍡','🍧','🍨','🍦',
        '🥧','🧁','🍰','🎂','🍮','🍭','🍬','🍫','🍿','☕',
        '🍵','🧃','🥤','🧋','🍺','🍻','🥂','🍷','🥃'
    ],
    travel: [
        '✈️','🚀','🛸','🚁','🛺','🚗','🚕','🚙','🚌','🚎',
        '🏎️','🚓','🚑','🚒','🚐','🛻','🚚','🚛','🚜','🛵',
        '🏍️','🚲','🛴','🛹','🚂','🚃','🚄','🚅','🚆','🚇',
        '⛵','🚤','🛥️','🛳️','⛴️','🚢','⚓','🗺️','🗽','🗼',
        '🏰','🏯','🏟️','🎡','🎢','🎠','⛲','⛺','🌁','🏔️',
        '🌋','🗻','🏕️','🏖️','🏜️','🏝️','🏞️','🌃','🏙️','🌄',
        '🌅','🌆','🌇','🌉','🎑','🏳️','🏴','🚩','🎌'
    ],
    objects: [
        '💡','🔦','🕯️','🪔','💰','💳','💎','⚖️','🔑','🗝️',
        '🔨','🪓','⛏️','⚒️','🛠️','🗡️','⚔️','🛡️','🔧','🔩',
        '⚙️','🗜️','🔗','⛓️','🧲','🔪','🗃️','🗄️','🗑️','🔒',
        '🔓','📱','💻','🖥️','🖨️','⌨️','📷','📸','📹','🎥',
        '📽️','🎞️','📞','☎️','📟','📠','📺','📻','🎙️','🎚️',
        '🎛️','🧭','⏱️','⏲️','⏰','🕰️','📡','🔋','🔌','🔭',
        '🧰','🪣','🧲','💊','🩺','🩻','🩹','🧬','🔬','🧪'
    ],
    symbols: [
        '🔥','💯','✨','⭐','🌟','💫','⚡','🎉','🎊','🎈',
        '🎁','🎀','🎗️','🏆','🥇','🥈','🥉','🏅','🎖️','🎯',
        '🎮','🎲','🧩','♟️','🎭','🎨','🖼️','🎪','🎤','🎧',
        '🎼','🎵','🎶','🎷','🎺','🎸','🎹','🥁','🎻','🎬',
        '📢','📣','🔔','🔕','💬','💭','🗯️','♠️','♥️','♦️',
        '♣️','🃏','🀄','🎴','✅','❎','🔴','🟠','🟡','🟢',
        '🔵','🟣','⚫','⚪','🟤','🔶','🔷','🔸','🔹','🔺',
        '🔻','💠','🔘','🔲','🔳','▪️','▫️','◾','◽','◼️'
    ]
};

// ── AUTO-RESIZE TEXTAREA ──
function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ── SCROLL TO BOTTOM ──
function scrollToBottom() {
    const thread = document.getElementById('messageThread');
    if (thread) thread.scrollTop = thread.scrollHeight;
}

// ── ESCAPE HTML (prevent XSS) ──
function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/\n/g, "<br>");
}

// ── APPEND A MESSAGE BUBBLE ──
function appendBubble(msg) {
    const thread = document.getElementById('messageThread');
    if (!thread) return;

    const empty = thread.querySelector('.thread-empty');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `message-bubble ${msg.is_mine ? 'mine' : 'theirs'}`;
    div.dataset.msgId = msg.id;
    div.innerHTML = `
        <div class="bubble-text">${escapeHtml(msg.body)}</div>
        <div class="bubble-time">${msg.created_at}</div>
    `;
    thread.appendChild(div);
    scrollToBottom();
    lastMessageId = msg.id;
}

// ── SEND ON ENTER (Shift+Enter = newline) ──
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ── SEND MESSAGE ──
function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) return;

    const body = input.value.trim();
    if (!body) return;

    input.value = '';
    input.style.height = 'auto';

    fetch(`/chat/send/${RECEIVER_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body })
    })
    .then(r => r.json())
    .then(msg => {
        if (msg.error) { alert(msg.error); return; }
        appendBubble(msg);
    });
}

// ── POLL FOR NEW MESSAGES (every 3 seconds) ──
function poll() {
    fetch(`/chat/poll/${RECEIVER_ID}?since=${lastMessageId}`)
        .then(r => r.json())
        .then(messages => {
            messages.forEach(msg => {
                if (!msg.is_mine) {
                    appendBubble(msg);
                } else if (msg.id > lastMessageId) {
                    lastMessageId = msg.id;
                }
            });
        });
}

// ── FOLLOW TOGGLE IN CHAT HEADER ──
function toggleFollowHeader(userId, btn) {
    fetch(`/chat/follow/${userId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;
        const isNowFollowing = data.action === 'followed';
        btn.classList.toggle('following', isNowFollowing);
        btn.innerHTML = isNowFollowing
            ? '<i class="fas fa-user-check"></i> Following'
            : '<i class="fas fa-user-plus"></i> Follow';
    });
}

// ── EMOJI PICKER ──
function buildEmojiGrid(category) {
    const grid = document.getElementById('emojiGrid');
    if (!grid) return;
    grid.innerHTML = '';
    (EMOJI_DATA[category] || []).forEach(emoji => {
        const btn = document.createElement('button');
        btn.className = 'emoji-btn';
        btn.textContent = emoji;
        btn.type = 'button';
        btn.addEventListener('click', () => insertEmoji(emoji));
        grid.appendChild(btn);
    });
}

function insertEmoji(emoji) {
    const input = document.getElementById('messageInput');
    if (!input) return;

    const start = input.selectionStart;
    const end   = input.selectionEnd;
    const text  = input.value;

    input.value = text.slice(0, start) + emoji + text.slice(end);
    input.selectionStart = input.selectionEnd = start + emoji.length;
    input.focus();
    autoResize(input);
}

function initEmojiPicker() {
    const toggleBtn = document.getElementById('emojiToggleBtn');
    const picker    = document.getElementById('emojiPicker');
    if (!toggleBtn || !picker) return;

    // Build default category on first open
    buildEmojiGrid('smileys');

    // Toggle open/close
    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        picker.classList.toggle('open');
    });

    // Category switching
    document.querySelectorAll('.emoji-cat-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.emoji-cat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            buildEmojiGrid(btn.dataset.cat);
        });
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!picker.contains(e.target) && e.target !== toggleBtn) {
            picker.classList.remove('open');
        }
    });
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', function () {
    scrollToBottom();
    initEmojiPicker();

    if (typeof RECEIVER_ID !== 'undefined') {
        setInterval(poll, 3000);
    }
});