// Generate or retrieve user ID from localStorage
function getOrCreateUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        // Generate a random user ID
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('user_id', userId);
    }
    document.getElementById('user-id-display').textContent = userId;
    return userId;
}

// Set user ID on page load
document.addEventListener('DOMContentLoaded', () => {
    getOrCreateUserId();
    
    // Set up file input change handler
    document.getElementById('file-upload').addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || 'No file selected';
        e.target.nextElementSibling.textContent = `Upload ${fileName}`;
    });
});

// Show a modal
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Close any open modal
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.style.overflow = 'auto';
}

// Show status message
function showStatus(message, isError = false) {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${isError ? 'status-error' : 'status-success'}`;
    statusDiv.textContent = message;
    
    const uploadStatus = document.getElementById('upload-status');
    uploadStatus.innerHTML = '';
    uploadStatus.appendChild(statusDiv);
    
    setTimeout(() => {
        statusDiv.style.opacity = '0';
        setTimeout(() => statusDiv.remove(), 300);
    }, 3000);
}

// Create a new folder
async function createFolder() {
    const folderName = document.getElementById('folder-name').value.trim();
    const password = document.getElementById('admin-password').value;
    
    if (!folderName) {
        showStatus('Please enter a folder name', true);
        return;
    }
    
    try {
        const response = await fetch('/create_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                folder_name: folderName,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('Folder created successfully!');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showStatus(data.error || 'Failed to create folder', true);
        }
    } catch (error) {
        showStatus('Error creating folder: ' + error.message, true);
    }
}

// Delete a folder
async function deleteFolder() {
    const folderSelect = document.getElementById('folder-to-delete');
    const folderName = folderSelect.value;
    const password = document.getElementById('delete-folder-password').value;
    
    if (!folderName) {
        showStatus('Please select a folder to delete', true);
        return;
    }
    
    if (!confirm(`Are you sure you want to delete the folder "${folderName}"? This will delete all files inside it.`)) {
        return;
    }
    
    try {
        const response = await fetch('/delete_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                folder_name: folderName,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('Folder deleted successfully!');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showStatus(data.error || 'Failed to delete folder', true);
        }
    } catch (error) {
        showStatus('Error deleting folder: ' + error.message, true);
    }
}

// View files in a folder
async function viewFolder(folderName) {
    document.getElementById('files-folder-name').textContent = folderName;
    const filesList = document.getElementById('files-list');
    filesList.innerHTML = '<div class="loading">Loading files...</div>';
    
    try {
        const response = await fetch(`/files/${encodeURIComponent(folderName)}`);
        const data = await response.json();
        
        if (response.ok) {
            displayFiles(folderName, data.files);
        } else {
            filesList.innerHTML = `<div class="status-error">${data.error || 'Error loading files'}</div>`;
        }
    } catch (error) {
        filesList.innerHTML = `<div class="status-error">Error: ${error.message}</div>`;
    }
    
    // Show the upload modal with the current folder pre-selected
    document.getElementById('current-folder').textContent = folderName;
    showModal('upload-modal');
}

// Display files in the files modal
function displayFiles(folderName, files) {
    const filesList = document.getElementById('files-list');
    
    if (!files || files.length === 0) {
        filesList.innerHTML = '<p>No files in this folder yet.</p>';
        return;
    }
    
    filesList.innerHTML = '';
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info';
        
        const fileName = document.createElement('div');
        fileName.className = 'file-name';
        fileName.textContent = file.original_filename || file.stored_filename;
        
        const fileMeta = document.createElement('div');
        fileMeta.className = 'file-meta';
        fileMeta.textContent = `Uploaded by ${file.uploader_id} • ${formatFileSize(file.size)} • ${new Date(file.timestamp).toLocaleString()}`;
        
        fileInfo.appendChild(fileName);
        fileInfo.appendChild(fileMeta);
        
        const fileActions = document.createElement('div');
        fileActions.className = 'file-actions';
        
        const downloadBtn = document.createElement('button');
        downloadBtn.textContent = 'Download';
        downloadBtn.onclick = (e) => {
            e.stopPropagation();
            window.location.href = `/download/${encodeURIComponent(folderName)}/${encodeURIComponent(file.stored_filename)}`;
        };
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'danger';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteFile(folderName, file.stored_filename);
        };
        
        fileActions.appendChild(downloadBtn);
        fileActions.appendChild(deleteBtn);
        
        fileItem.appendChild(fileInfo);
        fileItem.appendChild(fileActions);
        
        filesList.appendChild(fileItem);
    });
    
    // Show the files modal
    showModal('files-modal');
}

// Upload a file
async function uploadFile() {
    const fileInput = document.getElementById('file-upload');
    const folderName = document.getElementById('current-folder').textContent;
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showStatus('Please select a file to upload', true);
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`/upload/${encodeURIComponent(folderName)}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('File uploaded successfully!');
            // Refresh the files list
            viewFolder(folderName);
            // Reset file input
            fileInput.value = '';
        } else {
            showStatus(data.error || 'Failed to upload file', true);
        }
    } catch (error) {
        showStatus('Error uploading file: ' + error.message, true);
    }
}

// Delete a file
async function deleteFile(folderName, storedFilename) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }
    
    const password = prompt('Enter admin password (leave empty if you are the uploader):');
    
    try {
        const response = await fetch('/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                folder: folderName,
                stored_filename: storedFilename,
                password: password || ''
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('File deleted successfully!');
            // Refresh the files list
            viewFolder(folderName);
        } else {
            showStatus(data.error || 'Failed to delete file', true);
        }
    } catch (error) {
        showStatus('Error deleting file: ' + error.message, true);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        closeModal();
    }
}
