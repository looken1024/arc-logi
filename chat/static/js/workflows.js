// 工作流管理页面 JavaScript

// 全局状态
let currentUser = null;
let workflows = [];
let workflowToDelete = null;

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    workflowsList: document.getElementById('workflowsList'),
    username: document.getElementById('username'),
    createWorkflowBtn: document.getElementById('createWorkflowBtn'),
    workflowModal: document.getElementById('workflowModal'),
    closeWorkflowModal: document.getElementById('closeWorkflowModal'),
    cancelWorkflowBtn: document.getElementById('cancelWorkflowBtn'),
    saveWorkflowBtn: document.getElementById('saveWorkflowBtn'),
    workflowForm: document.getElementById('workflowForm'),
    workflowModalTitle: document.getElementById('workflowModalTitle'),
    workflowId: document.getElementById('workflowId'),
    workflowName: document.getElementById('workflowName'),
    workflowDescription: document.getElementById('workflowDescription'),
    workflowStatus: document.getElementById('workflowStatus'),
    confirmDeleteModal: document.getElementById('confirmDeleteModal'),
    closeDeleteModal: document.getElementById('closeDeleteModal'),
    cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
    deleteMessage: document.getElementById('deleteMessage')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    initializeEventListeners();
    loadWorkflows();
});

// 加载用户信息
async function loadUserInfo() {
    try {
        const response = await fetch('/api/user');
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            elements.username.textContent = user.username;
        } else {
            // 未登录,重定向到登录页
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        window.location.href = '/login';
    }
}

// 初始化事件监听器
function initializeEventListeners() {
    // 侧边栏切换
    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('active');
    });

    // 新建工作流按钮
    elements.createWorkflowBtn.addEventListener('click', () => {
        openWorkflowModal();
    });

    // 关闭工作流模态框
    elements.closeWorkflowModal.addEventListener('click', closeWorkflowModal);
    elements.cancelWorkflowBtn.addEventListener('click', closeWorkflowModal);

    // 点击模态框背景关闭
    elements.workflowModal.addEventListener('click', (e) => {
        if (e.target === elements.workflowModal) {
            closeWorkflowModal();
        }
    });

    // 保存工作流
    elements.saveWorkflowBtn.addEventListener('click', saveWorkflow);

    // 确认删除模态框
    elements.closeDeleteModal.addEventListener('click', closeDeleteModal);
    elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    elements.confirmDeleteBtn.addEventListener('click', confirmDeleteWorkflow);

    // 点击删除模态框背景关闭
    elements.confirmDeleteModal.addEventListener('click', (e) => {
        if (e.target === elements.confirmDeleteModal) {
            closeDeleteModal();
        }
    });
}

// 加载工作流列表
async function loadWorkflows() {
    try {
        elements.workflowsList.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><span>加载中...</span></div>';
        
        const response = await fetch('/api/workflows');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        workflows = data.workflows || [];
        
        renderWorkflows();
    } catch (error) {
        console.error('加载工作流列表失败:', error);
        elements.workflowsList.innerHTML = `<div class="error-state">加载失败: ${escapeHtml(error.message)}</div>`;
    }
}

// 渲染工作流列表
function renderWorkflows() {
    if (workflows.length === 0) {
        elements.workflowsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-project-diagram"></i>
                <h3>暂无工作流</h3>
                <p>点击"新建工作流"按钮开始创建您的工作流</p>
                <button class="btn btn-primary" id="createFirstWorkflowBtn">
                    <i class="fas fa-plus"></i>
                    新建工作流
                </button>
            </div>
        `;
        
        // 添加事件监听器
        document.getElementById('createFirstWorkflowBtn')?.addEventListener('click', () => {
            openWorkflowModal();
        });
        
        return;
    }
    
    elements.workflowsList.innerHTML = '';
    
    workflows.forEach(workflow => {
        const workflowCard = createWorkflowCard(workflow);
        elements.workflowsList.appendChild(workflowCard);
    });
}

// 创建工作流卡片
function createWorkflowCard(workflow) {
    const card = document.createElement('div');
    card.className = 'workflow-card';
    card.dataset.workflowId = workflow.id;
    
    // 状态显示文本
    const statusText = {
        'draft': '草稿',
        'active': '启用',
        'paused': '暂停',
        'archived': '归档'
    }[workflow.status] || workflow.status;
    
    // 格式化时间
    const formatTime = (timestamp) => {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    };
    
    card.innerHTML = `
        <div class="workflow-header">
            <div class="workflow-title">${escapeHtml(workflow.name)}</div>
            <div class="workflow-actions">
                <button class="action-btn edit-btn" title="编辑" data-workflow-id="${workflow.id}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn delete-btn" title="删除" data-workflow-id="${workflow.id}">
                    <i class="fas fa-trash"></i>
                </button>
                ${workflow.status === 'active' ? 
                    `<button class="action-btn pause-btn" title="暂停" data-workflow-id="${workflow.id}">
                        <i class="fas fa-pause"></i>
                    </button>` : 
                    `<button class="action-btn start-btn" title="启动" data-workflow-id="${workflow.id}">
                        <i class="fas fa-play"></i>
                    </button>`
                }
                <button class="action-btn execute-btn" title="执行" data-workflow-id="${workflow.id}">
                    <i class="fas fa-play-circle"></i>
                </button>
                <button class="action-btn executions-btn" title="执行记录" data-workflow-id="${workflow.id}">
                    <i class="fas fa-history"></i>
                </button>
            </div>
        </div>
        <div class="workflow-meta">
            <div class="workflow-status status-${workflow.status}">
                <i class="fas fa-circle"></i>
                ${escapeHtml(statusText)}
            </div>
            <div class="workflow-time">
                更新于: ${formatTime(workflow.updated_at)}
            </div>
        </div>
        <div class="workflow-description">${escapeHtml(workflow.description || '暂无描述')}</div>
        <div class="workflow-footer">
            <div class="workflow-actions">
                <a href="/workflows/editor/${workflow.id}" class="btn btn-secondary">
                    <i class="fas fa-diagram-project"></i>
                    设计工作流
                </a>
            </div>
            <div class="workflow-time">
                创建于: ${formatTime(workflow.created_at)}
            </div>
        </div>
    `;
    
    // 添加事件监听器
    const editBtn = card.querySelector('.edit-btn');
    const deleteBtn = card.querySelector('.delete-btn');
    const startBtn = card.querySelector('.start-btn');
    const pauseBtn = card.querySelector('.pause-btn');
    const executeBtn = card.querySelector('.execute-btn');
    const executionsBtn = card.querySelector('.executions-btn');
    
    editBtn?.addEventListener('click', () => editWorkflow(workflow.id));
    deleteBtn?.addEventListener('click', () => showDeleteConfirm(workflow.id, workflow.name));
    startBtn?.addEventListener('click', () => startWorkflow(workflow.id));
    pauseBtn?.addEventListener('click', () => pauseWorkflow(workflow.id));
    executeBtn?.addEventListener('click', () => executeWorkflow(workflow.id));
    executionsBtn?.addEventListener('click', () => showExecutions(workflow.id));
    
    return card;
}

// 打开工作流模态框
function openWorkflowModal(workflow = null) {
    if (workflow) {
        // 编辑模式
        elements.workflowModalTitle.textContent = '编辑工作流';
        elements.workflowId.value = workflow.id;
        elements.workflowName.value = workflow.name || '';
        elements.workflowDescription.value = workflow.description || '';
        elements.workflowStatus.value = workflow.status || 'draft';
    } else {
        // 新建模式
        elements.workflowModalTitle.textContent = '新建工作流';
        elements.workflowForm.reset();
        elements.workflowId.value = '';
        elements.workflowStatus.value = 'draft';
    }
    
    elements.workflowModal.classList.add('active');
    elements.workflowName.focus();
}

// 关闭工作流模态框
function closeWorkflowModal() {
    elements.workflowModal.classList.remove('active');
    elements.workflowForm.reset();
    workflowToDelete = null;
}

// 保存工作流
async function saveWorkflow() {
    const workflowId = elements.workflowId.value;
    const name = elements.workflowName.value.trim();
    const description = elements.workflowDescription.value.trim();
    const status = elements.workflowStatus.value;
    
    if (!name) {
        alert('工作流名称不能为空');
        elements.workflowName.focus();
        return;
    }
    
    try {
        elements.saveWorkflowBtn.disabled = true;
        elements.saveWorkflowBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
        
        let response;
        if (workflowId) {
            // 更新现有工作流
            response = await fetch(`/api/workflows/${workflowId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, description, status })
            });
        } else {
            // 创建新工作流
            response = await fetch('/api/workflows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, description })
            });
        }
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '保存失败');
        }
        
        // 重新加载工作流列表
        await loadWorkflows();
        closeWorkflowModal();
        
    } catch (error) {
        console.error('保存工作流失败:', error);
        alert('保存失败: ' + error.message);
    } finally {
        elements.saveWorkflowBtn.disabled = false;
        elements.saveWorkflowBtn.innerHTML = '保存';
    }
}

// 编辑工作流
async function editWorkflow(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        openWorkflowModal(data.workflow);
    } catch (error) {
        console.error('获取工作流详情失败:', error);
        alert('获取工作流详情失败: ' + error.message);
    }
}

// 显示删除确认
function showDeleteConfirm(workflowId, workflowName) {
    workflowToDelete = workflowId;
    elements.deleteMessage.textContent = `确定要删除工作流 "${escapeHtml(workflowName)}" 吗？此操作不可撤销。`;
    elements.confirmDeleteModal.classList.add('active');
}

// 关闭删除确认模态框
function closeDeleteModal() {
    elements.confirmDeleteModal.classList.remove('active');
    workflowToDelete = null;
}

// 确认删除工作流
async function confirmDeleteWorkflow() {
    if (!workflowToDelete) return;
    
    try {
        elements.confirmDeleteBtn.disabled = true;
        elements.confirmDeleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 删除中...';
        
        const response = await fetch(`/api/workflows/${workflowToDelete}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '删除失败');
        }
        
        // 重新加载工作流列表
        await loadWorkflows();
        closeDeleteModal();
        
    } catch (error) {
        console.error('删除工作流失败:', error);
        alert('删除失败: ' + error.message);
    } finally {
        elements.confirmDeleteBtn.disabled = false;
        elements.confirmDeleteBtn.innerHTML = '删除';
    }
}

// 启动工作流
async function startWorkflow(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/start`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '启动失败');
        }
        
        // 重新加载工作流列表
        await loadWorkflows();
        
    } catch (error) {
        console.error('启动工作流失败:', error);
        alert('启动失败: ' + error.message);
    }
}

// 暂停工作流
async function pauseWorkflow(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/pause`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '暂停失败');
        }
        
        // 重新加载工作流列表
        await loadWorkflows();
        
    } catch (error) {
        console.error('暂停工作流失败:', error);
        alert('暂停失败: ' + error.message);
    }
}

// 执行工作流
async function executeWorkflow(workflowId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ input: {} })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || '执行失败');
        }
        
        const data = await response.json();
        alert(`工作流执行已创建，执行ID: ${data.execution_id}`);
        
    } catch (error) {
        console.error('执行工作流失败:', error);
        alert('执行失败: ' + error.message);
    }
}

// 显示执行记录
function showExecutions(workflowId) {
    alert('执行记录功能开发中...');
    // 这里可以跳转到执行记录页面或打开执行记录模态框
    // window.location.href = `/workflows/${workflowId}/executions`;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}