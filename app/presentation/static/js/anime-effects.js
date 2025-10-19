// ComfyUI AI Chat - 增強版動畫系統
// 柔和動漫風格交互效果

class AnimeEffects {
    constructor() {
        this.init();
    }

    init() {
        this.addButtonRippleEffect();
        this.addMessageAnimations();
        this.addTypingEffect();
        this.addSparkleEffect();
    }

    // 按鈕波紋效果
    addButtonRippleEffect() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn');
            if (!button) return;

            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.5);
                left: ${x}px;
                top: ${y}px;
                pointer-events: none;
                animation: ripple 0.6s ease-out;
            `;

            const style = document.createElement('style');
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(2);
                        opacity: 0;
                    }
                }
            `;
            
            if (!document.querySelector('#ripple-animation')) {
                style.id = 'ripple-animation';
                document.head.appendChild(style);
            }

            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    }

    // 消息進入動畫
    addMessageAnimations() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1 && node.classList.contains('message')) {
                        node.style.opacity = '0';
                        node.style.transform = 'translateY(20px)';
                        
                        requestAnimationFrame(() => {
                            node.style.transition = 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)';
                            node.style.opacity = '1';
                            node.style.transform = 'translateY(0)';
                        });
                    }
                });
            });
        });

        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            observer.observe(chatMessages, { childList: true });
        }
    }

    // 打字機效果（AI 回覆）
    addTypingEffect() {
        // 這個功能可以在 app.js 的 displayMessage 中調用
        window.typeWriterEffect = (element, text, speed = 30) => {
            let index = 0;
            element.innerHTML = '';
            
            const type = () => {
                if (index < text.length) {
                    element.innerHTML += text.charAt(index);
                    index++;
                    setTimeout(type, speed);
                } else {
                    // 完成後渲染 Markdown
                    if (typeof marked !== 'undefined') {
                        element.innerHTML = marked.parse(text);
                    }
                }
            };
            
            type();
        };
    }

    // 閃爍特效
    addSparkleEffect() {
        const createSparkle = (x, y) => {
            const sparkle = document.createElement('div');
            sparkle.className = 'sparkle';
            sparkle.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: linear-gradient(45deg, #ff6b9d, #c471ed);
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                left: ${x}px;
                top: ${y}px;
                animation: sparkleFloat 1s ease-out forwards;
            `;

            const style = document.createElement('style');
            style.textContent = `
                @keyframes sparkleFloat {
                    0% {
                        transform: translateY(0) scale(1);
                        opacity: 1;
                    }
                    100% {
                        transform: translateY(-50px) scale(0);
                        opacity: 0;
                    }
                }
            `;
            
            if (!document.querySelector('#sparkle-animation')) {
                style.id = 'sparkle-animation';
                document.head.appendChild(style);
            }

            document.body.appendChild(sparkle);
            setTimeout(() => sparkle.remove(), 1000);
        };

        // 為特定按鈕添加閃爍效果
        document.addEventListener('click', (e) => {
            const button = e.target.closest('#sendMessageBtn, #generateImageBtn, #createSessionBtn');
            if (button) {
                const rect = button.getBoundingClientRect();
                for (let i = 0; i < 5; i++) {
                    setTimeout(() => {
                        const x = rect.left + Math.random() * rect.width;
                        const y = rect.top + Math.random() * rect.height;
                        createSparkle(x, y);
                    }, i * 100);
                }
            }
        });
    }
}

// 平滑滾動
class SmoothScroll {
    constructor(container) {
        this.container = container;
    }

    scrollToBottom(duration = 300) {
        if (!this.container) return;
        
        const start = this.container.scrollTop;
        const end = this.container.scrollHeight - this.container.clientHeight;
        const change = end - start;
        
        if (change === 0) return;
        
        const startTime = performance.now();

        const animateScroll = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = this.easeOutCubic(progress);
            
            this.container.scrollTop = start + change * easeProgress;

            if (progress < 1) {
                requestAnimationFrame(animateScroll);
            }
        };

        requestAnimationFrame(animateScroll);
    }

    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
}

// 導出 SmoothScroll 類
window.SmoothScroll = SmoothScroll;

// 圖片預覽增強
class ImagePreview {
    constructor() {
        this.init();
    }

    init() {
        this.createLightbox();
        this.attachEventListeners();
    }

    createLightbox() {
        const lightbox = document.createElement('div');
        lightbox.id = 'imageLightbox';
        lightbox.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 10000;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        `;

        lightbox.innerHTML = `
            <div style="position: relative; max-width: 90%; max-height: 90%;">
                <img id="lightboxImage" style="max-width: 100%; max-height: 90vh; box-shadow: 0 0 50px rgba(255, 107, 157, 0.5);">
                <button id="closeLightbox" style="
                    position: absolute;
                    top: -40px;
                    right: -40px;
                    background: linear-gradient(135deg, #ff6b9d, #c471ed);
                    border: none;
                    color: white;
                    width: 40px;
                    height: 40px;
                    cursor: pointer;
                    font-size: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.3s;
                ">×</button>
            </div>
        `;

        document.body.appendChild(lightbox);

        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                this.closeLightbox();
            }
        });

        document.getElementById('closeLightbox').addEventListener('click', () => {
            this.closeLightbox();
        });
    }

    attachEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'IMG' && e.target.closest('.image-result-container')) {
                this.openLightbox(e.target.src);
            }
        });
    }

    openLightbox(src) {
        const lightbox = document.getElementById('imageLightbox');
        const img = document.getElementById('lightboxImage');
        img.src = src;
        lightbox.style.display = 'flex';
        
        // 動畫進入
        lightbox.style.opacity = '0';
        requestAnimationFrame(() => {
            lightbox.style.transition = 'opacity 0.3s';
            lightbox.style.opacity = '1';
        });
    }

    closeLightbox() {
        const lightbox = document.getElementById('imageLightbox');
        lightbox.style.opacity = '0';
        setTimeout(() => {
            lightbox.style.display = 'none';
        }, 300);
    }
}

// 載入進度指示器
class LoadingIndicator {
    constructor() {
        this.create();
    }

    create() {
        const loader = document.createElement('div');
        loader.id = 'customLoader';
        loader.style.cssText = `
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 9999;
        `;

        loader.innerHTML = `
            <div style="text-align: center;">
                <div class="anime-loader"></div>
                <p style="color: #ff6b9d; margin-top: 20px; font-weight: 600;">生成中...</p>
            </div>
        `;

        const style = document.createElement('style');
        style.textContent = `
            .anime-loader {
                width: 60px;
                height: 60px;
                border: 4px solid rgba(255, 107, 157, 0.2);
                border-top: 4px solid #ff6b9d;
                border-right: 4px solid #c471ed;
                border-radius: 50%;
                animation: animeLoaderSpin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
            }

            @keyframes animeLoaderSpin {
                0% { transform: rotate(0deg) scale(1); }
                50% { transform: rotate(180deg) scale(1.2); }
                100% { transform: rotate(360deg) scale(1); }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(loader);
    }

    show() {
        const loader = document.getElementById('customLoader');
        loader.style.display = 'block';
    }

    hide() {
        const loader = document.getElementById('customLoader');
        loader.style.display = 'none';
    }
}

// 初始化所有效果
document.addEventListener('DOMContentLoaded', () => {
    new AnimeEffects();
    new ImagePreview();
    window.loadingIndicator = new LoadingIndicator();
    
    // 為聊天區域添加平滑滾動
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        window.chatScroller = new SmoothScroll(chatMessages);
    }
    
    console.log('🎀 動漫風格系統已載入！');
});

// 工具函數：顯示通知
window.showNotification = (message, type = 'info') => {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'linear-gradient(135deg, #ff6b9d, #c471ed)' : '#fff'};
        color: ${type === 'success' ? '#fff' : '#5a3d52'};
        padding: 16px 24px;
        border-left: 4px solid ${type === 'success' ? '#ff4081' : '#ff6b9d'};
        box-shadow: 0 4px 16px rgba(255, 107, 157, 0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        max-width: 300px;
        word-wrap: break-word;
    `;

    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    if (!document.querySelector('#notification-animation')) {
        style.id = 'notification-animation';
        document.head.appendChild(style);
    }

    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
};

// 導出給 app.js 使用
window.animeUtils = {
    showNotification: window.showNotification,
    loadingIndicator: window.loadingIndicator,
    chatScroller: window.chatScroller,
    typeWriterEffect: window.typeWriterEffect
};
