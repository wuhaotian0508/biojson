// 全局状态
let isQuerying = false;
let conversationHistory = [];
let hasStartedConversation = false; // 新增：跟踪是否已开始对话

// 随机标语库
const welcomeSlogans = [
    "今天你想知道点什么？",
    "探索植物基因的奥秘",
    "有什么关于营养代谢的问题吗？",
    "让我帮你找到答案",
    "开始你的科研探索之旅",
    "基因的秘密，等你来发现",
    "想了解哪些基因的功能？",
    "营养代谢，从这里开始",
    "科学问答，随时为你服务",
    "深入了解植物营养基因",
    "你的科研助手已就绪",
    "问我关于基因的任何问题",
    "发现植物代谢的精彩世界",
    "让数据为你揭示真相",
    "基因调控，一问便知",
    "今天想研究什么代谢通路？",
    "文献中的答案，触手可及",
    "从问题到洞察，只需一步",
    "你的问题，我的使命",
    "科研路上，有我相伴"
];

// DOM 元素
const chatContainer = document.getElementById('chat-container');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const historyList = document.getElementById('history-list');
const sceneIntro = document.getElementById('scene-intro'); // 场景介绍元素
const welcomeSection = document.getElementById('welcome-section'); // 欢迎区域
const welcomeSlogan = document.getElementById('welcome-slogan'); // 标语元素

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupEventListeners();
    setRandomSlogan(); // 设置随机标语
});

// 设置随机标语
function setRandomSlogan() {
    const randomIndex = Math.floor(Math.random() * welcomeSlogans.length);
    if (welcomeSlogan) {
        welcomeSlogan.textContent = welcomeSlogans[randomIndex];
    }
}

// 设置事件监听
function setupEventListeners() {
    // 发送按钮
    sendBtn.addEventListener('click', handleSend);

    // 新对话按钮
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }

    // 回车发送 (Shift+Enter 换行)
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // 自动调整输入框高度
    queryInput.addEventListener('input', () => {
        queryInput.style.height = 'auto';
        queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + 'px';
    });
}

// 开始新对话
function startNewChat() {
    // 清空聊天容器
    chatContainer.innerHTML = '';

    // 重置对话状态
    hasStartedConversation = false;

    // 显示欢迎标语和场景介绍
    if (welcomeSection) {
        welcomeSection.classList.remove('hidden');
    }
    if (sceneIntro) {
        sceneIntro.classList.remove('hidden');
    }

    // 重新设置随机标语
    setRandomSlogan();

    // 清空输入框
    queryInput.value = '';
    queryInput.style.height = 'auto';

    // 聚焦输入框
    queryInput.focus();
}

// 处理发送
async function handleSend() {
    const query = queryInput.value.trim();
    if (!query || isQuerying) return;

    // 首次发送消息时隐藏欢迎标语和场景介绍
    if (!hasStartedConversation) {
        hideWelcomeAndScene();
        hasStartedConversation = true;
    }

    // 添加用户消息
    addMessage('user', query);

    // 清空输入框
    queryInput.value = '';
    queryInput.style.height = 'auto';

    // 禁用发送按钮
    isQuerying = true;
    sendBtn.disabled = true;

    // 创建助手消息占位
    const assistantMsgId = addMessage('assistant', '<div class="loading-dots"><span>•</span><span>•</span><span>•</span></div>');

    try {
        // 调用 API
        await streamQuery(query, assistantMsgId);

        // 保存到历史
        saveToHistory(query);

    } catch (error) {
        updateMessage(assistantMsgId, `<p style="color: red;">错误: ${error.message}</p>`);
    } finally {
        isQuerying = false;
        sendBtn.disabled = false;
    }
}

// 隐藏欢迎标语和场景介绍
function hideWelcomeAndScene() {
    if (welcomeSection) {
        welcomeSection.classList.add('hidden');
    }
    if (sceneIntro) {
        sceneIntro.classList.add('hidden');
    }
}

// 流式查询
async function streamQuery(query, messageId) {
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });

    if (!response.ok) {
        throw new Error('网络请求失败');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let answerText = '';
    let sources = [];

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));

                if (data.type === 'sources') {
                    sources = data.data;
                } else if (data.type === 'text') {
                    answerText += data.data;
                    updateMessage(messageId, formatAnswer(answerText) + renderSources(sources));
                } else if (data.type === 'done') {
                    updateMessage(messageId, formatAnswer(answerText) + renderSources(sources));
                } else if (data.type === 'error') {
                    throw new Error(data.data);
                }
            }
        }
    }
}

// 格式化答案 (将 [文章名 | 基因名] 转换为标签)
function formatAnswer(text) {
    // 将 [文章名 | 基因名] 转换为 HTML 标签
    const formatted = text.replace(
        /\[([^\]]+)\s*\|\s*([^\]]+)\]/g,
        '<span class="source-tag">$1 | $2</span>'
    );

    // 转换段落
    const paragraphs = formatted.split('\n\n').filter(p => p.trim());
    return paragraphs.map(p => `<p>${p}</p>`).join('');
}

// 渲染来源列表
function renderSources(sources) {
    if (!sources || sources.length === 0) return '';

    const items = sources.slice(0, 10).map((source, index) => `
        <div class="source-item">
            <strong>${index + 1}. ${source.gene_name}</strong> - ${source.paper_title}
            <span style="color: #999;">(相关度: ${source.score.toFixed(3)})</span>
        </div>
    `).join('');

    return `
        <div class="sources-section">
            <div class="sources-title">📚 参考文献 (共 ${sources.length} 条):</div>
            <div class="sources-list">${items}</div>
        </div>
    `;
}

// 添加消息
function addMessage(role, content) {
    const messageId = `msg-${Date.now()}-${Math.random()}`;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    messageDiv.id = messageId;

    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">🧬</div>
            <div class="message-body">
                <div class="message-content">${content}</div>
            </div>
        `;
    }

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return messageId;
}

// 更新消息
function updateMessage(messageId, content) {
    const messageEl = document.getElementById(messageId);
    if (messageEl) {
        const contentEl = messageEl.querySelector('.message-content');
        if (contentEl) {
            contentEl.innerHTML = content;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 保存到历史
function saveToHistory(query) {
    conversationHistory.unshift({
        query,
        timestamp: Date.now()
    });

    // 最多保存 20 条
    if (conversationHistory.length > 20) {
        conversationHistory = conversationHistory.slice(0, 20);
    }

    localStorage.setItem('conversation_history', JSON.stringify(conversationHistory));
    loadHistory();
}

// 加载历史
function loadHistory() {
    const saved = localStorage.getItem('conversation_history');
    if (saved) {
        conversationHistory = JSON.parse(saved);
    }

    historyList.innerHTML = '';

    if (conversationHistory.length === 0) {
        historyList.innerHTML = '<div class="history-loading">暂无历史记录</div>';
        return;
    }

    conversationHistory.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.textContent = item.query.slice(0, 30) + (item.query.length > 30 ? '...' : '');
        div.onclick = () => {
            queryInput.value = item.query;
            queryInput.focus();
        };
        historyList.appendChild(div);
    });
}

// 清空历史
function clearHistory() {
    if (confirm('确定要清空所有历史记录吗？')) {
        conversationHistory = [];
        localStorage.removeItem('conversation_history');
        loadHistory();
    }
}
