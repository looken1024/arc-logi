// 定时任务管理页面 JavaScript

// 全局状态
let currentUser = null;
let schedules = [];
let scheduleToDelete = null;
let currentScheduleId = null;
let currentTheme = 'dark';

// 分页状态
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let isLoading = false;
let hasMore = true;
let searchTerm = '';

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    schedulesList: document.getElementById('schedulesList'),
    username: document.getElementById('username'),
    createScheduleBtn: document.getElementById('createScheduleBtn'),
    searchScheduleInput: document.getElementById('searchScheduleInput'),
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
    loadingMore: document.getElementById('loadingMore'),
    loadMoreTrigger: document.getElementById('loadMoreTrigger')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    applyThemeFromCache();
    loadUserInfo();
    initializeEventListeners();
    loadSchedules(true);
    startThemeSync();
});

// 从 localStorage 应用主题色(早期加载，避免闪烁)
function applyThemeFromCache() {
    const cachedTheme = localStorage.getItem('user_theme');
    if (cachedTheme) {
        document.body.setAttribute('data-theme', cachedTheme);
        currentTheme = cachedTheme;
    }
}

// 定时同步主题（每5分钟执行一次）
let themeSyncInterval = null;
let themeVarsCache = null;
let themeVarsElement = null;

function startThemeSync() {
    if (themeSyncInterval) {
        clearInterval(themeSyncInterval);
    }
    loadThemeVars();
    themeSyncInterval = setInterval(async () => {
        await syncTheme();
        await loadThemeVars();
    }, 5 * 60 * 1000);
}

async function loadThemeVars() {
    try {
        const response = await fetch('/api/theme/css-vars', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const cssText = await response.text();
            if (!themeVarsElement) {
                themeVarsElement = document.createElement('style');
                themeVarsElement.id = 'theme-vars-dynamic';
                document.head.appendChild(themeVarsElement);
            }
            themeVarsElement.textContent = cssText;
            themeVarsCache = cssText;
        }
    } catch (error) {
        console.error('加载主题变量失败:', error);
    }
}

async function syncTheme() {
    try {
        const response = await fetch('/api/user', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const user = await response.json();
            const newTheme = user.theme || 'dark';
            if (newTheme !== currentTheme) {
                applyTheme(newTheme);
            }
        }
    } catch (error) {
        console.error('同步主题失败:', error);
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
            const cachedTheme = localStorage.getItem('user_theme');
            if (cachedTheme !== serverTheme) {
                localStorage.setItem('user_theme', serverTheme);
                localStorage.setItem('theme_timestamp', Date.now().toString());
                const appliedTheme = document.body.getAttribute('data-theme');
                if (appliedTheme !== serverTheme) {
                    applyTheme(serverTheme);
                }
            }
            await loadThemeVars();
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
        // 侧边栏状态保持不变，由用户手动控制
    });

    elements.createScheduleBtn?.addEventListener('click', () => {
        openScheduleModal();
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

    // 防抖搜索
    let searchTimeout;
    elements.searchScheduleInput?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = e.target.value.trim();
            currentPage = 1;
            schedules = [];
            loadSchedules(true);
        }, 300);
    });

    // 无限滚动
    if (elements.schedulesList) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && hasMore && !isLoading) {
                    loadSchedules(false);
                }
            });
        }, { threshold: 0.1 });

        if (elements.loadMoreTrigger) {
            observer.observe(elements.loadMoreTrigger);
        }
    }
}

// 加载定时任务列表
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

        const response = await fetch(`/api/schedules?${params}`, {
            credentials: 'same-origin'
        });

        if (response.ok) {
            const data = await response.json();
            
            if (reset) {
                schedules = data.schedules || [];
            } else {
                schedules = [...schedules, ...(data.schedules || [])];
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
        console.error('加载定时任务失败:', error);
        if (reset) {
            elements.schedulesList.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>加载失败</h3>
                    <p>无法加载定时任务，请刷新页面重试</p>
                    <button class="btn btn-primary" onclick="loadSchedules(true)">重试</button>
                </div>
            `;
        }
    } finally {
        isLoading = false;
        if (elements.loadingMore) {
            elements.loadingMore.style.display = 'none';
        }
    }
}

// 渲染定时任务列表
function renderSchedules(reset = false) {
    if (!schedules || schedules.length === 0) {
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
                    <h3>暂无定时任务</h3>
                    <p>点击"新建定时任务"按钮创建一个定时任务</p>
                </div>
            `;
        }
        return;
    }

    if (reset) {
        const headerHtml = `
            <div class="schedules-list-container">
                <div class="schedule-list-header">
                    <div class="schedule-list-col schedule-list-col-name">任务名称</div>
                    <div class="schedule-list-col schedule-list-col-status">状态</div>
                    <div class="schedule-list-col schedule-list-col-command">命令</div>
                    <div class="schedule-list-col schedule-list-col-cron">执行周期</div>
                    <div class="schedule-list-col schedule-list-col-created">执行时间</div>
                    <div class="schedule-list-col schedule-list-col-actions">操作</div>
                </div>
        `;
        elements.schedulesList.innerHTML = headerHtml;
    }

    const rowsHtml = schedules.map(schedule => {
        const createdAt = schedule.created_at ? new Date(schedule.created_at).toLocaleString('zh-CN') : '-';
        const lastRun = schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString('zh-CN') : '从未运行';
        const nextRun = schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString('zh-CN') : '-';
        
        return `
            <div class="schedule-list-item" data-id="${schedule.id}">
                <div class="schedule-list-col schedule-list-col-name">
                    <div style="font-weight: 500;">${escapeHtml(schedule.name)}</div>
                    ${schedule.description ? `<div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">${escapeHtml(schedule.description)}</div>` : ''}
                </div>
                <div class="schedule-list-col schedule-list-col-status">
                    <span class="status-badge ${schedule.status}">
                        ${schedule.status === 'active' ? '启用' : '暂停'}
                    </span>
                </div>
                <div class="schedule-list-col schedule-list-col-command">
                    <code style="font-size: 12px; word-break: break-all;">${escapeHtml(schedule.command)}</code>
                </div>
                <div class="schedule-list-col schedule-list-col-cron">
                    <code class="cron-expression">${escapeHtml(schedule.cron)}</code>
                </div>
                <div class="schedule-list-col schedule-list-col-created">
                    <div>创建: ${createdAt}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">上次: ${lastRun}</div>
                    <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">下次: ${nextRun}</div>
                </div>
                <div class="schedule-list-col schedule-list-col-actions">
                    <button class="btn-icon-sm run run-schedule-btn" title="立即执行">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn-icon-sm executions executions-schedule-btn" title="执行记录">
                        <i class="fas fa-history"></i>
                    </button>
                    <button class="btn-icon-sm edit edit-schedule-btn" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon-sm delete delete-schedule-btn" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    if (reset) {
        const footerHtml = `</div>`;
        elements.schedulesList.innerHTML += rowsHtml + footerHtml;
    } else {
        const container = elements.schedulesList.querySelector('.schedules-list-container');
        if (container) {
            const existingItems = container.querySelectorAll('.schedule-list-item');
            existingItems.forEach(item => item.remove());
            container.insertAdjacentHTML('beforeend', rowsHtml);
        }
    }

    // 绑定按钮事件
    document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleItem = e.target.closest('.schedule-list-item');
            const scheduleId = scheduleItem.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                openScheduleModal(schedule);
            }
        });
    });

    document.querySelectorAll('.delete-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleItem = e.target.closest('.schedule-list-item');
            const scheduleId = scheduleItem.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                openDeleteModal(schedule);
            }
        });
    });

    document.querySelectorAll('.run-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleItem = e.target.closest('.schedule-list-item');
            const scheduleId = scheduleItem.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                runSchedule(schedule);
            }
        });
    });

    document.querySelectorAll('.executions-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleItem = e.target.closest('.schedule-list-item');
            const scheduleId = scheduleItem.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                showScheduleExecutions(schedule);
            }
        });
    });
}

// 打开定时任务模态框
function openScheduleModal(schedule = null) {
    elements.scheduleForm.reset();
    elements.scheduleId.value = '';

    if (schedule) {
        elements.scheduleModalTitle.textContent = '编辑定时任务';
        elements.scheduleId.value = schedule.id;
        elements.scheduleName.value = schedule.name;
        elements.scheduleDescription.value = schedule.description || '';
        elements.scheduleCron.value = schedule.cron;
        elements.schedulePreset.value = schedule.preset || '';
        elements.scheduleCommand.value = schedule.command;
        elements.scheduleStatus.value = schedule.status;
    } else {
        elements.scheduleModalTitle.textContent = '新建定时任务';
        elements.scheduleStatus.value = 'active';
    }

    elements.scheduleModal.classList.add('active');
}

// 关闭定时任务模态框
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

// 保存定时任务
async function saveSchedule() {
    const scheduleId = elements.scheduleId.value;
    const scheduleData = {
        name: elements.scheduleName.value.trim(),
        description: elements.scheduleDescription.value.trim(),
        cron: elements.scheduleCron.value.trim(),
        preset: elements.schedulePreset.value,
        command: elements.scheduleCommand.value.trim(),
        status: elements.scheduleStatus.value
    };

    if (!scheduleData.name) {
        alert('请输入任务名称');
        return;
    }
    if (!scheduleData.cron) {
        alert('请输入 Cron 表达式');
        return;
    }
    if (!scheduleData.command) {
        alert('请输入执行命令');
        return;
    }

    try {
        const url = scheduleId ? `/api/schedules/${scheduleId}` : '/api/schedules';
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
            currentPage = 1;
            schedules = [];
            await loadSchedules(true);
        } else {
            const error = await response.text();
            alert(`保存失败: ${error}`);
        }
    } catch (error) {
        console.error('保存定时任务失败:', error);
        alert('保存失败，请检查网络连接');
    }
}

// 打开删除确认模态框
function openDeleteModal(schedule) {
    scheduleToDelete = schedule;
    elements.deleteMessage.textContent = `确定要删除定时任务 "${schedule.name}" 吗？此操作不可撤销。`;
    elements.confirmDeleteModal.classList.add('active');
}

// 关闭删除确认模态框
function closeDeleteModal() {
    elements.confirmDeleteModal.classList.remove('active');
    scheduleToDelete = null;
}

// 删除定时任务
async function deleteSchedule() {
    if (!scheduleToDelete) return;

    try {
        const response = await fetch(`/api/schedules/${scheduleToDelete.id}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        if (response.ok) {
            closeDeleteModal();
            currentPage = 1;
            schedules = [];
            await loadSchedules(true);
        } else {
            const error = await response.text();
            alert(`删除失败: ${error}`);
        }
    } catch (error) {
        console.error('删除定时任务失败:', error);
        alert('删除失败，请检查网络连接');
    }
}

// 立即执行定时任务
async function runSchedule(schedule) {
    if (!confirm(`确定要立即执行定时任务 "${schedule.name}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/schedules/${schedule.id}/execute`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const data = await response.json();
            alert(`执行已启动: ${data.message}\n执行ID: ${data.execution_id}`);
        } else {
            const error = await response.text();
            alert(`执行失败: ${error}`);
        }
    } catch (error) {
        console.error('执行定时任务失败:', error);
        alert('执行失败，请检查网络连接');
    }
}

// 关闭执行记录模态框
function closeExecutionsModal() {
    elements.executionsModal.classList.remove('active');
    currentScheduleId = null;
}

// 显示定时任务执行记录（使用模态框）
async function showScheduleExecutions(schedule) {
    currentScheduleId = schedule.id;
    elements.executionsModalTitle.textContent = `定时任务 "${schedule.name}" 的执行记录`;
    
    elements.executionsLoading.style.display = 'block';
    elements.executionsList.style.display = 'none';
    elements.executionsEmpty.style.display = 'none';
    
    elements.executionsModal.classList.add('active');
    
    try {
        const response = await fetch(`/api/schedules/${schedule.id}/executions`, {
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
