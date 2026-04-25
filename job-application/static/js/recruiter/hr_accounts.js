// ========================================
// HR ACCOUNTS PAGE WITH PAGINATION + UNDO DELETE
// ========================================

var currentPage = 1;
var rowsPerPage = 6;
var allRowsArray = [];
var currentFilteredRows = [];

// Tracks where the current visible window starts
var windowStart = 1;

// ── Undo timers: keyed by hr_id (or 'all') ──
// Each entry: { timerId, commitTimerId, seconds }
var undoTimers = {};

// Duration (ms) the undo toast stays alive before committing
var UNDO_DURATION = 8000;

// Add this at the very top of hr_accounts.js, before $(document).ready
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

    // ─────────────────────────────────────────────
    // Filter dropdown
    // ─────────────────────────────────────────────
    $('#filterBtn').on('click', function(e) {
        e.stopPropagation();
        $('#filterMenu').toggleClass('show');
    });

    $(document).on('click', function(e) {
        if (!$(e.target).closest('.hra-filter-dropdown').length) {
            $('#filterMenu').removeClass('show');
        }
    });

    var currentSort = null;
    var currentStatusFilter = null;

    $('.hra-filter-option').on('click', function() {
        var sortType = $(this).data('sort');
        var filterType = $(this).data('filter');

        if (sortType === 'name_asc') {
            currentSort = 'name_asc';
            currentStatusFilter = null;
            $('#filterBtn').html('<i class="fas fa-sort-alpha-down"></i>');
        } else if (sortType === 'name_desc') {
            currentSort = 'name_desc';
            currentStatusFilter = null;
            $('#filterBtn').html('<i class="fas fa-sort-alpha-up"></i>');
        } else if (filterType === 'active') {
            currentStatusFilter = 'active';
            currentSort = null;
            $('#filterBtn').html('<i class="fas fa-check-circle"></i>');
        } else if (filterType === 'pending') {
            currentStatusFilter = 'pending';
            currentSort = null;
            $('#filterBtn').html('<i class="fas fa-clock"></i>');
        } else if (filterType === 'all') {
            currentStatusFilter = null;
            currentSort = null;
            $('#filterBtn').html('<i class="fas fa-sort"></i>');
        }

        $('#filterMenu').removeClass('show');
        currentPage = 1;
        windowStart = 1;
        applyFiltersAndPagination();
    });

    $('.hra-filter-tab').on('click', function() {
        $('.hra-filter-tab').removeClass('active');
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

    // ─────────────────────────────────────────────
    // Pagination helpers
    // ─────────────────────────────────────────────
    function applyFiltersAndPagination() {
        var searchTerm = $('#hrSearch').val().toLowerCase();
        var activeTabFilter = $('.hra-filter-tab.active').data('filter');

        var filteredRows = [];

        allRowsArray.forEach(function($row) {
            var name   = ($row.data('name')  || '').toString();
            var email  = ($row.data('email') || '').toString();
            var status = $row.data('status');

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
                var nameA = ($(a).data('fullname') || '').toString().toLowerCase();
                var nameB = ($(b).data('fullname') || '').toString().toLowerCase();
                return nameA.localeCompare(nameB);
            });
        } else if (currentSort === 'name_desc') {
            filteredRows.sort(function(a, b) {
                var nameA = ($(a).data('fullname') || '').toString().toLowerCase();
                var nameB = ($(b).data('fullname') || '').toString().toLowerCase();
                return nameB.localeCompare(nameA);
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

        $('#paginationInfo').hide();
        $('#prevBtn').prop('disabled', currentPage === 1);
        $('#nextBtn').prop('disabled', currentPage === totalPages);
        renderPageNumbers(totalPages);

        if (totalRows === 0) {
            $('.hra-empty-results').show();
            $('#paginationWrap').hide();
        } else {
            $('.hra-empty-results').hide();
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

            var cls   = 'hra-page-num' + (isActive ? ' active' : '') + (showDots ? ' has-more' : '');
            var label = showDots ? (i + '…') : i;

            $pn.append('<div class="' + cls + '" data-page="' + i + '">' + label + '</div>');
        }

        $pn.off('click').on('click', '.hra-page-num', function() {
            var clickedPage = parseInt($(this).data('page'));
            var isDotted    = $(this).hasClass('has-more');

            currentPage = clickedPage;

            if (isDotted) {
                windowStart = windowStart + 1;
            }

            applyFiltersAndPagination();
        });
    }

    $('#prevBtn').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            if (currentPage < windowStart) {
                windowStart = Math.max(1, windowStart - 1);
            }
            applyFiltersAndPagination();
        }
    });

    $('#nextBtn').on('click', function() {
        var totalPages = Math.max(1, Math.ceil(currentFilteredRows.length / rowsPerPage));
        if (currentPage < totalPages) {
            currentPage++;
            var windowEnd = windowStart + 5 - 1;
            if (currentPage > windowEnd) {
                windowStart = windowStart + 1;
            }
            applyFiltersAndPagination();
        }
    });

    // ─────────────────────────────────────────────
    // View HR → redirect to profile page
    // ─────────────────────────────────────────────
    $(document).on('click', '.view-hr', function() {
        var hrId = $(this).data('id');
        window.location.href = '/profile/' + hrId;
    });

    // ─────────────────────────────────────────────
    // Delete single HR — soft-delete with undo toast
    // ─────────────────────────────────────────────
    $(document).on('click', '.delete-hr', function() {
        var hrId   = $(this).data('id');
        var hrName = $(this).data('name');
        var $row   = $(this).closest('tr');

        // Cancel any existing undo for this same HR (shouldn't happen but safety)
        cancelUndoTimer(hrId);

        $.ajax({
            url: '/recruiter/soft-delete-hr/' + hrId,
            method: 'POST',
            success: function(response) {
                if (!response.success) {
                    showNotification(response.error || 'Delete failed', 'error');
                    return;
                }

                // Visually remove the row immediately
                $row.addClass('hra-row-fading');
                setTimeout(function() {
                    // Remove from allRowsArray so pagination ignores it
                    var idx = allRowsArray.indexOf($row);
                    if (idx > -1) allRowsArray.splice(idx, 1);
                    $row.remove();
                    applyFiltersAndPagination();
                    updateHeaderStats();
                }, 300);

                // Show undo toast, then commit after UNDO_DURATION
                showUndoToast(
                    hrId,
                    '<i class="fas fa-user-slash"></i> <strong>' + hrName + '</strong> deleted.',
                    // On undo:
                    function() {
                        $.ajax({
                            url: '/recruiter/undo-delete-hr/' + hrId,
                            method: 'POST',
                            success: function(res) {
                                if (res.success) {
                                    // Reload page to bring the row back cleanly
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
                    // On commit (undo window expired):
                    function() {
                        $.ajax({
                            url: '/recruiter/commit-delete-hr/' + hrId,
                            method: 'POST',
                            error: function() {
                                // Silent — user didn't undo so just proceed
                            }
                        });
                    }
                );
            },
            error: function(xhr) {
                showNotification('Delete failed: ' + xhr.status, 'error');
            }
        });
    });

    // ─────────────────────────────────────────────
    // Delete All HR — soft-delete with undo toast
    // ─────────────────────────────────────────────
    $(document).on('click', '#deleteAllHrBtn', function() {
        // Dismiss any existing undo toasts first so the user
        // doesn't get confused with stale per-account toasts
        dismissAllUndoToasts();

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

                // Visually clear the table
                $('#hrTableBody tr').addClass('hra-row-fading');
                setTimeout(function() {
                    allRowsArray = [];
                    $('#hrTableBody').empty();
                    applyFiltersAndPagination();
                    updateHeaderStats();
                }, 300);

                showUndoToast(
                    'all',
                    '<i class="fas fa-users-slash"></i> All <strong>' + count + '</strong> HR account(s) deleted.',
                    // On undo:
                    function() {
                        $.ajax({
                            url: '/recruiter/undo-delete-all-hr',
                            method: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({ ids: deletedIds }),
                            success: function(res) {
                                if (res.success) {
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
                    // On commit:
                    function() {
                        $.ajax({
                            url: '/recruiter/commit-delete-all-hr',
                            method: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify({ ids: deletedIds }),
                            error: function() {
                                // Silent
                            }
                        });
                    }
                );
            },
            error: function(xhr) {
                showNotification('Delete all failed: ' + xhr.status, 'error');
            }
        });
    });

    // ─────────────────────────────────────────────
    // Close modals via X button
    // ─────────────────────────────────────────────
    $('.hra-modal-close').on('click', function() {
        $(this).closest('.hra-modal').removeClass('show');
    });

    $(window).on('click', function(e) {
        if ($(e.target).hasClass('hra-modal')) {
            $(e.target).removeClass('show');
        }
    });

    applyFiltersAndPagination();
});

// ================================================================
//  UNDO TOAST SYSTEM
// ================================================================

/**
 * Show an undo toast with a live countdown bar.
 * @param {string|number} key      - Unique key (hr_id or 'all')
 * @param {string}        html     - Inner HTML for the message
 * @param {Function}      onUndo   - Called if user clicks Undo
 * @param {Function}      onCommit - Called when the window expires
 */
function showUndoToast(key, html, onUndo, onCommit) {
    // Remove any existing toast for this key
    cancelUndoTimer(key);
    $('#undoToast-' + key).remove();

    var $toast = $(
        '<div class="hra-undo-toast" id="undoToast-' + key + '">' +
            '<div class="hra-undo-message">' + html + '</div>' +
            '<button class="hra-undo-btn" id="undoBtn-' + key + '">' +
                '<i class="fas fa-rotate-left"></i> Undo' +
            '</button>' +
            '<button class="hra-undo-dismiss" id="undoDismiss-' + key + '" title="Dismiss">' +
                '<i class="fas fa-times"></i>' +
            '</button>' +
            '<div class="hra-undo-bar" id="undoBar-' + key + '"></div>' +
        '</div>'
    );

    $('body').append($toast);
    // Trigger CSS animation on the next frame
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            $toast.addClass('show');
            // Start the shrinking progress bar
            $('#undoBar-' + key).css('transition-duration', UNDO_DURATION + 'ms');
            $('#undoBar-' + key).addClass('shrink');
        });
    });

    // ── Undo button ──
    $('#undoBtn-' + key).on('click', function() {
        cancelUndoTimer(key);
        $toast.removeClass('show');
        setTimeout(function() { $toast.remove(); }, 350);
        onUndo();
    });

    // ── Dismiss (×) button ── fires commit immediately
    $('#undoDismiss-' + key).on('click', function() {
        cancelUndoTimer(key);
        $toast.removeClass('show');
        setTimeout(function() { $toast.remove(); }, 350);
        onCommit();
    });

    // ── Auto-commit after UNDO_DURATION ──
    var commitTimerId = setTimeout(function() {
        $toast.removeClass('show');
        setTimeout(function() { $toast.remove(); }, 350);
        onCommit();
        delete undoTimers[key];
    }, UNDO_DURATION);

    undoTimers[key] = { commitTimerId: commitTimerId };
}

/** Cancel the pending commit timer for a key (used on undo click). */
function cancelUndoTimer(key) {
    if (undoTimers[key]) {
        clearTimeout(undoTimers[key].commitTimerId);
        delete undoTimers[key];
    }
}

/** Remove every visible undo toast and cancel their timers. */
function dismissAllUndoToasts() {
    Object.keys(undoTimers).forEach(function(key) {
        cancelUndoTimer(key);
        var $t = $('#undoToast-' + key);
        $t.removeClass('show');
        setTimeout(function() { $t.remove(); }, 350);
    });
}

// ================================================================
//  Helpers shared with inline HTML
// ================================================================

function copyPassword() {
    var passwordInput = document.getElementById('tempPassword');
    if (!passwordInput) return;
    navigator.clipboard.writeText(passwordInput.value).then(function() {
        var btn = document.querySelector('.hra-copy-btn');
        var originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('copied');
        setTimeout(function() {
            btn.innerHTML = originalHtml;
            btn.classList.remove('copied');
        }, 2000);
    });
}

function closePasswordBox() {
    var box = document.getElementById('tempPasswordBox');
    if (box) {
        box.parentNode.removeChild(box);
    }
}

function closeConfirmModal() {
    $('#confirmModal').removeClass('show');
}

function showConfirmModal(title, message, onConfirm) {
    $('#confirmTitle').text(title);
    $('#confirmMessage').html(message);
    $('#confirmModal').addClass('show');
    $('#confirmActionBtn').off('click').on('click', function() {
        $('#confirmModal').removeClass('show');
        onConfirm();
    });
}

function showNotification(message, type) {
    var notification = $(
        '<div class="hra-notification hra-notification-' + type + '">' +
        '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle') + '"></i>' +
        '<span>' + message + '</span></div>'
    );
    $('body').append(notification);
    setTimeout(function() { notification.addClass('show'); }, 10);
    setTimeout(function() {
        notification.removeClass('show');
        setTimeout(function() { notification.remove(); }, 300);
    }, 3000);
}

/** Re-compute the three stat cards in the header without a page reload. */
function updateHeaderStats() {
    var total   = allRowsArray.length;
    var active  = 0;
    var pending = 0;
    allRowsArray.forEach(function($row) {
        if ($row.data('status') === 'active')  active++;
        if ($row.data('status') === 'pending') pending++;
    });

    // Update stat cards (values are the first .hra-stat-value inside each .hra-stat-card)
    var $cards = $('.hra-stat-value');
    if ($cards.length >= 3) {
        $cards.eq(0).text(total);
        $cards.eq(1).text(active);
        $cards.eq(2).text(pending);
    }

    // Update tab labels
    $('.hra-filter-tab[data-filter="all"]').text('All (' + total + ')');
    $('.hra-filter-tab[data-filter="active"]').text('Active (' + active + ')');
    $('.hra-filter-tab[data-filter="pending"]').text('Pending (' + pending + ')');
}