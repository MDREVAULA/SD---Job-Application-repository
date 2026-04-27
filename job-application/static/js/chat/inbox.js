// ============================================================
// inbox.js — Messaging + Follow + Emoji Picker
//            + Reply / Edit / Unsend + Reactions
// ============================================================

let replyToId   = null;
let editMsgId   = null;
let ctxTargetEl = null;
let _activeMenuAnchorBtn = null;

const REACTIONS = [
    { key: "like",  emoji: "👍", label: "Like"  },
    { key: "heart", emoji: "❤️", label: "Heart" },
    { key: "haha",  emoji: "😂", label: "Haha"  },
    { key: "wow",   emoji: "😮", label: "Wow"   },
    { key: "sad",   emoji: "😢", label: "Sad"   },
    { key: "angry", emoji: "😡", label: "Angry" },
];

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

function csrfFetch(url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    return fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            ...(options.headers || {}),
        }
    });
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function scrollToBottom() {
    const thread = document.getElementById('messageThread');
    if (thread) thread.scrollTop = thread.scrollHeight;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/\n/g, "<br>");
}

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

function removeBubbleFromDom(el) {
    el.style.transition = 'opacity 0.25s, transform 0.25s';
    el.style.opacity    = '0';
    el.style.transform  = 'scale(0.92)';
    setTimeout(() => el.remove(), 270);
}

function appendBubble(msg) {
    const thread = document.getElementById('messageThread');
    if (!thread) return;

    const empty = thread.querySelector('.thread-empty');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `message-bubble ${msg.is_mine ? 'mine' : 'theirs'}`;
    div.dataset.msgId      = msg.id;
    div.dataset.isMine     = msg.is_mine ? 'true' : 'false';
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

    csrfFetch(`/chat/send/${RECEIVER_ID}`, {
        method: 'POST',
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(msg => {
        if (msg.error) { alert(msg.error); return; }
        appendBubble(msg);
    });
}

function poll() {
    const knownIds = Array.from(
        document.querySelectorAll('.message-bubble[data-msg-id]')
    ).map(el => el.dataset.msgId).join(',');

    fetch(`/chat/poll/${RECEIVER_ID}?since=${lastMessageId}&known_ids=${knownIds}`)
        .then(r => r.json())
        .then(data => {
            const newMsgs = Array.isArray(data) ? data : (data.messages || []);
            const edited  = Array.isArray(data) ? [] : (data.edited  || []);
            const deleted = Array.isArray(data) ? [] : (data.deleted || []);

            newMsgs.forEach(msg => {
                if (!msg.is_mine) {
                    appendBubble(msg);
                } else if (msg.id > lastMessageId) {
                    lastMessageId = msg.id;
                }
            });

            edited.forEach(msg => {
                const bubble = document.querySelector(`.message-bubble[data-msg-id="${msg.id}"]`);
                if (!bubble) return;
                const textEl = bubble.querySelector('.bubble-text');
                if (textEl) textEl.innerHTML = escapeHtml(msg.body);
                const timeEl = bubble.querySelector('.bubble-time');
                if (timeEl && !timeEl.querySelector('.edited-label')) {
                    timeEl.insertAdjacentHTML('beforeend', ' <span class="edited-label">· edited</span>');
                }
            });

            deleted.forEach(msgId => {
                const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
                if (bubble) removeBubbleFromDom(bubble);
            });
        });
}

function pollReactions() {
    fetch(`/chat/poll-reactions/${RECEIVER_ID}`)
        .then(r => r.json())
        .then(data => {
            Object.entries(data).forEach(([msgId, info]) => {
                updateReactionBar(parseInt(msgId), info.counts, info.my_reaction);
            });
        })
        .catch(() => {});
}

function toggleFollowHeader(userId, btn) {
    csrfFetch(`/chat/follow/${userId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;
 
        if (data.action === 'followed') {
            btn.classList.add('following');
            btn.innerHTML = '<i class="fas fa-user-check"></i> Following';
 
        } else if (data.action === 'unfollowed') {
            btn.classList.remove('following');
            btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
 
        } else if (data.action === 'request_sent') {
            btn.classList.remove('following');
            btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Requested';
 
        } else if (data.action === 'request_cancelled') {
            btn.classList.remove('following');
            btn.innerHTML = '<i class="fas fa-user-plus"></i> Follow';
        }
    });
}

// ============================================================
//  REACTION PICKER
// ============================================================

let reactionPickerEl    = null;
let reactionPickerMsgId = null;

function createReactionPicker() {
    const el = document.createElement('div');
    el.id        = 'reactionPicker';
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

    const bubble = document.querySelector(`.message-bubble[data-msg-id="${msgId}"]`);
    const myR    = bubble ? (bubble.dataset.myReaction || '') : '';
    reactionPickerEl.querySelectorAll('.rp-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.r === myR);
    });

    reactionPickerMsgId = msgId;
    reactionPickerEl.classList.add('open');

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
    reactionPickerEl.querySelectorAll('.rp-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    hideReactionPicker();
    csrfFetch(`/chat/react/${msgId}`, {
        method: 'POST',
        body: JSON.stringify({ reaction: reactionKey })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) return;
        updateReactionBar(data.msg_id, data.counts, data.my_reaction);
    });
}

function onChipClick(chipEl) {
    const bubble = chipEl.closest('.message-bubble');
    if (!bubble) return;
    const msgId = parseInt(bubble.dataset.msgId);
    const rKey  = chipEl.dataset.r;
    csrfFetch(`/chat/react/${msgId}`, {
        method: 'POST',
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
    bubble.dataset.myReaction = myReaction || '';
    let wrap = bubble.querySelector('.reaction-bar-wrap');
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.className = 'reaction-bar-wrap';
        bubble.appendChild(wrap);
    }
    wrap.innerHTML = buildReactionBarHtml(counts, myReaction);
}

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

function positionMenuNearBtn(btn) {
    const menu      = ctxMenu();
    const rect      = btn.getBoundingClientRect();
    const mw        = menu.offsetWidth  || 160;
    const mh        = menu.offsetHeight || 180;

    // Boundaries: top = bottom of chat header, bottom = top of input bar
    const chatHeader = document.querySelector('.chat-header');
    const inputBar   = document.querySelector('.message-input-bar');
    const topBound   = chatHeader ? chatHeader.getBoundingClientRect().bottom : 64;
    const botBound   = inputBar  ? inputBar.getBoundingClientRect().top      : window.innerHeight - 80;

    let x = rect.left;
    let y = rect.bottom + 6;

    // Prefer above the button if below would overflow
    if (y + mh > botBound) y = rect.top - mh - 6;

    // If it still goes out of bounds on either edge, close instead
    if (y < topBound || y + mh > botBound) {
        hideContextMenu();
        return;
    }

    if (x + mw > window.innerWidth) x = window.innerWidth - mw - 8;

    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';
}

function showContextMenu(e, bubbleEl) {
    e.preventDefault();
    ctxTargetEl  = bubbleEl;
    const menu   = ctxMenu();
    const isMine = bubbleEl.dataset.isMine === 'true';

    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });

    const removeForYouBtn = document.getElementById('ctxRemoveForYou');
    if (removeForYouBtn) removeForYouBtn.style.display = 'flex';

    const reportBtn = document.getElementById('ctxReport');
    if (reportBtn) reportBtn.style.display = isMine ? 'none' : 'flex';

    menu.classList.add('open');

    // Right-click: position at cursor, not anchored to a button
    _activeMenuAnchorBtn = null;
    const mw = menu.offsetWidth, mh = menu.offsetHeight;
    let x = e.clientX, y = e.clientY;
    if (x + mw > window.innerWidth)  x = window.innerWidth  - mw - 8;
    if (y + mh > window.innerHeight) y = window.innerHeight - mh - 8;
    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';

    // Keep toolbar visible on the right-clicked bubble
    document.querySelectorAll('.message-bubble.menu-open').forEach(b => b.classList.remove('menu-open'));
    bubbleEl.classList.add('menu-open');
}

function hideContextMenu() {
    ctxMenu().classList.remove('open');
    document.querySelectorAll('.message-bubble.menu-open').forEach(b => b.classList.remove('menu-open'));
    _activeMenuAnchorBtn = null;
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
    csrfFetch(`/chat/unsend/${msgId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) { alert(data.error); return; }
        removeBubbleFromDom(el);
    });
}

function ctxRemoveForYouClick() {
    if (!ctxTargetEl) return;
    const msgId = parseInt(ctxTargetEl.dataset.msgId);
    const el    = ctxTargetEl;
    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();
    if (!confirm('Remove this message for you only? The other person can still see it.')) return;
    csrfFetch(`/chat/remove-for-me/${msgId}`, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        if (data.error) { alert(data.error); return; }
        removeBubbleFromDom(el);
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
    replyToId            = msgId;
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
    if (bar)      bar.style.display    = 'none';
    if (authorEl) authorEl.textContent = '';
    if (textEl)   textEl.textContent   = '';
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
    editMsgId              = msgId;
    input.value            = currentText;
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
    if (editBar) editBar.style.display = 'none';
    if (input)   { input.value = ''; input.style.height = 'auto'; }
    if (sendBtn) sendBtn.innerHTML     = '<i class="fas fa-paper-plane"></i>';
}

function saveEdit() {
    const input = document.getElementById('messageInput');
    const body  = input.value.trim();
    if (!body) return;
    const msgId = editMsgId;
    cancelEdit();
    csrfFetch(`/chat/edit/${msgId}`, {
        method: 'POST',
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
        const btn       = document.createElement('button');
        btn.className   = 'emoji-btn';
        btn.textContent = emoji;
        btn.type        = 'button';
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
    const bubble   = btn.closest('.message-bubble');
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

    const menu   = ctxMenu();
    const isMine = bubble.dataset.isMine === 'true';

    // Toggle off if already open for this exact button
    if (menu.classList.contains('open') && _activeMenuAnchorBtn === btn) {
        hideContextMenu();
        return;
    }

    ctxTargetEl          = bubble;
    _activeMenuAnchorBtn = btn;

    menu.querySelectorAll('.ctx-mine-only').forEach(el => {
        el.style.display = isMine ? 'flex' : 'none';
    });

    const removeForYouBtn = document.getElementById('ctxRemoveForYou');
    if (removeForYouBtn) removeForYouBtn.style.display = 'flex';

    const reportBtn = document.getElementById('ctxReport');
    if (reportBtn) reportBtn.style.display = isMine ? 'none' : 'flex';

    // Mark this bubble so its toolbar stays visible
    document.querySelectorAll('.message-bubble.menu-open').forEach(b => b.classList.remove('menu-open'));
    bubble.classList.add('menu-open');

    menu.classList.add('open');
    positionMenuNearBtn(btn);
}

function ctxReportClick() {
    _ctxJustActioned = true;
    ctxTargetEl = null;
    hideContextMenu();
    if (typeof pamOpenReport === 'function') {
        pamOpenReport();
    }
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

    // Reposition dropdown when thread scrolls
    thread.addEventListener('scroll', () => {
        const menu = ctxMenu();
        if (menu.classList.contains('open') && _activeMenuAnchorBtn) {
            positionMenuNearBtn(_activeMenuAnchorBtn);
        }
    }, { passive: true });

    document.addEventListener('click', (e) => {
        if (_ctxJustActioned) { _ctxJustActioned = false; return; }
        const menu = ctxMenu();
        if (menu && !menu.contains(e.target)) {
            menu.classList.remove('open');
            document.querySelectorAll('.message-bubble.menu-open').forEach(b => b.classList.remove('menu-open'));
            _activeMenuAnchorBtn = null;
            ctxTargetEl = null;
        }
        if (reactionPickerEl && reactionPickerEl.classList.contains('open')) {
            if (!reactionPickerEl.contains(e.target) && !e.target.closest('.bubble-action-react')) {
                hideReactionPicker();
            }
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideContextMenu();
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

    document.querySelectorAll('.message-bubble[data-msg-id]').forEach(bubble => {
        let rawCounts = {};
        try { rawCounts = JSON.parse(bubble.dataset.reactionCounts || '{}'); } catch(e) {}
        const myReaction = bubble.dataset.myReaction || '';
        if (Object.keys(rawCounts).length > 0) {
            updateReactionBar(parseInt(bubble.dataset.msgId), rawCounts, myReaction);
        }
    });

    if (typeof RECEIVER_ID !== 'undefined') {
        setInterval(poll, 3000);
        setInterval(pollReactions, 3000);
    }
});