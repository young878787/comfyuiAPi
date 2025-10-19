/**
 * 代碼塊增強系統
 * 為 Markdown 渲染的代碼塊添加複製按鈕和橫向滾動
 */

class CodeBlockEnhancer {
    constructor() {
        this.init();
    }

    init() {
        // 監聽新消息的添加
        this.observeMessages();
        // 處理現有的代碼塊
        this.enhanceAllCodeBlocks();
    }

    observeMessages() {
        const chatContainer = document.getElementById('chatMessages');
        if (!chatContainer) return;

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('message')) {
                        this.enhanceCodeBlocksInElement(node);
                    }
                });
            });
        });

        observer.observe(chatContainer, {
            childList: true,
            subtree: true
        });
    }

    enhanceAllCodeBlocks() {
        const messages = document.querySelectorAll('.message-content');
        messages.forEach(message => {
            this.enhanceCodeBlocksInElement(message);
        });
    }

    enhanceCodeBlocksInElement(element) {
        const preElements = element.querySelectorAll('pre');
        preElements.forEach(pre => {
            // 避免重複處理
            if (pre.parentElement.classList.contains('code-block-wrapper')) {
                return;
            }

            this.wrapCodeBlock(pre);
        });
    }

    wrapCodeBlock(pre) {
        const codeElement = pre.querySelector('code');
        if (!codeElement) return;

        // 獲取語言類型
        const className = codeElement.className || '';
        const languageMatch = className.match(/language-(\w+)/);
        const language = languageMatch ? languageMatch[1] : 'text';

        // 獲取代碼內容
        const codeText = codeElement.textContent;

        // 創建包裝容器
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';

        // 創建頭部
        const header = document.createElement('div');
        header.className = 'code-block-header';

        // 語言標籤
        const languageLabel = document.createElement('span');
        languageLabel.className = 'code-block-language';
        languageLabel.textContent = language;

        // 複製按鈕
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i><span>複製</span>';
        copyBtn.onclick = () => this.copyCode(codeText, copyBtn);

        header.appendChild(languageLabel);
        header.appendChild(copyBtn);

        // 替換原始 pre 元素
        const newPre = pre.cloneNode(true);
        
        wrapper.appendChild(header);
        wrapper.appendChild(newPre);

        pre.parentNode.replaceChild(wrapper, pre);
    }

    async copyCode(text, button) {
        try {
            await navigator.clipboard.writeText(text);
            
            // 更新按鈕狀態
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check-lg"></i><span>已複製</span>';
            button.classList.add('copied');

            // 顯示通知
            if (window.showNotification) {
                window.showNotification('代碼已複製到剪貼板', 'success');
            }

            // 2秒後恢復按鈕
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);

        } catch (err) {
            console.error('Failed to copy code:', err);
            
            // 備用方案：使用舊方法
            this.copyCodeFallback(text, button);
        }
    }

    copyCodeFallback(text, button) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand('copy');
            
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="bi bi-check-lg"></i><span>已複製</span>';
            button.classList.add('copied');

            if (window.showNotification) {
                window.showNotification('代碼已複製到剪貼板', 'success');
            }

            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('copied');
            }, 2000);

        } catch (err) {
            console.error('Fallback copy failed:', err);
            if (window.showNotification) {
                window.showNotification('複製失敗，請手動選擇複製', 'error');
            }
        } finally {
            document.body.removeChild(textarea);
        }
    }
}

/**
 * 提示詞檢測和格式化
 * 自動識別 AI 回覆中的提示詞並添加特殊樣式
 */
class PromptDetector {
    constructor() {
        this.promptKeywords = [
            '正向提示詞', 'Positive Prompt', 'positive prompt',
            '負向提示詞', 'Negative Prompt', 'negative prompt',
            '提示詞', 'Prompt', 'prompt'
        ];
    }

    detectAndFormat(messageElement) {
        const content = messageElement.querySelector('.message-content');
        if (!content) return;

        // 查找包含提示詞的段落或代碼塊
        const paragraphs = content.querySelectorAll('p, li');
        
        paragraphs.forEach(p => {
            const text = p.textContent;
            
            // 檢查是否包含提示詞關鍵字
            const hasPromptKeyword = this.promptKeywords.some(keyword => 
                text.includes(keyword)
            );

            if (hasPromptKeyword) {
                // 提取提示詞內容（假設在冒號或換行後）
                const colonIndex = text.indexOf('：') !== -1 ? text.indexOf('：') : text.indexOf(':');
                
                if (colonIndex !== -1) {
                    const promptText = text.substring(colonIndex + 1).trim();
                    
                    if (promptText.length > 10) { // 確保是實際的提示詞內容
                        this.createPromptBlock(p, promptText);
                    }
                }
            }
        });
    }

    createPromptBlock(parentElement, promptText) {
        // 創建提示詞區塊
        const promptBlock = document.createElement('div');
        promptBlock.className = 'prompt-block';
        
        // 創建文字內容容器（確保不換行）
        const textContent = document.createElement('span');
        textContent.textContent = promptText;
        textContent.style.whiteSpace = 'nowrap';
        textContent.style.display = 'inline-block';
        
        // 添加複製按鈕
        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        // 移除內聯樣式，讓 CSS 控制定位
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i><span>複製</span>';
        copyBtn.onclick = async () => {
            try {
                await navigator.clipboard.writeText(promptText);
                copyBtn.innerHTML = '<i class="bi bi-check-lg"></i><span>已複製</span>';
                copyBtn.classList.add('copied');

                if (window.showNotification) {
                    window.showNotification('提示詞已複製', 'success');
                }

                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="bi bi-clipboard"></i><span>複製</span>';
                    copyBtn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy prompt:', err);
            }
        };

        // 先添加複製按鈕，再添加文字內容
        promptBlock.appendChild(copyBtn);
        promptBlock.appendChild(textContent);

        // 在父元素後插入
        parentElement.parentNode.insertBefore(promptBlock, parentElement.nextSibling);
    }
}

// 初始化增強功能
document.addEventListener('DOMContentLoaded', () => {
    // 延遲初始化，確保其他腳本已載入
    setTimeout(() => {
        window.codeBlockEnhancer = new CodeBlockEnhancer();
        window.promptDetector = new PromptDetector();
        
        // 為現有消息應用提示詞檢測
        document.querySelectorAll('.message-assistant').forEach(msg => {
            window.promptDetector.detectAndFormat(msg);
        });
        
        console.log('✨ 代碼塊增強系統已啟動');
    }, 500);
});

// 導出給 app.js 使用
window.enhanceNewMessage = function(messageElement) {
    if (window.codeBlockEnhancer) {
        window.codeBlockEnhancer.enhanceCodeBlocksInElement(messageElement);
    }
    if (window.promptDetector && messageElement.classList.contains('message-assistant')) {
        window.promptDetector.detectAndFormat(messageElement);
    }
};
