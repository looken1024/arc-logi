document.addEventListener('DOMContentLoaded', async () => {
    await loadSkills();
});

async function loadSkills() {
    const skillsGrid = document.getElementById('skillsGrid');
    
    try {
        const response = await fetch('/api/skills/scan', {
            credentials: 'same-origin'
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '扫描技能列表失败');
        }

        skillsGrid.innerHTML = '';

        if (data.skills.length === 0) {
            skillsGrid.innerHTML = '<div class="empty-state"><i class="fas fa-robot"></i><span>暂无可用技能</span></div>';
            return;
        }

        data.skills.forEach(skill => {
            const skillItem = document.createElement('div');
            skillItem.className = 'skill-card';
            skillItem.dataset.skillName = skill.name;

            skillItem.innerHTML = `
                <div class="skill-icon">
                    <i class="fas fa-cube"></i>
                </div>
                <div class="skill-info">
                    <h3>${escapeHtml(skill.name)}</h3>
                    <p>${escapeHtml(skill.description)}</p>
                </div>
                <label class="switch">
                    <input type="checkbox" class="skill-toggle" data-skill="${escapeHtml(skill.name)}" ${skill.enabled ? 'checked' : ''}>
                    <span class="slider"></span>
                </label>
            `;

            skillsGrid.appendChild(skillItem);
        });

        document.querySelectorAll('.skill-toggle').forEach(toggle => {
            toggle.addEventListener('change', async (e) => {
                const skillName = e.target.dataset.skill;
                const enabled = e.target.checked;
                await updateSkillStatus(skillName, enabled);
            });
        });

    } catch (error) {
        console.error('加载技能列表失败:', error);
        skillsGrid.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i><span>${escapeHtml(error.message)}</span></div>`;
    }
}

async function updateSkillStatus(skillName, enabled) {
    try {
        const response = await fetch(`/api/user/skills/${encodeURIComponent(skillName)}`, {
            method: 'PUT',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ enabled })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '更新技能状态失败');
        }

        console.log(`技能 "${skillName}" 已${enabled ? '启用' : '禁用'}`);

    } catch (error) {
        console.error('更新技能状态失败:', error);
        // 恢复切换状态
        const toggle = document.querySelector(`.skill-toggle[data-skill="${skillName}"]`);
        if (toggle) {
            toggle.checked = !enabled;
        }
        alert(`更新技能状态失败: ${error.message}`);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
