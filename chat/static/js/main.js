// 全局状态
let currentConversationId = generateUUID();
let isGenerating = false;
let currentAgent = null;
let currentModel = 'deepseek-chat';
let currentSystemPrompt = '';
let agents = [];
let currentUser = null;
let currentTheme = 'dark';

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    mainContent: document.getElementById('mainContent'),
    newChatBtn: document.getElementById('newChatBtn'),
    conversationsList: document.getElementById('conversationsList'),
    chatContainer: document.getElementById('chatContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    agentSelect: document.getElementById('agentSelect'),
    clearBtn: document.getElementById('clearBtn'),
    settingsBtn: document.getElementById('settingsBtn'),
    username: document.getElementById('username'),
    logoutBtn: document.getElementById('logoutBtn'),
    settingsModal: document.getElementById('settingsModal'),
    closeSettings: document.getElementById('closeSettings'),
    moreActionsBtn: document.getElementById('moreActionsBtn'),
    moreActionsMenu: document.getElementById('moreActionsMenu'),
    dropdown: document.getElementById('moreActionsDropdown')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    initializeEventListeners();
    loadAgentsForSelect();
    if (document.getElementById('conversationsList')) {
        loadConversations();
    }
    autoResizeTextarea();
    initSidebar();
});

// 初始化侧边栏状态
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth > 768 && sidebar) {
        sidebar.classList.add('active');
    }
}

// 加载用户信息
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            if (elements.username) {
                elements.username.textContent = user.username;
            }
            currentTheme = user.theme || 'dark';
            applyTheme(currentTheme);
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 应用主题
function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
    
    // 更新主题选项的选中状态
    document.querySelectorAll('.theme-option').forEach(option => {
        if (option.dataset.theme === theme) {
            option.classList.add('active');
        } else {
            option.classList.remove('active');
        }
    });
}

// 加载Agent列表
async function loadAgentsForSelect() {
    try {
        const response = await fetch('/api/agents', {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            agents = data.agents || [];
            
            const optionsHtml = agents.map(agent => 
                `<option value="${agent.id}">${escapeHtml(agent.name)}</option>`
            ).join('');
            
            if (elements.agentSelect) {
                elements.agentSelect.innerHTML = `<option value="">默认模式</option>${optionsHtml}`;
            }
        }
    } catch (error) {
        console.error('加载Agent列表失败:', error);
    }
}

// 初始化事件监听器
function initializeEventListeners() {
    // 侧边栏切换
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // 移动端点击主内容区关闭侧边栏
    elements.mainContent?.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            e.target.closest('.sidebar-toggle') === null &&
            elements.sidebar?.classList.contains('active')) {
            elements.sidebar.classList.remove('active');
        }
    });

    // 移动端左滑关闭侧边栏
    let touchStartX = 0;
    let touchEndX = 0;
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    document.addEventListener('touchend', (e) => {
        if (window.innerWidth <= 768) {
            touchEndX = e.changedTouches[0].screenX;
            if (touchStartX - touchEndX > 50 && elements.sidebar?.classList.contains('active')) {
                elements.sidebar.classList.remove('active');
            }
        }
    });

    // 窗口大小变化时更新侧边栏状态
    window.addEventListener('resize', () => {
        const sidebar = document.getElementById('sidebar');
        if (window.innerWidth > 768 && sidebar) {
            sidebar.classList.add('active');
        }
    });

    // 新对话按钮
    elements.newChatBtn?.addEventListener('click', createNewConversation);

    // 发送消息
    elements.sendBtn?.addEventListener('click', sendMessage);
    
    // 输入框事件
    elements.messageInput?.addEventListener('input', () => {
        elements.sendBtn.disabled = !elements.messageInput.value.trim();
        autoResizeTextarea();
    });

    elements.messageInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isGenerating && elements.messageInput.value.trim()) {
                sendMessage();
            }
        }
    });

    // Agent选择
    elements.agentSelect?.addEventListener('change', async (e) => {
        const agentId = e.target.value;
        if (agentId) {
            const agent = agents.find(a => a.id === parseInt(agentId));
            if (agent) {
                currentAgent = agent;
                currentModel = agent.model || 'deepseek-chat';
                currentSystemPrompt = agent.system_prompt || '';
                console.log('[Agent选择] agent:', agent.name, 'system_prompt长度:', agent.system_prompt ? agent.system_prompt.length : 0, 'prompt_id:', agent.prompt_id);
            }
        } else {
            currentAgent = null;
            currentModel = 'deepseek-chat';
            currentSystemPrompt = '';
            console.log('[Agent选择] 切换到默认模式，无agent');
        }
    });

    // 清空对话
    elements.clearBtn?.addEventListener('click', clearCurrentConversation);

    // 退出登录
    elements.logoutBtn?.addEventListener('click', logout);

    // 设置按钮
    elements.settingsBtn?.addEventListener('click', () => {
        elements.settingsModal?.classList.add('active');
    });

    // 关闭设置
    elements.closeSettings?.addEventListener('click', () => {
        elements.settingsModal?.classList.remove('active');
    });

    // 点击模态框背景关闭
    elements.settingsModal?.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) {
            elements.settingsModal.classList.remove('active');
        }
    });

    // 更多操作下拉菜单
    elements.moreActionsBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.moreActionsMenu?.classList.toggle('active');
    });

    // 点击下拉菜单项
    document.getElementById('openTools')?.addEventListener('click', () => {
        window.location.href = '/tools';
    });

    // 打开超级管理员
    document.getElementById('openAdmin')?.addEventListener('click', () => {
        window.location.href = '/admin';
    });

    // 打开定时任务
    document.getElementById('openSchedules')?.addEventListener('click', () => {
        window.location.href = '/schedules';
    });

    // 打开工作流管理
    document.getElementById('openWorkflows')?.addEventListener('click', () => {
        window.location.href = '/workflows';
    });

    // 打开提示词管理
    document.getElementById('openPrompts')?.addEventListener('click', () => {
        window.location.href = '/prompts';
    });

    // 打开Agent管理
    document.getElementById('openAgents')?.addEventListener('click', () => {
        window.location.href = '/agents';
    });

    // 点击其他地方关闭下拉菜单
    document.addEventListener('click', () => {
        elements.moreActionsMenu?.classList.remove('active');
    });

    // 主题选择
    document.querySelectorAll('.theme-option').forEach(option => {
        option.addEventListener('click', async () => {
            const theme = option.dataset.theme;
            await updateTheme(theme);
        });
    });

    // 示例提示词
    document.querySelectorAll('.example-prompt').forEach(prompt => {
        prompt.addEventListener('click', () => {
            const text = prompt.dataset.prompt;
            elements.messageInput.value = text;
            elements.sendBtn.disabled = false;
            elements.messageInput.focus();
        });
    });

    // 设置导航高亮
    highlightCurrentNav();
}

// 退出登录
async function logout() {
    if (!confirm('确定要退出登录吗?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('退出登录失败:', error);
    }
}

// 更新主题
async function updateTheme(theme) {
    try {
        const response = await fetch('/api/user/theme', {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ theme })
        });
        
        if (response.ok) {
            applyTheme(theme);
        }
    } catch (error) {
        console.error('更新主题失败:', error);
    }
}

// 生成 UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 创建新对话
function createNewConversation() {
    currentConversationId = generateUUID();
    elements.messagesContainer.innerHTML = '';
    elements.welcomeScreen.style.display = 'flex';
    elements.messageInput.value = '';
    elements.sendBtn.disabled = true;
    
    // 更新对话列表选中状态
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
}

// 发送消息
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || isGenerating) return;

    // 隐藏欢迎屏幕
    elements.welcomeScreen.style.display = 'none';

    // 添加用户消息
    appendMessage('user', message);

    // 清空输入框
    elements.messageInput.value = '';
    elements.sendBtn.disabled = true;
    autoResizeTextarea();

    // 添加助手消息占位符
    const assistantMessageId = appendMessage('assistant', '', true);
    
    isGenerating = true;
    elements.sendBtn.innerHTML = '<i class="fas fa-stop"></i>';

    try {
        const requestBody = {
            message: message,
            conversation_id: currentConversationId,
            model: currentModel
        };
        
        if (currentAgent) {
            requestBody.agent_id = currentAgent.id;
            requestBody.system_prompt = currentSystemPrompt;
            console.log('[发送消息] 使用agent:', currentAgent.name, 'system_prompt长度:', currentSystemPrompt.length);
        }
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error('请求失败');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.error) {
                            showError(data.error);
                            break;
                        }
                        
                        if (data.content) {
                            fullResponse += data.content;
                            updateMessage(assistantMessageId, fullResponse);
                        }
                        
                        if (data.thinking) {
                            updateThinking(assistantMessageId, data.thinking);
                        }
                        
                        if (data.done) {
                            removeTypingIndicator(assistantMessageId);
                        }
                    } catch (e) {
                        console.error('解析响应错误:', e);
                    }
                }
            }
        }

        // 更新对话列表
        await loadConversations();

    } catch (error) {
        console.error('发送消息错误:', error);
        showError('发送消息失败,请重试');
        removeMessage(assistantMessageId);
    } finally {
        isGenerating = false;
        elements.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    }
}

// 添加消息到界面
function appendMessage(role, content, isTyping = false) {
    const messageId = generateUUID();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.dataset.messageId = messageId;

    const avatar = role === 'user' 
        ? '<i class="fas fa-user"></i>' 
        : '<i class="fas fa-robot"></i>';
    
    const author = role === 'user' ? (currentUser?.username || '你') : 'AI 助手';

    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <div class="message-author">${author}</div>
        </div>
        <div class="message-content">
            ${isTyping ? '<div class="typing-indicator"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>' : formatMessage(content)}
        </div>
    `;

    elements.messagesContainer.appendChild(messageDiv);
    scrollToBottom();

    return messageId;
}

// 更新消息内容
function updateMessage(messageId, content) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        const contentDiv = messageDiv.querySelector('.message-content');
        contentDiv.innerHTML = formatMessage(content);
        scrollToBottom();
    }
}

// 移除输入指示器
function removeTypingIndicator(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        const typingIndicator = messageDiv.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// 更新思考过程
function updateThinking(messageId, thinking) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) return;
    
    let thinkingDiv = messageDiv.querySelector('.thinking-process');
    if (!thinkingDiv) {
        thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'thinking-process';
        messageDiv.insertBefore(thinkingDiv, messageDiv.querySelector('.message-content'));
        messageDiv.classList.add('has-thinking');
    }
    
    if (thinking.type === 'calling_function') {
        const functionItem = document.createElement('div');
        functionItem.className = 'thinking-item calling';
        functionItem.innerHTML = `
            <div class="thinking-header">
                <i class="fas fa-cog fa-spin"></i>
                <span>调用函数: ${escapeHtml(thinking.function)}</span>
            </div>
            <div class="thinking-args">${escapeHtml(JSON.stringify(thinking.args, null, 2))}</div>
        `;
        thinkingDiv.appendChild(functionItem);
    } else if (thinking.type === 'function_result') {
        const functionItem = document.createElement('div');
        functionItem.className = 'thinking-item result';
        functionItem.innerHTML = `
            <div class="thinking-header">
                <i class="fas fa-check-circle"></i>
                <span>函数结果: ${escapeHtml(thinking.function)}</span>
            </div>
            <div class="thinking-result">${escapeHtml(JSON.stringify(thinking.result, null, 2))}</div>
        `;
        thinkingDiv.appendChild(functionItem);
    }
    
    scrollToBottom();
}

// 移除消息
function removeMessage(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (messageDiv) {
        messageDiv.remove();
    }
}

// 格式化消息内容(支持 Markdown)
function formatMessage(content) {
    if (!content) return '';

    const renderer = new marked.Renderer();
    
    renderer.code = function(code, language) {
        const validLang = language || 'plaintext';
        const highlighted = window.Prism && window.Prism.languages[validLang] 
            ? window.Prism.highlight(code, window.Prism.languages[validLang], validLang)
            : escapeHtml(code);
        return `<pre><code class="language-${validLang}">${highlighted}</code></pre>`;
    };

    marked.setOptions({
        renderer: renderer,
        breaks: true,
        gfm: true
    });

    return marked.parse(content);
}

// 加载对话列表
async function loadConversations() {
    try {
        const response = await fetch('/api/conversations', {
            credentials: 'same-origin'
        });
        const data = await response.json();
        
        elements.conversationsList.innerHTML = '';
        
        data.conversations.forEach(conv => {
            const item = document.createElement('div');
            item.className = 'conversation-item';
            if (conv.id === currentConversationId) {
                item.classList.add('active');
            }
            
            item.innerHTML = `
                <div class="conversation-item-content">
                    <div class="conversation-title">${escapeHtml(conv.title)}</div>
                    <div class="conversation-time">${formatTime(conv.updated_at)}</div>
                </div>
                <button class="conversation-delete" onclick="deleteConversation('${conv.id}', event)">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            item.addEventListener('click', () => loadConversation(conv.id));
            elements.conversationsList.appendChild(item);
        });
    } catch (error) {
        console.error('加载对话列表失败:', error);
    }
}

// 加载特定对话
async function loadConversation(conversationId) {
    try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
            credentials: 'same-origin'
        });
        const data = await response.json();
        
        currentConversationId = conversationId;
        elements.messagesContainer.innerHTML = '';
        elements.welcomeScreen.style.display = 'none';
        
        data.messages.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'assistant') {
                appendMessage(msg.role, msg.content);
            }
        });
        
        // 更新选中状态
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        event?.target.closest('.conversation-item')?.classList.add('active');
        
        // 移动端点击对话后关闭侧边栏
        if (window.innerWidth <= 768) {
            elements.sidebar?.classList.remove('active');
        }
        
    } catch (error) {
        console.error('加载对话失败:', error);
        showError('加载对话失败');
    }
}

// 删除对话
async function deleteConversation(conversationId, event) {
    event.stopPropagation();
    
    if (!confirm('确定要删除这个对话吗?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/conversations/${conversationId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            if (conversationId === currentConversationId) {
                createNewConversation();
            }
            await loadConversations();
        }
    } catch (error) {
        console.error('删除对话失败:', error);
        showError('删除对话失败');
    }
}

// 清空当前对话
function clearCurrentConversation() {
    if (confirm('确定要清空当前对话吗?')) {
        elements.messagesContainer.innerHTML = '';
        elements.welcomeScreen.style.display = 'flex';
        deleteConversation(currentConversationId, { stopPropagation: () => {} });
    }
}

// 自动调整文本框高度
function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = elements.messageInput.scrollHeight + 'px';
}

// 滚动到底部
function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

// 显示错误消息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${escapeHtml(message)}`;
    
    elements.messagesContainer.appendChild(errorDiv);
    scrollToBottom();
    
    setTimeout(() => errorDiv.remove(), 5000);
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 格式化时间
function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;

    return date.toLocaleDateString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric'
    });
}

// 设置导航高亮
function highlightCurrentNav() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

