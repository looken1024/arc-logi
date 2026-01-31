// 注册页面逻辑

const registerForm = document.getElementById('registerForm');
const submitBtn = document.getElementById('submitBtn');
const errorMessage = document.getElementById('errorMessage');

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    // 验证
    if (!username || username.length < 3) {
        showError('用户名至少3个字符');
        return;
    }
    
    if (!password || password.length < 6) {
        showError('密码至少6个字符');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('两次输入的密码不一致');
        return;
    }
    
    // 显示加载状态
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    submitBtn.querySelector('span').textContent = '注册中...';
    hideError();
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 注册成功
            submitBtn.querySelector('span').textContent = '注册成功!';
            setTimeout(() => {
                window.location.href = '/login';
            }, 1000);
        } else {
            // 注册失败
            showError(data.error || '注册失败,请重试');
            resetButton();
        }
    } catch (error) {
        console.error('注册错误:', error);
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
    submitBtn.querySelector('span').textContent = '注册';
}

// 密码确认实时验证
document.getElementById('confirmPassword').addEventListener('input', (e) => {
    const password = document.getElementById('password').value;
    const confirmPassword = e.target.value;
    
    if (confirmPassword && password !== confirmPassword) {
        e.target.style.borderColor = '#ff6b6b';
    } else {
        e.target.style.borderColor = '';
    }
});

// 自动聚焦到用户名输入框
document.getElementById('username').focus();
