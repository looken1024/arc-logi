// 工作流编辑器 JavaScript

// 全局状态
let currentUser = null;
let currentWorkflow = null;
let jsPlumbInstance = null;
let selectedNode = null;
let nodes = {};
let edges = {};
let nodeCounter = 0;
let jsPlumbLoading = false;

// 动态加载 jsPlumb 库
function loadJsPlumbLibrary() {
    if (jsPlumbLoading || typeof jsPlumb !== 'undefined') {
        return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
        jsPlumbLoading = true;
        console.log('Loading jsPlumb library...');
        
        // 检查jQuery是否已加载（jsPlumb可能需要jQuery）
        if (typeof jQuery === 'undefined') {
            console.warn('jQuery not loaded, jsPlumb might need it');
        }
        
        const cdnSources = [
            '/static/js/jsplumb.min.js',  // 本地版本优先
            'https://cdnjs.cloudflare.com/ajax/libs/jsplumb/2.15.5/js/jsplumb.min.js',
            'https://unpkg.com/jsplumb@2.15.5/dist/js/jsplumb.min.js',
            'https://cdn.jsdelivr.net/npm/jsplumb@2.15.5/dist/js/jsplumb.min.js'
        ];
        
        let currentSourceIndex = 0;
        let loaded = false;
        
        function tryLoadSource() {
            if (currentSourceIndex >= cdnSources.length) {
                console.error('All CDN sources failed');
                jsPlumbLoading = false;
                reject(new Error('All CDN sources failed to load jsPlumb'));
                return;
            }
            
            const source = cdnSources[currentSourceIndex];
            console.log(`Trying to load jsPlumb from: ${source}`);
            
            const script = document.createElement('script');
            script.src = source;
            script.onload = () => {
                if (loaded) return;
                loaded = true;
                console.log(`jsPlumb library loaded successfully from: ${source}`);
                jsPlumbLoading = false;
                // 等待一小段时间确保全局变量可用
                setTimeout(() => {
                    if (typeof jsPlumb === 'undefined') {
                        console.error('jsPlumb still not defined after loading script');
                        reject(new Error('jsPlumb not defined after loading'));
                    } else {
                        resolve();
                    }
                }, 100);
            };
            script.onerror = () => {
                console.warn(`Failed to load from: ${source}`);
                currentSourceIndex++;
                setTimeout(tryLoadSource, 500);
            };
            
            document.head.appendChild(script);
        }
        
        // 设置超时
        const timeout = setTimeout(() => {
            if (!loaded) {
                loaded = true;
                jsPlumbLoading = false;
                reject(new Error('Timeout loading jsPlumb'));
            }
        }, 15000);
        
        tryLoadSource();
    });
}

// DOM 元素
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    workflowTitle: document.getElementById('workflowTitle'),
    username: document.getElementById('username'),
    saveWorkflowBtn: document.getElementById('saveWorkflowBtn'),
    addNodeBtn: document.getElementById('addNodeBtn'),
    workflowActionsBtn: document.getElementById('workflowActionsBtn'),
    executeWorkflowBtn: document.getElementById('executeWorkflowBtn'),
    exportWorkflowBtn: document.getElementById('exportWorkflowBtn'),
    importWorkflowBtn: document.getElementById('importWorkflowBtn'),
    nodePalette: document.getElementById('nodePalette'),
    workflowCanvas: document.getElementById('workflowCanvas'),
    nodeProperties: document.getElementById('nodeProperties'),
    noSelectionMessage: document.getElementById('noSelectionMessage'),
    nodePropertiesForm: document.getElementById('nodePropertiesForm'),
    nodeId: document.getElementById('nodeId'),
    nodeType: document.getElementById('nodeType'),
    nodeName: document.getElementById('nodeName'),
    nodeDescription: document.getElementById('nodeDescription'),
    nodeConfigGroup: document.getElementById('nodeConfigGroup'),
    zoomInBtn: document.getElementById('zoomInBtn'),
    zoomOutBtn: document.getElementById('zoomOutBtn'),
    resetZoomBtn: document.getElementById('resetZoomBtn'),
    deleteSelectedBtn: document.getElementById('deleteSelectedBtn'),
    clearCanvasBtn: document.getElementById('clearCanvasBtn'),
    nodeConfigModal: document.getElementById('nodeConfigModal'),
    closeNodeConfigModal: document.getElementById('closeNodeConfigModal'),
    cancelNodeConfigBtn: document.getElementById('cancelNodeConfigBtn'),
    saveNodeConfigBtn: document.getElementById('saveNodeConfigBtn'),
    nodeConfigForm: document.getElementById('nodeConfigForm'),
    nodeConfigTitle: document.getElementById('nodeConfigTitle')
};

// 节点类型配置
const nodeTypes = {
    start: {
        icon: 'fas fa-play-circle',
        label: '开始',
        color: '#10a37f',
        ports: { inputs: 0, outputs: 1 }
    },
    end: {
        icon: 'fas fa-stop-circle',
        label: '结束',
        color: '#ef4146',
        ports: { inputs: 1, outputs: 0 }
    },
    llm: {
        icon: 'fas fa-brain',
        label: 'LLM',
        color: '#19c37d',
        ports: { inputs: 1, outputs: 1 },
        configFields: [
            { name: 'model', label: '模型', type: 'select', options: ['gpt-3.5-turbo', 'gpt-4', 'deepseek-chat'], required: true },
            { name: 'prompt', label: '提示词', type: 'textarea', required: true },
            { name: 'temperature', label: '温度', type: 'number', min: 0, max: 2, step: 0.1, value: 0.7 }
        ]
    },
    script: {
        icon: 'fas fa-code',
        label: '脚本',
        color: '#f4a261',
        ports: { inputs: 1, outputs: 1 },
        configFields: [
            { name: 'language', label: '语言', type: 'select', options: ['python', 'javascript', 'bash'], required: true },
            { name: 'code', label: '代码', type: 'textarea', required: true }
        ]
    },
    condition: {
        icon: 'fas fa-code-branch',
        label: '条件',
        color: '#9d4edd',
        ports: { inputs: 1, outputs: 2 },
        configFields: [
            { name: 'condition', label: '条件表达式', type: 'textarea', required: true }
        ]
    },
    input: {
        icon: 'fas fa-keyboard',
        label: '输入',
        color: '#4cc9f0',
        ports: { inputs: 0, outputs: 1 },
        configFields: [
            { name: 'variable', label: '变量名', type: 'text', required: true },
            { name: 'default', label: '默认值', type: 'text' }
        ]
    },
    output: {
        icon: 'fas fa-terminal',
        label: '输出',
        color: '#f72585',
        ports: { inputs: 1, outputs: 0 },
        configFields: [
            { name: 'variable', label: '变量名', type: 'text', required: true }
        ]
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    loadUserInfo();
    initializeEventListeners();
    
    // 确保jsPlumb加载完成
    if (typeof jsPlumb === 'undefined') {
        console.log('jsPlumb not loaded, trying to load...');
        try {
            await loadJsPlumbLibrary();
            console.log('jsPlumb library loaded successfully');
        } catch (error) {
            console.error('Failed to load jsPlumb library:', error);
            alert('无法加载图形库（jsPlumb），请检查网络连接后刷新页面。');
            return;
        }
    }
    
    // 现在初始化jsPlumb
    initializeJsPlumb();
    loadWorkflow();
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
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 加载工作流
async function loadWorkflow(retryCount = 0) {
    if (!workflowId) {
        console.error('未提供工作流ID');
        return;
    }
    
    // 等待 jsPlumb 初始化完成
    if (!jsPlumbInstance && retryCount < 10) {
        console.log(`等待 jsPlumb 初始化... (重试 ${retryCount + 1}/10)`);
        setTimeout(() => {
            loadWorkflow(retryCount + 1);
        }, 300);
        return;
    } else if (!jsPlumbInstance) {
        console.error('jsPlumb 初始化超时，无法加载工作流');
        return;
    }
    
    console.log('jsPlumb 已就绪，开始加载工作流');
    
    try {
        const response = await fetch(`/api/workflows/${workflowId}`);
        if (response.ok) {
            currentWorkflow = await response.json();
            elements.workflowTitle.textContent = `工作流编辑器 - ${currentWorkflow.name}`;
            
            // 加载节点和边
            await loadNodes();
            await loadEdges();
        } else {
            alert('加载工作流失败');
        }
    } catch (error) {
        console.error('加载工作流失败:', error);
    }
}

// 加载节点
async function loadNodes() {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/nodes`);
        if (response.ok) {
            const nodesData = await response.json();
            nodes = {};
            
            nodesData.forEach(nodeData => {
                createNodeFromData(nodeData);
            });
            
            // 重新绘制连接
            setTimeout(() => {
                Object.values(edges).forEach(edge => {
                    connectNodes(edge.source_node_id, edge.target_node_id);
                });
            }, 100);
        }
    } catch (error) {
        console.error('加载节点失败:', error);
    }
}

// 加载边
async function loadEdges() {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/edges`);
        if (response.ok) {
            const edgesData = await response.json();
            edges = {};
            
            edgesData.forEach(edgeData => {
                edges[edgeData.id] = edgeData;
            });
        }
    } catch (error) {
        console.error('加载边失败:', error);
    }
}

// 初始化事件监听器
function initializeEventListeners() {
    // 侧边栏切换
    elements.sidebarToggle?.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });
    
    // 保存工作流
    elements.saveWorkflowBtn?.addEventListener('click', saveWorkflow);
    
    // 添加节点按钮
    elements.addNodeBtn?.addEventListener('click', showAddNodeMenu);
    
    // 画布操作按钮
    elements.zoomInBtn?.addEventListener('click', zoomIn);
    elements.zoomOutBtn?.addEventListener('click', zoomOut);
    elements.resetZoomBtn?.addEventListener('click', resetZoom);
    elements.deleteSelectedBtn?.addEventListener('click', deleteSelected);
    elements.clearCanvasBtn?.addEventListener('click', clearCanvas);
    
    // 节点属性表单
    elements.nodePropertiesForm?.addEventListener('submit', saveNodeProperties);
    
    // 节点配置模态框
    elements.closeNodeConfigModal?.addEventListener('click', hideNodeConfigModal);
    elements.cancelNodeConfigBtn?.addEventListener('click', hideNodeConfigModal);
    elements.saveNodeConfigBtn?.addEventListener('click', saveNodeConfig);
    
    // 节点面板拖放
    setupPaletteDragAndDrop();
    
    // 执行工作流
    elements.executeWorkflowBtn?.addEventListener('click', executeWorkflow);
    
    // 画布点击事件（用于测试）
    elements.workflowCanvas.addEventListener('click', (e) => {
        console.log('Canvas clicked at:', e.clientX, e.clientY, 'target:', e.target);
    });
    
    elements.workflowCanvas.addEventListener('mousedown', (e) => {
        console.log('Canvas mousedown:', e.target);
    });
}

// 初始化 jsPlumb
function initializeJsPlumb() {
    console.log('Initializing jsPlumb...');
    console.log('jsPlumb global available:', typeof jsPlumb !== 'undefined');
    
    if (typeof jsPlumb === 'undefined') {
        console.error('jsPlumb library not loaded! This should not happen as we load it before initialization.');
        throw new Error('jsPlumb library not loaded');
    }
    
    console.log('jsPlumb version:', jsPlumb ? jsPlumb.version : 'unknown');
    console.log('jsPlumb methods:', Object.keys(jsPlumb || {}).filter(key => typeof jsPlumb[key] === 'function'));
    
    try {
        // 确保容器存在
        if (!elements.workflowCanvas) {
            console.error('Workflow canvas element not found!');
            return;
        }
        console.log('Canvas element found:', elements.workflowCanvas);
        
        jsPlumbInstance = jsPlumb.getInstance({
            Container: elements.workflowCanvas,
            Connector: ['Flowchart', { stub: [40, 60], gap: 10, cornerRadius: 5 }],
            PaintStyle: { stroke: '#10a37f', strokeWidth: 2 },
            EndpointStyle: { radius: 6, fill: '#10a37f' },
            HoverPaintStyle: { stroke: '#19c37d', strokeWidth: 3 },
            ConnectionOverlays: [
                ['Arrow', { location: 1, width: 12, length: 12 }],
                ['Label', { label: '', location: 0.5, cssClass: 'connection-label' }]
            ],
            dragOptions: { cursor: 'move', zIndex: 2000, containment: 'parent' }
        });
        console.log('jsPlumb instance created:', jsPlumbInstance);
        console.log('jsPlumbInstance methods:', Object.keys(jsPlumbInstance).filter(key => typeof jsPlumbInstance[key] === 'function'));
    } catch (error) {
        console.error('Failed to create jsPlumb instance:', error);
        console.error('Error details:', error.message, error.stack);
        jsPlumbInstance = null;
        return;
    }
    
    // 设置画布为 droppable
    jsPlumbInstance.setDraggable(elements.workflowCanvas, false);
    console.log('Canvas dimensions:', elements.workflowCanvas.clientWidth, elements.workflowCanvas.clientHeight);
    
    // 连接事件监听
    jsPlumbInstance.bind('connection', (info, originalEvent) => {
        if (originalEvent) {
            // 用户创建的连接
            const sourceNodeId = info.sourceId;
            const targetNodeId = info.targetId;
            createEdge(sourceNodeId, targetNodeId);
        }
    });
    
    jsPlumbInstance.bind('connectionDetached', (info, originalEvent) => {
        if (originalEvent && info.connection) {
            // 用户删除的连接，需要找到对应的edge id并删除
            const sourceNodeId = info.sourceId;
            const targetNodeId = info.targetId;
            deleteEdgeByNodes(sourceNodeId, targetNodeId);
        }
    });
    
    // 测试 jsPlumb 是否工作正常
    console.log('jsPlumb ready:', jsPlumbInstance);
    setTimeout(() => {
        const testNodes = document.querySelectorAll('.workflow-node');
        console.log('Found', testNodes.length, 'workflow nodes');
        testNodes.forEach(node => {
            console.log('Node:', node.id, 'position:', node.style.left, node.style.top, 'classList:', node.classList);
            // 测试是否可拖动
            const draggable = jsPlumbInstance.isDraggable(node);
            console.log('Node', node.id, 'isDraggable:', draggable);
        });
        
        // 创建测试节点
        if (testNodes.length === 0) {
            console.log('Creating test node...');
            createNode('llm', 100, 100);
        }
    }, 1000);
}
// 创建边
async function createEdge(sourceNodeId, targetNodeId) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/edges`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_node_id: sourceNodeId,
                target_node_id: targetNodeId,
                condition: ''
            })
        });
        
        if (response.ok) {
            const edge = await response.json();
            edges[edge.id] = edge;
            console.log('边创建成功:', edge);
        } else {
            console.error('创建边失败');
        }
    } catch (error) {
        console.error('创建边失败:', error);
    }
}

// 通过节点ID删除边
async function deleteEdgeByNodes(sourceNodeId, targetNodeId) {
    // 找到匹配的边
    const edge = Object.values(edges).find(e => 
        e.source_node_id === sourceNodeId && e.target_node_id === targetNodeId
    );
    
    if (!edge) return;
    
    try {
        const response = await fetch(`/api/workflows/${workflowId}/edges/${edge.id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            delete edges[edge.id];
            console.log('边删除成功:', edge.id);
        } else {
            console.error('删除边失败');
        }
    } catch (error) {
        console.error('删除边失败:', error);
    }
}
// 删除与节点相关的所有边
async function deleteEdgesForNode(nodeId) {
    const edgesToDelete = Object.values(edges).filter(e => 
        e.source_node_id === nodeId || e.target_node_id === nodeId
    );
    
    for (const edge of edgesToDelete) {
        try {
            const response = await fetch(`/api/workflows/${workflowId}/edges/${edge.id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                delete edges[edge.id];
                // 从 jsPlumb 移除连接
                if (jsPlumbInstance) {
                    try {
                        const connections = jsPlumbInstance.getConnections({
                            source: edge.source_node_id,
                            target: edge.target_node_id
                        });
                        connections.forEach(conn => jsPlumbInstance.deleteConnection(conn));
                        console.log('边删除成功:', edge.id);
                    } catch (error) {
                        console.error('Error removing connections:', error);
                    }
                } else {
                    console.warn('jsPlumbInstance is null, skipping connection removal');
                }
            } else {
                console.error('删除边失败');
            }
        } catch (error) {
            console.error('删除边失败:', error);
        }
    }
}

// 设置节点面板拖放
function setupPaletteDragAndDrop() {
    const paletteNodes = document.querySelectorAll('.palette-node');
    
    paletteNodes.forEach(node => {
        node.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('nodeType', node.dataset.type);
        });
    });
    
    elements.workflowCanvas.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    elements.workflowCanvas.addEventListener('drop', (e) => {
        e.preventDefault();
        const nodeType = e.dataTransfer.getData('nodeType');
        if (nodeType) {
            const rect = elements.workflowCanvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            createNode(nodeType, x, y);
        }
    });
}

// 创建节点
function createNode(nodeType, x, y) {
    const typeConfig = nodeTypes[nodeType];
    if (!typeConfig) return;
    
    nodeCounter++;
    const nodeId = `node_${nodeCounter}`;
    
    const nodeData = {
        id: nodeId,
        workflow_id: workflowId,
        node_type: nodeType,
        name: `${typeConfig.label} ${nodeCounter}`,
        description: '',
        config: '{}',
        position_x: Math.round(x),
        position_y: Math.round(y),
        created_at: new Date().toISOString()
    };
    
    createNodeElement(nodeData);
    
    // 保存到服务器
    saveNodeToServer(nodeData);
}

// 从数据创建节点
function createNodeFromData(nodeData) {
    nodes[nodeData.id] = nodeData;
    createNodeElement(nodeData);
}

// 创建节点元素
function createNodeElement(nodeData) {
    const typeConfig = nodeTypes[nodeData.node_type] || {};
    
    const nodeElement = document.createElement('div');
    nodeElement.className = 'workflow-node';
    nodeElement.id = nodeData.id;
    nodeElement.dataset.nodeId = nodeData.id;
    nodeElement.dataset.nodeType = nodeData.node_type;
    nodeElement.style.left = `${nodeData.position_x}px`;
    nodeElement.style.top = `${nodeData.position_y}px`;
    
    const config = nodeData.config ? JSON.parse(nodeData.config) : {};
    
    nodeElement.innerHTML = `
        <div class="workflow-node-header">
            <i class="workflow-node-icon ${typeConfig.icon || 'fas fa-circle'}"></i>
            <span class="workflow-node-title">${nodeData.name}</span>
            <span class="workflow-node-status">${nodeData.node_type}</span>
        </div>
        <div class="workflow-node-content">
            ${config.prompt ? config.prompt.substring(0, 50) + '...' : nodeData.description || ''}
        </div>
        <div class="workflow-node-ports">
            ${typeConfig.ports?.inputs > 0 ? '<div class="workflow-node-port input"></div>' : ''}
            ${typeConfig.ports?.outputs > 0 ? '<div class="workflow-node-port output"></div>' : ''}
        </div>
    `;
    
    elements.workflowCanvas.appendChild(nodeElement);
    
    // 方法1: 使用jsPlumb使节点可拖动
    console.log('Making node draggable:', nodeData.id);
    setTimeout(() => {
        if (jsPlumbInstance) {
            console.log('jsPlumbInstance available, trying to make draggable');
            try {
                // jsPlumb 2.x 使用 makeDraggable 而不是 draggable
                if (jsPlumbInstance.makeDraggable) {
                    jsPlumbInstance.makeDraggable(nodeElement, {
                        start: function(params) {
                            console.log('Node drag start (makeDraggable):', params.el.id);
                        },
                        stop: function(params) {
                            const nodeId = params.el.id;
                            console.log('Node drag stop (makeDraggable):', nodeId);
                            const position = params.el.getBoundingClientRect();
                            const canvasRect = elements.workflowCanvas.getBoundingClientRect();
                            
                            const x = position.left - canvasRect.left;
                            const y = position.top - canvasRect.top;
                            
                            updateNodePosition(nodeId, Math.round(x), Math.round(y));
                            jsPlumbInstance.repaint(nodeId);
                        }
                    });
                    console.log('makeDraggable applied:', nodeData.id);
                } else if (jsPlumbInstance.draggable) {
                    // 备用方法
                    jsPlumbInstance.draggable(nodeElement, {
                        start: function(params) {
                            console.log('Node drag start (draggable):', params.el.id);
                        },
                        stop: function(params) {
                            const nodeId = params.el.id;
                            console.log('Node drag stop (draggable):', nodeId);
                            const position = params.el.getBoundingClientRect();
                            const canvasRect = elements.workflowCanvas.getBoundingClientRect();
                            
                            const x = position.left - canvasRect.left;
                            const y = position.top - canvasRect.top;
                            
                            updateNodePosition(nodeId, Math.round(x), Math.round(y));
                            jsPlumbInstance.repaint(nodeId);
                        }
                    });
                    console.log('draggable applied:', nodeData.id);
                } else {
                    console.error('No draggable method found on jsPlumbInstance');
                }
            } catch (error) {
                console.error('Error making node draggable:', error);
                console.log('Error details:', error.message, error.stack);
            }
        } else {
            console.error('jsPlumbInstance is null!');
        }
    }, 200);
    
    // 点击选择节点
    nodeElement.addEventListener('click', (e) => {
        console.log('Node clicked:', nodeData.id, 'event:', e);
        e.stopPropagation();
        e.preventDefault();
        selectNode(nodeData.id);
    });
    
    // 双击编辑节点
    nodeElement.addEventListener('dblclick', (e) => {
        console.log('Node double clicked:', nodeData.id);
        e.stopPropagation();
        e.preventDefault();
        editNode(nodeData.id);
    });
    
    // 添加鼠标事件测试
    nodeElement.addEventListener('mousedown', (e) => {
        console.log('Node mousedown:', nodeData.id, e.button);
    });
    
    nodeElement.addEventListener('mouseup', (e) => {
        console.log('Node mouseup:', nodeData.id);
    });
    
    // 添加端点
    setTimeout(() => {
        if (!jsPlumbInstance) {
            console.error('jsPlumbInstance is null, cannot add endpoints for node:', nodeData.id);
            return;
        }
        if (typeConfig.ports?.inputs > 0) {
            try {
                jsPlumbInstance.addEndpoint(nodeElement, {
                    anchor: 'Left',
                    isSource: false,
                    isTarget: true,
                    maxConnections: -1
                });
                console.log('Input endpoint added for node:', nodeData.id);
            } catch (error) {
                console.error('Error adding input endpoint:', error);
            }
        }
        
        if (typeConfig.ports?.outputs > 0) {
            try {
                jsPlumbInstance.addEndpoint(nodeElement, {
                    anchor: 'Right',
                    isSource: true,
                    isTarget: false,
                    maxConnections: -1
                });
                console.log('Output endpoint added for node:', nodeData.id);
            } catch (error) {
                console.error('Error adding output endpoint:', error);
            }
        }
    }, 200);
}

// 选择节点
function selectNode(nodeId) {
    console.log('selectNode called:', nodeId);
    // 清除之前的选择
    document.querySelectorAll('.workflow-node.selected').forEach(node => {
        node.classList.remove('selected');
    });
    
    // 选择新节点
    const nodeElement = document.getElementById(nodeId);
    if (nodeElement) {
        nodeElement.classList.add('selected');
        selectedNode = nodeId;
        console.log('Node selected:', nodeId);
        
        // 显示节点属性
        showNodeProperties(nodeId);
    } else {
        console.log('Node element not found:', nodeId);
    }
}

// 显示节点属性
function showNodeProperties(nodeId) {
    const node = nodes[nodeId];
    if (!node) return;
    
    elements.noSelectionMessage.style.display = 'none';
    elements.nodePropertiesForm.style.display = 'block';
    
    elements.nodeId.value = node.id;
    elements.nodeType.value = node.node_type;
    elements.nodeName.value = node.name;
    elements.nodeDescription.value = node.description || '';
    
    // 动态生成配置字段
    const typeConfig = nodeTypes[node.node_type];
    elements.nodeConfigGroup.innerHTML = '';
    
    if (typeConfig.configFields) {
        const config = node.config ? JSON.parse(node.config) : {};
        
        typeConfig.configFields.forEach(field => {
            const div = document.createElement('div');
            div.className = 'form-group';
            
            const label = document.createElement('label');
            label.textContent = field.label;
            label.htmlFor = `config_${field.name}`;
            
            let input;
            if (field.type === 'select') {
                input = document.createElement('select');
                input.id = `config_${field.name}`;
                input.name = field.name;
                field.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option;
                    optionEl.textContent = option;
                    if (config[field.name] === option) optionEl.selected = true;
                    input.appendChild(optionEl);
                });
            } else if (field.type === 'textarea') {
                input = document.createElement('textarea');
                input.id = `config_${field.name}`;
                input.name = field.name;
                input.rows = 4;
                input.value = config[field.name] || '';
            } else {
                input = document.createElement('input');
                input.type = field.type;
                input.id = `config_${field.name}`;
                input.name = field.name;
                input.value = config[field.name] || field.value || '';
                if (field.min) input.min = field.min;
                if (field.max) input.max = field.max;
                if (field.step) input.step = field.step;
            }
            
            if (field.required) input.required = true;
            
            div.appendChild(label);
            div.appendChild(input);
            elements.nodeConfigGroup.appendChild(div);
        });
    }
}

// 保存节点属性
async function saveNodeProperties(e) {
    e.preventDefault();
    
    const nodeId = elements.nodeId.value;
    const node = nodes[nodeId];
    if (!node) return;
    
    node.name = elements.nodeName.value;
    node.description = elements.nodeDescription.value;
    
    // 收集配置字段
    const config = {};
    const typeConfig = nodeTypes[node.node_type];
    if (typeConfig.configFields) {
        typeConfig.configFields.forEach(field => {
            const input = document.getElementById(`config_${field.name}`);
            config[field.name] = input.value;
        });
    }
    node.config = JSON.stringify(config);
    
    // 更新节点显示
    const nodeElement = document.getElementById(nodeId);
    if (nodeElement) {
        const title = nodeElement.querySelector('.workflow-node-title');
        if (title) title.textContent = node.name;
        
        const content = nodeElement.querySelector('.workflow-node-content');
        if (content) {
            content.textContent = config.prompt ? 
                config.prompt.substring(0, 50) + '...' : 
                node.description || '';
        }
    }
    
    // 保存到服务器
    await updateNodeOnServer(node);
    
    alert('节点属性已保存');
}

// 编辑节点（打开配置模态框）
function editNode(nodeId) {
    const node = nodes[nodeId];
    if (!node) return;
    
    const typeConfig = nodeTypes[node.node_type];
    if (!typeConfig.configFields || typeConfig.configFields.length === 0) {
        alert('此节点类型无需配置');
        return;
    }
    
    elements.nodeConfigTitle.textContent = `配置 ${node.name}`;
    elements.nodeConfigForm.innerHTML = '';
    
    const config = node.config ? JSON.parse(node.config) : {};
    
    typeConfig.configFields.forEach(field => {
        const div = document.createElement('div');
        div.className = 'form-group';
        
        const label = document.createElement('label');
        label.textContent = field.label;
        
        let input;
        if (field.type === 'select') {
            input = document.createElement('select');
            input.name = field.name;
            field.options.forEach(option => {
                const optionEl = document.createElement('option');
                optionEl.value = option;
                optionEl.textContent = option;
                if (config[field.name] === option) optionEl.selected = true;
                input.appendChild(optionEl);
            });
        } else if (field.type === 'textarea') {
            input = document.createElement('textarea');
            input.name = field.name;
            input.rows = 6;
            input.value = config[field.name] || '';
        } else {
            input = document.createElement('input');
            input.type = field.type;
            input.name = field.name;
            input.value = config[field.name] || field.value || '';
            if (field.min) input.min = field.min;
            if (field.max) input.max = field.max;
            if (field.step) input.step = field.step;
        }
        
        if (field.required) input.required = true;
        
        div.appendChild(label);
        div.appendChild(input);
        elements.nodeConfigForm.appendChild(div);
    });
    
    elements.nodeConfigModal.style.display = 'flex';
}

// 隐藏节点配置模态框
function hideNodeConfigModal() {
    elements.nodeConfigModal.style.display = 'none';
}

// 保存节点配置
async function saveNodeConfig() {
    const formData = new FormData(elements.nodeConfigForm);
    const config = {};
    
    formData.forEach((value, key) => {
        config[key] = value;
    });
    
    const node = nodes[selectedNode];
    if (node) {
        node.config = JSON.stringify(config);
        await updateNodeOnServer(node);
        
        // 更新节点显示
        const nodeElement = document.getElementById(selectedNode);
        if (nodeElement) {
            const content = nodeElement.querySelector('.workflow-node-content');
            if (content && config.prompt) {
                content.textContent = config.prompt.substring(0, 50) + '...';
            }
        }
    }
    
    hideNodeConfigModal();
    alert('节点配置已保存');
}

// 连接节点
function connectNodes(sourceNodeId, targetNodeId) {
    if (!jsPlumbInstance) {
        console.error('jsPlumbInstance is null in connectNodes');
        return;
    }
    try {
        jsPlumbInstance.connect({
            source: sourceNodeId,
            target: targetNodeId
        });
        console.log('Connected nodes:', sourceNodeId, '->', targetNodeId);
    } catch (error) {
        console.error('Error connecting nodes:', error);
    }
}

// 显示添加节点菜单
function showAddNodeMenu() {
    // 简单实现：在画布中央添加一个LLM节点
    const canvasRect = elements.workflowCanvas.getBoundingClientRect();
    const x = canvasRect.width / 2 - 80;
    const y = canvasRect.height / 2 - 30;
    
    createNode('llm', x, y);
}

// 缩放功能
let zoomLevel = 1;
function zoomIn() {
    zoomLevel += 0.1;
    updateZoom();
}

function zoomOut() {
    zoomLevel = Math.max(0.3, zoomLevel - 0.1);
    updateZoom();
}

function resetZoom() {
    zoomLevel = 1;
    updateZoom();
}

function updateZoom() {
    elements.workflowCanvas.style.transform = `scale(${zoomLevel})`;
    elements.workflowCanvas.style.transformOrigin = 'top left';
}

// 删除选中节点
function deleteSelected() {
    if (!selectedNode) {
        alert('请先选择一个节点');
        return;
    }
    
    if (confirm('确定要删除这个节点吗？')) {
        deleteNode(selectedNode);
    }
}

// 清空画布
function clearCanvas() {
    if (confirm('确定要清空所有节点吗？此操作不可撤销。')) {
        Object.keys(nodes).forEach(nodeId => {
            deleteNode(nodeId);
        });
    }
}

// 删除节点
async function deleteNode(nodeId) {
    try {
        // 先删除与节点相关的边
        await deleteEdgesForNode(nodeId);
        
        const response = await fetch(`/api/workflows/${workflowId}/nodes/${nodeId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // 从DOM移除
            const nodeElement = document.getElementById(nodeId);
            if (nodeElement) {
                nodeElement.remove();
                if (jsPlumbInstance) {
                    try {
                        jsPlumbInstance.remove(nodeElement);
                    } catch (error) {
                        console.error('Error removing node from jsPlumb:', error);
                    }
                }
            }
            
            // 从状态移除
            delete nodes[nodeId];
            
            if (selectedNode === nodeId) {
                selectedNode = null;
                elements.noSelectionMessage.style.display = 'block';
                elements.nodePropertiesForm.style.display = 'none';
            }
        } else {
            alert('删除节点失败');
        }
    } catch (error) {
        console.error('删除节点失败:', error);
    }
}

// 保存工作流
async function saveWorkflow() {
    if (!currentWorkflow) return;
    
    try {
        const response = await fetch(`/api/workflows/${currentWorkflow.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentWorkflow)
        });
        
        if (response.ok) {
            alert('工作流已保存');
        } else {
            alert('保存工作流失败');
        }
    } catch (error) {
        console.error('保存工作流失败:', error);
    }
}

// 保存节点到服务器
async function saveNodeToServer(nodeData) {
    try {
        const response = await fetch(`/api/workflows/${workflowId}/nodes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const savedNode = await response.json();
            nodes[savedNode.id] = savedNode;
            
            // 更新节点ID
            const nodeElement = document.getElementById(nodeData.id);
            if (nodeElement) {
                nodeElement.id = savedNode.id;
                nodeElement.dataset.nodeId = savedNode.id;
            }
        }
    } catch (error) {
        console.error('保存节点失败:', error);
    }
}

// 更新节点位置
async function updateNodePosition(nodeId, x, y) {
    const node = nodes[nodeId];
    if (!node) return;
    
    node.position_x = x;
    node.position_y = y;
    
    try {
        await fetch(`/api/workflows/${workflowId}/nodes/${nodeId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ position_x: x, position_y: y })
        });
    } catch (error) {
        console.error('更新节点位置失败:', error);
    }
}

// 更新节点到服务器
async function updateNodeOnServer(node) {
    try {
        await fetch(`/api/workflows/${workflowId}/nodes/${node.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(node)
        });
    } catch (error) {
        console.error('更新节点失败:', error);
    }
}

// 执行工作流
async function executeWorkflow() {
    if (!workflowId) return;
    
    try {
        const response = await fetch(`/api/workflows/${workflowId}/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const execution = await response.json();
            alert(`工作流执行已启动，执行ID: ${execution.id}`);
        } else {
            alert('执行工作流失败');
        }
    } catch (error) {
        console.error('执行工作流失败:', error);
    }
}