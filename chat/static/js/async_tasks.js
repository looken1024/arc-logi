// 异步任务管理页面 JavaScript

// 全局状态
let currentUser = null;
let tasks = [];
let scheduleToDelete = null;
let currentScheduleId = null;
let currentTheme = 'dark';
let currentOutputTaskId = null;
let outputPollInterval = null;
let globalPollInterval = null;

// 分页状态
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let isLoading = false;
let isRefreshing = false;
let hasMore = true;
let searchTerm = '';
let scrollObserver = null;
let refreshDebounceTimer = null;

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    schedulesList: document.getElementById('schedulesList'),
    username: document.getElementById('username'),
    createScheduleBtn: document.getElementById('createScheduleBtn'),
    searchTaskInput: document.getElementById('searchTaskInput'),
    refreshListBtn: document.getElementById('refreshListBtn'),

    scheduleModal: document.getElementById('scheduleModal'),
    closeScheduleModal: document.getElementById('closeScheduleModal'),
    cancelScheduleBtn: document.getElementById('cancelScheduleBtn'),
    saveScheduleBtn: document.getElementById('saveScheduleBtn'),
    scheduleForm: document.getElementById('scheduleForm'),
    scheduleModalTitle: document.getElementById('scheduleModalTitle'),
    scheduleId: document.getElementById('scheduleId'),
    scheduleName: document.getElementById('scheduleName'),
    scheduleDescription: document.getElementById('scheduleDescription'),
    scheduleCron: document.getElementById('scheduleCron'),
    schedulePreset: document.getElementById('schedulePreset'),
    scheduleCommand: document.getElementById('scheduleCommand'),
    scheduleStatus: document.getElementById('scheduleStatus'),
    scheduleDelay: document.getElementById('scheduleDelay'),
    confirmDeleteModal: document.getElementById('confirmDeleteModal'),
    closeDeleteModal: document.getElementById('closeDeleteModal'),
    cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
    confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
    deleteMessage: document.getElementById('deleteMessage'),
    executionsModal: document.getElementById('executionsModal'),
    closeExecutionsModal: document.getElementById('closeExecutionsModal'),
    closeExecutionsBtn: document.getElementById('closeExecutionsBtn'),
    executionsModalTitle: document.getElementById('executionsModalTitle'),
    executionsLoading: document.getElementById('executionsLoading'),
    executionsList: document.getElementById('executionsList'),
    executionsEmpty: document.getElementById('executionsEmpty'),
    outputModal: document.getElementById('outputModal'),
    closeOutputModal: document.getElementById('closeOutputModal'),
    closeOutputBtn: document.getElementById('closeOutputBtn'),
    outputModalTitle: document.getElementById('outputModalTitle'),
    outputTaskName: document.getElementById('outputTaskName'),
    outputTaskStatus: document.getElementById('outputTaskStatus'),
    outputTaskStarted: document.getElementById('outputTaskStarted'),
    outputTaskCompleted: document.getElementById('outputTaskCompleted'),
    outputContent: document.getElementById('outputContent'),
    copyOutputBtn: document.getElementById('copyOutputBtn'),
    refreshOutputBtn: document.getElementById('refreshOutputBtn'),
    loadingMore: document.getElementById('loadingMore'),
    loadMoreTrigger: document.getElementById('loadMoreTrigger')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    currentTheme = document.body.getAttribute('data-theme') || 'dark';
    syncThemeToLocalStorage();
    loadUserInfo();
    initializeEventListeners();
    loadSchedules(true);
});

// 同步主题到 localStorage
function syncThemeToLocalStorage() {
    const cachedTheme = localStorage.getItem('user_theme');
    if (cachedTheme !== currentTheme) {
        localStorage.setItem('user_theme', currentTheme);
        localStorage.setItem('theme_timestamp', Date.now().toString());
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
            elements.username.textContent = user.username;
            const serverTheme = user.theme || 'dark';
            // 同步主题色到 localStorage
            localStorage.setItem('user_theme', serverTheme);
            localStorage.setItem('theme_timestamp', Date.now().toString());
            if (currentTheme !== serverTheme) {
                applyTheme(serverTheme);
            }
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

// 初始化事件监听器
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

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && elements.sidebar) {
            elements.sidebar.classList.add('active');
        }
    });

    elements.createScheduleBtn?.addEventListener('click', () => {
        openScheduleModal();
    });

    elements.refreshListBtn?.addEventListener('click', () => {
        refreshTaskList();
    });

    elements.closeScheduleModal?.addEventListener('click', () => {
        closeScheduleModal();
    });
    elements.cancelScheduleBtn?.addEventListener('click', () => {
        closeScheduleModal();
    });

    elements.saveScheduleBtn?.addEventListener('click', async () => {
        await saveSchedule();
    });

    elements.schedulePreset?.addEventListener('change', () => {
        updateCronFromPreset();
    });

    elements.closeDeleteModal?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.cancelDeleteBtn?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.confirmDeleteBtn?.addEventListener('click', async () => {
        await deleteSchedule();
    });

    elements.scheduleModal?.addEventListener('click', (e) => {
        if (e.target === elements.scheduleModal) {
            closeScheduleModal();
        }
    });
    elements.confirmDeleteModal?.addEventListener('click', (e) => {
        if (e.target === elements.confirmDeleteModal) {
            closeDeleteModal();
        }
    });

    elements.scheduleForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        saveSchedule();
    });

    elements.closeExecutionsModal?.addEventListener('click', () => {
        closeExecutionsModal();
    });
    elements.closeExecutionsBtn?.addEventListener('click', () => {
        closeExecutionsModal();
    });
    elements.executionsModal?.addEventListener('click', (e) => {
        if (e.target === elements.executionsModal) {
            closeExecutionsModal();
        }
    });

    elements.closeOutputModal?.addEventListener('click', () => {
        closeOutputModal();
    });
    elements.closeOutputBtn?.addEventListener('click', () => {
        closeOutputModal();
    });
    elements.outputModal?.addEventListener('click', (e) => {
        if (e.target === elements.outputModal) {
            closeOutputModal();
        }
    });
    elements.copyOutputBtn?.addEventListener('click', () => {
        copyOutputToClipboard();
    });
    elements.refreshOutputBtn?.addEventListener('click', () => {
        refreshOutput();
    });

    // 防抖搜索
    let searchTimeout;
    elements.searchTaskInput?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = e.target.value.trim();
            currentPage = 1;
            tasks = [];
            loadSchedules(true);
        }, 300);
    });

    // 无限滚动 - 使用 IntersectionObserver
    if (elements.schedulesList && elements.loadMoreTrigger) {
        elements.schedulesList.appendChild(elements.loadMoreTrigger);

        scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && hasMore && !isLoading) {
                    loadSchedules(false);
                }
            });
        }, { threshold: 0.1 });

        scrollObserver.observe(elements.loadMoreTrigger);
    }
}

// 加载异步任务列表
async function loadSchedules(reset = false) {
    if (isLoading) return;
    isLoading = true;

    try {
        if (reset) {
            elements.schedulesList.innerHTML = `
                <div class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>加载中...</span>
                </div>
            `;
        } else if (elements.loadingMore) {
            elements.loadingMore.style.display = 'block';
        }

        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            search: searchTerm
        });

        const response = await fetch(`/api/async_tasks?${params}`, {
            credentials: 'same-origin'
        });

        if (response.ok) {
            const data = await response.json();
            
            if (reset) {
                tasks = data.tasks || [];
            } else {
                tasks = [...tasks, ...(data.tasks || [])];
            }
            
            totalPages = data.total_pages || 1;
            hasMore = currentPage < totalPages;
            currentPage++;

            renderSchedules(reset);
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else {
            throw new Error('加载失败');
        }
    } catch (error) {
        console.error('加载异步任务失败:', error);
        if (reset) {
            elements.schedulesList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>加载失败</h3>
                    <p>无法加载异步任务，请刷新页面重试</p>
                    <button class="btn btn-primary" onclick="loadSchedules(true)">重试</button>
                </div>
            `;
        } else if (elements.loadingMore) {
            elements.loadingMore.innerHTML = `
                <i class="fas fa-exclamation-circle"></i>
                <span>加载失败，点击重试</span>
            `;
            elements.loadingMore.style.cursor = 'pointer';
            elements.loadingMore.onclick = () => {
                elements.loadingMore.innerHTML = `
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>加载更多...</span>
                `;
                elements.loadingMore.style.cursor = 'default';
                elements.loadingMore.onclick = null;
                loadSchedules(false);
            };
        }
    } finally {
        isLoading = false;
        if (elements.loadingMore && hasMore) {
            elements.loadingMore.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <span>加载更多...</span>
            `;
            elements.loadingMore.style.cursor = 'default';
            elements.loadingMore.onclick = null;
        }
        // 重新观察loadMoreTrigger
        if (scrollObserver && elements.loadMoreTrigger) {
            scrollObserver.observe(elements.loadMoreTrigger);
        }
    }
}

// 渲染异步任务列表
function renderSchedules(reset = false) {
    if (!tasks || tasks.length === 0) {
        if (searchTerm) {
            elements.schedulesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>未找到匹配的任务</h3>
                    <p>尝试使用其他关键词搜索</p>
                </div>
            `;
        } else {
            elements.schedulesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <h3>暂无异步任务</h3>
                    <p>点击"新建异步任务"按钮创建一个异步任务</p>
                </div>
            `;
        }
        return;
    }

    const headerHtml = `
        <div class="schedules-list-container">
            <div class="schedule-list-header">
                <div class="schedule-list-col schedule-list-col-name">任务名称</div>
                <div class="schedule-list-col schedule-list-col-status">状态</div>
                <div class="schedule-list-col schedule-list-col-command">命令</div>
                <div class="schedule-list-col schedule-list-col-created">创建/执行时间</div>
                <div class="schedule-list-col schedule-list-col-actions">操作</div>
            </div>
    `;

    if (reset) {
        elements.schedulesList.innerHTML = headerHtml;
    }

    const rowsHtml = tasks.map(task => {
        const createdAt = task.created_at ? new Date(task.created_at).toLocaleString('zh-CN') : '-';
        const startedAt = task.started_at ? new Date(task.started_at).toLocaleString('zh-CN') : '-';
        const completedAt = task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '-';
        const statusTextMap = {
            'pending': '等待中',
            'scheduled': '已调度',
            'running': '运行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消'
        };
        const statusText = statusTextMap[task.status] || task.status;
        
        let statusExtra = '';
        if (task.status === 'failed' && task.error_message) {
            const match = task.error_message?.match(/Exit code: (-?\d+)/);
            if (match) {
                statusExtra = ` (${match[1]})`;
            }
        }
        
        return `
            <div class="schedule-list-item" data-id="${task.id}">
                <div class="schedule-list-col schedule-list-col-name">
                    <div style="font-weight: 500;">${escapeHtml(task.task_name)}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">${escapeHtml(task.description || '无描述')}</div>
                </div>
                <div class="schedule-list-col schedule-list-col-status">
                    <span class="status-badge status-${task.status}">${statusText}${statusExtra}</span>
                </div>
                <div class="schedule-list-col schedule-list-col-command">
                    <code style="font-size: 12px; word-break: break-all;">${escapeHtml(task.command)}</code>
                </div>
                <div class="schedule-list-col schedule-list-col-created">
                    <div>创建: ${createdAt}</div>
                    ${startedAt !== '-' ? `<div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">开始: ${startedAt}</div>` : ''}
                    ${completedAt !== '-' ? `<div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">完成: ${completedAt}</div>` : ''}
                </div>
                <div class="schedule-list-col schedule-list-col-actions">
                    <button class="btn-icon-sm output" data-id="${task.id}" title="查看输出">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon-sm edit" data-id="${task.id}" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${task.status === 'failed' || task.status === 'cancelled' || task.status === 'completed' ? `
                    <button class="btn-icon-sm retry" data-id="${task.id}" title="重试">
                        <i class="fas fa-redo"></i>
                    </button>` : ''}
                    ${task.status === 'running' ? `
                    <button class="btn-icon-sm cancel" data-id="${task.id}" title="取消">
                        <i class="fas fa-stop"></i>
                    </button>` : ''}
                    <button class="btn-icon-sm delete" data-id="${task.id}" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (reset) {
        const footerHtml = `</div>`;
        elements.schedulesList.innerHTML = headerHtml + rowsHtml + footerHtml;
        
        if (elements.loadMoreTrigger && elements.schedulesList && !elements.schedulesList.contains(elements.loadMoreTrigger)) {
            elements.schedulesList.appendChild(elements.loadMoreTrigger);
        }
    } else {
        const container = elements.schedulesList.querySelector('.schedules-list-container');
        if (container) {
            const existingItems = container.querySelectorAll('.schedule-list-item');
            existingItems.forEach(item => item.remove());
            container.insertAdjacentHTML('beforeend', rowsHtml);
        }
    }

    // 绑定按钮事件
    document.querySelectorAll('.btn-icon-sm.output').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.target.closest('.schedule-list-item').dataset.id;
            const task = tasks.find(t => t.id == taskId);
            if (task) showTaskOutput(task);
        });
    });

    document.querySelectorAll('.btn-icon-sm.edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.target.closest('.schedule-list-item').dataset.id;
            const task = tasks.find(t => t.id == taskId);
            if (task) editTask(task);
        });
    });

    document.querySelectorAll('.btn-icon-sm.retry').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.target.closest('.schedule-list-item').dataset.id;
            const task = tasks.find(t => t.id == taskId);
            if (task) retryTask(task);
        });
    });

    document.querySelectorAll('.btn-icon-sm.cancel').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.target.closest('.schedule-list-item').dataset.id;
            const task = tasks.find(t => t.id == taskId);
            if (task) cancelTask(task);
        });
    });

    document.querySelectorAll('.btn-icon-sm.delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const taskId = e.target.closest('.schedule-list-item').dataset.id;
            const task = tasks.find(t => t.id == taskId);
            if (task) deleteTask(task);
        });
    });

    // 显示"没有更多数据"提示
    if (!reset && !hasMore && tasks.length > 0 && elements.loadingMore) {
        elements.loadingMore.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>已加载全部数据</span>
        `;
        elements.loadingMore.style.display = 'block';
    }
}

// 编辑任务
function editTask(task) {
    const scheduleData = {
        id: task.id,
        name: task.task_name,
        description: task.description || '',
        command: task.command,
        status: task.status,
        cron: '',
        preset: '',
        delay: 0
    };
    openScheduleModal(scheduleData);
}

// 重试任务
async function retryTask(task) {
    if (!confirm(`确定要重试任务 "${task.task_name}" 吗？`)) {
        return;
    }
    try {
        const response = await fetch('/api/async_tasks', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                task_name: `${task.task_name} (重试)`,
                description: task.description || '',
                command: task.command,
                delay_minutes: 0
            })
        });
        if (response.ok) {
            showToast('重试任务已创建', 'success');
            currentPage = 1;
            tasks = [];
            await loadSchedules(true);
        } else {
            const error = await response.text();
            showToast(`重试失败: ${error}`, 'error');
        }
    } catch (error) {
        console.error('重试任务失败:', error);
        showToast('重试失败，请检查网络连接', 'error');
    }
}

// 删除任务
function deleteTask(task) {
    openDeleteModal(task);
}

// 打开异步任务模态框
function openScheduleModal(schedule = null) {
    elements.scheduleForm.reset();
    elements.scheduleId.value = '';

    if (schedule) {
        elements.scheduleModalTitle.textContent = '编辑异步任务';
        elements.scheduleId.value = schedule.id;
        elements.scheduleName.value = schedule.name;
        elements.scheduleDescription.value = schedule.description || '';
        elements.scheduleCron.value = schedule.cron;
        elements.schedulePreset.value = schedule.preset || '';
        elements.scheduleCommand.value = schedule.command;
        elements.scheduleStatus.value = schedule.status;
        elements.scheduleDelay.value = schedule.delay || 0;
    } else {
        elements.scheduleModalTitle.textContent = '新建异步任务';
        elements.scheduleStatus.value = 'active';
        elements.scheduleDelay.value = 0;
    }

    elements.scheduleModal.classList.add('active');
}

// 关闭异步任务模态框
function closeScheduleModal() {
    elements.scheduleModal.classList.remove('active');
    elements.scheduleForm.reset();
}

// 更新 cron 表达式根据预设
function updateCronFromPreset() {
    const preset = elements.schedulePreset.value;
    const cronMap = {
        'every_minute': '* * * * *',
        'every_5min': '*/5 * * * *',
        'every_10min': '*/10 * * * *',
        'every_15min': '*/15 * * * *',
        'every_30min': '*/30 * * * *',
        'hourly': '0 * * * *',
        'hourly_30': '30 * * * *',
        'hourly_1': '1 * * * *',
        'hourly_15': '15 * * * *',
        'hourly_45': '45 * * * *',
        'daily_midnight': '0 0 * * *',
        'daily_6am': '0 6 * * *',
        'daily_9am': '0 9 * * *',
        'daily_12pm': '0 12 * * *',
        'daily_6pm': '0 18 * * *',
        'daily_9pm': '0 21 * * *',
        'weekly_monday': '0 0 * * 1',
        'weekly_friday': '0 0 * * 5',
        'weekday_9am': '0 9 * * 1-5',
        'monthly_1st': '0 0 1 * *',
        'monthly_15th': '0 0 15 * *'
    };
    if (cronMap[preset]) {
        elements.scheduleCron.value = cronMap[preset];
    }
}

// 保存异步任务
async function saveSchedule() {
    const scheduleId = elements.scheduleId.value;
    const scheduleData = {
        task_name: elements.scheduleName.value.trim(),
        description: elements.scheduleDescription.value.trim(),
        command: elements.scheduleCommand.value.trim(),
        delay_minutes: parseInt(elements.scheduleDelay.value) || 0
    };

    if (!scheduleData.task_name) {
        alert('请输入任务名称');
        return;
    }
    if (!scheduleData.command) {
        alert('请输入执行命令');
        return;
    }

    try {
        const url = scheduleId ? `/api/async_tasks/${scheduleId}` : '/api/async_tasks';
        const method = scheduleId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(scheduleData)
        });

        if (response.ok) {
            closeScheduleModal();
            showToast(scheduleId ? '任务已更新' : '任务已创建', 'success');
            currentPage = 1;
            tasks = [];
            await loadSchedules(true);
        } else {
            const error = await response.text();
            showToast(`保存失败: ${error}`, 'error');
        }
    } catch (error) {
        console.error('保存异步任务失败:', error);
        showToast('保存失败，请检查网络连接', 'error');
    }
}

// 打开删除确认模态框
function openDeleteModal(schedule) {
    scheduleToDelete = schedule;
    elements.deleteMessage.textContent = `确定要删除异步任务 "${schedule.task_name || schedule.name}" 吗？此操作不可撤销。`;
    elements.confirmDeleteModal.classList.add('active');
}

// 关闭删除确认模态框
function closeDeleteModal() {
    elements.confirmDeleteModal.classList.remove('active');
    scheduleToDelete = null;
}

// 删除异步任务
async function deleteSchedule() {
    if (!scheduleToDelete) return;

    try {
        const response = await fetch(`/api/async_tasks/${scheduleToDelete.id}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        if (response.ok) {
            closeDeleteModal();
            showToast('任务已删除', 'success');
            currentPage = 1;
            tasks = [];
            await loadSchedules(true);
        } else {
            const error = await response.text();
            showToast(`删除失败: ${error}`, 'error');
        }
    } catch (error) {
        console.error('删除异步任务失败:', error);
        showToast('删除失败，请检查网络连接', 'error');
    }
}

// 关闭执行记录模态框
function closeExecutionsModal() {
    elements.executionsModal.classList.remove('active');
    currentScheduleId = null;
}

// 显示异步任务执行记录（使用模态框）
async function showScheduleExecutions(schedule) {
    currentScheduleId = schedule.id;
    elements.executionsModalTitle.textContent = `异步任务 "${schedule.name}" 的执行记录`;
    
    elements.executionsLoading.style.display = 'block';
    elements.executionsList.style.display = 'none';
    elements.executionsEmpty.style.display = 'none';
    
    elements.executionsModal.classList.add('active');
    
    try {
        const response = await fetch(`/api/async_tasks/${schedule.id}/executions`, {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const data = await response.json();
            const executions = data.executions || [];
            
            elements.executionsLoading.style.display = 'none';
            
            if (executions.length === 0) {
                elements.executionsEmpty.style.display = 'block';
                return;
            }
            
            renderExecutionsList(executions);
            elements.executionsList.style.display = 'block';
        } else {
            const error = await response.text();
            alert(`加载执行记录失败: ${error}`);
            closeExecutionsModal();
        }
    } catch (error) {
        console.error('加载执行记录失败:', error);
        alert('加载执行记录失败，请检查网络连接');
        closeExecutionsModal();
    }
}

// 渲染执行记录列表
function renderExecutionsList(executions) {
    const executionsHtml = executions.map((exec, index) => {
        const statusText = {
            'pending': '待执行',
            'running': '执行中',
            'completed': '已完成',
            'failed': '失败'
        }[exec.status] || exec.status;
        
        const statusClass = {
            'pending': 'status-pending',
            'running': 'status-running',
            'completed': 'status-completed',
            'failed': 'status-failed'
        }[exec.status] || 'status-pending';
        
        const startTime = exec.started_at ? new Date(exec.started_at).toLocaleString() : '未开始';
        const endTime = exec.completed_at ? new Date(exec.completed_at).toLocaleString() : '未完成';
        const duration = exec.started_at && exec.completed_at ? 
            Math.round((new Date(exec.completed_at) - new Date(exec.started_at)) / 1000) + '秒' : '-';
        
        return `
            <div class="execution-item" data-id="${exec.id}">
                <div class="execution-header">
                    <div class="execution-info">
                        <span class="execution-index">#${index + 1}</span>
                        <span class="execution-status ${statusClass}">${statusText}</span>
                        <span class="execution-time">${startTime}</span>
                    </div>
                    <button class="btn btn-icon toggle-details-btn" title="查看详情">
                        <i class="fas fa-chevron-down"></i>
                    </button>
                </div>
                <div class="execution-details" style="display: none;">
                    <div class="detail-row">
                        <span class="detail-label">开始时间:</span>
                        <span class="detail-value">${startTime}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">结束时间:</span>
                        <span class="detail-value">${endTime}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">执行时长:</span>
                        <span class="detail-value">${duration}</span>
                    </div>
                    ${exec.error_message ? `
                    <div class="detail-row">
                        <span class="detail-label">错误信息:</span>
                        <span class="detail-value error-text">${escapeHtml(exec.error_message)}</span>
                    </div>
                    ` : ''}
                    ${exec.output ? `
                    <div class="detail-row">
                        <span class="detail-label">输出:</span>
                        <pre class="detail-value output-text">${escapeHtml(exec.output)}</pre>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    elements.executionsList.innerHTML = executionsHtml;
    
    document.querySelectorAll('.toggle-details-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const executionItem = e.target.closest('.execution-item');
            const details = executionItem.querySelector('.execution-details');
            const icon = e.target.closest('button').querySelector('i');
            
            if (details.style.display === 'none') {
                details.style.display = 'block';
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                details.style.display = 'none';
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
    });
}

// HTML 转义辅助函数
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 显示任务输出（打开实时输出模态框）
async function showTaskOutput(task) {
    currentOutputTaskId = task.id;
    elements.outputTaskName.textContent = task.task_name;
    elements.outputTaskStatus.textContent = {'pending': '等待中', 'scheduled': '已调度', 'running': '运行中', 'completed': '已完成', 'failed': '失败'}[task.status] || task.status;
    elements.outputTaskStarted.textContent = task.started_at ? new Date(task.started_at).toLocaleString('zh-CN') : '-';
    elements.outputTaskCompleted.textContent = task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '-';
    
    elements.outputModal.classList.add('active');
    
    startOutputPolling();
}

// 开始轮询输出
function startOutputPolling() {
    if (outputPollInterval) {
        clearInterval(outputPollInterval);
    }
    loadOutput();
    outputPollInterval = setInterval(loadOutput, 2000);
}

// 加载输出内容
async function loadOutput() {
    if (!currentOutputTaskId) return;
    
    try {
        const response = await fetch(`/api/async_tasks/${currentOutputTaskId}/output`, {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const data = await response.json();
            elements.outputContent.textContent = data.output || '无输出';
            const terminal = elements.outputContent.parentElement;
            terminal.scrollTop = terminal.scrollHeight;
            
            await updateTaskMeta();
            
            const task = tasks.find(t => t.id == currentOutputTaskId);
            if (task && (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled')) {
                stopOutputPolling();
            }
        } else {
            console.error('获取输出失败');
        }
    } catch (error) {
        console.error('获取输出失败:', error);
    }
}

async function updateTaskMeta() {
    if (!currentOutputTaskId) return;
    
    try {
        const response = await fetch(`/api/async_tasks/${currentOutputTaskId}`, {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const data = await response.json();
            const task = data.task;
            if (task) {
                elements.outputTaskStatus.textContent = {'pending': '等待中', 'scheduled': '已调度', 'running': '运行中', 'completed': '已完成', 'failed': '失败', 'cancelled': '已取消'}[task.status] || task.status;
                elements.outputTaskStarted.textContent = task.started_at ? new Date(task.started_at).toLocaleString('zh-CN') : '-';
                elements.outputTaskCompleted.textContent = task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '-';
            }
        }
    } catch (error) {
        console.error('更新任务元数据失败:', error);
    }
}

// 停止轮询输出
function stopOutputPolling() {
    if (outputPollInterval) {
        clearInterval(outputPollInterval);
        outputPollInterval = null;
    }
}

// 关闭输出模态框
function closeOutputModal() {
    elements.outputModal.classList.remove('active');
    stopOutputPolling();
    currentOutputTaskId = null;
}

// 复制输出到剪贴板
function copyOutputToClipboard() {
    const text = elements.outputContent.textContent;
    navigator.clipboard.writeText(text).then(() => {
        showToast('输出已复制到剪贴板', 'success');
    }).catch(err => {
        console.error('复制失败:', err);
        showToast('复制失败', 'error');
    });
}

// 手动刷新输出
function refreshOutput() {
    loadOutput();
}

// 启动全局轮询（用于更新任务状态）
function startGlobalPolling() {
    if (globalPollInterval) {
        clearInterval(globalPollInterval);
    }
    checkTasksNeedPolling();
    globalPollInterval = setInterval(checkTasksNeedPolling, 5000);
}

// 停止全局轮询
function stopGlobalPolling() {
    if (globalPollInterval) {
        clearInterval(globalPollInterval);
        globalPollInterval = null;
    }
}

// 检查是否有需要轮询的任务（scheduled 或 running）
function checkTasksNeedPolling() {
    const hasActiveTasks = tasks.some(task => 
        task.status === 'scheduled' || task.status === 'running'
    );
    if (hasActiveTasks) {
        loadSchedules(false);
    }
}

// 取消任务
async function cancelTask(task) {
    if (!confirm(`确定要取消任务 "${task.task_name}" 吗？`)) {
        return;
    }
    try {
        const response = await fetch(`/api/async_tasks/${task.id}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ status: 'cancelled' })
        });
        if (response.ok) {
            showToast('任务已取消', 'success');
            currentPage = 1;
            tasks = [];
            await loadSchedules(true);
        } else {
            showToast('取消失败', 'error');
        }
    } catch (error) {
        console.error('取消失败:', error);
        showToast('取消失败，请检查网络连接', 'error');
    }
}

// 刷新任务列表（带防抖）
function refreshTaskList() {
    if (isRefreshing) return;
    
    clearTimeout(refreshDebounceTimer);
    refreshDebounceTimer = setTimeout(() => {
        performRefresh();
    }, 300);
}

// 执行刷新操作
async function performRefresh() {
    if (isRefreshing) return;
    isRefreshing = true;
    
    elements.refreshListBtn.classList.add('refreshing');
    elements.refreshListBtn.disabled = true;
    
    try {
        currentPage = 1;
        tasks = [];
        await loadSchedules(true);
        showToast('刷新成功', 'success');
    } catch (error) {
        console.error('刷新失败:', error);
        showToast('刷新失败，请重试', 'error');
    } finally {
        isRefreshing = false;
        elements.refreshListBtn.classList.remove('refreshing');
        elements.refreshListBtn.disabled = false;
    }
}

// 显示提示消息
function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.refresh-toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = `refresh-toast ${type}`;
    
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${iconMap[type] || iconMap.info}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
