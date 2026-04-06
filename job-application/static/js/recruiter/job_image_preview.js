document.addEventListener("DOMContentLoaded", function(){

    const fileInput = document.getElementById("posterInput");
    const previewContainer = document.getElementById("imagePreviewContainer");
    
    let selectedFiles = [];
    
    fileInput.addEventListener("change", function () {
    
        const newFiles = Array.from(this.files);
        
        newFiles.forEach(file => {
        
            selectedFiles.push(file);
            
            const reader = new FileReader();
            
            reader.onload = function(e){
            
                const card = document.createElement("div");
                card.classList.add("preview-card");
                
                const img = document.createElement("img");
                img.src = e.target.result;
                
                const removeBtn = document.createElement("button");
                removeBtn.classList.add("remove-btn");
                removeBtn.type = "button";
                
                removeBtn.onclick = function(){
                
                    const index = selectedFiles.indexOf(file);
                    
                    if(index > -1){
                        selectedFiles.splice(index,1);
                    }
                    
                    card.remove();
                    updateFileInput();
                
                }
                
                card.appendChild(img);
                card.appendChild(removeBtn);
                
                previewContainer.appendChild(card);
            
            }
            
            reader.readAsDataURL(file);
        
        });
        
        updateFileInput();
    
    });
    
    
    function updateFileInput(){
    
        const dataTransfer = new DataTransfer();
        
        selectedFiles.forEach(file => {
            dataTransfer.items.add(file);
        });
        
        fileInput.files = dataTransfer.files;
    
    }

});