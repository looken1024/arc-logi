// 任务调度系统主类
class TaskScheduler {
    constructor() {
        this.tasks = [];
        this.taskGroups = [];
        this.logs = [];
        this.selectedTask = null;
        this.currentTab = 'graph';
        
        // 初始化数据
        this.initializeData();
        this.bindEvents();
        this.render();
        
        // 初始化Mermaid
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }
        });
    }

    // 初始化示例数据
    initializeData() {
        // 创建任务组
        this.taskGroups = [
            { id: 'daily', name: '日常任务', description: '每日定时执行的任务', color: '#3498db' },
            { id: 'backup', name: '备份任务', description: '数据备份相关任务', color: '#e74c3c' },
            { id: 'report', name: '报表任务', description: '报表生成和发送任务', color: '#2ecc71' },
            { id: 'cleanup', name: '清理任务', description: '系统清理和维护任务', color: '#f39c12' }
        ];

        // 创建示例任务
        this.tasks = [
            {
                id: 'task1',
                name: '数据库备份',
                groupId: 'backup',
                type: 'shell',
                command: 'mysqldump -u root -p database > backup.sql',
                description: '每日凌晨2点备份数据库',
                cronExpression: '0 0 2 * * ?',
                dependencies: [],
                enabled: true,
                status: 'active',
                timeout: 300,
                createdAt: new Date().toISOString(),
                lastRun: null,
                nextRun: this.getNextRunTime('0 0 2 * * ?')
            },
            {
                id: 'task2',
                name: '日志清理',
                groupId: 'cleanup',
                type: 'shell',
                command: 'find /var/log -name "*.log" -mtime +7 -delete',
                description: '清理7天前的日志文件',
                cronExpression: '0 0 3 * * ?',
                dependencies: ['task1'],
                enabled: true,
                status: 'active',
                timeout: 600,
                createdAt: new Date().toISOString(),
                lastRun: null,
                nextRun: this.getNextRunTime('0 0 3 * * ?')
            },
            {
                id: 'task3',
                name: '日报生成',
                groupId: 'report',
                type: 'python',
                command: 'python generate_daily_report.py',
                description: '生成每日业务报表',
                cronExpression: '0 0 8 * * ?',
                dependencies: ['task1', 'task2'],
                enabled: true,
                status: 'active',
                timeout: 180,
                createdAt: new Date().toISOString(),
                lastRun: null,
                nextRun: this.getNextRunTime('0 0 8 * * ?')
            },
            {
                id: 'task4',
                name: '邮件发送',
                groupId: 'report',
                type: 'http',
                command: 'POST https://api.email.com/send',
                description: '发送日报邮件',
                cronExpression: '0 30 8 * * ?',
                dependencies: ['task3'],
                enabled: true,
                status: 'active',
                timeout: 120,
                createdAt: new Date().toISOString(),
                lastRun: null,
                nextRun: this.getNextRunTime('0 30 8 * * ?')
            },
            {
                id: 'task5',
                name: '健康检查',
                groupId: 'daily',
                type: 'shell',
                command: 'curl -f http://localhost/health || exit 1',
                description: '检查系统健康状态',
                cronExpression: '*/5 * * * * ?',
                dependencies: [],
                enabled: true,
                status: 'active',
                timeout: 30,
                createdAt: new Date().toISOString(),
                lastRun: null,
                nextRun: this.getNextRunTime('*/5 * * * * ?')
            }
        ];

        // 生成示例日志
        this.generateSampleLogs();
    }

    // 生成示例日志
    generateSampleLogs() {
        const levels = ['info', 'warning', 'error'];
        const messages = [
            '任务执行开始',
            '任务执行成功',
            '任务执行失败',
            '连接超时',
            '内存使用率过高',
            '磁盘空间不足',
            '网络连接正常',
            '数据备份完成'
        ];

        for (let i = 0; i < 50; i++) {
            const date = new Date();
            date.setMinutes(date.getMinutes() - Math.floor(Math.random() * 1440)); // 随机时间
            
            this.logs.push({
                id: `log${i}`,
                taskId: this.tasks[Math.floor(Math.random() * this.tasks.length)].id,
                timestamp: date.toISOString(),
                level: levels[Math.floor(Math.random() * levels.length)],
                message: messages[Math.floor(Math.random() * messages.length)]
            });
        }
        
        // 按时间排序
        this.logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    }

    // 绑定事件
    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.currentTarget.dataset.tab);
            });
        });

        // 新建任务
        document.getElementById('addTaskBtn').addEventListener('click', () => {
            this.showTaskModal();
        });

        // 新建任务组
        document.getElementById('addGroupBtn').addEventListener('click', () => {
            this.showGroupModal();
        });

        // 任务表单
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTask();
        });

        // 任务组表单
        document.getElementById('groupForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveGroup();
        });

        // 调度配置表单
        document.getElementById('scheduleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSchedule();
        });

        // 弹窗关闭
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal('taskModal');
        });

        document.getElementById('closeGroupModal').addEventListener('click', () => {
            this.closeModal('groupModal');
        });

        document.getElementById('cancelTask').addEventListener('click', () => {
            this.closeModal('taskModal');
        });

        document.getElementById('cancelGroup').addEventListener('click', () => {
            this.closeModal('groupModal');
        });

        document.getElementById('cancelSchedule').addEventListener('click', () => {
            this.resetScheduleForm();
        });

        // Crontab相关
        document.getElementById('crontabHelper').addEventListener('click', () => {
            this.showCrontabHelp();
        });

        document.getElementById('generateCron').addEventListener('click', () => {
            this.generateCronExpression();
        });

        // 监听cron字段变化
        ['cronMinutes', 'cronHours', 'cronDay', 'cronMonth', 'cronWeek'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => {
                this.previewCronExpression();
            });
        });

        // 图表控制
        document.getElementById('refreshGraph').addEventListener('click', () => {
            this.renderDependencyGraph();
        });

        // 日志控制
        document.getElementById('refreshLogs').addEventListener('click', () => {
            this.renderLogs();
        });

        // 筛选器
        document.getElementById('groupFilter').addEventListener('change', () => {
            this.renderTaskList();
        });

        document.getElementById('statusFilter').addEventListener('change', () => {
            this.renderTaskList();
        });

        document.getElementById('logLevel').addEventListener('change', () => {
            this.renderLogs();
        });

        document.getElementById('logDate').addEventListener('change', () => {
            this.renderLogs();
        });

        // 点击弹窗外部关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }

    // 切换标签页
    switchTab(tabName) {
        this.currentTab = tabName;
        
        // 更新标签页状态
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // 更新内容显示
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // 根据标签页执行相应操作
        switch (tabName) {
            case 'graph':
                this.renderDependencyGraph();
                break;
            case 'logs':
                this.renderLogs();
                break;
            case 'monitor':
                this.renderMonitor();
                break;
        }
    }

    // 渲染任务列表
    renderTaskList() {
        const taskList = document.getElementById('taskList');
        const groupFilter = document.getElementById('groupFilter').value;
        const statusFilter = document.getElementById('statusFilter').value;
        
        let filteredTasks = this.tasks;
        
        // 应用筛选
        if (groupFilter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.groupId === groupFilter);
        }
        
        if (statusFilter !== 'all') {
            filteredTasks = filteredTasks.filter(task => task.status === statusFilter);
        }
        
        taskList.innerHTML = '';
        
        filteredTasks.forEach(task => {
            const taskItem = this.createTaskItem(task);
            taskList.appendChild(taskItem);
        });
    }

    // 创建任务项
    createTaskItem(task) {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        taskItem.dataset.taskId = task.id;
        
        const group = this.taskGroups.find(g => g.id === task.groupId);
        const statusClass = `status-${task.status}`;
        const statusText = task.status === 'active' ? '活跃' : 
                          task.status === 'paused' ? '暂停' : '失败';
        
        taskItem.innerHTML = `
            <div class="task-item-header">
                <span class="task-name">${task.name}</span>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            <div class="task-info">
                <span>${group ? group.name : '未分组'}</span>
                <span>${this.formatCron(task.cronExpression)}</span>
            </div>
        `;
        
        taskItem.addEventListener('click', () => {
            this.selectTask(task);
        });
        
        return taskItem;
    }

    // 选择任务
    selectTask(task) {
        this.selectedTask = task;
        
        // 更新选中状态
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected');
        });
        document.querySelector(`[data-task-id="${task.id}"]`).classList.add('selected');
        
        // 填充调度配置表单
        this.fillScheduleForm(task);
    }

    // 填充调度配置表单
    fillScheduleForm(task) {
        document.getElementById('taskName').value = task.name;
        document.getElementById('taskGroup').value = task.groupId;
        document.getElementById('crontabExpression').value = task.cronExpression;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskTimeout').value = task.timeout || 300;
        document.getElementById('taskEnabled').checked = task.enabled;
        
        // 填充依赖任务
        const dependenciesSelect = document.getElementById('taskDependencies');
        dependenciesSelect.innerHTML = '';
        
        this.tasks.filter(t => t.id !== task.id).forEach(t => {
            const option = document.createElement('option');
            option.value = t.id;
            option.textContent = t.name;
            option.selected = task.dependencies.includes(t.id);
            dependenciesSelect.appendChild(option);
        });
        
        this.parseAndVisualizeCron(task.cronExpression);
    }

    // 渲染依赖关系图
    renderDependencyGraph() {
        const container = document.getElementById('mermaidGraph');
        
        if (this.tasks.length === 0) {
            container.innerHTML = '<div class="empty-state">暂无任务数据</div>';
            return;
        }
        
        // 生成Mermaid流程图代码
        let mermaidCode = 'graph TD\n';
        
        this.tasks.forEach(task => {
            const statusSymbol = task.enabled ? '🟢' : '🔴';
            mermaidCode += `    ${task.id}[${statusSymbol} ${task.name}]\n`;
        });
        
        this.tasks.forEach(task => {
            task.dependencies.forEach(depId => {
                mermaidCode += `    ${depId} --> ${task.id}\n`;
            });
        });
        
        // 渲染Mermaid图表
        container.innerHTML = '<div class="mermaid">' + mermaidCode + '</div>';
        
        mermaid.run().catch(error => {
            console.error('Mermaid渲染失败:', error);
            container.innerHTML = '<div class="error">图表渲染失败，请检查依赖关系</div>';
        });
    }

    // 渲染日志
    renderLogs() {
        const logList = document.getElementById('logList');
        const levelFilter = document.getElementById('logLevel').value;
        const dateFilter = document.getElementById('logDate').value;
        
        let filteredLogs = this.logs;
        
        // 应用筛选
        if (levelFilter !== 'all') {
            filteredLogs = filteredLogs.filter(log => log.level === levelFilter);
        }
        
        if (dateFilter) {
            const filterDate = new Date(dateFilter).toDateString();
            filteredLogs = filteredLogs.filter(log => 
                new Date(log.timestamp).toDateString() === filterDate
            );
        }
        
        logList.innerHTML = '';
        
        filteredLogs.forEach(log => {
            const logItem = this.createLogItem(log);
            logList.appendChild(logItem);
        });
    }

    // 创建日志项
    createLogItem(log) {
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        
        const task = this.tasks.find(t => t.id === log.taskId);
        const taskName = task ? task.name : '未知任务';
        
        logItem.innerHTML = `
            <div class="log-time">${this.formatTime(log.timestamp)}</div>
            <div class="log-level log-${log.level}">${log.level.toUpperCase()}</div>
            <div class="log-message">
                <strong>[${taskName}]</strong> ${log.message}
            </div>
        `;
        
        return logItem;
    }

    // 渲染监控面板
    renderMonitor() {
        // 统计数据
        const activeTasks = this.tasks.filter(t => t.status === 'active').length;
        const failedTasks = this.tasks.filter(t => t.status === 'failed').length;
        const pausedTasks = this.tasks.filter(t => t.status === 'paused').length;
        const totalTasks = this.tasks.length;
        
        document.getElementById('successCount').textContent = activeTasks;
        document.getElementById('failedCount').textContent = failedTasks;
        document.getElementById('pendingCount').textContent = pausedTasks;
        document.getElementById('totalTasks').textContent = totalTasks;
        
        // 绘制图表
        this.drawTrendChart();
        this.drawStatusChart();
    }

    // 绘制趋势图
    drawTrendChart() {
        const canvas = document.getElementById('trendChart');
        const ctx = canvas.getContext('2d');
        
        // 生成示例数据
        const data = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            data.push({
                date: date.toLocaleDateString(),
                success: Math.floor(Math.random() * 20) + 10,
                failed: Math.floor(Math.random() * 5)
            });
        }
        
        // 简单的柱状图绘制
        this.drawBarChart(ctx, canvas, data);
    }

    // 绘制状态饼图
    drawStatusChart() {
        const canvas = document.getElementById('statusChart');
        const ctx = canvas.getContext('2d');
        
        const activeTasks = this.tasks.filter(t => t.status === 'active').length;
        const failedTasks = this.tasks.filter(t => t.status === 'failed').length;
        const pausedTasks = this.tasks.filter(t => t.status === 'paused').length;
        
        const data = [
            { label: '活跃', value: activeTasks, color: '#2ecc71' },
            { label: '失败', value: failedTasks, color: '#e74c3c' },
            { label: '暂停', value: pausedTasks, color: '#f39c12' }
        ];
        
        this.drawPieChart(ctx, canvas, data);
    }

    // 绘制柱状图
    drawBarChart(ctx, canvas, data) {
        const padding = 40;
        const width = canvas.width - padding * 2;
        const height = canvas.height - padding * 2;
        const barWidth = width / data.length / 2;
        const maxValue = Math.max(...data.map(d => d.success + d.failed));
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 绘制坐标轴
        ctx.strokeStyle = '#ddd';
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();
        
        // 绘制柱状图
        data.forEach((item, index) => {
            const x = padding + (index * width / data.length) + barWidth / 2;
            const successHeight = (item.success / maxValue) * height;
            const failedHeight = (item.failed / maxValue) * height;
            
            // 成功柱
            ctx.fillStyle = '#2ecc71';
            ctx.fillRect(x, canvas.height - padding - successHeight, barWidth / 2 - 2, successHeight);
            
            // 失败柱
            ctx.fillStyle = '#e74c3c';
            ctx.fillRect(x + barWidth / 2 + 2, canvas.height - padding - failedHeight, barWidth / 2 - 2, failedHeight);
            
            // 标签
            ctx.fillStyle = '#666';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(item.date, x + barWidth / 2, canvas.height - padding + 15);
        });
    }

    // 绘制饼图
    drawPieChart(ctx, canvas, data) {
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 30;
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const total = data.reduce((sum, item) => sum + item.value, 0);
        let currentAngle = -Math.PI / 2;
        
        data.forEach(item => {
            const sliceAngle = (item.value / total) * Math.PI * 2;
            
            // 绘制扇形
            ctx.fillStyle = item.color;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.closePath();
            ctx.fill();
            
            // 绘制标签
            const labelAngle = currentAngle + sliceAngle / 2;
            const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
            const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);
            
            ctx.fillStyle = 'white';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`${item.label} (${item.value})`, labelX, labelY);
            
            currentAngle += sliceAngle;
        });
    }

    // 显示任务弹窗
    showTaskModal(task = null) {
        const modal = document.getElementById('taskModal');
        const title = document.getElementById('modalTitle');
        
        title.textContent = task ? '编辑任务' : '新建任务';
        
        // 填充表单
        if (task) {
            document.getElementById('modalTaskName').value = task.name;
            document.getElementById('modalTaskGroup').value = task.groupId;
            document.getElementById('modalTaskType').value = task.type;
            document.getElementById('modalTaskCommand').value = task.command;
            document.getElementById('modalTaskDescription').value = task.description || '';
        } else {
            document.getElementById('taskForm').reset();
        }
        
        // 填充任务组选项
        this.fillGroupOptions('modalTaskGroup');
        
        modal.classList.add('show');
    }

    // 显示任务组弹窗
    showGroupModal() {
        document.getElementById('groupModal').classList.add('show');
    }

    // 关闭弹窗
    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('show');
    }

    // 保存任务
    saveTask() {
        const taskData = {
            name: document.getElementById('modalTaskName').value,
            groupId: document.getElementById('modalTaskGroup').value,
            type: document.getElementById('modalTaskType').value,
            command: document.getElementById('modalTaskCommand').value,
            description: document.getElementById('modalTaskDescription').value,
            cronExpression: '0 0 * * * ?', // 默认每天零点
            dependencies: [],
            enabled: true,
            status: 'active',
            timeout: 300,
            createdAt: new Date().toISOString(),
            lastRun: null,
            nextRun: this.getNextRunTime('0 0 * * * ?')
        };
        
        const taskId = this.selectedTask ? this.selectedTask.id : 'task' + Date.now();
        taskData.id = taskId;
        
        if (this.selectedTask) {
            // 更新现有任务
            const index = this.tasks.findIndex(t => t.id === taskId);
            if (index !== -1) {
                this.tasks[index] = { ...this.tasks[index], ...taskData };
            }
        } else {
            // 添加新任务
            this.tasks.push(taskData);
        }
        
        this.closeModal('taskModal');
        this.render();
        this.showToast('任务保存成功！');
    }

    // 保存任务组
    saveGroup() {
        const groupData = {
            id: 'group' + Date.now(),
            name: document.getElementById('groupName').value,
            description: document.getElementById('groupDescription').value,
            color: document.getElementById('groupColor').value
        };
        
        this.taskGroups.push(groupData);
        this.closeModal('groupModal');
        this.render();
        this.showToast('任务组创建成功！');
    }

    // 保存调度配置
    saveSchedule() {
        if (!this.selectedTask) return;
        
        const taskIndex = this.tasks.findIndex(t => t.id === this.selectedTask.id);
        if (taskIndex === -1) return;
        
        const dependencies = Array.from(document.getElementById('taskDependencies').selectedOptions)
            .map(option => option.value);
        
        this.tasks[taskIndex] = {
            ...this.tasks[taskIndex],
            name: document.getElementById('taskName').value,
            groupId: document.getElementById('taskGroup').value,
            cronExpression: document.getElementById('crontabExpression').value,
            description: document.getElementById('taskDescription').value,
            timeout: parseInt(document.getElementById('taskTimeout').value),
            enabled: document.getElementById('taskEnabled').checked,
            dependencies: dependencies,
            nextRun: this.getNextRunTime(document.getElementById('crontabExpression').value)
        };
        
        this.selectedTask = this.tasks[taskIndex];
        this.render();
        this.showToast('调度配置保存成功！');
    }

    // 重置调度表单
    resetScheduleForm() {
        document.getElementById('scheduleForm').reset();
        this.selectedTask = null;
    }

    // 填充任务组选项
    fillGroupOptions(selectId) {
        const select = document.getElementById(selectId);
        const currentValue = select.value;
        
        select.innerHTML = '<option value="">选择任务组</option>';
        
        this.taskGroups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            select.appendChild(option);
        });
        
        select.value = currentValue;
    }

    // Crontab相关方法
    generateCronExpression() {
        const minutes = document.getElementById('cronMinutes').value || '*';
        const hours = document.getElementById('cronHours').value || '*';
        const day = document.getElementById('cronDay').value || '*';
        const month = document.getElementById('cronMonth').value || '*';
        const week = document.getElementById('cronWeek').value || '*';
        
        const expression = `${minutes} ${hours} ${day} ${month} ${week}`;
        document.getElementById('crontabExpression').value = expression;
        
        this.previewCronExpression();
        this.showToast('Cron表达式生成成功！');
    }

    parseAndVisualizeCron(expression) {
        const parts = expression.split(' ');
        if (parts.length >= 5) {
            document.getElementById('cronMinutes').value = parts[0] || '*';
            document.getElementById('cronHours').value = parts[1] || '*';
            document.getElementById('cronDay').value = parts[2] || '*';
            document.getElementById('cronMonth').value = parts[3] || '*';
            document.getElementById('cronWeek').value = parts[4] || '*';
        }
    }

    previewCronExpression() {
        const minutes = document.getElementById('cronMinutes').value || '*';
        const hours = document.getElementById('cronHours').value || '*';
        const day = document.getElementById('cronDay').value || '*';
        const month = document.getElementById('cronMonth').value || '*';
        const week = document.getElementById('cronWeek').value || '*';
        
        const expression = `${minutes} ${hours} ${day} ${month} ${week}`;
        const preview = document.getElementById('cronPreview');
        
        preview.textContent = `预览: ${expression}`;
        preview.style.display = 'block';
    }

    showCrontabHelp() {
        const helpText = `
Cron表达式格式: 分钟 小时 日期 月份 星期

字段说明:
分钟: 0-59
小时: 0-23
日期: 1-31
月份: 1-12
星期: 0-7 (0和7都表示周日)

特殊字符:
* : 任意值
, : 多个值 (如: 1,3,5)
- : 范围 (如: 1-5)
/ : 步长 (如: */5 表示每5个单位)

示例:
0 0 12 * * ?   每天中午12点
0 */5 * * * ?   每5分钟
0 0 * * 1       每周一午夜
        `;
        
        alert(helpText);
    }

    // 计算下次执行时间
    getNextRunTime(cronExpression) {
        // 这里是简化版实现，实际应该使用cron解析库
        const now = new Date();
        now.setHours(now.getHours() + 1); // 简化为1小时后
        return now.toISOString();
    }

    // 格式化Cron表达式
    formatCron(expression) {
        const parts = expression.split(' ');
        if (parts.length >= 3) {
            return `${parts[1]}:${parts[0]}`;
        }
        return expression;
    }

    // 格式化时间
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('zh-CN', { 
            hour: '2-digit', 
            minute: '2-digit',
            second: '2-digit'
        });
    }

    // 显示提示消息
    showToast(message) {
        const existing = document.querySelector('.toast-message');
        if (existing) {
            existing.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast-message';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // 渲染所有组件
    render() {
        this.renderTaskList();
        this.fillGroupOptions('groupFilter');
        this.fillGroupOptions('taskGroup');
        this.fillGroupOptions('modalTaskGroup');
        
        if (this.currentTab === 'graph') {
            this.renderDependencyGraph();
        } else if (this.currentTab === 'logs') {
            this.renderLogs();
        } else if (this.currentTab === 'monitor') {
            this.renderMonitor();
        }
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .empty-state {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: #999;
        font-size: 16px;
    }
    
    .error {
        color: #e74c3c;
        text-align: center;
        padding: 20px;
    }
`;
document.head.appendChild(style);

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new TaskScheduler();
});