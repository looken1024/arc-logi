// 表情包小程序主脚本
class EmojiApp {
    constructor() {
        this.currentPage = 1;
        this.currentCategory = 'all';
        this.searchQuery = '';
        this.favorites = this.loadFavorites();
        this.pageSize = 20;
        this.isLoading = false;
        
        // 表情包数据
        this.emojiData = this.generateEmojiData();
        this.filteredData = [...this.emojiData];
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.renderEmojis();
        this.updateLoadMoreButton();
    }

    // 生成表情包数据
    generateEmojiData() {
        const categories = ['popular', 'funny', 'cute', 'emotion', 'meme'];
        const titles = [
            '开心', '难过', '生气', '惊讶', '无语', '尴尬', '调皮', '卖萌', '鄙视', '赞',
            '吐血', '晕倒', '流泪', '笑哭', '猪头', '吃瓜', '狗头', '滑稽', '白眼', '给力',
            '加油', '666', '来了来了', '冲鸭', '喵喵喵', '汪汪汪', '哈哈哈', '嘿嘿嘿', '嘻嘻', '嗯嗯',
            '爱你哟', '么么哒', '抱抱', '比心', '撒花', '庆祝', '鼓掌', '跳舞', '唱歌', '干杯'
        ];
        
        const data = [];
        for (let i = 1; i <= 200; i++) {
            const category = categories[Math.floor(Math.random() * categories.length)];
            const title = titles[Math.floor(Math.random() * titles.length)];
            
            data.push({
                id: i,
                title: `${title}${i}`,
                category: category,
                url: `https://picsum.photos/seed/emoji${i}/200/200.jpg`,
                thumbnail: `https://picsum.photos/seed/emoji${i}/150/150.jpg`,
                likes: Math.floor(Math.random() * 1000),
                downloads: Math.floor(Math.random() * 500)
            });
        }
        
        return data;
    }

    // 加载收藏数据
    loadFavorites() {
        const saved = localStorage.getItem('emojiFavorites');
        return saved ? JSON.parse(saved) : [];
    }

    // 保存收藏数据
    saveFavorites() {
        localStorage.setItem('emojiFavorites', JSON.stringify(this.favorites));
    }

    // 绑定事件
    bindEvents() {
        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        
        searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.trim();
            this.debounceSearch();
        });
        
        searchBtn.addEventListener('click', () => {
            this.performSearch();
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // 分类切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchCategory(e.target.dataset.category);
            });
        });

        // 加载更多
        document.getElementById('loadMoreBtn').addEventListener('click', () => {
            this.loadMore();
        });

        // 底部按钮
        document.getElementById('randomBtn').addEventListener('click', () => {
            this.showRandomEmoji();
        });

        document.getElementById('favoriteBtn').addEventListener('click', () => {
            this.showFavorites();
        });

        document.getElementById('uploadBtn').addEventListener('click', () => {
            this.showUploadDialog();
        });

        // 预览弹窗
        const modal = document.getElementById('previewModal');
        const closeBtn = document.getElementById('closeModal');
        
        closeBtn.addEventListener('click', () => {
            this.closeModal();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // 预览操作按钮
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadCurrentEmoji();
        });

        document.getElementById('shareBtn').addEventListener('click', () => {
            this.shareCurrentEmoji();
        });

        document.getElementById('favoriteToggleBtn').addEventListener('click', () => {
            this.toggleFavorite();
        });

        // 滚动加载更多
        window.addEventListener('scroll', () => {
            this.handleScroll();
        });
    }

    // 防抖搜索
    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch();
        }, 300);
    }

    // 执行搜索
    performSearch() {
        this.currentPage = 1;
        this.filterData();
        this.renderEmojis();
    }

    // 切换分类
    switchCategory(category) {
        this.currentCategory = category;
        this.currentPage = 1;
        
        // 更新分类标签样式
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
        
        this.filterData();
        this.renderEmojis();
    }

    // 过滤数据
    filterData() {
        this.filteredData = this.emojiData.filter(emoji => {
            const matchCategory = this.currentCategory === 'all' || emoji.category === this.currentCategory;
            const matchSearch = !this.searchQuery || 
                emoji.title.toLowerCase().includes(this.searchQuery.toLowerCase());
            return matchCategory && matchSearch;
        });
    }

    // 渲染表情包
    renderEmojis() {
        const grid = document.getElementById('emojiGrid');
        const start = 0;
        const end = this.currentPage * this.pageSize;
        const dataToShow = this.filteredData.slice(start, end);
        
        if (this.currentPage === 1) {
            grid.innerHTML = '';
        }
        
        dataToShow.forEach(emoji => {
            const card = this.createEmojiCard(emoji);
            grid.appendChild(card);
        });
        
        this.updateLoadMoreButton();
    }

    // 创建表情包卡片
    createEmojiCard(emoji) {
        const card = document.createElement('div');
        card.className = 'emoji-card';
        card.dataset.id = emoji.id;
        
        const isFavorite = this.favorites.includes(emoji.id);
        const favoriteMark = isFavorite ? '<div class="favorite-mark">❤️</div>' : '';
        
        card.innerHTML = `
            <img src="${emoji.thumbnail}" alt="${emoji.title}" loading="lazy">
            <div class="emoji-info">${emoji.title}</div>
            ${favoriteMark}
        `;
        
        card.addEventListener('click', () => {
            this.showPreview(emoji);
        });
        
        return card;
    }

    // 显示预览
    showPreview(emoji) {
        this.currentEmoji = emoji;
        const modal = document.getElementById('previewModal');
        const previewImage = document.getElementById('previewImage');
        const favoriteBtn = document.getElementById('favoriteToggleBtn');
        
        previewImage.src = emoji.url;
        previewImage.alt = emoji.title;
        
        // 更新收藏按钮状态
        const isFavorite = this.favorites.includes(emoji.id);
        favoriteBtn.textContent = isFavorite ? '取消收藏' : '收藏';
        
        modal.classList.add('show');
        
        // 防止页面滚动
        document.body.style.overflow = 'hidden';
    }

    // 关闭弹窗
    closeModal() {
        const modal = document.getElementById('previewModal');
        modal.classList.remove('show');
        document.body.style.overflow = '';
        this.currentEmoji = null;
    }

    // 下载表情包
    downloadCurrentEmoji() {
        if (!this.currentEmoji) return;
        
        const link = document.createElement('a');
        link.href = this.currentEmoji.url;
        link.download = `${this.currentEmoji.title}.jpg`;
        link.target = '_blank';
        
        // 触发下载
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 显示下载成功提示
        this.showToast('下载成功！');
        
        // 更新下载次数
        this.currentEmoji.downloads++;
    }

    // 分享表情包
    shareCurrentEmoji() {
        if (!this.currentEmoji) return;
        
        if (navigator.share) {
            navigator.share({
                title: this.currentEmoji.title,
                text: `分享一个有趣的表情包：${this.currentEmoji.title}`,
                url: this.currentEmoji.url
            }).then(() => {
                this.showToast('分享成功！');
            }).catch(() => {
                this.copyToClipboard();
            });
        } else {
            this.copyToClipboard();
        }
    }

    // 复制到剪贴板
    copyToClipboard() {
        if (!this.currentEmoji) return;
        
        const text = `${this.currentEmoji.title}: ${this.currentEmoji.url}`;
        
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showToast('链接已复制到剪贴板！');
            });
        } else {
            // 兼容旧版浏览器
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showToast('链接已复制到剪贴板！');
        }
    }

    // 切换收藏状态
    toggleFavorite() {
        if (!this.currentEmoji) return;
        
        const index = this.favorites.indexOf(this.currentEmoji.id);
        const favoriteBtn = document.getElementById('favoriteToggleBtn');
        
        if (index > -1) {
            // 取消收藏
            this.favorites.splice(index, 1);
            favoriteBtn.textContent = '收藏';
            this.showToast('已取消收藏');
        } else {
            // 添加收藏
            this.favorites.push(this.currentEmoji.id);
            favoriteBtn.textContent = '取消收藏';
            this.showToast('收藏成功！');
        }
        
        this.saveFavorites();
        this.updateFavoriteMarks();
    }

    // 更新收藏标记
    updateFavoriteMarks() {
        document.querySelectorAll('.emoji-card').forEach(card => {
            const id = parseInt(card.dataset.id);
            const favoriteMark = card.querySelector('.favorite-mark');
            const isFavorite = this.favorites.includes(id);
            
            if (isFavorite && !favoriteMark) {
                const mark = document.createElement('div');
                mark.className = 'favorite-mark';
                mark.textContent = '❤️';
                card.appendChild(mark);
            } else if (!isFavorite && favoriteMark) {
                favoriteMark.remove();
            }
        });
    }

    // 显示随机表情
    showRandomEmoji() {
        const randomIndex = Math.floor(Math.random() * this.emojiData.length);
        const randomEmoji = this.emojiData[randomIndex];
        this.showPreview(randomEmoji);
    }

    // 显示收藏
    showFavorites() {
        const favoriteEmojis = this.emojiData.filter(emoji => 
            this.favorites.includes(emoji.id)
        );
        
        if (favoriteEmojis.length === 0) {
            this.showToast('暂无收藏的表情包');
            return;
        }
        
        // 临时切换到收藏模式
        this.filteredData = favoriteEmojis;
        this.currentPage = 1;
        this.currentCategory = 'favorites';
        
        // 更新UI
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        this.renderEmojis();
        this.showToast(`显示 ${favoriteEmojis.length} 个收藏表情包`);
    }

    // 显示上传对话框
    showUploadDialog() {
        this.showToast('上传功能开发中，敬请期待！');
    }

    // 加载更多
    loadMore() {
        if (this.isLoading) return;
        
        const hasMore = this.currentPage * this.pageSize < this.filteredData.length;
        
        if (hasMore) {
            this.currentPage++;
            this.renderEmojis();
        } else {
            this.showToast('没有更多表情包了');
        }
    }

    // 处理滚动
    handleScroll() {
        if (this.isLoading) return;
        
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        
        // 当滚动到接近底部时自动加载
        if (scrollTop + windowHeight >= documentHeight - 100) {
            const hasMore = this.currentPage * this.pageSize < this.filteredData.length;
            if (hasMore) {
                this.loadMore();
            }
        }
    }

    // 更新加载更多按钮状态
    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        const hasMore = this.currentPage * this.pageSize < this.filteredData.length;
        
        if (hasMore) {
            loadMoreBtn.style.display = 'block';
            loadMoreBtn.textContent = '加载更多';
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }

    // 显示提示消息
    showToast(message) {
        // 移除现有的toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            z-index: 10000;
            animation: fadeIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 2000);
    }
}

// 添加fadeout动画
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new EmojiApp();
});