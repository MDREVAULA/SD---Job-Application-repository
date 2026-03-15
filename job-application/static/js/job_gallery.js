// Job Image Gallery Functionality

let currentImageIndex = 0;

// Update image display
function updateImage() {
    const imageElement = document.getElementById('jobImage');
    const counterElement = document.getElementById('imageCounter');
    const thumbnails = document.querySelectorAll('.thumbnail');
    const galleryMain = document.querySelector('.gallery-main');
    
    if (imageElement && jobImages.length > 0) {
        imageElement.src = jobImages[currentImageIndex];
        
        // Set blurred background
        if (galleryMain) {
            galleryMain.style.setProperty('--bg-image', `url('${jobImages[currentImageIndex]}')`);
        }
        
        // Update counter
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
    }
}

// Go to next image
function nextImage() {
    if (jobImages.length > 0) {
        currentImageIndex = (currentImageIndex + 1) % jobImages.length;
        updateImage();
    }
}

// Go to previous image
function prevImage() {
    if (jobImages.length > 0) {
        currentImageIndex = (currentImageIndex - 1 + jobImages.length) % jobImages.length;
        updateImage();
    }
}

// Go to specific image
function goToImage(index) {
    if (jobImages.length > 0 && index >= 0 && index < jobImages.length) {
        currentImageIndex = index;
        updateImage();
    }
}

// Keyboard navigation
document.addEventListener('keydown', function(event) {
    if (jobImages.length > 0) {
        if (event.key === 'ArrowRight') {
            nextImage();
        } else if (event.key === 'ArrowLeft') {
            prevImage();
        }
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    updateImage();
});