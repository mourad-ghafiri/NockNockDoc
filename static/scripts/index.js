var stream_completion_ws = new WebSocket(window.location.origin.replace(/^http/, 'ws') + "/stream_completion");
var isStreamFinished = false;

stream_completion_ws.onmessage = function (event) {
    var response = document.getElementById('response');
    var loadingSpinner = document.getElementById('loadingSpinner');
    message = JSON.parse(event.data);
    if (message.type === 'message') {
        var lastMessage = response.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('bot-message')) {
            // Convert newlines to <br> and append the new text
            lastMessage.innerHTML += message.data.replace(/\n/g, '<br>');
        } else {
            var el = document.createElement('div');
            el.style = "color: white; background: #967e6b;";
            el.className = "message bot-message p-2 rounded-md";
            // Convert newlines to <br> for the new message
            el.innerHTML = message.data.replace(/\n/g, '<br>');
            response.appendChild(el);
        }
        // Hide spinner
        loadingSpinner.classList.add('hidden');
    }

    response.scrollTop = response.scrollHeight; // Auto-scroll to bottom
};


function sendMessage(event) {
    var input = document.getElementById("messageText");
    var response = document.getElementById('response');
    var loadingSpinner = document.getElementById('loadingSpinner');

    if (input.value.trim() !== '') {
        var userEl = document.createElement('div');
        userEl.className = "message user-message bg-gray-200 p-2 my-2 rounded-md";
        userEl.textContent = "Question: " + input.value;
        response.appendChild(userEl);

        // Show spinner
        loadingSpinner.classList.remove('hidden');

        stream_completion_ws.send(input.value);
        input.value = '';
    }

    event.preventDefault();
}

function uploadFile() {
    // Show the loading spinner
    document.getElementById('upload-loading-spinner').classList.remove('hidden');

    var fileInput = document.getElementById('fileInput');
    var statusDiv = document.getElementById('uploadStatus');

    if (fileInput.files.length === 0) {
        statusDiv.textContent = 'Please select a file first.';
        statusDiv.className = 'text-red-600';  // Setting text to red for errors.
        return;
    }

    var file = fileInput.files[0];
    var formData = new FormData();
    formData.append('file', file);

    fetch('/upload', { // Assuming this is your FastAPI upload endpoint
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            statusDiv.textContent = 'Document uploaded successfully!';
            statusDiv.className = 'text-blue-600 bg-blue-100 p-2 rounded';  // Using informative color for success.
            fetchUploadedFiles();
            // Upload complete, hide the loading spinner
            document.getElementById('upload-loading-spinner').classList.add('hidden');

        })
        .catch(error => {
            console.error('There was an error uploading the Document!', error);
            statusDiv.textContent = 'Error uploading the Document.';
            statusDiv.className = 'text-red-600';  // Setting text to red for errors.
            // Upload complete, hide the loading spinner
            document.getElementById('upload-loading-spinner').classList.add('hidden');
        });
}

function fetchUploadedFiles() {
    fetch('/documents')
        .then(response => response.json())
        .then(files => {
            const uploadedFiles = document.getElementById('uploadedFiles');
            uploadedFiles.innerHTML = ''; // Clear the current list
            files.forEach(file => {
                const li = document.createElement('li');
                li.className = 'flex justify-between items-center bg-gray-50 rounded-md p-2 hover:bg-gray-100 transition-all';

                const fileNameSpan = document.createElement('span');
                fileNameSpan.textContent = file;
                fileNameSpan.className = 'text-gray-600 font-medium';
                li.appendChild(fileNameSpan);

                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500 hover:text-red-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M6.293 9.293a1 1 0 011.414 0L10 11.586l2.293-2.293a1 1 0 111.414 1.414l-2.293 2.293 2.293 2.293a1 1 0 01-1.414 1.414L10 14.414l-2.293 2.293a1 1 0 01-1.414-1.414l2.293-2.293L6.293 10.707a1 1 0 010-1.414z" clip-rule="evenodd" /></svg>'; // SVG for delete icon
                deleteBtn.className = 'focus:outline-none';
                deleteBtn.onclick = () => deleteFile(file);
                li.appendChild(deleteBtn);

                uploadedFiles.appendChild(li);
            });
        })
        .catch(error => {
            console.error('Error fetching uploaded files:', error);
        });
}


function deleteFile(fileName) {
    fetch(`/delete-document/${fileName}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                fetchUploadedFiles(); // refresh the list after deletion
            } else {
                console.error('Error deleting file:', fileName);
            }
        })
        .catch(error => {
            console.error('Error sending delete request:', error);
        });
}

window.onload = function () {
    fetchUploadedFiles();
};

function dragOverHandler(event) {
    event.preventDefault();
    document.getElementById('uploadSection').classList.add('dragover');
}

function dragLeaveHandler(event) {
    document.getElementById('uploadSection').classList.remove('dragover');
}

function dropHandler(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('bg-blue-100', 'border-blue-400');
    if (ev.dataTransfer.items) {
        for (var i = 0; i < ev.dataTransfer.items.length; i++) {
            if (ev.dataTransfer.items[i].kind === 'file') {
                var file = ev.dataTransfer.items[i].getAsFile();
                document.getElementById('fileInput').files = ev.dataTransfer.files;
                uploadFile(); // Automatically upload the file once it's dropped
            }
        }
    }
}

function debounce(func, delay) {
    let debounceTimer;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(context, args), delay);
    };
}


const debouncedFetchSuggestions = debounce(async function() {
    const inputField = document.getElementById('messageText');
    const suggestionsPanel = document.getElementById('suggestions');
    const query = inputField.value;

    if (query.length < 3) { // Adjust this number as needed
        suggestionsPanel.innerHTML = '';
        suggestionsPanel.classList.add('hidden');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/queries', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query, top_k: 10 })
        });

        const suggestions = await response.json();

        if (suggestions.length > 0) {
            suggestionsPanel.innerHTML = '';
            suggestions.forEach(suggestion => {
                const div = document.createElement('div');
                div.innerHTML = suggestion;
                div.classList.add('suggestion-item');
                div.onclick = function() {
                    inputField.value = this.innerText;
                    suggestionsPanel.classList.add('hidden');
                };
                suggestionsPanel.appendChild(div);
            });
            suggestionsPanel.classList.remove('hidden');
        } else {
            suggestionsPanel.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}, 1000); // 1000 milliseconds = 1 second