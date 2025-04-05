document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileCount = document.getElementById('file-count');
    const processButton = document.getElementById('process-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const statusElement = document.getElementById('status');
    const resultsContainer = document.getElementById('results-container');
    const downloadLink = document.getElementById('download-link');
    
    let selectedFiles = [];
    
    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        selectedFiles = Array.from(e.target.files).filter(file => file.name.toLowerCase().endsWith('.pdf'));
        
        if (selectedFiles.length > 0) {
            fileCount.textContent = `${selectedFiles.length} PDF files selected`;
            processButton.disabled = false;
        } else {
            fileCount.textContent = 'No PDF files selected';
            processButton.disabled = true;
        }
    });
    
    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (selectedFiles.length === 0) {
            showStatus('Please select PDF files to process', 'error');
            return;
        }
        
        // Disable form elements
        processButton.disabled = true;
        fileInput.disabled = true;
        
        // Show progress container
        progressContainer.style.display = 'block';
        statusElement.style.display = 'none';
        resultsContainer.style.display = 'none';
        
        // Create FormData to send files
        const formData = new FormData();
        
        // Add all selected files with their relative paths
        for (let file of selectedFiles) {
            formData.append('files', file, file.webkitRelativePath);
        }
        
        try {
            // Simulate file upload progress
            let progress = 0;
            const totalFiles = selectedFiles.length;
            const progressInterval = setInterval(() => {
                if (progress < 95) {
                    progress += 5;
                    progressBar.style.width = `${progress}%`;
                    progressText.textContent = `Processing files... (${Math.round(progress)}%)`;
                }
            }, 300);
            
            // Send files to server
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });
            
            // Clear progress interval
            clearInterval(progressInterval);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process files');
            }
            
            // Complete progress bar
            progressBar.style.width = '100%';
            progressText.textContent = 'Processing complete!';
            
            // Get the blob data for the CSV file
            const blob = await response.blob();
            
            // Create a URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Set the download link
            downloadLink.href = url;
            downloadLink.download = 'tds_data_output.csv';
            
            // Add click event to trigger download
            downloadLink.addEventListener('click', function() {
                // Trigger download
                const tmpLink = document.createElement('a');
                tmpLink.href = url;
                tmpLink.download = 'tds_data_output.csv';
                document.body.appendChild(tmpLink);
                tmpLink.click();
                document.body.removeChild(tmpLink);
                
                // Clean up the URL
                window.URL.revokeObjectURL(url);
            });
            
            // Show success message and download button
            showStatus('TDS data processing completed successfully!', 'success');
            resultsContainer.style.display = 'block';
            
        } catch (error) {
            // Show error message
            showStatus(`Error: ${error.message}`, 'error');
            progressBar.style.width = '0%';
            progressText.textContent = 'Processing failed';
        } finally {
            // Re-enable form elements
            processButton.disabled = false;
            fileInput.disabled = false;
        }
    });
    
    function showStatus(message, type) {
        statusElement.textContent = message;
        statusElement.className = `status ${type}`;
        statusElement.style.display = 'block';
    }
});