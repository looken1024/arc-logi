// 提示词管理页面 JavaScript

let currentUser = null;
let prompts = [];
let promptToDelete = null;
let editingPromptId = null;
let currentTags = [];

const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    promptsList: document.getElementById('promptsList'),
    username: document.getElementById('username'),
    searchInput: document.getElementById('searchInput'),
    createPromptBtn: document.getElementById('createPromptBtn'),
    promptModal: document.getElementById('promptModal'),
    closePromptModal: document.getElementById('closePromptModal'),
    cancelPromptBtn: document.getElementById('cancelPromptBtn'),
    savePromptBtn: document.getElementById('savePromptBtn'),
    promptForm: document.getElementById('promptForm'),
    promptModalTitle: document.getElementById('promptModalTitle'),
    promptId: document.getElementById('promptId'),
    promptName: document.getElementById('promptName'),
    promptDescription: document.getElementById('promptDescription'),
    promptContent: document.getElementById('promptContent'),
    tagsContainer: document.getElementById('tagsContainer'),
    tagsInput: document.getElementById('tagsInput'),
    confirmDeleteModal: document.getElementById('confirmDeleteModal'),
    closeDeleteModal: document.getElementById('closeDeleteModal'),
    cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
    deleteMessage: document.getElementById('deleteMessage'),
    promptDetailModal: document.getElementById('promptDetailModal'),
    closeDetailModal: document.getElementById('closeDetailModal'),
    closeDetailBtn: document.getElementById('closeDetailBtn'),
    promptDetailTitle: document.getElementById('promptDetailTitle'),
    promptDetailContent: document.getElementById('promptDetailContent'),
    usePromptBtn: document.getElementById('usePromptBtn')
};

document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    initializeEventListeners();
    loadPrompts();
});

async function loadUserInfo() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            elements.username.textContent = user.username;
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

function initializeEventListeners() {
    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });

    elements.createPromptBtn?.addEventListener('click', () => {
        openPromptModal();
    });

    elements.closePromptModal?.addEventListener('click', () => {
        closePromptModal();
    });
    elements.cancelPromptBtn?.addEventListener('click', () => {
        closePromptModal();
    });

    elements.savePromptBtn?.addEventListener('click', async () => {
        await savePrompt();
    });

    elements.closeDeleteModal?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.cancelDeleteBtn?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.confirmDeleteBtn?.addEventListener('click', async () => {
        await deletePrompt();
    });

    elements.closeDetailModal?.addEventListener('click', () => {
        closeDetailModal();
    });
    elements.closeDetailBtn?.addEventListener('click', () => {
        closeDetailModal();
    });
    elements.usePromptBtn?.addEventListener('click', () => {
        usePrompt();
    });

    elements.searchInput?.addEventListener('input', debounce(() => {
        loadPrompts(elements.searchInput.value);
    }, 300));

    elements.tagsInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
        } else if (e.key === 'Backspace' && elements.tagsInput.value === '' && currentTags.length > 0) {
            currentTags.pop();
            renderTags();
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target === elements.promptModal) {
            closePromptModal();
        }
        if (e.target === elements.confirmDeleteModal) {
            closeDeleteModal();
        }
        if (e.target === elements.promptDetailModal) {
            closeDetailModal();
        }
    });
}

async function loadPrompts(search = '') {
    try {
        const url = search ? `/api/prompts?search=${encodeURIComponent(search)}` : '/api/prompts';
        const response = await fetch(url, {
            credentials: 'same-origin'
        });
        
        if (response.ok) {
            const data = await response.json();
            prompts = data.prompts || [];
            renderPrompts();
        } else {
            console.error('加载提示词失败');
        }
    } catch (error) {
        console.error('加载提示词失败:', error);
    }
}

function renderPrompts() {
    if (prompts.length === 0) {
        elements.promptsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <h3>暂无提示词</h3>
                <p>点击"新建提示词"创建一个吧</p>
            </div>
        `;
        return;
    }

    elements.promptsList.innerHTML = prompts.map(prompt => `
        <div class="prompt-card" data-id="${prompt.id}">
            <div class="prompt-card-header">
                <h3 class="prompt-card-title">${escapeHtml(prompt.name)}</h3>
                <div class="prompt-card-actions">
                    <button class="edit-btn" title="编辑" data-id="${prompt.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="delete-btn" title="删除" data-id="${prompt.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <p class="prompt-card-description">${escapeHtml(prompt.description || '暂无描述')}</p>
            <div class="prompt-card-preview">${escapeHtml(prompt.content)}</div>
            ${prompt.tags && prompt.tags.length > 0 ? `
                <div class="prompt-card-tags">
                    ${prompt.tags.map(tag => `<span class="prompt-tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
            <div class="prompt-card-meta">
                <span>更新时间: ${formatDate(prompt.updated_at)}</span>
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.prompt-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('.prompt-card-actions')) return;
            const promptId = parseInt(card.dataset.id);
            showPromptDetail(promptId);
        });
    });

    document.querySelectorAll('.prompt-card .edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const promptId = parseInt(btn.dataset.id);
            editPrompt(promptId);
        });
    });

    document.querySelectorAll('.prompt-card .delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const promptId = parseInt(btn.dataset.id);
            confirmDeletePrompt(promptId);
        });
    });
}

function openPromptModal(prompt = null) {
    editingPromptId = prompt ? prompt.id : null;
    currentTags = prompt ? [...(prompt.tags || [])] : [];
    
    elements.promptModalTitle.textContent = prompt ? '编辑提示词' : '新建提示词';
    elements.promptName.value = prompt ? prompt.name : '';
    elements.promptDescription.value = prompt ? prompt.description || '' : '';
    elements.promptContent.value = prompt ? prompt.content : '';
    elements.promptId.value = prompt ? prompt.id : '';
    
    renderTags();
    elements.promptModal.classList.add('active');
    elements.promptName.focus();
}

function closePromptModal() {
    elements.promptModal.classList.remove('active');
    elements.promptForm.reset();
    editingPromptId = null;
    currentTags = [];
    renderTags();
}

async function savePrompt() {
    const name = elements.promptName.value.trim();
    const content = elements.promptContent.value.trim();
    const description = elements.promptDescription.value.trim();
    
    if (!name) {
        alert('请输入提示词名称');
        return;
    }
    if (!content) {
        alert('请输入提示词内容');
        return;
    }

    const promptData = {
        name,
        content,
        description,
        tags: currentTags
    };

    try {
        let response;
        if (editingPromptId) {
            response = await fetch(`/api/prompts/${editingPromptId}`, {
                method: 'PUT',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(promptData)
            });
        } else {
            response = await fetch('/api/prompts', {
                method: 'POST',
                credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(promptData)
            });
        }

        if (response.ok) {
            closePromptModal();
            loadPrompts(elements.searchInput?.value || '');
        } else {
            const error = await response.json();
            alert(error.error || '保存失败');
        }
    } catch (error) {
        console.error('保存提示词失败:', error);
        alert('保存失败');
    }
}

function editPrompt(promptId) {
    const prompt = prompts.find(p => p.id === promptId);
    if (prompt) {
        openPromptModal(prompt);
    }
}

function confirmDeletePrompt(promptId) {
    promptToDelete = promptId;
    elements.deleteMessage.textContent = '确定要删除这个提示词吗？此操作不可撤销。';
    elements.confirmDeleteModal.classList.add('active');
}

function closeDeleteModal() {
    elements.confirmDeleteModal.classList.remove('active');
    promptToDelete = null;
}

async function deletePrompt() {
    if (!promptToDelete) return;

    try {
        const response = await fetch(`/api/prompts/${promptToDelete}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        if (response.ok) {
            closeDeleteModal();
            loadPrompts(elements.searchInput?.value || '');
        } else {
            const error = await response.json();
            alert(error.error || '删除失败');
        }
    } catch (error) {
        console.error('删除提示词失败:', error);
        alert('删除失败');
    }
}

let currentDetailPromptId = null;

function showPromptDetail(promptId) {
    const prompt = prompts.find(p => p.id === promptId);
    if (!prompt) return;

    currentDetailPromptId = promptId;
    elements.promptDetailTitle.textContent = prompt.name;
    
    elements.promptDetailContent.innerHTML = `
        <div style="margin-bottom: 16px;">
            <strong>描述:</strong>
            <p>${escapeHtml(prompt.description || '暂无描述')}</p>
        </div>
        <div style="margin-bottom: 16px;">
            <strong>标签:</strong>
            <div class="prompt-card-tags" style="margin-top: 8px;">
                ${prompt.tags && prompt.tags.length > 0 
                    ? prompt.tags.map(tag => `<span class="prompt-tag">${escapeHtml(tag)}</span>`).join('') 
                    : '<span style="color: var(--text-muted, #888);">暂无标签</span>'}
            </div>
        </div>
        <div>
            <strong>内容:</strong>
            <pre style="background: var(--bg-tertiary, #333); padding: 16px; border-radius: 8px; margin-top: 8px; white-space: pre-wrap; word-break: break-word;">${escapeHtml(prompt.content)}</pre>
        </div>
        <div style="margin-top: 16px; color: var(--text-muted, #888); font-size: 12px;">
            创建时间: ${formatDate(prompt.created_at)}<br>
            更新时间: ${formatDate(prompt.updated_at)}
        </div>
    `;
    
    elements.promptDetailModal.classList.add('active');
}

function closeDetailModal() {
    elements.promptDetailModal.classList.remove('active');
    currentDetailPromptId = null;
}

function usePrompt() {
    const prompt = prompts.find(p => p.id === currentDetailPromptId);
    if (prompt) {
        window.location.href = `/?prompt=${encodeURIComponent(prompt.content)}`;
    }
}

function addTag() {
    const tagsInput = document.getElementById('tagsInput');
    const tag = tagsInput.value.trim();
    if (tag && !currentTags.includes(tag)) {
        currentTags.push(tag);
        renderTags();
    }
    tagsInput.value = '';
}

function removeTag(tag) {
    currentTags = currentTags.filter(t => t !== tag);
    renderTags();
}

function renderTags() {
    const tagsHtml = currentTags.map(tag => `
        <span class="tag-item">
            ${escapeHtml(tag)}
            <button type="button" onclick="removeTag('${escapeHtml(tag)}')">&times;</button>
        </span>
    `).join('');
    
    const inputHtml = '<input type="text" class="tags-input" id="tagsInput" placeholder="输入标签后按回车添加">';
    elements.tagsContainer.innerHTML = tagsHtml + inputHtml;
    
    const newTagsInput = document.getElementById('tagsInput');
    newTagsInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
        } else if (e.key === 'Backspace' && newTagsInput.value === '' && currentTags.length > 0) {
            currentTags.pop();
            renderTags();
        }
    });
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
