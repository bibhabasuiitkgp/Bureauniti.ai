
// const sendMessage = document.getElementById('sendMessage');

// Todo functionality
const todoInput = document.getElementById('todoInput');
const addTodo = document.getElementById('addTodo');
const todoList = document.getElementById('todoList');

// Load todos from localStorage
let todos = JSON.parse(localStorage.getItem('todos')) || [];

// Chat Functions
// function addMessage(message, isUser = true) {
//     const messageDiv = document.createElement('div');
//     messageDiv.classList.add('message');
//     messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
//     messageDiv.textContent = message;
//     chatMessages.appendChild(messageDiv);
//     chatMessages.scrollTop = chatMessages.scrollHeight;
// }

function handleChatSubmit() {
    const message = chatInput.value.trim();
    if (message) {
        addMessage(message, true);
        // Simulate bot response
        setTimeout(() => {
            addMessage('This is a demo response from the chatbot!', false);
        }, 1000);
        chatInput.value = '';
    }
}

// Todo Functions
function saveTodos() {
    localStorage.setItem('todos', JSON.stringify(todos));
}

function createTodoElement(todo) {
    const li = document.createElement('li');
    li.classList.add('todo-item');
    if (todo.completed) {
        li.classList.add('completed');
    }

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.classList.add('checkbox');
    checkbox.checked = todo.completed;
    checkbox.addEventListener('change', () => toggleTodo(todo.id));

    const todoText = document.createElement('span');
    todoText.classList.add('todo-text');
    todoText.textContent = todo.text;

    const deleteButton = document.createElement('button');
    deleteButton.classList.add('delete-todo');
    deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
    deleteButton.addEventListener('click', () => deleteTodo(todo.id));

    li.appendChild(checkbox);
    li.appendChild(todoText);
    li.appendChild(deleteButton);

    return li;
}

function renderTodos() {
    todoList.innerHTML = '';
    todos.forEach(todo => {
        todoList.appendChild(createTodoElement(todo));
    });
}

function addTodoItem() {
    const text = todoInput.value.trim();
    if (text) {
        const todo = {
            id: Date.now(),
            text,
            completed: false
        };
        todos.push(todo);
        saveTodos();
        renderTodos();
        todoInput.value = '';
    }
}

function deleteTodo(id) {
    todos = todos.filter(todo => todo.id !== id);
    saveTodos();
    renderTodos();
}

function toggleTodo(id) {
    todos = todos.map(todo =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
    );
    saveTodos();
    renderTodos();
}

// Event Listeners
// sendMessage.addEventListener('click', handleChatSubmit);
// chatInput.addEventListener('keypress', (e) => {
//     if (e.key === 'Enter' && !e.shiftKey) {
//         e.preventDefault();
//         handleChatSubmit();
//     }
// });

addTodo.addEventListener('click', addTodoItem);
todoInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addTodoItem();
    }
});

// Initial render
renderTodos();

// Add some sample messages to the chat
setTimeout(() => {
    addMessage('Welcome to the chat! 👋', false);
    addMessage('How can I help you today?', false);
}, 500);









// Global state
let currentAgent = 'general';
const API_BASE_URL = 'http://127.0.0.1:8000'; // Adjust according to your backend URL

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendMessage');
const fileInput = document.getElementById('fileInput');
const fileInputArea = document.getElementById('fileInputArea');
const translationOptions = document.getElementById('translationOptions');
const currentAgentTitle = document.getElementById('currentAgent');

// Initialize menu clicks
document.querySelectorAll('.menu-box').forEach(menuItem => {
    menuItem.addEventListener('click', () => {
        // Remove active class from all menu items
        document.querySelectorAll('.menu-box').forEach(item => item.classList.remove('active'));
        // Add active class to clicked item
        menuItem.classList.add('active');

        // Update current agent
        currentAgent = menuItem.dataset.agent;
        currentAgentTitle.textContent = menuItem.textContent;

        // Show/hide relevant input areas
        updateInputAreas();
    });
});

// Enhanced updateInputAreas function with file type restrictions
function updateInputAreas() {
    fileInputArea.style.display = 'none';
    translationOptions.style.display = 'none';

    switch (currentAgent) {
        case 'image':
            fileInputArea.style.display = 'block';
            fileInput.accept = '.jpg, .jpeg, .png';
            break;
        case 'document':
            fileInputArea.style.display = 'block';
            fileInput.accept = '.pdf';
            break;
        case 'voice':
            fileInputArea.style.display = 'block';
            fileInput.accept = 'audio/*';
            break;
        case 'translate':
            translationOptions.style.display = 'block';
            break;
    }
}


function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleSendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, true);
    chatInput.value = '';

    try {
        let response;
        let responseText;

        switch (currentAgent) {
            case 'general':
                response = await fetch(`${API_BASE_URL}/inference`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: message })
                });
                const inferenceData = await response.json();
                responseText = inferenceData.data;
                break;

            case 'translate':
                const sourceLang = document.getElementById('sourceLang').value;
                const targetLang = document.getElementById('targetLang').value;
                response = await fetch(`${API_BASE_URL}/translate/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: message,
                        source_lang: sourceLang,
                        target_lang: targetLang,
                        country: 'India'
                    })
                });
                const translationData = await response.json();
                responseText = translationData.translated_text;
                break;

            case 'grammar':
                response = await fetch(`${API_BASE_URL}/correct-text/?text=${encodeURIComponent(message)}`);
                const grammarData = await response.json();
                responseText = grammarData.corrected_response;
                break;

            case 'image':
                // For image analysis, we need a file input
                const imageFile = fileInput.files[0];
                console.log('Image File:', imageFile); // This shows the file object

                if (!imageFile) {
                    throw new Error('Please select an image file first');
                }

                const imageFormData = new FormData();
                imageFormData.append('file', imageFile);

                console.log('FormData:', imageFormData); // This shows the FormData object

                // Method 1: Log each entry in the FormData
                for (let pair of imageFormData.entries()) {
                    console.log('FormData Entry:', pair[0], pair[1]);
                }

                response = await fetch(`${API_BASE_URL}/analyze`, {
                    method: 'POST',
                    body: imageFile
                });
                const imageData = await response.json();
                console.log('Image Data:', imageData); // This shows the response data
                responseText = JSON.stringify(imageData.data, null, 2);
                break;

            case 'document':
                // For document Q&A, we need both the file and the question
                const docFile = fileInput.files[0];
                if (!docFile) {
                    throw new Error('Please select a PDF document first');
                }
                const docFormData = new FormData();
                docFormData.append('file', docFile);
                docFormData.append('question', message);

                response = await fetch(`${API_BASE_URL}/process`, {
                    method: 'POST',
                    body: docFormData
                });
                const documentData = await response.json();
                responseText = documentData.answer;
                break;

            case 'voice':
                // For voice processing, we need an audio file
                const audioFile = fileInput.files[0];
                if (!audioFile) {
                    throw new Error('Please select an audio file first');
                }
                const audioFormData = new FormData();
                audioFormData.append('file', audioFile);

                response = await fetch(`${API_BASE_URL}/process-audio/`, {
                    method: 'POST',
                    body: audioFormData
                });
                const voiceData = await response.json();
                responseText = `Transcription: ${voiceData.transcription}\n\nCorrected Response: ${voiceData.corrected_response}`;
                break;

            default:
                throw new Error('Invalid agent type');
        }

        if (response.ok) {
            addMessage(responseText);
        } else {
            throw new Error(`API request failed with status ${response.status}`);
        }
    } catch (error) {
        addMessage('Error: ' + error.message);
    }
}

// Enhanced file input handler with additional validation
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file types based on current agent
    let isValidFile = false;
    let errorMessage = '';

    switch (currentAgent) {
        case 'image':
            isValidFile = file.type.startsWith('image/');
            errorMessage = 'Please select a valid image file';
            break;
        case 'voice':
            isValidFile = file.type.startsWith('audio/') || file.type === 'application/octet-stream';
            errorMessage = 'Please select a valid audio file';
            break;
        case 'document':
            isValidFile = file.type === 'application/pdf';
            errorMessage = 'Please select a valid PDF file';
            break;
    }

    if (!isValidFile) {
        addMessage(`Error: ${errorMessage}`);
        fileInput.value = '';
        return;
    }

    // Add a message to show that the file was successfully uploaded
    addMessage(`File "${file.name}" has been selected. You can now send your message.`, true);
});

// Event listeners
sendButton.addEventListener('click', handleSendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

// Initial setup
updateInputAreas();