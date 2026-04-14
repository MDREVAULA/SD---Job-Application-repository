// ============================================================
// inbox.js — Messaging + Follow + Emoji Picker
//            + Reply / Edit / Unsend + Reactions
// ============================================================

// Variables injected by the template before this file loads:
//   RECEIVER_ID, CURRENT_USER_ID, ACTIVE_DISP_NAME, lastMessageId

// ── STATE ──
let replyToId   = null;
let editMsgId   = null;
let ctxTargetEl = null;

// ── REACTION CONFIG ──
const REACTIONS = [
    { key: "like",  emoji: "👍", label: "Like"  },
    { key: "heart", emoji: "❤️", label: "Heart" },
    { key: "haha",  emoji: "😂", label: "Haha"  },
    { key: "wow",   emoji: "😮", label: "Wow"   },
    { key: "sad",   emoji: "😢", label: "Sad"   },
    { key: "angry", emoji: "😡", label: "Angry" },
];

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

// ── ESCAPE HTML ──
function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/\n/g, "<br>");
}

// ── BUILD REACTION BAR HTML ──
function buildReactionBarHtml(counts, myReaction) {
    if (!counts || Object.keys(counts).length === 0) return '';
    const chips = REACTIONS
        .filter(r => counts[r.key] && counts[r.key] > 0)
        .map(r => {
            const isMine = myReaction === r.key;
            return `<button class="reaction-chip${isMine ? ' mine' : ''}" data-r="${r.key}" title="${r.label}" onclick="onChipClick(this)">${r.emoji} <span class="chip-cnt">${counts[r.key]}</span></button>`;
        })
        .join('');
    return chips ? `<div class="reaction-bar">${chips}</div>` : '';
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
    div.dataset.myReaction = '';

    let replyHtml = '';
    if (msg.reply_to_body) {
        replyHtml = `
        <div class="reply-quote">
            <span class="reply-quote-author">${escapeHtml(msg.reply_to_author)}</span>
            <span class="reply-quote-text">${escapeHtml(msg.reply_to_body.substring(0, 80))}${msg.reply_to_body.length > 80 ? '…' : ''}</span>
        </div>`;
    }

    const toolbarHtml = `
        <div class="bubble-actions">
            <button class="bubble-action-btn bubble-action-react" title="React" onclick="bubbleReact(event, this)">
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
        <div class="reaction-bar-wrap"></div>
    `;
    thread.appendChild(div);
    scrollToBottom();
    lastMessageId = msg.id;
}

// ── SEND ON ENTER ──
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
}

function handleSend() {
    if (editMsgId !== null) {
        saveEdit();
    } else {
        sendMessage();
    }
}

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

// ── POLL NEW MESSAGES ──
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

// ── POLL REACTIONS (real-time reaction sync) ──
function pollReactions() {
    fetch(`/chat/poll-reactions/${RECEIVER_ID}`)
        .then(r => r.json())
        .then(data => {
            Object.entries(data).forEach(([msgId, info]) => {
                updateReactionBar(parseInt(msgId), info.counts, info.my_reaction);
            });
        })
        .catch(() => {
            // Silently ignore network errors for reaction polling
        });
}

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
//  REACTION PICKER
// ============================================================

let reactionPickerEl = null;      // the floating picker DOM node
let reactionPickerMsgId = null;   // which bubble it's attached to

function createReactionPicker() {
    const el = document.createElement('div');
    el.id = 'reactionPicker';
    el.className = 'bubble-reaction-picker';
    el.innerHTML = REACTIONS.map(r =>
        `<button class="rp-btn" data-r="${r.key}" title="${r.label}" onclick="pickReaction('${r.key}', this)">
            <span class="rp-emoji">${r.emoji}</span>
            <span class="rp-label">${r.label}</span>
        </button>`
    ).join('');
    document.body.appendChild(el);
    return el;
}

function showReactionPicker(triggerEl, msgId) {
    if (!reactionPickerEl) reactionPickerEl = createReactionPicker();

    // Mark current user's reaction
    const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
    const myR = bubble ? (bubble.dataset.myReaction || '') : '';
    reactionPickerEl.querySelectorAll('.rp-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.r === myR);
    });

    reactionPickerMsgId = msgId;
    reactionPickerEl.classList.add('open');

    // Position above the trigger button
    const rect = triggerEl.getBoundingClientRect();
    const pw   = reactionPickerEl.offsetWidth  || 260;
    const ph   = reactionPickerEl.offsetHeight || 60;
    let x = rect.left + rect.width / 2 - pw / 2;
    let y = rect.top - ph - 8;

    if (x < 8) x = 8;
    if (x + pw > window.innerWidth - 8) x = window.innerWidth - pw - 8;
    if (y < 8) y = rect.bottom + 8;

    reactionPickerEl.style.left = x + 'px';
    reactionPickerEl.style.top  = y + 'px';
}

function hideReactionPicker() {
    if (reactionPickerEl) reactionPickerEl.classList.remove('open');
    reactionPickerMsgId = null;
}

function pickReaction(reactionKey, btn) {
    const msgId = reactionPickerMsgId;
    if (!msgId) return;

    // Optimistically toggle active state in picker
    reactionPickerEl.querySelectorAll('.rp-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    hideReactionPicker();

    fetch(`/chat/react/${msgId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reaction: reactionKey })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;
        updateReactionBar(data.msg_id, data.counts, data.my_reaction);
    });
}

// Called when user clicks an existing chip under a bubble
function onChipClick(chipEl) {
    const bubble = chipEl.closest('.message-bubble');
    if (!bubble) return;

    const msgId  = parseInt(bubble.dataset.msgId);
    const rKey   = chipEl.dataset.r;

    fetch(`/chat/react/${msgId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reaction: rKey })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;
        updateReactionBar(data.msg_id, data.counts, data.my_reaction);
    });
}

function updateReactionBar(msgId, counts, myReaction) {
    const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
    if (!bubble) return;

    // Store my reaction on the bubble for picker to read later
    bubble.dataset.myReaction = myReaction || '';

    let wrap = bubble.querySelector('.reaction-bar-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.className = 'reaction-bar-wrap';
        bubble.appendChild(wrap);
    }
    wrap.innerHTML = buildReactionBarHtml(counts, myReaction);
}

// ── BUBBLE REACT BUTTON CLICK ──
function bubbleReact(e, btn) {
    e.stopPropagation();
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    const msgId = parseInt(bubble.dataset.msgId);

    if (reactionPickerEl && reactionPickerEl.classList.contains('open') && reactionPickerMsgId === msgId) {
        hideReactionPicker();
        return;
    }
    showReactionPicker(btn, msgId);
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
    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });
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
}

let _ctxJustActioned = false;

function ctxReplyClick() {
    if (!ctxTargetEl) return;
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
    const bar      = document.getElementById('replyPreviewBar');
    const authorEl = document.getElementById('replyPreviewAuthor');
    const textEl   = document.getElementById('replyPreviewText');
    const input    = document.getElementById('messageInput');
    if (!bar || !authorEl || !textEl || !input) return;
    editMsgId = null;
    const editBar = document.getElementById('editModeBar');
    if (editBar) editBar.style.display = 'none';
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    replyToId = msgId;
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
    const editBar = document.getElementById('editModeBar');
    const input   = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    if (!editBar || !input || !sendBtn) return;
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
        const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
        if (!bubble) return;
        const textEl = bubble.querySelector('.bubble-text');
        if (textEl) textEl.innerHTML = escapeHtml(data.body);
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
//  BUBBLE HOVER TOOLBAR
// ============================================================
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

function bubbleMoreBtn(e, btn) {
    e.stopPropagation();
    const bubble = btn.closest('.message-bubble');
    if (!bubble) return;
    ctxTargetEl = bubble;
    const menu   = ctxMenu();
    const isMine = bubble.dataset.isMine === 'true';
    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });
    menu.classList.add('open');
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

function ctxReportClick() {
    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();
    alert('Report submitted. Thank you for helping keep HireBon safe.');
}

// ============================================================
//  CONTEXT MENU INIT
// ============================================================
function initContextMenu() {
    const thread = document.getElementById('messageThread');
    if (!thread) return;
    thread.addEventListener('contextmenu', (e) => {
        const bubble = e.target.closest('.message-bubble');
        if (!bubble) return;
        showContextMenu(e, bubble);
    });
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
    document.addEventListener('click', (e) => {
        if (_ctxJustActioned) { _ctxJustActioned = false; return; }
        const menu = ctxMenu();
        if (menu && !menu.contains(e.target)) {
            menu.classList.remove('open');
            ctxTargetEl = null;
        }
        // Hide reaction picker on outside click
        if (reactionPickerEl && reactionPickerEl.classList.contains('open')) {
            if (!reactionPickerEl.contains(e.target) && !e.target.closest('.bubble-action-react')) {
                hideReactionPicker();
            }
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            ctxMenu().classList.remove('open');
            ctxTargetEl = null;
            cancelReply();
            cancelEdit();
            hideReactionPicker();
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

    // Load existing reactions for all bubbles on page load
    document.querySelectorAll('.message-bubble[data-msg-id]').forEach(bubble => {
        let rawCounts = {};
        try {
            rawCounts = JSON.parse(bubble.dataset.reactionCounts || '{}');
        } catch(e) {
            rawCounts = {};
        }
        const myReaction = bubble.dataset.myReaction || '';
        if (Object.keys(rawCounts).length > 0) {
            updateReactionBar(parseInt(bubble.dataset.msgId), rawCounts, myReaction);
        }
    });

    if (typeof RECEIVER_ID !== 'undefined') {
        // Poll new messages every 3 seconds
        setInterval(poll, 3000);
        // Poll reactions every 3 seconds for real-time reaction updates
        setInterval(pollReactions, 3000);
    }
});