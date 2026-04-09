// ============================================================
// inbox.js — Messaging + Follow + Emoji Picker
//            + Reply / Edit / Unsend
// ============================================================

// Variables injected by the template before this file loads:
//   RECEIVER_ID, CURRENT_USER_ID, ACTIVE_DISP_NAME, lastMessageId

// ── STATE ──
let replyToId   = null;   // id of the message being replied to
let editMsgId   = null;   // id of the message being edited
let ctxTargetEl = null;   // the bubble element the context menu opened on

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
    div.dataset.msgId  = msg.id;
    div.dataset.isMine = msg.is_mine ? 'true' : 'false';

    let replyHtml = '';
    if (msg.reply_to_body) {
        replyHtml = `
        <div class="reply-quote">
            <span class="reply-quote-author">${escapeHtml(msg.reply_to_author)}</span>
            <span class="reply-quote-text">${escapeHtml(msg.reply_to_body.substring(0, 80))}${msg.reply_to_body.length > 80 ? '…' : ''}</span>
        </div>`;
    }

    // Toolbar is identical for every bubble; JS event delegation handles the rest
    const toolbarHtml = `
        <div class="bubble-actions">
            <button class="bubble-action-btn" title="React" onclick="bubbleReact(this)">
                <i class="far fa-smile"></i>
            </button>
            <button class="bubble-action-btn" title="Reply" onclick="bubbleReplyBtn(this)">
                <i class="fas fa-reply"></i>
            </button>
            <button class="bubble-action-btn bubble-action-more" title="More" onclick="bubbleMoreBtn(event, this)">
                <i class="fas fa-ellipsis-h"></i>
            </button>
        </div>`;

    div.innerHTML = `
        ${toolbarHtml}
        ${replyHtml}
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
        handleSend();
    }
}

// ── HANDLE SEND (new message OR save edit) ──
function handleSend() {
    if (editMsgId !== null) {
        saveEdit();
    } else {
        sendMessage();
    }
}

// ── SEND NEW MESSAGE ──
function sendMessage() {
    const input = document.getElementById('messageInput');
    if (!input) return;

    const body = input.value.trim();
    if (!body) return;

    const payload = { body };
    if (replyToId !== null) payload.reply_to_id = replyToId;

    input.value = '';
    input.style.height = 'auto';
    cancelReply();

    fetch(`/chat/send/${RECEIVER_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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

// ============================================================
//  CONTEXT MENU
// ============================================================
const ctxMenu = () => document.getElementById('bubbleContextMenu');

function showContextMenu(e, bubbleEl) {
    e.preventDefault();
    ctxTargetEl = bubbleEl;
    const menu  = ctxMenu();
    const isMine = bubbleEl.dataset.isMine === 'true';

    // Show/hide mine-only items
    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });

    // Position — keep inside viewport
    menu.classList.add('open');
    const mw = menu.offsetWidth, mh = menu.offsetHeight;
    let x = e.clientX, y = e.clientY;
    if (x + mw > window.innerWidth)  x = window.innerWidth  - mw - 8;
    if (y + mh > window.innerHeight) y = window.innerHeight - mh - 8;
    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';
}

function hideContextMenu() {
    ctxMenu().classList.remove('open');
    // NOTE: do NOT null ctxTargetEl here — action handlers read it after hiding
}

// ── CONTEXT MENU ACTIONS ──
// IMPORTANT: each handler captures what it needs FIRST, then hides the menu.
// The document click-outside listener uses a flag so it doesn't race with these.

let _ctxJustActioned = false;  // prevents the outside-click listener from firing on the same click

function ctxReplyClick() {
    if (!ctxTargetEl) return;

    // Capture everything before hiding
    const msgId    = parseInt(ctxTargetEl.dataset.msgId);
    const isMine   = ctxTargetEl.dataset.isMine === 'true';
    const bodyEl   = ctxTargetEl.querySelector('.bubble-text');
    const bodyText = bodyEl ? bodyEl.innerText.replace(/\n/g, ' ').trim() : '';
    const author   = isMine ? 'You' : ACTIVE_DISP_NAME;

    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();

    startReply(msgId, author, bodyText);
}

function ctxEditClick() {
    if (!ctxTargetEl) return;

    // Capture everything before hiding
    const msgId    = parseInt(ctxTargetEl.dataset.msgId);
    const bodyEl   = ctxTargetEl.querySelector('.bubble-text');
    const bodyText = bodyEl ? bodyEl.innerText.replace(/\n/g, ' ').trim() : '';

    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();

    startEdit(msgId, bodyText);
}

function ctxUnsendClick() {
    if (!ctxTargetEl) return;

    const msgId = parseInt(ctxTargetEl.dataset.msgId);
    const el    = ctxTargetEl;

    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();

    if (!confirm('Unsend this message? It will be removed for everyone.')) return;

    fetch(`/chat/unsend/${msgId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) { alert(data.error); return; }
        el.style.transition = 'opacity 0.25s, transform 0.25s';
        el.style.opacity    = '0';
        el.style.transform  = 'scale(0.92)';
        setTimeout(() => el.remove(), 270);
    });
}

// ============================================================
//  REPLY
// ============================================================
function startReply(msgId, author, bodyText) {
    // Guard: reply bar only exists when a conversation is open
    const bar        = document.getElementById('replyPreviewBar');
    const authorEl   = document.getElementById('replyPreviewAuthor');
    const textEl     = document.getElementById('replyPreviewText');
    const input      = document.getElementById('messageInput');
    if (!bar || !authorEl || !textEl || !input) return;

    // Exit any active edit first (but don't recurse into cancelReply)
    editMsgId = null;
    const editBar = document.getElementById('editModeBar');
    if (editBar) editBar.style.display = 'none';
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';

    replyToId        = msgId;
    authorEl.textContent = author;
    textEl.textContent   = bodyText.length > 70 ? bodyText.substring(0, 70) + '…' : bodyText;
    bar.style.display    = 'flex';
    input.focus();
}

function cancelReply() {
    replyToId = null;
    const bar      = document.getElementById('replyPreviewBar');
    const authorEl = document.getElementById('replyPreviewAuthor');
    const textEl   = document.getElementById('replyPreviewText');
    if (bar)      bar.style.display     = 'none';
    if (authorEl) authorEl.textContent  = '';
    if (textEl)   textEl.textContent    = '';
}

// ============================================================
//  EDIT
// ============================================================
function startEdit(msgId, currentText) {
    // Guard: edit bar only exists when a conversation is open
    const editBar = document.getElementById('editModeBar');
    const input   = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    if (!editBar || !input || !sendBtn) return;

    // Exit any active reply first (but don't recurse into cancelEdit)
    replyToId = null;
    const bar      = document.getElementById('replyPreviewBar');
    const authorEl = document.getElementById('replyPreviewAuthor');
    const textEl   = document.getElementById('replyPreviewText');
    if (bar)      bar.style.display    = 'none';
    if (authorEl) authorEl.textContent = '';
    if (textEl)   textEl.textContent   = '';

    editMsgId         = msgId;
    input.value       = currentText;
    autoResize(input);
    input.focus();
    // Move cursor to end of text
    input.selectionStart = input.selectionEnd = input.value.length;

    editBar.style.display  = 'flex';
    sendBtn.innerHTML      = '<i class="fas fa-check"></i>';
}

function cancelEdit() {
    editMsgId = null;
    const editBar = document.getElementById('editModeBar');
    const input   = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    if (editBar) editBar.style.display  = 'none';
    if (input)   { input.value = ''; input.style.height = 'auto'; }
    if (sendBtn) sendBtn.innerHTML      = '<i class="fas fa-paper-plane"></i>';
}

function saveEdit() {
    const input = document.getElementById('messageInput');
    const body  = input.value.trim();
    if (!body) return;

    const msgId = editMsgId;
    cancelEdit();

    fetch(`/chat/edit/${msgId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) { alert(data.error); return; }

        // Update the bubble in-place
        const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
        if (!bubble) return;
        const textEl = bubble.querySelector('.bubble-text');
        if (textEl) textEl.innerHTML = escapeHtml(data.body);

        // Add or update "edited" label in the time element
        const timeEl = bubble.querySelector('.bubble-time');
        if (timeEl && !timeEl.querySelector('.edited-label')) {
            timeEl.insertAdjacentHTML('beforeend', ' <span class="edited-label">· edited</span>');
        }
    });
}

// ============================================================
//  EMOJI PICKER
// ============================================================
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

    buildEmojiGrid('smileys');

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        picker.classList.toggle('open');
    });

    document.querySelectorAll('.emoji-cat-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.emoji-cat-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            buildEmojiGrid(btn.dataset.cat);
        });
    });

    document.addEventListener('click', (e) => {
        if (!picker.contains(e.target) && e.target !== toggleBtn) {
            picker.classList.remove('open');
        }
    });
}

// ============================================================
//  BUBBLE HOVER TOOLBAR HANDLERS
// ============================================================

// React button — placeholder, shows a small toast for now
function bubbleReact(btn) {
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    // TODO: implement full emoji reaction picker
    const toast = document.createElement('div');
    toast.className = 'reaction-toast';
    toast.textContent = 'Reactions coming soon!';
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 200); }, 1800);
}

// Reply button — same as right-click → Reply
function bubbleReplyBtn(btn) {
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    const msgId    = parseInt(bubble.dataset.msgId);
    const isMine   = bubble.dataset.isMine === 'true';
    const bodyEl   = bubble.querySelector('.bubble-text');
    const bodyText = bodyEl ? bodyEl.innerText.replace(/\n/g, ' ').trim() : '';
    const author   = isMine ? 'You' : ACTIVE_DISP_NAME;
    startReply(msgId, author, bodyText);
}

// More (three dots) button — opens the context menu anchored to the button
function bubbleMoreBtn(e, btn) {
    e.stopPropagation();
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;

    // Reuse the same context menu logic
    ctxTargetEl = bubble;
    const menu   = ctxMenu();
    const isMine = bubble.dataset.isMine === 'true';

    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });

    menu.classList.add('open');

    // Position below/above the three-dots button
    const rect = btn.getBoundingClientRect();
    const mw   = menu.offsetWidth;
    const mh   = menu.offsetHeight;
    let x = rect.left;
    let y = rect.bottom + 6;

    if (x + mw > window.innerWidth)  x = window.innerWidth  - mw - 8;
    if (y + mh > window.innerHeight) y = rect.top - mh - 6;

    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';
}

// Report button — placeholder
function ctxReportClick() {
    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();
    // TODO: implement report flow
    alert('Report submitted. Thank you for helping keep HireBon safe.');
}



// ============================================================
//  BUBBLE CONTEXT MENU — EVENT BINDING
// ============================================================
function initContextMenu() {
    const thread = document.getElementById('messageThread');
    if (!thread) return;

    // Right-click on desktop
    thread.addEventListener('contextmenu', (e) => {
        const bubble = e.target.closest('.message-bubble');
        if (!bubble) return;
        showContextMenu(e, bubble);
    });

    // Long-press on mobile
    let pressTimer = null;
    thread.addEventListener('touchstart', (e) => {
        const bubble = e.target.closest('.message-bubble');
        if (!bubble) return;
        pressTimer = setTimeout(() => {
            const touch = e.touches[0];
            showContextMenu(
                { preventDefault(){}, clientX: touch.clientX, clientY: touch.clientY },
                bubble
            );
        }, 500);
    }, { passive: true });

    thread.addEventListener('touchend', () => {
        clearTimeout(pressTimer);
    }, { passive: true });

    // Close on outside click — but not on the same click that triggered an action
    document.addEventListener('click', (e) => {
        if (_ctxJustActioned) { _ctxJustActioned = false; return; }
        const menu = ctxMenu();
        if (menu && !menu.contains(e.target)) {
            menu.classList.remove('open');
            ctxTargetEl = null;
        }
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            ctxMenu().classList.remove('open');
            ctxTargetEl = null;
            cancelReply();
            cancelEdit();
        }
    });
}

// ============================================================
//  INIT
// ============================================================
document.addEventListener('DOMContentLoaded', function () {
    scrollToBottom();
    initEmojiPicker();
    initContextMenu();

    if (typeof RECEIVER_ID !== 'undefined') {
        setInterval(poll, 3000);
    }
});
