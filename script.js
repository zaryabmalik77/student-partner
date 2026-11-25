const chatbox = document.getElementById("chatbox");
const input = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const fileInput = document.getElementById("pdf-upload");
const uploadStatus = document.getElementById("upload-status");

function addMessage(text, sender) {
    const div = document.createElement("div");
    div.classList.add("message", sender);
    div.textContent = text;
    chatbox.appendChild(div);
    chatbox.scrollTop = chatbox.scrollHeight;
    return div;
}

// Handle Chat
async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    
    addMessage(text, "user");
    input.value = "";
    sendBtn.disabled = true;
    const thinkingMsg = addMessage("Thinking...", "bot");
    
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        
        const data = await response.json();
        thinkingMsg.textContent = data.reply;
    } catch (error) {
        thinkingMsg.textContent = "Something went wrong. Check your terminal.";
    }
    
    sendBtn.disabled = false;
    input.focus();
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

// Handle PDF Upload
fileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    uploadStatus.textContent = "Uploading...";
    uploadStatus.style.color = "#f59e0b"; // Orange

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.textContent = "✅ Notes Loaded!";
            uploadStatus.style.color = "#10b981"; // Green
            addMessage(data.message, "bot");
        } else {
            uploadStatus.textContent = "❌ Error loading notes";
            uploadStatus.style.color = "#ef4444"; // Red
            addMessage(data.error, "bot");
        }
    } catch (error) {
        uploadStatus.textContent = "❌ Upload failed";
        uploadStatus.style.color = "#ef4444"; 
    }
});