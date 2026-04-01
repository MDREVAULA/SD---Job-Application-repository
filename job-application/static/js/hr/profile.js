function startEdit(section) {
    document.getElementById('view-' + section).style.display = 'none';
    document.getElementById('btn-edit-' + section).style.display = 'none';

    const form = document.getElementById('form-' + section);
    form.classList.remove('hidden');
    form.style.animation = 'none';
    requestAnimationFrame(() => {
        form.style.animation = 'formIn .22s ease both';
    });
}

function cancelEdit(section) {
    document.getElementById('form-' + section).classList.add('hidden');
    document.getElementById('view-' + section).style.display = '';
    document.getElementById('btn-edit-' + section).style.display = '';
}

(function () {
    const s = document.createElement('style');
    s.textContent = `
        @keyframes formIn {
            from { opacity: 0; transform: translateY(5px); }
            to   { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(s);
})();