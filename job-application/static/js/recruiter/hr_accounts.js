// ========================================
// HR ACCOUNTS PAGE WITH PAGINATION
// ========================================

var currentPage = 1;
var rowsPerPage = 6;
var allRowsArray = [];
var currentFilteredRows = [];

// Tracks where the current visible window starts
var windowStart = 1;

$(document).ready(function() {

    function storeAllRows() {
        allRowsArray = [];
        $('#hrTableBody tr').each(function() {
            allRowsArray.push($(this));
        });
    }
    storeAllRows();

    // Filter dropdown
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

        // Clamp windowStart so the window never goes out of bounds
        windowStart = Math.max(1, Math.min(windowStart, totalPages - maxVisible + 1));

        var windowEnd = Math.min(windowStart + maxVisible - 1, totalPages);
        var hasMore   = windowEnd < totalPages; // pages still exist beyond this window

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

            // Shift the window forward by 1 ONLY when the "…" page is clicked
            if (isDotted) {
                windowStart = windowStart + 1;
            }

            applyFiltersAndPagination();
        });
    }

    $('#prevBtn').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            // If previous goes behind the window, slide the window back
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
            // If next goes beyond the window, slide the window forward
            if (currentPage > windowEnd) {
                windowStart = windowStart + 1;
            }
            applyFiltersAndPagination();
        }
    });

    $(document).on('click', '.view-hr', function() {
        var hrId     = $(this).data('id');
        var hrName   = $(this).closest('tr').find('.hra-member-name').text();
        var hrEmail  = $(this).closest('tr').find('.hra-contact-info div').text().trim();
        var hrStatus = $(this).closest('tr').find('.hra-badge').text().trim();

        var detailsHtml =
            '<div class="hr-detail-section">' +
                '<h4><i class="fas fa-user"></i> Basic Information</h4>' +
                '<div class="hr-detail-row"><div class="hr-detail-label">Full Name:</div><div class="hr-detail-value"><strong>' + hrName + '</strong></div></div>' +
                '<div class="hr-detail-row"><div class="hr-detail-label">Email:</div><div class="hr-detail-value">' + hrEmail + '</div></div>' +
                '<div class="hr-detail-row"><div class="hr-detail-label">Status:</div><div class="hr-detail-value">' + hrStatus + '</div></div>' +
            '</div>' +
            '<div class="hr-detail-section">' +
                '<h4><i class="fas fa-chart-line"></i> Activity Timeline</h4>' +
                '<div id="hrActivityTimeline"><p style="color:#9ca3af;text-align:center;padding:20px;">Loading activity data...</p></div>' +
            '</div>';

        $('#hrDetailsContent').html(detailsHtml);
        $('#hrDetailsModal').addClass('show');

        $.ajax({
            url: '/recruiter/hr-activity/' + hrId,
            method: 'GET',
            success: function(response) {
                if (response.activities && response.activities.length > 0) {
                    var html = '<div class="hra-timeline">';
                    response.activities.forEach(function(a) {
                        html += '<div class="hra-timeline-item"><div class="hra-timeline-time">' + a.time + '</div><div class="hra-timeline-content"><i class="fas ' + a.icon + '"></i><span>' + a.message + '</span></div></div>';
                    });
                    html += '</div>';
                    $('#hrActivityTimeline').html(html);
                } else {
                    $('#hrActivityTimeline').html('<p style="color:#9ca3af;text-align:center;padding:20px;">No recent activity</p>');
                }
            },
            error: function() {
                $('#hrActivityTimeline').html('<p style="color:#9ca3af;text-align:center;padding:20px;">Unable to load activity data</p>');
            }
        });
    });

    $(document).on('click', '.delete-hr', function() {
    var hrId   = $(this).data('id');
    var hrName = $(this).data('name');

    showConfirmModal(
        'Delete HR Account',
        'Are you sure you want to delete <strong>' + hrName + '</strong>? This action cannot be undone.',
        function() {
            $.ajax({
                url: '/recruiter/delete-hr',
                method: 'POST',
                data: { hr_id: hrId },  // SIMPLIFIED - no CSRF
                success: function(response) {
                    console.log('Delete response:', response);  // DEBUG
                    if (response.success) {
                        showNotification('HR member deleted successfully!', 'success');
                        setTimeout(function() { location.reload(); }, 1500);
                    } else {
                        showNotification(response.error || 'Delete failed', 'error');
                    }
                },
                error: function(xhr) {
                    console.log('Delete error:', xhr.responseText);  // DEBUG
                    showNotification('Delete failed: ' + xhr.status, 'error');
                }
            });
        }
    );
});

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

// ── Helpers ──────────────────────────────────────────────

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
    if (box) box.style.display = 'none';
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