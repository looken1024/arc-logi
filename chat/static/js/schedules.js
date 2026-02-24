// 定时任务管理页面 JavaScript

// 全局状态
let currentUser = null;
let schedules = [];
let scheduleToDelete = null;
let currentScheduleId = null;
let currentTheme = 'dark';

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    schedulesList: document.getElementById('schedulesList'),
    username: document.getElementById('username'),
    createScheduleBtn: document.getElementById('createScheduleBtn'),
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
    executionsEmpty: document.getElementById('executionsEmpty')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    initializeEventListeners();
    loadSchedules();
});

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
            currentTheme = user.theme || 'dark';
            applyTheme(currentTheme);
        } else {
            // 未登录,重定向到登录页
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

    // 侧边栏切换
    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('active');
    });

    // 移动端点击主内容区关闭侧边栏
    mainContent?.addEventListener('click', (e) => {
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
        if (window.innerWidth > 768 && elements.sidebar) {
            elements.sidebar.classList.add('active');
        }
    });

    // 新建定时任务按钮
    elements.createScheduleBtn?.addEventListener('click', () => {
        openScheduleModal();
    });

    // 关闭模态框按钮
    elements.closeScheduleModal?.addEventListener('click', () => {
        closeScheduleModal();
    });
    elements.cancelScheduleBtn?.addEventListener('click', () => {
        closeScheduleModal();
    });

    // 保存定时任务按钮
    elements.saveScheduleBtn?.addEventListener('click', async () => {
        await saveSchedule();
    });

    // 预设选择改变时更新 cron 表达式
    elements.schedulePreset?.addEventListener('change', () => {
        updateCronFromPreset();
    });

    // 确认删除模态框
    elements.closeDeleteModal?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.cancelDeleteBtn?.addEventListener('click', () => {
        closeDeleteModal();
    });
    elements.confirmDeleteBtn?.addEventListener('click', async () => {
        await deleteSchedule();
    });

    // 点击模态框背景关闭
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

    // 表单提交
    elements.scheduleForm?.addEventListener('submit', (e) => {
        e.preventDefault();
        saveSchedule();
    });

    // 执行记录模态框
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
}

// 加载定时任务列表
async function loadSchedules() {
    try {
        elements.schedulesList.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>加载中...</span>
            </div>
        `;

        const response = await fetch('/api/schedules', {
            credentials: 'same-origin'
        });
        if (response.ok) {
            schedules = await response.json();
            renderSchedules();
        } else {
            elements.schedulesList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clock"></i>
                    <h3>暂无定时任务</h3>
                    <p>点击“新建定时任务”按钮创建一个定时任务</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('加载定时任务失败:', error);
        elements.schedulesList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>无法加载定时任务，请刷新页面重试</p>
            </div>
        `;
    }
}

// 渲染定时任务列表
function renderSchedules() {
    if (!schedules || schedules.length === 0) {
        elements.schedulesList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clock"></i>
                <h3>暂无定时任务</h3>
                <p>点击"新建定时任务"按钮创建一个定时任务</p>
            </div>
        `;
        return;
    }

    const schedulesHtml = schedules.map(schedule => {
        const lastRun = schedule.last_run_at ? new Date(schedule.last_run_at).toLocaleString('zh-CN') : '从未运行';
        const nextRun = schedule.next_run_at ? new Date(schedule.next_run_at).toLocaleString('zh-CN') : '-';
        
        return `
        <div class="schedule-card" data-id="${schedule.id}">
            <div class="schedule-card-header">
                <h3 class="schedule-name">${escapeHtml(schedule.name)}</h3>
                <span class="schedule-status ${schedule.status}">
                    ${schedule.status === 'active' ? '启用' : '暂停'}
                </span>
            </div>
            <div class="schedule-card-body">
                <p class="schedule-description">${escapeHtml(schedule.description || '无描述')}</p>
                <div class="schedule-details">
                    <div class="detail-item">
                        <i class="fas fa-clock"></i>
                        <span class="detail-label">执行周期</span>
                        <code class="cron-expression">${escapeHtml(schedule.cron)}</code>
                    </div>
                    <div class="detail-item">
                        <i class="fas fa-terminal"></i>
                        <span class="detail-label">执行命令</span>
                        <span class="schedule-command">${escapeHtml(schedule.command)}</span>
                    </div>
                </div>
                <div class="schedule-meta">
                    <div class="meta-item">
                        <i class="fas fa-play-circle"></i>
                        <span>上次运行: ${lastRun}</span>
                    </div>
                    <div class="meta-item">
                        <i class="fas fa-forward"></i>
                        <span>下次运行: ${nextRun}</span>
                    </div>
                </div>
            </div>
            <div class="schedule-card-footer">
                <button class="btn btn-icon run-schedule-btn" title="立即执行">
                    <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-icon executions-schedule-btn" title="执行记录">
                    <i class="fas fa-history"></i>
                </button>
                <button class="btn btn-icon edit-schedule-btn" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon delete-schedule-btn" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `}).join('');

    elements.schedulesList.innerHTML = `
        <div class="schedules-grid">
            ${schedulesHtml}
        </div>
    `;

    // 绑定编辑和删除按钮事件
    document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleCard = e.target.closest('.schedule-card');
            const scheduleId = scheduleCard.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                openScheduleModal(schedule);
            }
        });
    });

    document.querySelectorAll('.delete-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleCard = e.target.closest('.schedule-card');
            const scheduleId = scheduleCard.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                openDeleteModal(schedule);
            }
        });
    });

    // 绑定立即执行按钮事件
    document.querySelectorAll('.run-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleCard = e.target.closest('.schedule-card');
            const scheduleId = scheduleCard.dataset.id;
            const schedule = schedules.find(s => s.id == scheduleId);
            if (schedule) {
                runSchedule(schedule);
            }
        });
    });

    // 绑定执行记录按钮事件
    document.querySelectorAll('.executions-schedule-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const scheduleCard = e.target.closest('.schedule-card');
            const scheduleId = scheduleCard.dataset.id;
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

    // 简单验证
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
            await loadSchedules();
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
            await loadSchedules();
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
            // 可以在这里刷新执行记录或任务列表
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
    
    // 显示加载状态
    elements.executionsLoading.style.display = 'block';
    elements.executionsList.style.display = 'none';
    elements.executionsEmpty.style.display = 'none';
    
    // 打开模态框
    elements.executionsModal.classList.add('active');
    
    try {
        const response = await fetch(`/api/schedules/${schedule.id}/executions`, {
            credentials: 'same-origin'
        });
        if (response.ok) {
            const data = await response.json();
            const executions = data.executions || [];
            
            // 隐藏加载状态
            elements.executionsLoading.style.display = 'none';
            
            if (executions.length === 0) {
                elements.executionsEmpty.style.display = 'block';
                return;
            }
            
            // 渲染执行记录列表
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
    
    // 绑定展开/收起详情事件
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
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}