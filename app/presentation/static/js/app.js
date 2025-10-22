// ComfyUI AI Chat - Main JavaScript

let currentSessionId = null;
let isGenerating = false;

// Initialize app on page load
document.addEventListener('DOMContentLoaded', function() {
    loadSessions();
    
    // Initialize textarea auto-resize
    const textarea = document.getElementById('messageInput');
    if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }
    
    // Bind event listeners
    document.getElementById('createSessionBtn').addEventListener('click', createSession);
    document.getElementById('editTitleBtn').addEventListener('click', editSessionTitle);
    document.getElementById('deleteSessionBtn').addEventListener('click', deleteCurrentSession);
    document.getElementById('sendMessageBtn').addEventListener('click', sendMessage);
    document.getElementById('messageInput').addEventListener('keydown', handleMessageKeydown);
    document.getElementById('messageInput').addEventListener('input', autoResizeTextarea);
    document.getElementById('generateImageBtn').addEventListener('click', generateImage);
});

// ===== Session Management =====

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const sessions = await response.json();
        
        const sessionList = document.getElementById('sessionList');
        sessionList.innerHTML = '';
        
        if (sessions.length === 0) {
            sessionList.innerHTML = '<div class="text-muted small">尚無對話</div>';
            return;
        }
        
        sessions.forEach(session => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action session-item';
            item.dataset.sessionId = session.id;
            item.onclick = (e) => {
                e.preventDefault();
                loadSession(session.id);
            };
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${escapeHtml(session.title)}</h6>
                </div>
                <small class="text-muted">
                    <i class="bi bi-chat"></i> ${session.message_count} 
                    <i class="bi bi-image ms-2"></i> ${session.image_count}
                </small>
            `;
            
            if (currentSessionId === session.id) {
                item.classList.add('active');
            }
            
            sessionList.appendChild(item);
        });
        
    } catch (error) {
        console.error('Failed to load sessions:', error);
        showError('載入對話列表失敗: ' + error.message);
    }
}

async function createSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const session = await response.json();
        await loadSessions();
        await loadSession(session.id);
        
    } catch (error) {
        console.error('Failed to create session:', error);
        showError('創建對話失敗: ' + error.message);
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    
    try {
        // Load session info
        const sessionResponse = await fetch(`/api/sessions/${sessionId}`);
        if (!sessionResponse.ok) {
            throw new Error(`HTTP error! status: ${sessionResponse.status}`);
        }
        const session = await sessionResponse.json();
        
        document.getElementById('sessionTitle').textContent = session.title;
        
        // Load chat history
        const historyResponse = await fetch(`/api/chat/history/${sessionId}`);
        if (!historyResponse.ok) {
            throw new Error(`HTTP error! status: ${historyResponse.status}`);
        }
        const history = await historyResponse.json();
        
        displayChatHistory(history.messages);
        
        // Update session list selection
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.sessionId === sessionId) {
                item.classList.add('active');
            }
        });
        
        // Load latest image if exists
        if (session.image_count > 0) {
            await loadLatestImage(sessionId);
        }
        
    } catch (error) {
        console.error('Failed to load session:', error);
        showError('載入對話失敗: ' + error.message);
    }
}

async function editSessionTitle() {
    if (!currentSessionId) {
        showError('請先選擇一個對話');
        return;
    }
    
    const currentTitle = document.getElementById('sessionTitle').textContent;
    const newTitle = prompt('輸入新標題:', currentTitle);
    
    if (!newTitle || newTitle === currentTitle) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${currentSessionId}/title`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: newTitle })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        document.getElementById('sessionTitle').textContent = newTitle;
        await loadSessions();
        
    } catch (error) {
        console.error('Failed to update title:', error);
        showError('更新標題失敗: ' + error.message);
    }
}

async function deleteCurrentSession() {
    if (!currentSessionId) {
        showError('請先選擇一個對話');
        return;
    }
    
    if (!confirm('確定要刪除此對話嗎?所有訊息和圖片都會被刪除。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${currentSessionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        currentSessionId = null;
        document.getElementById('chatMessages').innerHTML = '<div class="text-center text-muted py-5"><i class="bi bi-chat-text" style="font-size: 3rem;"></i><p class="mt-3">開始與 AI 角色設計師對話</p></div>';
        document.getElementById('sessionTitle').textContent = 'ComfyUI AI 角色設計助手';
        
        await loadSessions();
        
    } catch (error) {
        console.error('Failed to delete session:', error);
        showError('刪除對話失敗: ' + error.message);
    }
}

function displayChatHistory(messages) {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';
    
    messages.forEach(msg => {
        appendMessage(msg.role, msg.content, msg.timestamp);
    });
    
    scrollToBottom();
}

function appendMessage(role, content, timestamp) {
    const container = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (role === 'assistant') {
        // Render markdown for assistant messages
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-timestamp';
    timeDiv.textContent = new Date(timestamp).toLocaleString('zh-TW');
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    container.appendChild(messageDiv);
    
    // 增強代碼塊和提示詞顯示
    if (typeof window.enhanceNewMessage === 'function') {
        window.enhanceNewMessage(messageDiv);
    }
}

async function sendMessage() {
    if (!currentSessionId) {
        // Create a new session if none exists
        await createSession();
        if (!currentSessionId) {
            showError('無法創建對話');
            return;
        }
    }
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) {
        return;
    }
    
    if (isGenerating) {
        showError('請等待 AI 回應完成');
        return;
    }
    
    // Disable input
    input.disabled = true;
    isGenerating = true;
    
    // Add user message to UI
    appendMessage('user', message, new Date().toISOString());
    input.value = '';
    resetTextareaHeight();
    scrollToBottom();
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message message-assistant';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = '<div class="message-content"><span class="loading-spinner"></span> AI 正在思考中...</div>';
    document.getElementById('chatMessages').appendChild(loadingDiv);
    scrollToBottom();
    
    try {
        const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        document.getElementById('loading-message').remove();
        
        // Add assistant response
        appendMessage(data.role, data.content, data.timestamp);
        scrollToBottom();
        
        // Reload sessions to update message count
        await loadSessions();
        
    } catch (error) {
        console.error('Failed to send message:', error);
        const loadingElement = document.getElementById('loading-message');
        if (loadingElement) {
            loadingElement.remove();
        }
        showError('發送訊息失敗: ' + error.message);
    } finally {
        input.disabled = false;
        isGenerating = false;
        input.focus();
    }
}

function handleMessageKeydown(event) {
    // Send message on Enter (unless Shift is pressed for newline)
    if (event.key === 'Enter') {
        if (event.shiftKey) {
            // Allow Shift+Enter for newline
            return;
        }
        // Enter to send
        event.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('messageInput');
    if (!textarea) return;
    
    // Reset height to calculate scrollHeight correctly
    textarea.style.height = 'auto';
    
    // Set new height based on scrollHeight, capped at max-height (200px)
    const newHeight = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = newHeight + 'px';
}

function resetTextareaHeight() {
    const textarea = document.getElementById('messageInput');
    if (textarea) {
        textarea.style.height = 'auto';
    }
}

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    
    // 使用平滑滾動動畫
    if (window.chatScroller && container === window.chatScroller.container) {
        window.chatScroller.scrollToBottom(300);
    } else {
        // 更新 chatScroller 的容器引用
        if (window.SmoothScroll) {
            window.chatScroller = new window.SmoothScroll(container);
            window.chatScroller.scrollToBottom(300);
        } else {
            // 備用方案：直接滾動
            container.scrollTop = container.scrollHeight;
        }
    }
}

// ===== Image Functions =====

async function generateImage() {
    // Auto-create session if not exists
    if (!currentSessionId) {
        try {
            await createSession();
            if (!currentSessionId) {
                showError('無法創建對話,請手動點擊「新對話」按鈕');
                return;
            }
        } catch (error) {
            showError('創建對話失敗,請手動點擊「新對話」按鈕');
            return;
        }
    }
    
    const positivePrompt = document.getElementById('positivePrompt').value.trim();
    
    if (!positivePrompt) {
        showError('請輸入正向提示詞');
        return;
    }
    
    if (isGenerating) {
        showError('請等待當前任務完成');
        return;
    }
    
    isGenerating = true;
    
    const resultDiv = document.getElementById('imageResult');
    resultDiv.innerHTML = '<div class="text-center text-muted"><span class="loading-spinner" style="margin: 0 auto;"></span></div>';
    
    // 顯示自訂加載動畫
    if (window.loadingIndicator) {
        window.loadingIndicator.show();
    }
    
    const seed = document.getElementById('imageSeed').value;
    
    try {
        const response = await fetch('/api/image/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                positive_prompt: positivePrompt,
                negative_prompt: document.getElementById('negativePrompt').value,
                width: parseInt(document.getElementById('imageWidth').value),
                height: parseInt(document.getElementById('imageHeight').value),
                steps: parseInt(document.getElementById('imageSteps').value),
                cfg: parseFloat(document.getElementById('imageCfg').value),
                seed: seed ? parseInt(seed) : null,
                sampler: 'dpmpp_2m_sde_gpu',
                scheduler: 'simple'
            })
        });
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            // 如果響應包含錯誤詳情
            const errorMsg = data.detail || `HTTP error! status: ${response.status}`;
            throw new Error(errorMsg);
        }
        
        // 驗證必要的數據字段
        if (!data.url || !data.filename) {
            console.error('Invalid response data:', data);
            throw new Error('伺服器返回的數據格式不正確');
        }
        
        // 隱藏加載動畫
        if (window.loadingIndicator) {
            window.loadingIndicator.hide();
        }
        
        // 顯示成功通知
        if (window.showNotification) {
            window.showNotification('圖片生成成功！', 'success');
        }
        
        resultDiv.innerHTML = `
            <img src="${data.url}" alt="Generated Image" class="img-fluid">
            <div class="image-metadata mt-2">
                <strong>檔名:</strong> ${escapeHtml(data.filename)}<br>
                <strong>尺寸:</strong> ${data.metadata.width}x${data.metadata.height}<br>
                <strong>Seed:</strong> ${data.metadata.seed}
            </div>
            <div class="mt-3">
                <a href="/api/image/download/${currentSessionId}/${data.filename}" class="btn btn-primary" download>
                    <i class="bi bi-download"></i> 下載圖片
                </a>
            </div>
        `;
        
        // Reload sessions to update image count
        await loadSessions();
        
    } catch (error) {
        console.error('Failed to generate image:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack
        });
        
        // 隱藏加載動畫
        if (window.loadingIndicator) {
            window.loadingIndicator.hide();
        }
        
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <strong>圖片生成失敗</strong><br>
                ${escapeHtml(error.message)}
            </div>
        `;
    } finally {
        isGenerating = false;
    }
}

async function loadLatestImage(sessionId) {
    try {
        const response = await fetch(`/api/image/list/${sessionId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.latest_image) {
            const resultDiv = document.getElementById('imageResult');
            resultDiv.innerHTML = `
                <img src="/api/image/view/${sessionId}/${data.latest_image}" alt="Latest Image" class="img-fluid">
                <div class="mt-3">
                    <a href="/api/image/download/${sessionId}/${data.latest_image}" class="btn btn-primary" download>
                        <i class="bi bi-download"></i> 下載圖片
                    </a>
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load latest image:', error);
        // Silent fail for loading images - it's optional
    }
}

// ===== Utility Functions =====

function showError(message) {
    // 使用新的通知系統
    if (window.showNotification) {
        window.showNotification(message, 'error');
        return;
    }
    
    // 備用方案：創建 toast 通知
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
