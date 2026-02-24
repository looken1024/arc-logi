// Agent管理页面 JavaScript

let currentUser = null;
let agents = [];
let prompts = [];
let agentToDelete = null;
let editingAgentId = null;

const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    agentsList: document.getElementById('agentsList'),
    username: document.getElementById('username'),
    searchInput: document.getElementById('searchInput'),
    createAgentBtn: document.getElementById('createAgentBtn'),
    agentModal: document.getElementById('agentModal'),
    closeAgentModal: document.getElementById('closeAgentModal'),
    cancelAgentBtn: document.getElementById('cancelAgentBtn'),
    saveAgentBtn: document.getElementById('saveAgentBtn'),
    agentForm: document.getElementById('agentForm'),
    agentModalTitle: document.getElementById('agentModalTitle'),
    agentId: document.getElementById('agentId'),
    agentName: document.getElementById('agentName'),
    agentDescription: document.getElementById('agentDescription'),
    agentSystemPrompt: document.getElementById('agentSystemPrompt'),
    agentPromptId: document.getElementById('agentPromptId'),
    agentModel: document.getElementById('agentModel'),
    agentTemperature: document.getElementById('agentTemperature'),
    agentMaxTokens: document.getElementById('agentMaxTokens'),
    confirmDeleteModal: document.getElementById('confirmDeleteModal'),
    closeDeleteModal: document.getElementById('closeDeleteModal'),
    cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
    deleteMessage: document.getElementById('deleteMessage'),
    agentDetailModal: document.getElementById('agentDetailModal'),
    closeDetailModal: document.getElementById('closeDetailModal'),
    closeDetailBtn: document.getElementById('closeDetailBtn'),
    agentDetailTitle: document.getElementById('agentDetailTitle'),
    agentDetailContent: document.getElementById('agentDetailContent')
};

document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    initializeEventListeners();
    loadPromptsForSelect();
    loadAgents();
});

let currentTheme = 'dark';

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            elements.username.textContent = user.username;
            currentTheme = user.theme || 'dark';
            applyTheme(currentTheme);
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
}

function initializeEventListeners() {
    const mainContent = document.querySelector('.main-content');

    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('active');
    });

    mainContent?.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 &&
            e.target.closest('.sidebar-toggle') === null &&
            elements.sidebar?.classList.contains('active')) {
            elements.sidebar.classList.remove('active');
        }
    });

    elements.createAgentBtn?.addEventListener('click', () => {
        openAgentModal();
    });

    elements.closeAgentModal?.addEventListener('click', () => {
        closeAgentModal();
    });
    elements.cancelAgentBtn?.addEventListener('click', () => {
        closeAgentModal();
    });

    elements.saveAgentBtn?.addEventListener('click', async () => {
        await saveAgent();
    });

    elements.closeDeleteModal?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.cancelDeleteBtn?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.confirmDeleteBtn?.addEventListener('click', async () => {
        await deleteAgent();
    });

    elements.closeDetailModal?.addEventListener('click', () => {
        closeDetailModal();
    });
    elements.closeDetailBtn?.addEventListener('click', () => {
        closeDetailModal();
    });

    elements.searchInput?.addEventListener('input', debounce(() => {
        loadAgents(elements.searchInput.value);
    }, 300));

    elements.agentPromptId?.addEventListener('change', async (e) => {
        const promptId = e.target.value;
        if (promptId && prompts.length > 0) {
            const selectedPrompt = prompts.find(p => p.id === parseInt(promptId));
            if (selectedPrompt && !elements.agentSystemPrompt.value) {
                elements.agentSystemPrompt.value = selectedPrompt.content;
            }
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target === elements.agentModal) {
            closeAgentModal();
        }
        if (e.target === elements.confirmDeleteModal) {
            closeDeleteModal();
        }
        if (e.target === elements.agentDetailModal) {
            closeDetailModal();
        }
    });
}

async function loadPromptsForSelect() {
    try {
        const response = await fetch('/api/prompts', {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            prompts = data.prompts || [];
            
            const optionsHtml = prompts.map(prompt => 
                `<option value="${prompt.id}">${escapeHtml(prompt.name)}</option>`
            ).join('');
            
            elements.agentPromptId.innerHTML = `<option value="">-- 不使用提示词模板 --</option>${optionsHtml}`;
        }
    } catch (error) {
        console.error('加载提示词列表失败:', error);
    }
}

async function loadAgents(search = '') {
    try {
        const url = search ? `/api/agents?search=${encodeURIComponent(search)}` : '/api/agents';
        const response = await fetch(url, {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            agents = data.agents || [];
            renderAgents();
        } else {
            console.error('加载Agent失败');
            elements.agentsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle"></i>
                    <h3>加载失败</h3>
                    <p>请刷新页面重试</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载Agent失败:', error);
        elements.agentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle"></i>
                <h3>加载失败</h3>
                <p>请刷新页面重试</p>
            </div>
        `;
    }
}

function renderAgents() {
    if (agents.length === 0) {
        elements.agentsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-robot"></i>
                <h3>暂无 Agent</h3>
                <p>点击"新建 Agent"创建一个吧</p>
            </div>
        `;
        return;
    }

    elements.agentsList.innerHTML = agents.map(agent => `
        <div class="agent-card" data-id="${agent.id}">
            <div class="agent-card-header">
                <h3 class="agent-card-title">${escapeHtml(agent.name)}</h3>
                <div class="agent-card-actions">
                    <button class="edit-btn" title="编辑" data-id="${agent.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-btn" title="删除" data-id="${agent.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <p class="agent-card-description">${escapeHtml(agent.description || '暂无描述')}</p>
            <div class="agent-card-preview">${escapeHtml(agent.system_prompt || '暂无系统提示词')}</div>
            <div class="agent-card-meta">
                <span class="agent-model-badge">${escapeHtml(agent.model)}</span>
                ${agent.prompt_name ? `<span class="agent-prompt-badge">${escapeHtml(agent.prompt_name)}</span>` : ''}
                <span>更新: ${formatDate(agent.updated_at)}</span>
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.agent-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.agent-card-actions')) return;
            const agentId = parseInt(card.dataset.id);
            showAgentDetail(agentId);
        });
    });

    document.querySelectorAll('.agent-card .edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const agentId = parseInt(btn.dataset.id);
            editAgent(agentId);
        });
    });

    document.querySelectorAll('.agent-card .delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const agentId = parseInt(btn.dataset.id);
            confirmDeleteAgent(agentId);
        });
    });
}

function openAgentModal(agent = null) {
    editingAgentId = agent ? agent.id : null;
    
    elements.agentModalTitle.textContent = agent ? '编辑 Agent' : '新建 Agent';
    elements.agentName.value = agent ? agent.name : '';
    elements.agentDescription.value = agent ? agent.description || '' : '';
    elements.agentSystemPrompt.value = agent ? agent.system_prompt || '' : '';
    elements.agentPromptId.value = agent && agent.prompt_id ? agent.prompt_id : '';
    elements.agentModel.value = agent && agent.model ? agent.model : 'gpt-4';
    elements.agentTemperature.value = agent && agent.temperature ? agent.temperature : '0.7';
    elements.agentMaxTokens.value = agent && agent.max_tokens ? agent.max_tokens : '2000';
    elements.agentId.value = agent ? agent.id : '';
    
    elements.agentModal.classList.add('active');
    elements.agentName.focus();
}

function closeAgentModal() {
    elements.agentModal.classList.remove('active');
    elements.agentForm.reset();
    editingAgentId = null;
}

async function saveAgent() {
    const name = elements.agentName.value.trim();
    const description = elements.agentDescription.value.trim();
    const system_prompt = elements.agentSystemPrompt.value.trim();
    const prompt_id = elements.agentPromptId.value ? parseInt(elements.agentPromptId.value) : null;
    const model = elements.agentModel.value;
    const temperature = parseFloat(elements.agentTemperature.value) || 0.7;
    const max_tokens = parseInt(elements.agentMaxTokens.value) || 2000;
    
    if (!name) {
        alert('请输入Agent名称');
        return;
    }
    if (!system_prompt && !prompt_id) {
        alert('请设置系统提示词或选择提示词模板');
        return;
    }

    const agentData = {
        name,
        description,
        system_prompt,
        prompt_id,
        model,
        temperature,
        max_tokens
    };

    try {
        let response;
        if (editingAgentId) {
            response = await fetch(`/api/agents/${editingAgentId}`, {
                method: 'PUT',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentData)
            });
        } else {
            response = await fetch('/api/agents', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(agentData)
            });
        }

        if (response.ok) {
            closeAgentModal();
            loadAgents(elements.searchInput?.value || '');
        } else {
            const error = await response.json();
            alert(error.error || '保存失败');
        }
    } catch (error) {
        console.error('保存Agent失败:', error);
        alert('保存失败');
    }
}

function editAgent(agentId) {
    const agent = agents.find(a => a.id === agentId);
    if (agent) {
        openAgentModal(agent);
    }
}

function confirmDeleteAgent(agentId) {
    agentToDelete = agentId;
    elements.deleteMessage.textContent = '确定要删除这个Agent吗？此操作不可撤销。';
    elements.confirmDeleteModal.classList.add('active');
}

function closeDeleteModal() {
    elements.confirmDeleteModal.classList.remove('active');
    agentToDelete = null;
}

async function deleteAgent() {
    if (!agentToDelete) return;

    try {
        const response = await fetch(`/api/agents/${agentToDelete}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        if (response.ok) {
            closeDeleteModal();
            loadAgents(elements.searchInput?.value || '');
        } else {
            const error = await response.json();
            alert(error.error || '删除失败');
        }
    } catch (error) {
        console.error('删除Agent失败:', error);
        alert('删除失败');
    }
}

function showAgentDetail(agentId) {
    const agent = agents.find(a => a.id === agentId);
    if (!agent) return;

    elements.agentDetailTitle.textContent = agent.name;
    
    elements.agentDetailContent.innerHTML = `
        <div style="margin-bottom: 16px;">
            <strong>描述:</strong>
            <p>${escapeHtml(agent.description || '暂无描述')}</p>
        </div>
        <div style="margin-bottom: 16px;">
            <strong>模型:</strong>
            <span class="agent-model-badge" style="margin-left: 8px;">${escapeHtml(agent.model)}</span>
        </div>
        <div style="margin-bottom: 16px;">
            <strong>Temperature:</strong>
            <span style="margin-left: 8px;">${agent.temperature}</span>
        </div>
        <div style="margin-bottom: 16px;">
            <strong>最大 Token:</strong>
            <span style="margin-left: 8px;">${agent.max_tokens}</span>
        </div>
        ${agent.prompt_name ? `
            <div style="margin-bottom: 16px;">
                <strong>关联提示词:</strong>
                <span class="agent-prompt-badge" style="margin-left: 8px;">${escapeHtml(agent.prompt_name)}</span>
            </div>
        ` : ''}
        <div>
            <strong>系统提示词:</strong>
            <pre style="background: var(--bg-tertiary, #333); padding: 16px; border-radius: 8px; margin-top: 8px; white-space: pre-wrap; word-break: break-word;">${escapeHtml(agent.system_prompt || '暂无系统提示词')}</pre>
        </div>
        <div style="margin-top: 16px; color: var(--text-muted, #888); font-size: 12px;">
            创建时间: ${formatDate(agent.created_at)}<br>
            更新时间: ${formatDate(agent.updated_at)}
        </div>
    `;
    
    elements.agentDetailModal.classList.add('active');
}

function closeDetailModal() {
    elements.agentDetailModal.classList.remove('active');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
