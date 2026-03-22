// 全局状态
let currentConversationId = generateUUID();
let isGenerating = false;
let currentAgent = null;
let currentModel = 'deepseek-chat';
let currentSystemPrompt = '';
let agents = [];
let currentUser = null;
let currentTheme = 'dark';
let currentPage = 1;
let hasMoreConversations = false;
let isRecording = false;
let recognition = null;
let mediaRecorder = null;
let audioChunks = [];

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    mainContent: document.querySelector('.main-content'),
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
    dropdown: document.getElementById('moreActionsDropdown'),
    loadMoreBtn: document.getElementById('loadMoreBtn'),
    loadMoreContainer: document.getElementById('loadMoreContainer'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    voiceBtn: document.getElementById('voiceBtn')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    applyThemeFromCache();
    detectDevice();
    loadUserInfo();
    initializeEventListeners();
    loadAgentsForSelect();
    loadPresetInputs();
    initPresetEventListeners();
    if (document.getElementById('conversationsList')) {
        loadConversations();
    }
    autoResizeTextarea();
    initSidebar();
});

// 从 localStorage 应用主题色(早期加载，避免闪烁)
function applyThemeFromCache() {
    const cachedTheme = localStorage.getItem('user_theme');
    if (cachedTheme) {
        document.body.setAttribute('data-theme', cachedTheme);
        currentTheme = cachedTheme;
    }
}

// 检测设备类型
function detectDevice() {
    const isMobile = window.innerWidth < 768 || 
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.body.classList.add('is-mobile-device');
    } else {
        document.body.classList.remove('is-mobile-device');
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth < 768 || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            document.body.classList.add('is-mobile-device');
        } else {
            document.body.classList.remove('is-mobile-device');
        }
    });
}

// 初始化侧边栏状态（默认收起，与其他管理页面保持一致）
function initSidebar() {
    // 所有页面的侧边栏默认状态统一为收起
    // 用户可以通过点击切换按钮来展开/收起侧边栏
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
            const serverTheme = user.theme || 'dark';
            const cachedTheme = localStorage.getItem('user_theme');
            if (cachedTheme !== serverTheme) {
                localStorage.setItem('user_theme', serverTheme);
                localStorage.setItem('theme_timestamp', Date.now().toString());
                const appliedTheme = document.body.getAttribute('data-theme');
                if (appliedTheme !== serverTheme) {
                    applyTheme(serverTheme);
                }
            }
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 加载用户个人信息和偏好设置
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const data = await response.json();
            
            // 填充个人信息表单
            const profile = data.profile || {};
            const nicknameEl = document.getElementById('nickname');
            const realNameEl = document.getElementById('realName');
            const genderEl = document.getElementById('gender');
            const ageEl = document.getElementById('age');
            const occupationEl = document.getElementById('occupation');
            const bioEl = document.getElementById('bio');
            
            if (nicknameEl) nicknameEl.value = profile.nickname || '';
            if (realNameEl) realNameEl.value = profile.real_name || '';
            if (genderEl) genderEl.value = profile.gender || 'unknown';
            if (ageEl) ageEl.value = profile.age || '';
            if (occupationEl) occupationEl.value = profile.occupation || '';
            if (bioEl) bioEl.value = profile.bio || '';
            
            // 填充偏好设置表单
            const prefs = data.preferences || {};
            const useNicknameEl = document.getElementById('useNickname');
            const rememberContextEl = document.getElementById('rememberContext');
            const personalizedResponsesEl = document.getElementById('personalizedResponses');
            const aiPersonalityEl = document.getElementById('aiPersonality');
            
            if (useNicknameEl) useNicknameEl.checked = prefs.use_nickname === 1;
            if (rememberContextEl) rememberContextEl.checked = prefs.remember_context === 1;
            if (personalizedResponsesEl) personalizedResponsesEl.checked = prefs.personalized_responses === 1;
            if (aiPersonalityEl) aiPersonalityEl.value = prefs.ai_personality || 'friendly';
        }
    } catch (error) {
        console.error('加载用户 profile 失败:', error);
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
    // 禁用双指捏合缩放
    document.addEventListener('gesturestart', (e) => {
        e.preventDefault();
    });
    document.addEventListener('gesturechange', (e) => {
        e.preventDefault();
    });
    document.addEventListener('gestureend', (e) => {
        e.preventDefault();
    });

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
        // 侧边栏状态保持不变，由用户手动控制
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
    elements.settingsBtn?.addEventListener('click', async () => {
        elements.settingsModal?.classList.add('active');
        await loadUserProfile();
        await loadPresetManagement();
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



    // 打开定时任务
    document.getElementById('openSchedules')?.addEventListener('click', () => {
        window.location.href = '/schedules';
    });

    // 打开异步任务
    document.getElementById('openAsyncTasks')?.addEventListener('click', () => {
        window.location.href = '/async_tasks';
    });

    // 打开工作流管理
    document.getElementById('openWorkflows')?.addEventListener('click', () => {
        window.location.href = '/workflows';
    });

    // 打开知识库管理
    document.getElementById('openKnowledge')?.addEventListener('click', () => {
        window.location.href = '/knowledge';
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

    // 保存个人信息
    document.getElementById('saveProfileBtn')?.addEventListener('click', async () => {
        const btn = document.getElementById('saveProfileBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
        
        try {
            const profileData = {
                nickname: document.getElementById('nickname')?.value || '',
                real_name: document.getElementById('realName')?.value || '',
                gender: document.getElementById('gender')?.value || 'unknown',
                age: document.getElementById('age')?.value || null,
                occupation: document.getElementById('occupation')?.value || '',
                bio: document.getElementById('bio')?.value || ''
            };

            const response = await fetch('/api/user/profile', {
                method: 'PUT',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                alert('个人信息保存成功');
            } else {
                const error = await response.json();
                alert('保存失败: ' + (error.error || '未知错误'));
            }
        } catch (error) {
            console.error('保存个人信息失败:', error);
            alert('保存失败，请检查网络连接');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save"></i><span>保存个人信息</span>';
        }
    });

    // 保存偏好设置
    document.getElementById('savePreferencesBtn')?.addEventListener('click', async () => {
        const btn = document.getElementById('savePreferencesBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
        
        try {
            const prefsData = {
                greeting_enabled: true,
                use_nickname: document.getElementById('useNickname')?.checked ?? true,
                remember_context: document.getElementById('rememberContext')?.checked ?? true,
                personalized_responses: document.getElementById('personalizedResponses')?.checked ?? true,
                ai_personality: document.getElementById('aiPersonality')?.value || 'friendly'
            };

            const response = await fetch('/api/user/preferences', {
                method: 'PUT',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(prefsData)
            });

            if (response.ok) {
                alert('偏好设置保存成功');
            } else {
                const error = await response.json();
                alert('保存失败: ' + (error.error || '未知错误'));
            }
        } catch (error) {
            console.error('保存偏好设置失败:', error);
            alert('保存失败，请检查网络连接');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save"></i><span>保存偏好设置</span>';
        }
    });

    // 语音输入
    elements.voiceBtn?.addEventListener('click', toggleVoiceRecognition);

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
            localStorage.removeItem('user_theme');
            localStorage.removeItem('theme_timestamp');
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
            // 同步更新 localStorage
            localStorage.setItem('user_theme', theme);
            localStorage.setItem('theme_timestamp', Date.now().toString());
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
    stopVoiceRecognition();
    currentConversationId = generateUUID();
    elements.messagesContainer.innerHTML = '';
    elements.welcomeScreen.style.display = 'flex';
    elements.messageInput.value = '';
    elements.sendBtn.disabled = true;
    
    // 收起侧边栏（移动端和桌面端）
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.remove('active');
    }
    
    // 更新对话列表选中状态
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
}

// 发送消息
async function sendMessage() {
    stopVoiceRecognition();
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
async function loadConversations(reset = true) {
    try {
        if (reset) {
            currentPage = 1;
            elements.conversationsList.innerHTML = '';
        }
        
        const response = await fetch(`/api/conversations?page=${currentPage}&limit=10`, {
            credentials: 'same-origin'
        });
        const data = await response.json();
        
        hasMoreConversations = data.has_more;
        
        if (elements.loadMoreContainer) {
            elements.loadMoreContainer.style.display = hasMoreConversations ? 'block' : 'none';
        }
        
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

        if (elements.loadMoreContainer) {
            elements.conversationsList.appendChild(elements.loadMoreContainer);
        }
    } catch (error) {
        console.error('加载对话列表失败:', error);
    }
}

// 加载更多对话
async function loadMoreConversations() {
    if (!hasMoreConversations) return;
    
    if (elements.loadMoreBtn) {
        elements.loadMoreBtn.style.display = 'none';
    }
    if (elements.loadingSpinner) {
        elements.loadingSpinner.style.display = 'block';
    }
    
    try {
        currentPage++;
        const response = await fetch(`/api/conversations?page=${currentPage}&limit=10`, {
            credentials: 'same-origin'
        });
        const data = await response.json();
        
        hasMoreConversations = data.has_more;
        
        if (elements.loadMoreContainer) {
            elements.loadMoreContainer.style.display = hasMoreConversations ? 'block' : 'none';
        }
        
        if (elements.loadMoreBtn) {
            elements.loadMoreBtn.style.display = 'block';
        }
        if (elements.loadingSpinner) {
            elements.loadingSpinner.style.display = 'none';
        }
        
        if (elements.loadMoreContainer) {
            elements.loadMoreContainer.remove();
        }
        
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
        
        if (elements.loadMoreContainer) {
            elements.conversationsList.appendChild(elements.loadMoreContainer);
        }
    } catch (error) {
        console.error('加载更多对话失败:', error);
        currentPage--;
        if (elements.loadMoreBtn) {
            elements.loadMoreBtn.style.display = 'block';
        }
        if (elements.loadingSpinner) {
            elements.loadingSpinner.style.display = 'none';
        }
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
        stopVoiceRecognition();
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

// 语音识别
function toggleVoiceRecognition() {
    const hasSpeechRecognition = ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
    
    if (hasSpeechRecognition) {
        if (isRecording) {
            stopVoiceRecognition();
        } else {
            startVoiceRecognition();
        }
    } else {
        const hasMediaRecorder = navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder;
        if (!hasMediaRecorder) {
            showError('您的浏览器不支持语音识别功能，请使用 Chrome 或 Edge 等现代浏览器');
            return;
        }
        
        if (isRecording) {
            stopModelRecording();
        } else {
            startModelRecording();
        }
    }
}

function startVoiceRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'zh-CN';

    recognition.onstart = () => {
        isRecording = true;
        elements.voiceBtn.classList.add('recording');
        elements.voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        elements.voiceBtn.title = '点击停止录音';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        elements.messageInput.value += transcript;
        elements.sendBtn.disabled = !elements.messageInput.value.trim();
        autoResizeTextarea();
        elements.messageInput.focus();
    };

    recognition.onerror = (event) => {
        console.error('语音识别错误:', event.error);
        if (event.error === 'not-allowed') {
            showError('请允许浏览器使用麦克风权限');
        } else {
            showError('语音识别失败: ' + event.error);
        }
        stopVoiceRecognition();
    };

    recognition.onend = () => {
        stopVoiceRecognition();
    };

    try {
        recognition.start();
    } catch (error) {
        console.error('启动语音识别失败:', error);
        showError('启动语音识别失败');
        isRecording = false;
        elements.voiceBtn.classList.remove('recording');
        elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    }
}

function stopVoiceRecognition() {
    if (recognition) {
        try {
            recognition.stop();
        } catch (e) {
            // ignore
        }
        recognition = null;
    }
    isRecording = false;
    elements.voiceBtn.classList.remove('recording');
    elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    elements.voiceBtn.title = '点击开始录音';
}

function startModelRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('您的浏览器不支持音频录制功能');
        return;
    }
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                sendAudioToServer(audioBlob);
                
                stream.getTracks().forEach(track => track.stop());
            });
            
            mediaRecorder.start();
            isRecording = true;
            elements.voiceBtn.classList.add('recording');
            elements.voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            elements.voiceBtn.title = '点击停止录音';
        })
        .catch(error => {
            console.error('获取麦克风权限失败:', error);
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                showError('请允许浏览器使用麦克风权限');
            } else {
                showError('无法访问麦克风: ' + error.message);
            }
        });
}

function stopModelRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    isRecording = false;
    elements.voiceBtn.classList.remove('recording');
    elements.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
    elements.voiceBtn.title = '点击开始录音';
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    
    fetch('/api/voice/recognize', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            elements.messageInput.value += data.text;
            elements.sendBtn.disabled = !elements.messageInput.value.trim();
            autoResizeTextarea();
            elements.messageInput.focus();
        } else {
            showError('语音识别失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('上传音频失败:', error);
        showError('语音识别失败: ' + error.message);
    });
}

// 预设输入相关变量
let presetGroups = [];
let currentEditingGroupId = null;
let currentEditingItemId = null;
let draggedItem = null;

// 加载预设输入显示
async function loadPresetInputs() {
    try {
        const response = await fetch('/api/preset-groups', {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            presetGroups = data.groups || [];
            renderPresetInputContainer();
        }
    } catch (error) {
        console.error('加载预设输入失败:', error);
    }
}

// 渲染预设输入显示区域
function renderPresetInputContainer() {
    const container = document.getElementById('presetInputContainer');
    if (!container) return;
    
    const enabledGroups = presetGroups.filter(g => g.enabled);
    
    if (enabledGroups.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    for (const group of enabledGroups) {
        if (group.items && group.items.length > 0) {
            for (const item of group.items) {
                html += `<button class="preset-tag" data-content="${escapeHtml(item.content)}" onclick="fillPresetInput(this)">${escapeHtml(item.content)}</button>`;
            }
        }
    }
    
    container.innerHTML = html;
}

// 填充预设输入到输入框
function fillPresetInput(btn) {
    const content = btn.dataset.content;
    elements.messageInput.value = content;
    elements.sendBtn.disabled = false;
    elements.messageInput.focus();
    autoResizeTextarea();
}

// 加载预设管理列表
async function loadPresetManagement() {
    try {
        const response = await fetch('/api/preset-groups', {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            presetGroups = data.groups || [];
            renderPresetGroupsList();
        }
    } catch (error) {
        console.error('加载预设管理失败:', error);
    }
}

// 渲染预设分组列表
function renderPresetGroupsList() {
    const container = document.getElementById('presetGroupsList');
    if (!container) return;
    
    if (presetGroups.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-layer-group"></i>
                <p>暂无预设组</p>
                <p style="font-size: 12px; margin-top: 8px;">点击上方按钮添加预设组</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    for (const group of presetGroups) {
        const itemCount = group.items ? group.items.length : 0;
        html += `
            <div class="preset-group-card ${group.enabled ? '' : 'disabled'}" data-id="${group.id}" onclick="openPresetGroupModal(${group.id})">
                <div class="preset-group-header">
                    <span class="preset-group-name">${escapeHtml(group.name)}</span>
                    <div class="preset-group-toggle" onclick="event.stopPropagation();">
                        <label class="switch">
                            <input type="checkbox" ${group.enabled ? 'checked' : ''} onchange="togglePresetGroup(${group.id}, this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
                <div class="preset-group-info">${itemCount} 个预设项</div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// 打开预设组编辑模态框
function openPresetGroupModal(groupId) {
    currentEditingGroupId = groupId;
    const group = presetGroups.find(g => g.id === groupId);
    
    if (!group) return;
    
    document.getElementById('presetGroupModalTitle').innerHTML = '<i class="fas fa-layer-group"></i> 编辑预设组';
    document.getElementById('presetGroupName').value = group.name;
    document.getElementById('presetGroupEnabled').checked = group.enabled;
    
    renderPresetItemsList(group.items || []);
    
    document.getElementById('presetGroupModal').classList.add('active');
}

// 渲染预设项列表
function renderPresetItemsList(items) {
    const container = document.getElementById('presetItemsList');
    if (!container) return;
    
    if (items.length === 0) {
        container.innerHTML = '<div class="empty-state" style="padding: 20px; color: var(--text-secondary);"><p>暂无预设项，点击下方按钮添加</p></div>';
        return;
    }
    
    let html = '';
    for (const item of items) {
        html += `
            <div class="preset-item-row" data-id="${item.id}" draggable="true">
                <span class="drag-handle"><i class="fas fa-bars"></i></span>
                <span class="preset-item-content">${escapeHtml(item.content)}</span>
                <div class="preset-item-actions">
                    <button onclick="openPresetItemModal(${item.id})" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete" onclick="deletePresetItem(${item.id})" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
    
    // 拖拽排序
    container.querySelectorAll('.preset-item-row').forEach(row => {
        row.addEventListener('dragstart', handleDragStart);
        row.addEventListener('dragend', handleDragEnd);
        row.addEventListener('dragover', handleDragOver);
        row.addEventListener('drop', handleDrop);
    });
}

function handleDragStart(e) {
    draggedItem = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd() {
    this.classList.remove('dragging');
    draggedItem = null;
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDrop(e) {
    e.preventDefault();
    if (this !== draggedItem) {
        const container = document.getElementById('presetItemsList');
        const items = [...container.querySelectorAll('.preset-item-row:not(.dragging)')];
        const draggedIdx = items.indexOf(draggedItem);
        const dropIdx = items.indexOf(this);
        
        if (draggedIdx < dropIdx) {
            container.insertBefore(draggedItem, this.nextSibling);
        } else {
            container.insertBefore(draggedItem, this);
        }
        
        // 更新排序
        updateItemsOrder();
    }
}

function updateItemsOrder() {
    const container = document.getElementById('presetItemsList');
    const rows = container.querySelectorAll('.preset-item-row');
    const items = [];
    
    rows.forEach((row, idx) => {
        items.push({
            id: parseInt(row.dataset.id),
            display_order: idx
        });
    });
    
    fetch('/api/preset-items/reorder', {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadPresetManagement();
            loadPresetInputs();
        }
    })
    .catch(error => {
        console.error('更新排序失败:', error);
    });
}

// 切换预设组启用状态
async function togglePresetGroup(groupId, enabled) {
    try {
        const response = await fetch(`/api/preset-groups/${groupId}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled })
        });
        
        if (response.ok) {
            loadPresetManagement();
            loadPresetInputs();
        }
    } catch (error) {
        console.error('切换预设组状态失败:', error);
    }
}

// 添加预设组
async function addPresetGroup() {
    try {
        const response = await fetch('/api/preset-groups', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: '新预设组', enabled: true })
        });
        
        if (response.ok) {
            const data = await response.json();
            loadPresetManagement();
            openPresetGroupModal(data.id);
        }
    } catch (error) {
        console.error('添加预设组失败:', error);
    }
}

// 保存预设组
async function savePresetGroup() {
    const name = document.getElementById('presetGroupName').value.trim();
    const enabled = document.getElementById('presetGroupEnabled').checked;
    
    if (!name) {
        alert('请输入预设组名称');
        return;
    }
    
    try {
        const response = await fetch(`/api/preset-groups/${currentEditingGroupId}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, enabled })
        });
        
        if (response.ok) {
            loadPresetManagement();
            loadPresetInputs();
            document.getElementById('presetGroupModal').classList.remove('active');
        }
    } catch (error) {
        console.error('保存预设组失败:', error);
    }
}

// 删除预设组
async function deletePresetGroup() {
    if (!confirm('确定要删除此预设组吗？组内的所有预设项也会被删除。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/preset-groups/${currentEditingGroupId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            loadPresetManagement();
            loadPresetInputs();
            document.getElementById('presetGroupModal').classList.remove('active');
        }
    } catch (error) {
        console.error('删除预设组失败:', error);
    }
}

// 添加预设项
async function addPresetItem() {
    try {
        const response = await fetch('/api/preset-items', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: currentEditingGroupId, content: '新预设项' })
        });
        
        if (response.ok) {
            const data = await response.json();
            openPresetItemModal(data.id, true);
        }
    } catch (error) {
        console.error('添加预设项失败:', error);
    }
}

// 打开预设项编辑模态框
function openPresetItemModal(itemId, isNew = false) {
    currentEditingItemId = itemId;
    
    if (isNew) {
        document.getElementById('presetItemModalTitle').innerHTML = '<i class="fas fa-plus"></i> 新建预设项';
        document.getElementById('presetItemContent').value = '';
    } else {
        const group = presetGroups.find(g => g.id === currentEditingGroupId);
        if (!group) return;
        
        const item = group.items.find(i => i.id === itemId);
        if (!item) {
            document.getElementById('presetItemModalTitle').innerHTML = '<i class="fas fa-edit"></i> 编辑预设项';
            document.getElementById('presetItemContent').value = '';
        } else {
            document.getElementById('presetItemModalTitle').innerHTML = '<i class="fas fa-edit"></i> 编辑预设项';
            document.getElementById('presetItemContent').value = item.content;
        }
    }
    
    document.getElementById('presetItemModal').classList.add('active');
}

// 保存预设项
async function savePresetItem() {
    const content = document.getElementById('presetItemContent').value.trim();
    
    if (!content) {
        alert('请输入预设内容');
        return;
    }
    
    try {
        const response = await fetch(`/api/preset-items/${currentEditingItemId}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        if (response.ok) {
            loadPresetManagement();
            loadPresetInputs();
            
            // 刷新当前编辑的组
            const group = presetGroups.find(g => g.id === currentEditingGroupId);
            if (group) {
                const updatedGroup = await fetch(`/api/preset-groups/${currentEditingGroupId}`, {
                    credentials: 'same-origin'
                }).then(r => r.json());
                if (updatedGroup.groups && updatedGroup.groups[0]) {
                    renderPresetItemsList(updatedGroup.groups[0].items || []);
                }
            }
            
            document.getElementById('presetItemModal').classList.remove('active');
        }
    } catch (error) {
        console.error('保存预设项失败:', error);
    }
}

// 删除预设项
async function deletePresetItem(itemId) {
    if (!confirm('确定要删除此预设项吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/preset-items/${itemId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            loadPresetManagement();
            loadPresetInputs();
            
            // 刷新当前编辑的组
            const group = presetGroups.find(g => g.id === currentEditingGroupId);
            if (group) {
                const updatedGroup = await fetch(`/api/preset-groups/${currentEditingGroupId}`, {
                    credentials: 'same-origin'
                }).then(r => r.json());
                if (updatedGroup.groups && updatedGroup.groups[0]) {
                    renderPresetItemsList(updatedGroup.groups[0].items || []);
                }
            }
        }
    } catch (error) {
        console.error('删除预设项失败:', error);
    }
}

// 初始化预设输入事件监听器
function initPresetEventListeners() {
    // 添加预设组按钮
    document.getElementById('addPresetGroupBtn')?.addEventListener('click', addPresetGroup);
    
    // 预设组模态框
    document.getElementById('closePresetGroupModal')?.addEventListener('click', () => {
        document.getElementById('presetGroupModal').classList.remove('active');
    });
    
    document.getElementById('presetGroupModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('presetGroupModal')) {
            document.getElementById('presetGroupModal').classList.remove('active');
        }
    });
    
    document.getElementById('savePresetGroupBtn')?.addEventListener('click', savePresetGroup);
    document.getElementById('deletePresetGroupBtn')?.addEventListener('click', deletePresetGroup);
    
    // 添加预设项按钮
    document.getElementById('addPresetItemBtn')?.addEventListener('click', addPresetItem);
    
    // 预设项模态框
    document.getElementById('closePresetItemModal')?.addEventListener('click', () => {
        document.getElementById('presetItemModal').classList.remove('active');
    });
    
    document.getElementById('presetItemModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('presetItemModal')) {
            document.getElementById('presetItemModal').classList.remove('active');
        }
    });
    
    document.getElementById('savePresetItemBtn')?.addEventListener('click', savePresetItem);
    document.getElementById('deletePresetItemBtn')?.addEventListener('click', () => {
        deletePresetItem(currentEditingItemId);
        document.getElementById('presetItemModal').classList.remove('active');
    });
}

