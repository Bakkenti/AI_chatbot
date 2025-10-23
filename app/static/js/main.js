const messages = document.getElementById("messages");
const input = document.getElementById("messageInput");
const fileInput = document.getElementById("fileInput");
let lastAIMessage = "";
let selectedFiles = new Set();
let currentChatId = null;
let chatWS;

function sendMessage() {
    const message = input.value?.trim();
    if (!message) return;
    if (!currentChatId) {
        alert("Please select a chat first.");
        return;
    }
    
    addMessage(`[user] ${message}`, "user");
    input.value = "";

    if (chatWS && chatWS.readyState === WebSocket.OPEN) {
        chatWS.send(message);
    }
}


function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.classList.add("msg", type);

    if (type === "ai") {
        msg.innerHTML = marked.parse(text)
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
            .replace(/\n/g, "<br>");
    } else {
        msg.textContent = text;
    }

    messages.appendChild(msg);
    msg.querySelectorAll("pre code").forEach(block => hljs.highlightElement(block));
    messages.scrollTop = messages.scrollHeight;
}

fileInput.addEventListener("change", async event => {
    const file = event.target.files[0];
    const arrayBuffer = await file.arrayBuffer();
    const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

    if (chatWS && chatWS.readyState === WebSocket.OPEN) {
        chatWS.send(JSON.stringify({
            sender: "user",
            filetype: "pdf",
            filename: file.name,
            content: base64
        }));
        addMessage(`📄 PDF '${file.name}' отправлен`, "user");
    }
});


function saveToStorage() {
    if (!lastAIMessage) {
        alert("Нет ответа от AI для сохранения!");
        return;
    }
    const timestamp = Date.now().toString(36);
    const defaultName = `saved_${timestamp}.pdf`;
    openSaveModal(defaultName, lastAIMessage);
}

function openSaveModal(defaultName, content) {
    const modal = document.createElement("div");
    modal.id = "saveModal";
    modal.style = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.6); display: flex;
        align-items: center; justify-content: center; z-index: 9999;
    `;

    modal.innerHTML = `
        <div style="background:#1a1a1a;color:#eee;padding:20px;border-radius:8px;width:350px;">
            <h2 style="margin-top:0;margin-bottom:10px;">Сохранение файла</h2>
            <label>Имя файла:</label>
            <input type="text" id="modalFilename" value="${defaultName}" style="width:100%;padding:6px;margin:8px 0;border-radius:4px;border:1px solid #444;background:#222;color:#eee;">
            <div style="text-align:right;margin-top:10px;">
                <button id="cancelSave" style="margin-right:8px;padding:6px 12px;border:none;border-radius:4px;background:#555;color:#eee;cursor:pointer;">Отмена</button>
                <button id="confirmSave" style="padding:6px 12px;border:none;border-radius:4px;background:#4a90e2;color:#fff;cursor:pointer;">Сохранить</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    document.getElementById("cancelSave").onclick = () => modal.remove();

    document.getElementById("confirmSave").onclick = () => {
        const filename = document.getElementById("modalFilename").value.trim();
        if (!filename) {
            alert("Введите имя файла!");
            return;
        }
        if (chatWS && chatWS.readyState === WebSocket.OPEN) {
const command = `savestorage ${filename}`;
chatWS.send(command);

            addMessage(`☁ Сохранение в MinIO как ${filename}...`, "user");
        }
        modal.remove();
    };
}



function showConfirm(action, file, callback) {
    const modal = document.createElement("div");
    modal.style = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.6); display: flex;
        align-items: center; justify-content: center; z-index: 9999;
    `;

    modal.innerHTML = `
        <div style="background:#1a1a1a;color:#eee;padding:30px;border-radius:12px;width:450px;text-align:center;box-shadow:0 0 20px #000;font-size:1.1rem;">
            <p style="margin-bottom:30px;font-size:1.2rem;">Вы хотите <b>${action}</b> файл "<b>${file}</b>"?</p>
            <div style="display:flex;justify-content:center;gap:20px;">
                <button id="confirmYes" class="fancy-btn">Да</button>
                <button id="confirmNo" class="fancy-btn no-btn">Нет</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById("confirmYes").onclick = () => {
        callback();
        modal.remove();
    };
    document.getElementById("confirmNo").onclick = () => modal.remove();
}

async function loadFiles() {
    const res = await fetch("/files");
    const files = await res.json();
    const list = document.getElementById("file-list");
    list.innerHTML = "";

    files.forEach(file => {
        const row = document.createElement("div");
        row.className = "file-row";

        const fileBox = document.createElement("a");
        fileBox.className = "file-box";
        fileBox.href = `/files/${file}`;
        fileBox.target = "_blank";
        fileBox.textContent = file;

        const actions = document.createElement("div");
        actions.className = "file-actions";

        const downloadBtn = document.createElement("button");
        downloadBtn.className = "download-btn";
        downloadBtn.textContent = "⬇️";
        downloadBtn.onclick = e => {
            e.stopPropagation();
            showConfirm("скачать", file, () => {
                const a = document.createElement("a");
                a.href = `/files/${file}`;
                a.download = file;
                a.click();
            });
        };

        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-btn";
        deleteBtn.textContent = "🗑";
        deleteBtn.onclick = e => {
            e.stopPropagation();
            showConfirm("удалить", file, () => {
                if (chatWS && chatWS.readyState === WebSocket.OPEN) {
                    chatWS.send(JSON.stringify({ action: "delete_files", files: [file] }));
                }
            });
        };

        actions.append(downloadBtn, deleteBtn);
        row.append(fileBox, actions);
        list.appendChild(row);
    });
}

document.getElementById("sendBtn").onclick = sendMessage;
document.getElementById("readPdfBtn").onclick = () => fileInput.click();
document.getElementById("saveBtn").onclick = saveToStorage;

input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

loadFiles();
loadChats();
setInterval(loadFiles, 15000);



async function loadChats() {
    const res = await fetch("/api/chats/");
    const chats = await res.json();
    const chatList = document.getElementById("chats-list");
    chatList.innerHTML = "";

    chats.forEach(chat => {
        const div = document.createElement("div");
        div.textContent = chat.name;
        div.className = "chat-item";
        div.onclick = () => openChat(chat.id);
        chatList.appendChild(div);
    });
}

async function createNewChat() {
    const name = prompt("Название нового чата:");
    if (!name) return;
    await fetch("/api/chats/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name })
    });
    await loadChats();
}

async function openChat(chatId) {
    currentChatId = chatId;
    messages.innerHTML = "";

    if (chatWS) chatWS.close();
    chatWS = new WebSocket(`ws://${location.host}/api/chats/ws/${chatId}`);

    chatWS.onopen = () => console.log("Connected to chat " + chatId);
    chatWS.onclose = () => console.log("Disconnected from chat " + chatId);

    chatWS.onmessage = event => {
        try {
            const data = JSON.parse(event.data);
            

            if (data.sender === "ai" || data.sender === "system") {
                if (data.sender === "ai" && data.content) {
                    lastAIMessage = data.content;
                }
                addMessage(`[${data.sender}] ${data.content}`, data.sender);
            }
        } catch {
            console.error("Invalid JSON:", event.data);
        }
    };

    const res = await fetch(`/api/chats/${chatId}/messages`);
    const oldMessages = await res.json();
    oldMessages.forEach(msg => addMessage(`[${msg.sender}] ${msg.content}`, msg.sender));
}

document.getElementById("new-chat-btn").onclick = createNewChat;