// 登录页面逻辑

const loginForm = document.getElementById('loginForm');
const submitBtn = document.getElementById('submitBtn');
const errorMessage = document.getElementById('errorMessage');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showError('请输入用户名和密码');
        return;
    }
    
    // 显示加载状态
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtn.querySelector('span').textContent = '登录中...';
    hideError();
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 登录成功
            submitBtn.querySelector('span').textContent = '登录成功!';
            setTimeout(() => {
                window.location.href = '/';
            }, 500);
        } else {
            // 登录失败
            showError(data.error || '登录失败,请重试');
            resetButton();
        }
    } catch (error) {
        console.error('登录错误:', error);
        showError('网络错误,请检查连接');
        resetButton();
    }
});

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

function hideError() {
    errorMessage.classList.remove('show');
}

function resetButton() {
    submitBtn.disabled = false;
    submitBtn.classList.remove('loading');
    submitBtn.querySelector('span').textContent = '登录';
}

// 自动聚焦到用户名输入框
document.getElementById('username').focus();
