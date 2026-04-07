// ========================================
// HR ACCOUNTS PAGE WITH PAGINATION
// ========================================

var currentPage = 1;
var rowsPerPage = 6;
var allRowsArray = [];
var currentFilteredRows = [];

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
        applyFiltersAndPagination();
    });

    $('.hra-filter-tab').on('click', function() {
        $('.hra-filter-tab').removeClass('active');
        $(this).addClass('active');
        currentPage = 1;
        applyFiltersAndPagination();
    });

    $('#hrSearch').on('keyup', function() {
        currentPage = 1;
        applyFiltersAndPagination();
    });

    function applyFiltersAndPagination() {
        var searchTerm = $('#hrSearch').val().toLowerCase();
        var activeTabFilter = $('.hra-filter-tab.active').data('filter');

        // FIX: build fresh copy from allRowsArray so sort works every time
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

        // FIX: sort on the data-fullname attribute directly
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

        var start    = (currentPage - 1) * rowsPerPage;
        var end      = start + rowsPerPage;
        var pageRows = filteredRows.slice(start, end);

        // FIX: detach all rows first, then re-append in sorted order, then show/hide
        var $tbody = $('#hrTableBody');
        $tbody.children('tr').detach();
        filteredRows.forEach(function($row) {
            $tbody.append($row);
        });
        // hide all non-page rows
        filteredRows.forEach(function($row, idx) {
            if (idx >= start && idx < end) {
                $row.show();
            } else {
                $row.hide();
            }
        });
        // hide rows not in filteredRows (filtered-out rows)
        allRowsArray.forEach(function($row) {
            if (filteredRows.indexOf($row) === -1) {
                $tbody.append($row);
                $row.hide();
            }
        });

        // Pagination info
        var startNum = totalRows === 0 ? 0 : start + 1;
        var endNum   = Math.min(end, totalRows);
        $('#paginationInfo').text('Showing ' + startNum + ' to ' + endNum + ' of ' + totalRows + ' entries');

        // Prev / Next buttons
        $('#prevBtn').prop('disabled', currentPage === 1);
        $('#nextBtn').prop('disabled', currentPage === totalPages);

        // Page numbers — show max 4, then "..." dropdown for the rest
        renderPageNumbers(totalPages);

        // Empty state
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

        var maxVisible = 4;
        // Calculate the start of the current "window" of 4
        // Window advances only when currentPage moves past it
        var windowStart = Math.floor((currentPage - 1) / maxVisible) * maxVisible + 1;
        var windowEnd   = Math.min(windowStart + maxVisible - 1, totalPages);

        for (var i = windowStart; i <= windowEnd; i++) {
            var activeClass = (i === currentPage) ? 'active' : '';
            $pn.append('<div class="hra-page-num ' + activeClass + '" data-page="' + i + '">' + i + '</div>');
        }

        if (windowEnd < totalPages) {
            var $dots = $('<div class="hra-page-dots" title="More pages">&#8230;</div>');
            var $allPagesMenu = $('<div class="hra-all-pages-menu"></div>');

            for (var j = 1; j <= totalPages; j++) {
                var activeClass2 = (j === currentPage) ? 'active' : '';
                $allPagesMenu.append('<div class="hra-all-page-item ' + activeClass2 + '" data-page="' + j + '">' + j + '</div>');
            }

            var $dotsWrap = $('<div class="hra-dots-wrap"></div>').append($dots).append($allPagesMenu);
            $pn.append($dotsWrap);

            $dots.on('click', function(e) {
                e.stopPropagation();
                $allPagesMenu.toggleClass('show');
            });

            $(document).on('click.dotsMenu', function() {
                $allPagesMenu.removeClass('show');
            });

            $allPagesMenu.on('click', '.hra-all-page-item', function() {
                currentPage = parseInt($(this).data('page'));
                $allPagesMenu.removeClass('show');
                applyFiltersAndPagination();
            });
        }

        // Page number click
        $pn.on('click', '.hra-page-num', function() {
            currentPage = parseInt($(this).data('page'));
            applyFiltersAndPagination();
        });
    }

    // FIX: Prev/Next buttons — use currentFilteredRows
    $('#prevBtn').on('click', function() {
        if (currentPage > 1) {
            currentPage--;
            applyFiltersAndPagination();
        }
    });

    $('#nextBtn').on('click', function() {
        var totalPages = Math.max(1, Math.ceil(currentFilteredRows.length / rowsPerPage));
        if (currentPage < totalPages) {
            currentPage++;
            applyFiltersAndPagination();
        }
    });

    // View HR Details
    $(document).on('click', '.view-hr', function() {
        var hrId     = $(this).data('id');
        var hrName   = $(this).closest('tr').find('.hra-member-name').text();
        var hrEmail  = $(this).closest('tr').find('.hra-contact-info div').text().trim();
        var hrStatus = $(this).closest('tr').find('.hra-badge').text().trim();

        var detailsHtml = `
            <div class="hr-detail-section">
                <h4><i class="fas fa-user"></i> Basic Information</h4>
                <div class="hr-detail-row">
                    <div class="hr-detail-label">Full Name:</div>
                    <div class="hr-detail-value"><strong>${hrName}</strong></div>
                </div>
                <div class="hr-detail-row">
                    <div class="hr-detail-label">Email:</div>
                    <div class="hr-detail-value">${hrEmail}</div>
                </div>
                <div class="hr-detail-row">
                    <div class="hr-detail-label">Status:</div>
                    <div class="hr-detail-value">${hrStatus}</div>
                </div>
            </div>
            <div class="hr-detail-section">
                <h4><i class="fas fa-chart-line"></i> Activity Timeline</h4>
                <div id="hrActivityTimeline">
                    <p style="color:#9ca3af;text-align:center;padding:20px;">Loading activity data...</p>
                </div>
            </div>
        `;

        $('#hrDetailsContent').html(detailsHtml);
        $('#hrDetailsModal').addClass('show');

        $.ajax({
            url: '/recruiter/hr-activity/' + hrId,
            method: 'GET',
            success: function(response) {
                if (response.activities && response.activities.length > 0) {
                    var html = '<div class="hra-timeline">';
                    response.activities.forEach(function(a) {
                        html += `<div class="hra-timeline-item">
                            <div class="hra-timeline-time">${a.time}</div>
                            <div class="hra-timeline-content"><i class="fas ${a.icon}"></i><span>${a.message}</span></div>
                        </div>`;
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

    // FIX: Delete — use delegated event so it works after pagination re-renders
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
                    data: { hr_id: hrId },
                    success: function(response) {
                        if (response.success) {
                            showNotification('HR member deleted successfully!', 'success');
                            setTimeout(function() { location.reload(); }, 1500);
                        } else {
                            showNotification(response.error || 'Delete failed', 'error');
                        }
                    },
                    error: function() {
                        showNotification('An error occurred', 'error');
                    }
                });
            }
        );
    });

    // Modal close
    $('.hra-modal-close').on('click', function() {
        $(this).closest('.hra-modal').removeClass('show');
    });

    $(window).on('click', function(e) {
        if ($(e.target).hasClass('hra-modal')) {
            $(e.target).removeClass('show');
        }
    });

    // Initialize
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
    // FIX: unbind previous handler before binding new one
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