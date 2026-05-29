const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const voiceBtn = document.getElementById('voice-btn');

let isRecording = false;
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        return;
    }
    if (text !== '') {
        const utterThis = new SpeechSynthesisUtterance(text);
        utterThis.onend = function (event) {
            console.log('SpeechSynthesisUtterance.onend');
        }
        utterThis.onerror = function (event) {
            console.error('SpeechSynthesisUtterance.onerror');
        }
        synth.speak(utterThis);
    }
}

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        chatInput.value = text;
        sendMessage();
    };

    recognition.onspeechend = function() {
        stopRecording();
    };

    recognition.onerror = function(event) {
        console.error('Speech recognition error detected: ' + event.error);
        stopRecording();
    };
} else {
    voiceBtn.style.display = 'none';
}

function startRecording() {
    if(recognition) {
        isRecording = true;
        voiceBtn.classList.add('recording');
        recognition.start();
    } else {
        alert("Speech recognition not supported in this browser.");
    }
}

function stopRecording() {
    if(recognition && isRecording) {
        isRecording = false;
        voiceBtn.classList.remove('recording');
        recognition.stop();
    }
}

voiceBtn.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

function addMessage(text, isUser = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    
    msgDiv.innerHTML = `
        <div class="avatar"><i class="fas ${isUser ? 'fa-user' : 'fa-robot'}"></i></div>
        <div class="text">${text}</div>
    `;
    
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage(text, true);
    chatInput.value = '';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });
        
        const data = await response.json();
        const replyText = data.reply;
        
        addMessage(replyText, false);
        speak(replyText); // Always speak bot responses
        
    } catch (error) {
        addMessage("Sorry, I'm having trouble connecting to the server.", false);
    }
}

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
