let currentImageIndex = 0;

function showImage(index) {
    const imageElement = document.getElementById("jobImage");
    if (!imageElement) return;
    imageElement.src = jobImages[index];
}

function nextImage() {
    currentImageIndex++;
    if (currentImageIndex >= jobImages.length) {
        currentImageIndex = 0;
    }
    showImage(currentImageIndex);
}

function prevImage() {
    currentImageIndex--;
    if (currentImageIndex < 0) {
        currentImageIndex = jobImages.length - 1;
    }
    showImage(currentImageIndex);
}