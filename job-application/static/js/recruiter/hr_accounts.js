var currentPage = 1;
var rowsPerPage = 6;
var allRowsArray = [];
var currentFilteredRows = [];
var windowStart = 1;
var pendingDeletes = {};

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader(
                'X-CSRFToken',
                $('meta[name="csrf-token"]').attr('content')
            );
        }
    }
});

$(document).ready(function() {

    function storeAllRows() {
        allRowsArray = [];
        $('#hrTableBody tr').each(function() {
            allRowsArray.push($(this));
        });
    }
    storeAllRows();

    $('#filterBtn').on('click', function(e) {
        e.stopPropagation();
        $('#filterMenu').toggleClass('show');
    });

    $(document).on('click', function(e) {
        if (!$(e.target).closest('.date-filter').length) {
            $('#filterMenu').removeClass('show');
        }
    });

    var currentSort = null;
    var currentStatusFilter = null;

    $(document).on('click', '.filter-option-modern', function() {
        var sortType   = $(this).data('sort');
        var filterType = $(this).data('filter');

        if (sortType === 'name_asc') {
            currentSort = 'name_asc';
            currentStatusFilter = null;
        } else if (sortType === 'name_desc') {
            currentSort = 'name_desc';
            currentStatusFilter = null;
        } else if (filterType === 'active') {
            currentStatusFilter = 'active';
            currentSort = null;
        } else if (filterType === 'pending') {
            currentStatusFilter = 'pending';
            currentSort = null;
        } else if (filterType === 'all') {
            currentStatusFilter = null;
            currentSort = null;
        }

        $('#filterMenu').removeClass('show');
        currentPage  = 1;
        windowStart  = 1;
        applyFiltersAndPagination();
    });

    $(document).on('click', '.status-filter-btn', function() {
        $('.status-filter-btn').removeClass('active');
        $(this).addClass('active');
        currentPage = 1;
        windowStart = 1;
        applyFiltersAndPagination();
    });

    $('#hrSearch').on('keyup', function() {
        currentPage = 1;
        windowStart = 1;
        applyFiltersAndPagination();
    });

    function applyFiltersAndPagination() {
        var searchTerm      = ($('#hrSearch').val() || '').toLowerCase();
        var activeTabFilter = $('.status-filter-btn.active').data('filter') || 'all';

        var filteredRows = [];

        allRowsArray.forEach(function($row) {
            var name   = ($row.data('name')  || '').toString();
            var email  = ($row.data('email') || '').toString();
            var status = ($row.data('status') || '').toString();

            var searchMatch = searchTerm === '' ||
                name.indexOf(searchTerm)  > -1  ||
                email.indexOf(searchTerm) > -1;

            var tabMatch = true;
            if (activeTabFilter === 'active')  tabMatch = (status === 'active');
            if (activeTabFilter === 'pending') tabMatch = (status === 'pending');

            var dropdownMatch = true;
            if (currentStatusFilter === 'active')  dropdownMatch = (status === 'active');
            if (currentStatusFilter === 'pending') dropdownMatch = (status === 'pending');

            if (searchMatch && tabMatch && dropdownMatch) {
                filteredRows.push($row);
            }
        });

        if (currentSort === 'name_asc') {
            filteredRows.sort(function(a, b) {
                return ($(a).data('fullname') || '').toString().toLowerCase()
                    .localeCompare(($(b).data('fullname') || '').toString().toLowerCase());
            });
        } else if (currentSort === 'name_desc') {
            filteredRows.sort(function(a, b) {
                return ($(b).data('fullname') || '').toString().toLowerCase()
                    .localeCompare(($(a).data('fullname') || '').toString().toLowerCase());
            });
        }

        currentFilteredRows = filteredRows;
        updateDisplay(filteredRows);
    }

    function updateDisplay(filteredRows) {
        var totalRows  = filteredRows.length;
        var totalPages = Math.max(1, Math.ceil(totalRows / rowsPerPage));
        if (currentPage > totalPages) currentPage = totalPages;

        var start = (currentPage - 1) * rowsPerPage;
        var end   = start + rowsPerPage;

        var $tbody = $('#hrTableBody');
        $tbody.children('tr').detach();

        filteredRows.forEach(function($row) {
            $tbody.append($row);
        });

        filteredRows.forEach(function($row, idx) {
            if (idx >= start && idx < end) {
                $row.show();
            } else {
                $row.hide();
            }
        });

        allRowsArray.forEach(function($row) {
            if (filteredRows.indexOf($row) === -1) {
                $tbody.append($row);
                $row.hide();
            }
        });

        $('#prevBtn').prop('disabled', currentPage === 1);
        $('#nextBtn').prop('disabled', currentPage === totalPages);
        renderPageNumbers(totalPages);

        if (totalRows === 0) {
            $('.hra-no-results-row').remove();
            if ($('.empty-state').length === 0) {
                $tbody.after(
                    '<tr class="hra-no-results-row"><td colspan="4" style="text-align:center;padding:48px;color:var(--text-secondary);">' +
                    'No HR members match your search.</td></tr>'
                );
            }
            $('#paginationWrap').hide();
        } else {
            $('.hra-no-results-row').remove();
            $('#paginationWrap').show();
        }
    }

    function renderPageNumbers(totalPages) {
        var $pn = $('#pageNumbers');
        $pn.empty();
        if (totalPages <= 1) return;

        var maxVisible = 5;
        windowStart = Math.max(1, Math.min(windowStart, totalPages - maxVisible + 1));
        var windowEnd = Math.min(windowStart + maxVisible - 1, totalPages);
        var hasMore   = windowEnd < totalPages;

        for (var i = windowStart; i <= windowEnd; i++) {
            var isActive = (i === currentPage);
            var isLast   = (i === windowEnd);
            var showDots = isLast && hasMore;
            var cls      = 'hra-page-num' + (isActive ? ' active' : '') + (showDots ? ' has-more' : '');
            var label    = showDots ? (i + '…') : i;
            $pn.append('<div class="' + cls + '" data-page="' + i + '">' + label + '</div>');
        }

        $pn.off('click').on('click', '.hra-page-num', function() {
            var clickedPage = parseInt($(this).data('page'));
            var isDotted    = $(this).hasClass('has-more');
            currentPage = clickedPage;
            if (isDotted) windowStart = windowStart + 1;
            applyFiltersAndPagination();
        });
    }

    $('#prevBtn').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            if (currentPage < windowStart) windowStart = Math.max(1, windowStart - 1);
            applyFiltersAndPagination();
        }
    });

    $('#nextBtn').on('click', function() {
        var totalPages = Math.max(1, Math.ceil(currentFilteredRows.length / rowsPerPage));
        if (currentPage < totalPages) {
            currentPage++;
            var windowEnd = windowStart + 5 - 1;
            if (currentPage > windowEnd) windowStart = windowStart + 1;
            applyFiltersAndPagination();
        }
    });

    $(document).on('click', '.view-hr', function() {
        var hrId = $(this).data('id');
        window.location.href = '/profile/' + hrId;
    });

    // ─────────────────────────────────────────────
    // Delete single HR — show confirm modal first
    // ─────────────────────────────────────────────
    $(document).on('click', '.delete-hr', function() {
        var hrId   = $(this).data('id');
        var hrName = $(this).data('name');

        showConfirmModal(
            'Remove HR Member',
            'Are you sure you want to remove <strong>' + escHtml(hrName) + '</strong>? You can undo this action after.',
            function() {
                executeSoftDelete(hrId, hrName);
            }
        );
    });

    function executeSoftDelete(hrId, hrName) {
        var $row = $('#hrTableBody tr[data-id="' + hrId + '"]');

        $.ajax({
            url: '/recruiter/soft-delete-hr/' + hrId,
            method: 'POST',
            success: function(response) {
                if (!response.success) {
                    showNotification(response.error || 'Delete failed', 'error');
                    return;
                }

                $row.css({ transition: 'opacity 0.3s, transform 0.3s', opacity: 0, transform: 'translateX(20px)' });
                setTimeout(function() {
                    var idx = allRowsArray.indexOf($row);
                    if (idx > -1) allRowsArray.splice(idx, 1);
                    $row.remove();
                    applyFiltersAndPagination();
                    updateHeaderStats();
                }, 300);

                pendingDeletes[hrId] = { ids: [hrId], type: 'single', name: hrName };

                showInlineUndo(
                    '<strong>' + escHtml(hrName) + '</strong> removed. Undo?',
                    function() {
                        $.ajax({
                            url: '/recruiter/undo-delete-hr/' + hrId,
                            method: 'POST',
                            success: function(res) {
                                if (res.success) {
                                    delete pendingDeletes[hrId];
                                    location.reload();
                                } else {
                                    showNotification('Undo failed: ' + (res.error || ''), 'error');
                                }
                            },
                            error: function() {
                                showNotification('Undo request failed.', 'error');
                            }
                        });
                    },
                    function() {
                        delete pendingDeletes[hrId];
                        $.ajax({ url: '/recruiter/commit-delete-hr/' + hrId, method: 'POST' });
                    }
                );
            },
            error: function(xhr) {
                showNotification('Delete failed (' + xhr.status + ')', 'error');
            }
        });
    }

    // ─────────────────────────────────────────────
    // Delete All HR — confirm modal first
    // ─────────────────────────────────────────────
    $(document).on('click', '#deleteAllHrBtn', function() {
        var count = allRowsArray.length;
        if (count === 0) {
            showNotification('No HR accounts to delete.', 'error');
            return;
        }

        showConfirmModal(
            'Remove All HR Members',
            'Are you sure you want to remove all <strong>' + count + '</strong> HR member(s)? You can undo this action after.',
            function() {
                executeDeleteAll();
            }
        );
    });

    function executeDeleteAll() {
        $.ajax({
            url: '/recruiter/soft-delete-all-hr',
            method: 'POST',
            success: function(response) {
                if (!response.success) {
                    showNotification(response.error || 'Delete all failed', 'error');
                    return;
                }

                var deletedIds = response.deleted_ids || [];
                var count      = deletedIds.length;

                if (count === 0) {
                    showNotification('No HR accounts to delete.', 'error');
                    return;
                }

                $('#hrTableBody tr').css({ transition: 'opacity 0.3s, transform 0.3s', opacity: 0, transform: 'translateX(20px)' });
                setTimeout(function() {
                    allRowsArray = [];
                    $('#hrTableBody').empty();
                    applyFiltersAndPagination();
                    updateHeaderStats();
                }, 300);

                pendingDeletes['all'] = { ids: deletedIds, type: 'all' };

                showInlineUndo(
                    'All <strong>' + count + '</strong> HR member(s) removed. Undo?',
                    function() {
                        $.ajax({
                            url: '/recruiter/undo-delete-all-hr',
                            method: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({ ids: deletedIds }),
                            success: function(res) {
                                if (res.success) {
                                    delete pendingDeletes['all'];
                                    location.reload();
                                } else {
                                    showNotification('Undo failed: ' + (res.error || ''), 'error');
                                }
                            },
                            error: function() {
                                showNotification('Undo request failed.', 'error');
                            }
                        });
                    },
                    function() {
                        delete pendingDeletes['all'];
                        $.ajax({
                            url: '/recruiter/commit-delete-all-hr',
                            method: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({ ids: deletedIds })
                        });
                    }
                );
            },
            error: function(xhr) {
                showNotification('Delete all failed (' + xhr.status + ')', 'error');
            }
        });
    }

    // Commit all pending deletes when navigating away
    window.addEventListener('beforeunload', function() {
        Object.keys(pendingDeletes).forEach(function(key) {
            var p = pendingDeletes[key];
            if (p.type === 'single') {
                navigator.sendBeacon('/recruiter/commit-delete-hr/' + p.ids[0]);
            } else {
                var blob = new Blob([JSON.stringify({ ids: p.ids })], { type: 'application/json' });
                navigator.sendBeacon('/recruiter/commit-delete-all-hr', blob);
            }
        });
    });

    $(document).on('click', '.hra-modal-close, #confirmCancelBtn', function() {
        $('#confirmModal').removeClass('show');
    });

    $(window).on('click', function(e) {
        if ($(e.target).attr('id') === 'confirmModal') {
            $('#confirmModal').removeClass('show');
        }
    });

    applyFiltersAndPagination();
});

// ================================================================
//  INLINE UNDO BANNER (below search/filter, no timer)
// ================================================================

var currentUndoCommit = null;

function showInlineUndo(html, onUndo, onCommit) {
    currentUndoCommit = onCommit;

    var $banner = $('#inlineUndoBanner');
    if ($banner.length === 0) {
        $banner = $(
            '<div id="inlineUndoBanner" style="' +
                'display:flex; align-items:center; gap:12px;' +
                'padding:12px 16px; margin-bottom:16px;' +
                'background:rgba(77,119,78,0.08);' +
                'border:1px solid var(--border-color);' +
                'border-left:4px solid var(--brand-green-dark);' +
                'border-radius:8px; font-size:13px; color:var(--text-primary);' +
            '">' +
                '<span id="inlineUndoMsg" style="flex:1;"></span>' +
                '<button id="inlineUndoBtn" style="' +
                    'display:flex; align-items:center; gap:6px;' +
                    'padding:7px 16px;' +
                    'background:var(--brand-green-dark); color:white;' +
                    'border:none; border-radius:6px;' +
                    'font-size:13px; font-weight:600; cursor:pointer;' +
                '">Undo</button>' +
                '<button id="inlineUndoDismiss" style="' +
                    'background:none; border:none; color:var(--text-muted);' +
                    'cursor:pointer; font-size:18px; line-height:1; padding:2px 6px;' +
                '">&#x2715;</button>' +
            '</div>'
        );

        var $controls = $('.section-controls').first();
        $controls.closest('.section-header').after($banner);
    }

    $('#inlineUndoMsg').html(html);
    $banner.show();

    $('#inlineUndoBtn').off('click').on('click', function() {
        currentUndoCommit = null;
        $banner.hide();
        onUndo();
    });

    $('#inlineUndoDismiss').off('click').on('click', function() {
        currentUndoCommit = null;
        $banner.hide();
        onCommit();
    });
}

function hideInlineUndo() {
    $('#inlineUndoBanner').hide();
}

// ================================================================
//  CONFIRM MODAL
// ================================================================

function showConfirmModal(title, message, onConfirm) {
    $('#confirmTitle').text(title);
    $('#confirmMessage').html(message);
    $('#confirmModal').addClass('show');

    $('#confirmActionBtn').off('click').on('click', function() {
        $('#confirmModal').removeClass('show');
        onConfirm();
    });
}

function closeConfirmModal() {
    $('#confirmModal').removeClass('show');
}

// ================================================================
//  Helpers
// ================================================================

function copyPassword() {
    var passwordInput = document.getElementById('tempPassword');
    if (!passwordInput) return;

    navigator.clipboard.writeText(passwordInput.value).then(function() {
        var btn = document.querySelector('.btn-copy-modern');
        if (!btn) return;
        var originalHtml = btn.innerHTML;
        btn.innerHTML = '&#x2713; Copied!';
        btn.classList.add('copied');
        setTimeout(function() {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2000);
    }).catch(function() {
        passwordInput.select();
        document.execCommand('copy');
        showNotification('Password copied!', 'success');
    });
}

function closePasswordBox() {
    var box = document.getElementById('tempPasswordBox');
    if (box) box.parentNode.removeChild(box);
}

function showNotification(message, type) {
    var notification = $(
        '<div class="hra-notification hra-notification-' + type + '">' +
        '<span>' + escHtml(message) + '</span></div>'
    );
    $('body').append(notification);
    setTimeout(function() { notification.addClass('show'); }, 10);
    setTimeout(function() {
        notification.removeClass('show');
        setTimeout(function() { notification.remove(); }, 300);
    }, 3000);
}

function updateHeaderStats() {
    var total   = allRowsArray.length;
    var active  = 0;
    var pending = 0;
    allRowsArray.forEach(function($row) {
        if ($row.data('status') === 'active')  active++;
        if ($row.data('status') === 'pending') pending++;
    });

    var $vals = $('.stat-value');
    if ($vals.length >= 3) {
        $vals.eq(0).text(total   + ' Members');
        $vals.eq(1).text(active  + ' Active');
        $vals.eq(2).text(pending + ' Pending');
    }

    $('.status-filter-btn[data-filter="all"]').text('All ('     + total   + ')');
    $('.status-filter-btn[data-filter="active"]').text('Active (' + active  + ')');
    $('.status-filter-btn[data-filter="pending"]').text('Pending (' + pending + ')');
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}