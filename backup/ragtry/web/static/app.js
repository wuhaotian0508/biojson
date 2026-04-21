// 基因信息 RAG 问答系统 - 前端逻辑

const chatContainer = document.getElementById('chat-container');
const questionInput = document.getElementById('question-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');
const exportBtn = document.getElementById('export-btn');

let currentMessageDiv = null;
let isGenerating = false;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    setupEventListeners();
});

// 设置事件监听
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSend);
    clearBtn.addEventListener('click', handleClear);
    exportBtn.addEventListener('click', handleExport);

    // 支持 Enter 发送，Shift+Enter 换行
    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
}

// 发送问题
function handleSend() {
    const question = questionInput.value.trim();

    if (!question) {
        showError('请输入问题');
        return;
    }

    if (isGenerating) {
        showError('正在生成答案，请稍候...');
        return;
    }

    // 清空输入框
    questionInput.value = '';

    // 显示用户问题
    appendMessage('user', question);

    // 发送请求
    sendQuestion(question);
}

// 发送问题到后端
function sendQuestion(question) {
    isGenerating = true;
    sendBtn.disabled = true;

    // 使用 fetch + ReadableStream 接收 SSE (支持 POST)
    fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({question: question})
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentAnswer = '';
        let sources = [];

        // 创建助手消息容器
        currentMessageDiv = createMessageDiv('assistant');

        function processChunk({done, value}) {
            if (done) {
                // 移除光标
                removeCursor();
                // 保存到历史
                saveToHistory(question, currentAnswer, sources);
                // 重置状态
                isGenerating = false;
                sendBtn.disabled = false;
                currentMessageDiv = null;
                return;
            }

            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // 保留不完整的行

            lines.forEach(line => {
                if (!line.trim()) return;
                const parts = line.split('\n');
                if (parts.length < 2) return;

                const eventLine = parts[0];
                const dataLine = parts[1];

                if (!eventLine.startsWith('event: ') || !dataLine.startsWith('data: ')) return;

                const event = eventLine.replace('event: ', '').trim();
                const data = dataLine.replace('data: ', '').trim();

                try {
                    if (event === 'sources') {
                        sources = JSON.parse(data);
                        showSources(sources);
                    } else if (event === 'token') {
                        const token = JSON.parse(data).content;
                        currentAnswer += token;
                        updateAnswer(currentAnswer);
                    } else if (event === 'done') {
                        // 完成
                    } else if (event === 'error') {
                        const errorMsg = JSON.parse(data).message;
                        showError('生成失败: ' + errorMsg);
                        isGenerating = false;
                        sendBtn.disabled = false;
                    }
                } catch (e) {
                    console.error('解析事件失败:', e, 'Event:', event, 'Data:', data);
                }
            });

            return reader.read().then(processChunk);
        }

        return reader.read().then(processChunk);
    })
    .catch(err => {
        showError('请求失败: ' + err.message);
        isGenerating = false;
        sendBtn.disabled = false;
        if (currentMessageDiv) {
            currentMessageDiv.remove();
            currentMessageDiv = null;
        }
    });
}

// 创建消息容器
function createMessageDiv(role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = role === 'user' ? '你' : 'AI 助手';

    const content = document.createElement('div');
    content.className = 'message-content';

    div.appendChild(label);
    div.appendChild(content);
    chatContainer.appendChild(div);

    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return div;
}

// 添加消息
function appendMessage(role, text, sources = null) {
    const div = createMessageDiv(role);
    const content = div.querySelector('.message-content');
    content.textContent = text;

    if (sources && sources.length > 0) {
        const sourcesDiv = createSourcesDiv(sources);
        div.insertBefore(sourcesDiv, content);
    }

    return div;
}

// 显示来源
function showSources(sources) {
    if (!currentMessageDiv || sources.length === 0) return;

    const sourcesDiv = createSourcesDiv(sources);
    const content = currentMessageDiv.querySelector('.message-content');
    currentMessageDiv.insertBefore(sourcesDiv, content);
}

// 创建来源显示
function createSourcesDiv(sources) {
    const div = document.createElement('div');
    div.className = 'sources';

    const title = document.createElement('div');
    title.className = 'sources-title';
    title.textContent = `📚 检索到 ${sources.length} 个相关基因：`;
    div.appendChild(title);

    sources.forEach((source, i) => {
        const item = document.createElement('div');
        item.className = 'source-item';
        item.innerHTML = `${i+1}. <span class="gene-name">${escapeHtml(source.gene)}</span> - ${escapeHtml(source.article)} <span class="score">(${source.score.toFixed(3)})</span>`;
        div.appendChild(item);
    });

    return div;
}

// 更新答案（流式）
function updateAnswer(text) {
    if (!currentMessageDiv) return;

    const content = currentMessageDiv.querySelector('.message-content');
    content.textContent = text;

    // 添加光标
    if (!content.querySelector('.cursor')) {
        const cursor = document.createElement('span');
        cursor.className = 'cursor';
        content.appendChild(cursor);
    }

    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 移除光标
function removeCursor() {
    if (!currentMessageDiv) return;
    const cursor = currentMessageDiv.querySelector('.cursor');
    if (cursor) cursor.remove();
}

// 显示错误
function showError(message) {
    const div = document.createElement('div');
    div.className = 'error';
    div.textContent = '❌ ' + message;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // 3秒后自动移除
    setTimeout(() => div.remove(), 3000);
}

// 保存到历史
function saveToHistory(question, answer, sources) {
    const history = JSON.parse(localStorage.getItem('rag-history') || '[]');
    history.push({
        q: question,
        a: answer,
        sources: sources,
        time: new Date().toISOString()
    });
    localStorage.setItem('rag-history', JSON.stringify(history));
}

// 加载历史
function loadHistory() {
    const history = JSON.parse(localStorage.getItem('rag-history') || '[]');
    history.forEach(item => {
        appendMessage('user', item.q);
        appendMessage('assistant', item.a, item.sources);
    });
}

// 清空对话
function handleClear() {
    if (!confirm('确定要清空所有对话吗？')) return;

    chatContainer.innerHTML = '';
    localStorage.removeItem('rag-history');
}

// 导出全部
function handleExport() {
    const history = JSON.parse(localStorage.getItem('rag-history') || '[]');

    if (history.length === 0) {
        showError('没有对话记录可导出');
        return;
    }

    const markdown = history.map((item, i) => {
        let md = `## 问题 ${i+1}\n${item.q}\n\n`;

        if (item.sources && item.sources.length > 0) {
            md += `### 检索来源\n`;
            item.sources.forEach((s, j) => {
                md += `${j+1}. ${s.gene} - ${s.article} (${s.score.toFixed(3)})\n`;
            });
            md += '\n';
        }

        md += `### 答案\n${item.a}\n\n`;
        md += `---\n\n`;
        return md;
    }).join('');

    const blob = new Blob([markdown], {type: 'text/markdown;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rag-history-${new Date().toISOString().slice(0,10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
