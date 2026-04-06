// Professional Job Gallery Functionality
// Compatible with job_details_professional.html

let currentImageIndex = 0;

/**
 * Update gallery display with current image
 */
function updateImage() {
    const imageElement = document.getElementById('jobImage');
    const counterElement = document.getElementById('imageCounter');
    const thumbnails = document.querySelectorAll('.thumbnail-btn');
    const galleryBackground = document.querySelector('.gallery-background');
    const galleryViewport = document.querySelector('.gallery-viewport');

    if (imageElement && jobImages.length > 0) {
        const currentImage = jobImages[currentImageIndex];

        // Update main gallery image
        imageElement.src = currentImage;

        // Update blurred background
        if (galleryBackground) {
            galleryBackground.style.backgroundImage = `url('${currentImage}')`;
        }

        // Fallback: set CSS variable for older browsers
        if (galleryViewport) {
            galleryViewport.style.setProperty('--bg-image', `url('${currentImage}')`);
        }

        // Update image counter
        if (counterElement) {
            counterElement.textContent = `${currentImageIndex + 1} / ${jobImages.length}`;
        }

        // Update active thumbnail
        thumbnails.forEach((thumb, index) => {
            if (index === currentImageIndex) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });

        // Smooth fade transition
        imageElement.style.opacity = '0';
        setTimeout(() => {
            imageElement.style.opacity = '1';
        }, 50);
    }
}

/**
 * Navigate to next image
 */
function nextImage() {
    if (jobImages.length > 0) {
        currentImageIndex = (currentImageIndex + 1) % jobImages.length;
        updateImage();
    }
}

/**
 * Navigate to previous image
 */
function prevImage() {
    if (jobImages.length > 0) {
        currentImageIndex = (currentImageIndex - 1 + jobImages.length) % jobImages.length;
        updateImage();
    }
}

/**
 * Go to specific image by index
 */
function goToImage(index) {
    if (jobImages.length > 0 && index >= 0 && index < jobImages.length) {
        currentImageIndex = index;
        updateImage();
    }
}

/**
 * Keyboard navigation support
 */
document.addEventListener('keydown', function(event) {
    if (jobImages.length > 0) {
        // Arrow key navigation
        if (event.key === 'ArrowRight') {
            nextImage();
            event.preventDefault();
        } else if (event.key === 'ArrowLeft') {
            prevImage();
            event.preventDefault();
        }
    }
});

/**
 * Touch/swipe support for mobile devices
 */
let touchStartX = 0;
let touchEndX = 0;
const swipeThreshold = 50; // Minimum distance for swipe

document.addEventListener('DOMContentLoaded', function() {
    const galleryViewport = document.querySelector('.gallery-viewport');
    const imageElement = document.getElementById('jobImage');

    // Add smooth transition to image
    if (imageElement) {
        imageElement.style.transition = 'opacity 0.3s ease';
    }

    // Touch event listeners for swipe gestures
    if (galleryViewport && jobImages.length > 1) {
        galleryViewport.addEventListener('touchstart', function(event) {
            touchStartX = event.changedTouches[0].screenX;
        }, { passive: true });

        galleryViewport.addEventListener('touchmove', function(event) {
            // Optional: Add visual feedback during swipe
        }, { passive: true });

        galleryViewport.addEventListener('touchend', function(event) {
            touchEndX = event.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }

    // Thumbnail click scroll into view
    const thumbnails = document.querySelectorAll('.thumbnail-btn');
    thumbnails.forEach((thumb, index) => {
        thumb.addEventListener('click', function() {
            // Scroll active thumbnail into view
            setTimeout(() => {
                thumb.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                });
            }, 100);
        });
    });

    // Initialize gallery
    updateImage();
});

/**
 * Handle swipe gestures
 */
function handleSwipe() {
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swiped left - next image
            nextImage();
        } else {
            // Swiped right - previous image
            prevImage();
        }
    }
}

/**
 * Optional: Preload adjacent images for smoother transitions
 */
function preloadAdjacentImages() {
    if (jobImages.length <= 1) return;

    const nextIndex = (currentImageIndex + 1) % jobImages.length;
    const prevIndex = (currentImageIndex - 1 + jobImages.length) % jobImages.length;

    const preloadNext = new Image();
    const preloadPrev = new Image();

    preloadNext.src = jobImages[nextIndex];
    preloadPrev.src = jobImages[prevIndex];
}

// Call preload after each navigation
document.addEventListener('DOMContentLoaded', function() {
    if (jobImages.length > 1) {
        preloadAdjacentImages();

        // Preload on navigation
        const originalNextImage = nextImage;
        const originalPrevImage = prevImage;
        const originalGoToImage = goToImage;

        window.nextImage = function() {
            originalNextImage();
            preloadAdjacentImages();
        };

        window.prevImage = function() {
            originalPrevImage();
            preloadAdjacentImages();
        };

        window.goToImage = function(index) {
            originalGoToImage(index);
            preloadAdjacentImages();
        };
    }
});

// ================================
// DESCRIPTION TOGGLE
// ================================
function toggleDescription() {
    const wrapper = document.getElementById('descriptionWrapper');
    const btn = document.getElementById('toggleDescBtn');
    const text = document.getElementById('toggleDescText');
    const icon = document.getElementById('toggleDescIcon');

    const isCollapsed = wrapper.classList.contains('collapsed');

    if (isCollapsed) {
        wrapper.classList.remove('collapsed');
        text.textContent = 'Show Less';
        btn.classList.add('expanded');
    } else {
        wrapper.classList.add('collapsed');
        text.textContent = 'Show More';
        btn.classList.remove('expanded');
        // Scroll back up to description heading smoothly
        wrapper.closest('.content-section').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Only show the toggle button if description is actually long enough
document.addEventListener('DOMContentLoaded', function () {
    const wrapper = document.getElementById('descriptionWrapper');
    const btn = document.getElementById('toggleDescBtn');

    if (!wrapper || !btn) return;

    // Measure full height before collapsing
    const fullHeight = wrapper.scrollHeight;

    if (fullHeight > 160) {
        // Long enough to need toggle — start collapsed
        wrapper.classList.add('collapsed');
        btn.style.display = 'flex';
    } else {
        // Short description — hide toggle and fade entirely
        btn.style.display = 'none';
        const fade = document.getElementById('descriptionFade');
        if (fade) fade.style.display = 'none';
    }
});