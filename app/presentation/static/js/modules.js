/**
 * Modular Components System
 * 提供模組化的 AI 對話和圖片生成組件
 */

// ===== Chat Module =====
class ChatModule {
    constructor(options = {}) {
        this.container = options.container || '#chat-panel';
        this.messagesContainer = options.messagesContainer || '#chatMessages';
        this.inputElement = options.inputElement || '#messageInput';
        this.sendButton = options.sendButton || '.chat-send-btn';
        
        this.messages = [];
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.renderEmptyState();
    }
    
    setupEventListeners() {
        const input = document.querySelector(this.inputElement);
        const sendBtn = document.querySelector(this.sendButton);
        
        if (input) {
            input.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }
        
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
    }
    
    renderEmptyState() {
        const container = document.querySelector(this.messagesContainer);
        if (container && this.messages.length === 0) {
            container.innerHTML = `
                <div class="chat-empty-state">
                    <i class="bi bi-chat-text"></i>
                    <p>開始與 AI 對話</p>
                </div>
            `;
        }
    }
    
    addMessage(content, type = 'assistant') {
        const message = {
            id: Date.now(),
            content: content,
            type: type,
            timestamp: new Date()
        };
        
        this.messages.push(message);
        this.renderMessage(message);
    }
    
    renderMessage(message) {
        const container = document.querySelector(this.messagesContainer);
        if (!container) return;
        
        if (this.messages.length === 1) {
            container.innerHTML = '';
        }
        
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${message.type}`;
        messageEl.innerHTML = `
            <div class="message-content">
                ${this.sanitizeHtml(message.content)}
            </div>
            <div class="message-timestamp">
                ${this.formatTime(message.timestamp)}
            </div>
        `;
        
        container.appendChild(messageEl);
        container.scrollTop = container.scrollHeight;
    }
    
    sendMessage() {
        const input = document.querySelector(this.inputElement);
        if (!input || !input.value.trim()) return;
        
        const message = input.value;
        this.addMessage(message, 'user');
        input.value = '';
        
        // Trigger send event for external handler
        this.dispatchEvent('messageSent', { message });
    }
    
    sanitizeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }
    
    formatTime(date) {
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }
    
    clear() {
        this.messages = [];
        this.renderEmptyState();
    }
}

// ===== Image Module =====
class ImageModule {
    constructor(options = {}) {
        this.container = options.container || '#image-panel';
        this.form = options.form || '#imageForm';
        this.resultContainer = options.resultContainer || '#imageResult';
        this.generateButton = options.generateButton || '.image-generate-btn';
        
        this.isLoading = false;
        this.currentImage = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadFormState();
    }
    
    setupEventListeners() {
        const form = document.querySelector(this.form);
        const generateBtn = document.querySelector(this.generateButton);
        
        if (generateBtn) {
            generateBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.generateImage();
            });
        }
        
        if (form) {
            form.addEventListener('change', () => this.saveFormState());
        }
    }
    
    getFormData() {
        const form = document.querySelector(this.form);
        if (!form) return null;
        
        return {
            positivePrompt: document.querySelector('#positivePrompt')?.value || '',
            negativePrompt: document.querySelector('#negativePrompt')?.value || '',
            width: parseInt(document.querySelector('#imageWidth')?.value) || 608,
            height: parseInt(document.querySelector('#imageHeight')?.value) || 1328,
            steps: parseInt(document.querySelector('#imageSteps')?.value) || 12,
            cfg: parseFloat(document.querySelector('#imageCfg')?.value) || 1.0,
            seed: document.querySelector('#imageSeed')?.value || ''
        };
    }
    
    validateForm() {
        const data = this.getFormData();
        
        if (!data.positivePrompt.trim()) {
            alert('請輸入正向提示詞');
            return false;
        }
        
        if (data.width < 256 || data.width > 2048) {
            alert('寬度必須在 256-2048 之間');
            return false;
        }
        
        if (data.height < 256 || data.height > 2048) {
            alert('高度必須在 256-2048 之間');
            return false;
        }
        
        if (data.steps < 1 || data.steps > 100) {
            alert('Steps 必須在 1-100 之間');
            return false;
        }
        
        if (data.cfg < 0.1 || data.cfg > 30) {
            alert('CFG 必須在 0.1-30 之間');
            return false;
        }
        
        return true;
    }
    
    async generateImage() {
        if (this.isLoading) return;
        if (!this.validateForm()) return;
        
        this.isLoading = true;
        this.setButtonState(true);
        this.showLoading();
        
        try {
            const data = this.getFormData();
            
            // Trigger generate event for external handler
            this.dispatchEvent('generateImage', { data });
            
        } catch (error) {
            console.error('Error generating image:', error);
            this.showError('生成圖片失敗: ' + error.message);
        } finally {
            this.isLoading = false;
            this.setButtonState(false);
        }
    }
    
    showLoading() {
        const resultContainer = document.querySelector(this.resultContainer);
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="image-empty-state">
                    <div class="loading-spinner"></div>
                    <p style="margin-top: 1rem;">生成中...</p>
                </div>
            `;
        }
    }
    
    showImage(imagePath) {
        const resultContainer = document.querySelector(this.resultContainer);
        if (resultContainer) {
            resultContainer.innerHTML = `
                <img src="${imagePath}" alt="生成的圖片">
            `;
            this.currentImage = imagePath;
            this.saveFormState();
        }
    }
    
    showError(message) {
        const resultContainer = document.querySelector(this.resultContainer);
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="image-empty-state">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }
    
    setButtonState(disabled) {
        const btn = document.querySelector(this.generateButton);
        if (btn) {
            btn.disabled = disabled;
            btn.innerHTML = disabled 
                ? '<i class="bi bi-hourglass-split"></i>生成中...'
                : '<i class="bi bi-magic"></i>生成圖片';
        }
    }
    
    saveFormState() {
        const data = this.getFormData();
        localStorage.setItem('imageFormState', JSON.stringify(data));
    }
    
    loadFormState() {
        const saved = localStorage.getItem('imageFormState');
        if (!saved) return;
        
        try {
            const data = JSON.parse(saved);
            if (data.positivePrompt) document.querySelector('#positivePrompt').value = data.positivePrompt;
            if (data.negativePrompt) document.querySelector('#negativePrompt').value = data.negativePrompt;
            if (data.width) document.querySelector('#imageWidth').value = data.width;
            if (data.height) document.querySelector('#imageHeight').value = data.height;
            if (data.steps) document.querySelector('#imageSteps').value = data.steps;
            if (data.cfg) document.querySelector('#imageCfg').value = data.cfg;
        } catch (error) {
            console.error('Error loading form state:', error);
        }
    }
    
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }
    
    reset() {
        const form = document.querySelector(this.form);
        if (form) form.reset();
        this.currentImage = null;
    }
}

// ===== Module Registry =====
const ModuleRegistry = {
    chatModule: null,
    imageModule: null,
    
    initChat(options) {
        this.chatModule = new ChatModule(options);
        return this.chatModule;
    },
    
    initImage(options) {
        this.imageModule = new ImageModule(options);
        return this.imageModule;
    },
    
    getChat() {
        return this.chatModule;
    },
    
    getImage() {
        return this.imageModule;
    }
};

// ===== Global Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modules if DOM elements exist
    if (document.querySelector('#chat-panel')) {
        ModuleRegistry.initChat({
            container: '#chat-panel',
            messagesContainer: '#chatMessages',
            inputElement: '#messageInput',
            sendButton: '.chat-send-btn'
        });
    }
    
    if (document.querySelector('#image-panel')) {
        ModuleRegistry.initImage({
            container: '#image-panel',
            form: '#imageForm',
            resultContainer: '#imageResult',
            generateButton: '.image-generate-btn'
        });
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatModule, ImageModule, ModuleRegistry };
}
