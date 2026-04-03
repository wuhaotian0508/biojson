// ===== 国际化 (i18n) =====
let currentLang = localStorage.getItem('lang') || 'zh';

const I18N = {
    zh: {
        // 语言按钮自身
        'lang.btn': '简体中文',
        // 侧边栏
        'sidebar.history': '历史会话',
        'sidebar.viewAll': '查看全部...',
        'sidebar.noHistory': '暂无历史记录',
        'sidebar.myLibrary': '我的知识库',
        // 头部
        'header.newChat': '+ 新对话',
        // 输入区
        'input.placeholder': '描述你的需求，例如：对衰老相关的Biomarker进行文献综述',
        'input.personal': '个人库',
        'input.depth': '深度调研',
        // 场景
        'scene.category': '场景介绍（类别）',
        'scene.detail': '场景介绍（图片文字）',
        // 知识库弹窗
        'kb.title': '我的知识库',
        'kb.uploadBtn': '+ 上传 PDF',
        'kb.uploading': '上传中...',
        'kb.parsing': '解析中...',
        'kb.uploadSuccess': '上传成功!',
        'kb.uploadFail': '上传失败',
        'kb.networkError': '网络错误',
        'kb.loadFail': '加载失败',
        'kb.empty': '暂无文件，点击上方按钮上传 PDF',
        'kb.confirmDelete': '确定删除 "{0}" 吗？',
        'kb.renamePrompt': '输入新文件名：',
        'kb.renameFail': '重命名失败',
        'kb.deleteFail': '删除失败',
        'kb.pages': '页',
        'kb.chunks': '块',
        'kb.rename': '重命名',
        'kb.delete': '删除',
        // 认证
        'auth.login': '登录',
        'auth.signup': '注册',
        'auth.loginBtn': '登 录',
        'auth.signupBtn': '注 册',
        'auth.emailPlaceholder': '邮箱地址',
        'auth.passwordPlaceholder': '密码',
        'auth.signupPasswordPlaceholder': '密码（至少6位）',
        'auth.confirmPasswordPlaceholder': '确认密码',
        'auth.nicknamePlaceholder': '昵称（选填）',
        'auth.avatarPlaceholder': '头像',
        'auth.chooseAvatar': '选择头像',
        'auth.expired': '登录已过期，请重新登录',
        'auth.networkFail': '网络请求失败',
        'auth.tagline': '智能植物营养基因问答平台',
        'auth.feature1': '基因数据库语义检索',
        'auth.feature2': 'PubMed 文献联网搜索',
        'auth.feature3': '个人知识库管理',
        'auth.feature4': 'AI 深度调研报告',
        // 管理后台
        'header.admin': '管理后台',
        'auth.logout': '退出登录',
        // 个人资料
        'profile.changeAvatar': '更换头像',
        'profile.save': '保存',
        'profile.saving': '保存中...',
        'profile.saveFail': '保存失败',
        'profile.deleteAccount': '注销账号',
        'profile.confirmDelete': '确定要永久删除账号吗？此操作不可恢复！',
        'profile.deleteFail': '删除失败',
        // 搜索进度
        'search.searching': '正在搜索...',
        'search.deepSearching': '深度调研中，正在检索更多文献并生成综合报告...',
        // 来源
        'source.title': '📚 参考来源',
        'source.gene_db': '基因库',
        'source.pubmed': 'PubMed',
        'source.jina_web': '网页',
        'source.personal': '个人库',
        // 其他
        'error.prefix': '错误',
        'history.oldRecord': '（旧记录，无回答内容）',
        'confirm.clearHistory': '确定要清空所有历史记录吗？',
        // 基因编辑器
        'gene.detected': '检测到以下可编辑基因：',
        'gene.addBtn': '+ 添加基因',
        'gene.inputPlaceholder': '输入基因名',
        'gene.removeTitle': '移除此基因',
        // 欢迎标语
        'slogans': [
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
        ],
    },
    en: {
        'lang.btn': 'English',
        'sidebar.history': 'Chat History',
        'sidebar.viewAll': 'View all...',
        'sidebar.noHistory': 'No history yet',
        'sidebar.myLibrary': 'My Library',
        'header.newChat': '+ New Chat',
        'input.placeholder': 'Describe your needs, e.g.: Literature review on aging-related biomarkers',
        'input.personal': 'Personal',
        'input.depth': 'Deep Research',
        'scene.category': 'Scenarios (Categories)',
        'scene.detail': 'Scenarios (Details)',
        'kb.title': 'My Library',
        'kb.uploadBtn': '+ Upload PDF',
        'kb.uploading': 'Uploading...',
        'kb.parsing': 'Parsing...',
        'kb.uploadSuccess': 'Upload successful!',
        'kb.uploadFail': 'Upload failed',
        'kb.networkError': 'Network error',
        'kb.loadFail': 'Failed to load',
        'kb.empty': 'No files yet. Click the button above to upload a PDF.',
        'kb.confirmDelete': 'Delete "{0}"?',
        'kb.renamePrompt': 'Enter new filename:',
        'kb.renameFail': 'Rename failed',
        'kb.deleteFail': 'Delete failed',
        'kb.pages': 'pages',
        'kb.chunks': 'chunks',
        'kb.rename': 'Rename',
        'kb.delete': 'Delete',
        'auth.login': 'Login',
        'auth.signup': 'Sign Up',
        'auth.loginBtn': 'Login',
        'auth.signupBtn': 'Sign Up',
        'auth.emailPlaceholder': 'Email address',
        'auth.passwordPlaceholder': 'Password',
        'auth.signupPasswordPlaceholder': 'Password (min 6 chars)',
        'auth.confirmPasswordPlaceholder': 'Confirm password',
        'auth.nicknamePlaceholder': 'Nickname (optional)',
        'auth.avatarPlaceholder': 'Avatar',
        'auth.chooseAvatar': 'Choose Avatar',
        'auth.expired': 'Session expired, please log in again',
        'auth.networkFail': 'Network request failed',
        'auth.tagline': 'Intelligent Plant Nutrient Gene Q&A Platform',
        'auth.feature1': 'Semantic gene database retrieval',
        'auth.feature2': 'PubMed literature online search',
        'auth.feature3': 'Personal library management',
        'auth.feature4': 'AI deep research reports',
        'header.admin': 'Admin Panel',
        'auth.logout': 'Log out',
        'profile.changeAvatar': 'Change Avatar',
        'profile.save': 'Save',
        'profile.saving': 'Saving...',
        'profile.saveFail': 'Save failed',
        'profile.deleteAccount': 'Delete Account',
        'profile.confirmDelete': 'Permanently delete your account? This cannot be undone!',
        'profile.deleteFail': 'Delete failed',
        'search.searching': 'Searching...',
        'search.deepSearching': 'Deep research: retrieving more literature and generating a comprehensive report...',
        'source.title': '📚 References',
        'source.gene_db': 'Gene DB',
        'source.pubmed': 'PubMed',
        'source.jina_web': 'Web',
        'source.personal': 'Personal',
        'error.prefix': 'Error',
        'history.oldRecord': '(Old record, no answer)',
        'confirm.clearHistory': 'Clear all history?',
        // Gene editor
        'gene.detected': 'Detected editable genes:',
        'gene.addBtn': '+ Add gene',
        'gene.inputPlaceholder': 'Gene name',
        'gene.removeTitle': 'Remove this gene',
        'slogans': [
            "What would you like to know today?",
            "Explore the secrets of plant genes",
            "Any questions about nutrient metabolism?",
            "Let me help you find the answer",
            "Start your research journey",
            "Gene secrets, waiting to be discovered",
            "Which gene functions interest you?",
            "Nutrient metabolism starts here",
            "Scientific Q&A, at your service",
            "Dive deep into plant nutrient genes",
            "Your research assistant is ready",
            "Ask me anything about genes",
            "Discover the world of plant metabolism",
            "Let data reveal the truth",
            "Gene regulation, one question away",
            "Which metabolic pathway today?",
            "Answers from literature, at your fingertips",
            "From questions to insights, one step",
            "Your questions, my mission",
            "On the research journey, together"
        ],
    },
};

/** Get translated string. Supports {0} placeholders. */
function t(key, ...args) {
    let str = I18N[currentLang]?.[key] ?? I18N['zh'][key] ?? key;
    args.forEach((arg, i) => { str = str.replace(`{${i}}`, arg); });
    return str;
}

/** Apply current language to all elements with data-i18n / data-i18n-placeholder */
function applyLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = t(key);
    });
    // Language button shows the *current* language name
    const langBtn = document.getElementById('lang-btn');
    if (langBtn) langBtn.textContent = t('lang.btn');
    // Update html lang
    document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';
    // Refresh slogan
    setRandomSlogan();
}

function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('lang', currentLang);
    applyLanguage();
    // Re-render history list (contains translated empty text)
    loadHistory();
}

// ===== 全局状态 =====
let isQuerying = false;
let conversationHistory = [];  // [{id, title, messages: [{query, answerText, sources, timestamp}], timestamp}]
let currentSessionId = null;   // 当前对话的 session ID
let hasStartedConversation = false;
let isDeepSearch = false;
let usePersonal = false;
const assistantTurnState = new Map();
let currentAbortController = null;  // 用于中断正在进行的 SSE 流
let currentStreamMsgId = null;      // 正在流式生成的 assistant 消息 ID

// 中断正在进行的 SSE 流，保存已有的部分回答
function abortCurrentStream() {
    if (!currentAbortController) return;
    // 先保存部分回答到历史
    if (currentStreamMsgId) {
        const state = assistantTurnState.get(currentStreamMsgId);
        if (state && state.answerText) {
            saveToHistory(state.query, state.answerText, state.sources, state.genes, state.sops);
        }
    }
    currentAbortController.abort();
    currentAbortController = null;
    currentStreamMsgId = null;
    isQuerying = false;
    sendBtn.disabled = false;
}

// DOM 元素
const chatContainer = document.getElementById('chat-container');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const historyList = document.getElementById('history-list');
const sceneIntro = document.getElementById('scene-intro');
const welcomeSection = document.getElementById('welcome-section');
const welcomeSlogan = document.getElementById('welcome-slogan');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    try {
        loadHistory();
        setupEventListeners();
        setRandomSlogan();
        setupKBModal();
        applyLanguage();

        // ===== 登录功能初始化 =====
        setupAuthListeners();
        initAuth();
    } catch (err) {
        console.error('前端初始化失败:', err);
        if (typeof showLoginOverlay === 'function') {
            showLoginOverlay();
        }
        if (typeof showAuthError === 'function') {
            showAuthError(err.message || '页面初始化失败');
        }
    }
});

// 设置随机标语
function setRandomSlogan() {
    const slogans = I18N[currentLang]?.slogans || I18N['zh'].slogans;
    const randomIndex = Math.floor(Math.random() * slogans.length);
    if (welcomeSlogan) {
        welcomeSlogan.textContent = slogans[randomIndex];
    }
}

// 设置事件监听
function setupEventListeners() {
    if (!sendBtn || !queryInput) {
        throw new Error('关键输入组件未找到');
    }

    sendBtn.addEventListener('click', handleSend);

    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', startNewChat);
    }

    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    queryInput.addEventListener('input', () => {
        queryInput.style.height = 'auto';
        queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + 'px';
    });

    // 深度调研按钮切换
    const depthBtn = document.getElementById('depth-btn');
    if (depthBtn) {
        depthBtn.addEventListener('click', () => {
            isDeepSearch = !isDeepSearch;
            depthBtn.classList.toggle('active', isDeepSearch);
        });
    }

    // 个人库按钮切换
    const personalBtn = document.getElementById('personal-btn');
    if (personalBtn) {
        personalBtn.addEventListener('click', () => {
            usePersonal = !usePersonal;
            personalBtn.classList.toggle('active', usePersonal);
        });
    }

    // 语言切换按钮
    const langBtn = document.getElementById('lang-btn');
    if (langBtn) {
        langBtn.addEventListener('click', toggleLanguage);
    }

    // 侧边栏折叠按钮
    const menuBtn = document.querySelector('.menu-btn');
    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('collapsed');
        });
    }
}

// ===== 知识库模态窗口 =====
function setupKBModal() {
    const toggle = document.getElementById('kb-toggle');
    const overlay = document.getElementById('kb-modal-overlay');
    const closeBtn = document.getElementById('kb-modal-close');
    const uploadBtn = document.getElementById('kb-upload-btn');
    const fileInput = document.getElementById('kb-file-input');

    if (!toggle || !overlay) return;

    toggle.addEventListener('click', () => {
        overlay.style.display = 'flex';
        loadPersonalFiles();
    });

    if (!closeBtn || !uploadBtn || !fileInput) {
        return;
    }

    closeBtn.addEventListener('click', () => {
        overlay.style.display = 'none';
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.display = 'none';
        }
    });

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;
        await uploadPDF(file);
        fileInput.value = '';
    });
}

// 加载个人库文件列表
async function loadPersonalFiles() {
    const listEl = document.getElementById('kb-file-list');
    const badgeEl = document.getElementById('kb-file-count');
    if (!listEl) return;

    try {
        const resp = await fetch('/api/personal/files', {
            headers: { 'Authorization': 'Bearer ' + getAccessToken() },
        });
        if (!resp.ok) {
            listEl.innerHTML = `<div class="kb-empty">${t('kb.loadFail')}</div>`;
            return;
        }
        const data = await resp.json();
        const files = data.files || [];

        if (badgeEl) {
            if (files.length > 0) {
                badgeEl.textContent = files.length;
                badgeEl.style.display = 'inline-block';
            } else {
                badgeEl.style.display = 'none';
            }
        }

        if (files.length === 0) {
            listEl.innerHTML = `<div class="kb-empty">${t('kb.empty')}</div>`;
            return;
        }

        listEl.innerHTML = files.map(f => `
            <div class="kb-file-item" data-filename="${escapeHtml(f.filename)}">
                <div class="kb-file-info">
                    <div class="kb-file-name">${escapeHtml(f.filename)}</div>
                    <div class="kb-file-meta">${f.num_pages} ${t('kb.pages')} · ${f.num_chunks} ${t('kb.chunks')} · ${f.size_mb}MB · ${f.upload_time}</div>
                </div>
                <div class="kb-file-actions">
                    <button class="kb-action-btn kb-rename-btn" title="${t('kb.rename')}" onclick="renameFile('${escapeHtml(f.filename)}')">✏️</button>
                    <button class="kb-action-btn kb-delete-btn" title="${t('kb.delete')}" onclick="deleteFile('${escapeHtml(f.filename)}')">🗑️</button>
                </div>
            </div>
        `).join('');

    } catch (e) {
        listEl.innerHTML = `<div class="kb-empty">${t('kb.loadFail')}</div>`;
    }
}

// 上传 PDF
async function uploadPDF(file) {
    const progressEl = document.getElementById('kb-upload-progress');
    const barEl = document.getElementById('kb-upload-progress-bar');
    const statusEl = document.getElementById('kb-upload-status');

    progressEl.style.display = 'flex';
    barEl.style.width = '30%';
    statusEl.textContent = t('kb.uploading');

    const formData = new FormData();
    formData.append('file', file);

    try {
        barEl.style.width = '60%';
        statusEl.textContent = t('kb.parsing');

        const resp = await fetch('/api/personal/upload', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + getAccessToken() },
            body: formData,
        });

        const data = await resp.json();
        if (!resp.ok) {
            barEl.style.width = '100%';
            barEl.style.background = '#E74C3C';
            statusEl.textContent = data.error || t('kb.uploadFail');
            setTimeout(() => { progressEl.style.display = 'none'; barEl.style.background = ''; }, 3000);
            return;
        }

        barEl.style.width = '100%';
        statusEl.textContent = t('kb.uploadSuccess');
        setTimeout(() => { progressEl.style.display = 'none'; }, 1500);

        loadPersonalFiles();

    } catch (e) {
        barEl.style.width = '100%';
        barEl.style.background = '#E74C3C';
        statusEl.textContent = t('kb.networkError');
        setTimeout(() => { progressEl.style.display = 'none'; barEl.style.background = ''; }, 3000);
    }
}

// 删除文件
async function deleteFile(filename) {
    if (!confirm(t('kb.confirmDelete', filename))) return;

    try {
        const resp = await fetch(`/api/personal/files/${encodeURIComponent(filename)}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + getAccessToken() },
        });
        if (resp.ok) {
            loadPersonalFiles();
        } else {
            const data = await resp.json();
            alert(data.error || t('kb.deleteFail'));
        }
    } catch (e) {
        alert(t('kb.networkError'));
    }
}

// 重命名文件
async function renameFile(filename) {
    const newName = prompt(t('kb.renamePrompt'), filename);
    if (!newName || newName === filename) return;

    try {
        const resp = await fetch(`/api/personal/files/${encodeURIComponent(filename)}/rename`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + getAccessToken(),
            },
            body: JSON.stringify({ new_name: newName }),
        });
        if (resp.ok) {
            loadPersonalFiles();
        } else {
            const data = await resp.json();
            alert(data.error || t('kb.renameFail'));
        }
    } catch (e) {
        alert(t('kb.networkError'));
    }
}

// 开始新对话
function startNewChat() {
    abortCurrentStream();
    chatContainer.innerHTML = '';
    hasStartedConversation = false;
    currentSessionId = null;

    if (welcomeSection) welcomeSection.classList.remove('hidden');
    if (sceneIntro) sceneIntro.classList.remove('hidden');

    setRandomSlogan();

    queryInput.value = '';
    queryInput.style.height = 'auto';
    queryInput.focus();

    isDeepSearch = false;
    usePersonal = false;
    const depthBtn = document.getElementById('depth-btn');
    const personalBtn = document.getElementById('personal-btn');
    if (depthBtn) depthBtn.classList.remove('active');
    if (personalBtn) personalBtn.classList.remove('active');

    // 取消侧边栏高亮
    document.querySelectorAll('.history-item.active').forEach(el => el.classList.remove('active'));
}

// 处理发送
async function handleSend() {
    const query = queryInput.value.trim();
    if (!query || isQuerying) return;

    if (!hasStartedConversation) {
        hideWelcomeAndScene();
        hasStartedConversation = true;
    }

    addMessage('user', query);

    queryInput.value = '';
    queryInput.style.height = 'auto';

    isQuerying = true;
    sendBtn.disabled = true;

    const loadingText = isDeepSearch ? t('search.deepSearching') : t('search.searching');
    const loadingHtml = `<div class="search-progress"><span class="search-spinner"></span>${escapeHtml(loadingText)}</div>`;
    const assistantMsgId = addMessage('assistant', loadingHtml);
    assistantTurnState.set(assistantMsgId, {
        query,
        answerText: '',
        sources: [],
        experimentRunning: false,
        experimentDone: false,
        genesAvailable: false,
        genes: [],  // 检测到的基因名列表（由后端 genes_available 事件填充）
        streamDone: false, // 标记流式传输是否完成，防止后续 updateMessage 覆盖按钮
    });

    try {
        const { answerText, sources } = await streamQuery(query, assistantMsgId);
        const state = getAssistantTurnState(assistantMsgId);
        saveToHistory(query, answerText, sources, state.genes, state.sops);
    } catch (error) {
        if (error.name === 'AbortError') {
            // 用户切换了对话，部分回答已在 abortCurrentStream() 中保存
        } else {
            updateMessage(assistantMsgId, `<p style="color: red;">${t('error.prefix')}: ${error.message}</p>`);
        }
    } finally {
        isQuerying = false;
        sendBtn.disabled = false;
    }
}

// 隐藏欢迎标语和场景介绍
function hideWelcomeAndScene() {
    if (welcomeSection) welcomeSection.classList.add('hidden');
    if (sceneIntro) sceneIntro.classList.add('hidden');
}

// 构建当前 session 的多轮历史（不含当前提问）
// 策略：保留第 1 轮（初始上下文）+ 最近 2 轮（最新讨论），避免 token 过长
function buildHistory() {
    if (!currentSessionId) return [];
    const session = conversationHistory.find(s => s.id === currentSessionId);
    if (!session || !session.messages.length) return [];

    const all = session.messages;
    let selected;
    if (all.length <= 3) {
        // 3 轮以内全部保留
        selected = all;
    } else {
        // 第 1 轮 + 最近 2 轮
        selected = [all[0], ...all.slice(-2)];
    }

    const history = [];
    for (const turn of selected) {
        history.push({ role: 'user', content: turn.query });
        if (turn.answerText) {
            history.push({ role: 'assistant', content: turn.answerText });
        }
    }
    return history;
}

// 流式查询
async function streamQuery(query, messageId) {
    const history = buildHistory();
    const abortController = new AbortController();
    currentAbortController = abortController;
    currentStreamMsgId = messageId;
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getAccessToken(),
        },
        body: JSON.stringify({
            query,
            use_personal: usePersonal,
            use_depth: isDeepSearch,
            history,
        }),
        signal: abortController.signal,
    });

    if (response.status === 401) {
        showLoginOverlay();
        throw new Error(t('auth.expired'));
    }

    if (!response.ok) {
        throw new Error(t('auth.networkFail'));
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let answerText = '';
    let sources = [];
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

        const lines = buffer.split('\n');
        buffer = done ? '' : (lines.pop() || '');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));

                    if (data.type === 'searching') {
                        updateMessage(messageId,
                            `<div class="search-progress"><span class="search-spinner"></span>${escapeHtml(data.data)}</div>`);
                    } else if (data.type === 'sources') {
                        sources = data.data;
                        const state = getAssistantTurnState(messageId);
                        state.sources = sources;
                    } else if (data.type === 'text') {
                        answerText += data.data;
                        const state = getAssistantTurnState(messageId);
                        state.answerText = answerText;
                        updateMessage(messageId, formatAnswer(answerText));
                    } else if (data.type === 'experiment_start') {
                        const state = getAssistantTurnState(messageId);
                        state.experimentRunning = true;
                        updateMessage(messageId, formatAnswer(answerText));
                        removeExperimentButton(messageId);
                        appendExperimentProgress(messageId, data.genes);
                    } else if (data.type === 'progress') {
                        updateExperimentProgress(messageId, data);
                    } else if (data.type === 'result' && data.sops) {
                        const state = getAssistantTurnState(messageId);
                        state.experimentDone = true;
                        state.experimentRunning = false;
                        state.sops = data.sops;
                        const msgEl = document.getElementById(messageId);
                        if (msgEl) {
                            const regions = getMessageRegions(messageId);
                            if (regions.extrasEl) renderSOPs(regions.extrasEl, data.sops);
                        }
                    } else if (data.type === 'genes_available') {
                        // 后端检测到回答中包含具体基因名，携带基因名列表
                        const state = getAssistantTurnState(messageId);
                        state.genesAvailable = true;
                        // 保存基因名列表（如 ["GmFAD2", "AtMYB4"]），供基因编辑器使用
                        if (data.genes && Array.isArray(data.genes)) {
                            state.genes = data.genes;
                        }
                    } else if (data.type === 'done') {
                        const state = getAssistantTurnState(messageId);
                        state.streamDone = true;
                        updateMessage(messageId, formatAnswer(answerText));
                        // 将来源渲染到 extrasEl（不会被 updateMessage 覆盖）
                        const { extrasEl } = getMessageRegions(messageId);
                        if (extrasEl && state.sources && state.sources.length > 0) {
                            const sourcesHtml = renderSources(state.sources);
                            if (sourcesHtml) {
                                const sourcesDiv = document.createElement('div');
                                sourcesDiv.className = 'sources-wrapper';
                                sourcesDiv.innerHTML = sourcesHtml;
                                extrasEl.appendChild(sourcesDiv);
                            }
                        }
                        renderExperimentButton(messageId);
                    } else if (data.type === 'error') {
                        const state = getAssistantTurnState(messageId);
                        state.experimentRunning = false;
                        if (data.msg) {
                            // pipeline error — show in progress area
                            handleExperimentError(messageId, data.msg);
                            renderExperimentButton(messageId);
                        } else {
                            throw new Error(data.data);
                        }
                    }
                } catch (parseErr) {
                    if (parseErr.message && !parseErr.message.startsWith('Unexpected')) {
                        throw parseErr;
                    }
                }
            }
        }

        if (done) {
            if (buffer.trim().startsWith('data: ')) {
                try {
                    const data = JSON.parse(buffer.trim().slice(6));
                    if (data.type === 'done') {
                        const state = getAssistantTurnState(messageId);
                        state.streamDone = true;
                        updateMessage(messageId, formatAnswer(answerText));
                        const { extrasEl } = getMessageRegions(messageId);
                        if (extrasEl && state.sources && state.sources.length > 0) {
                            const sourcesHtml = renderSources(state.sources);
                            if (sourcesHtml) {
                                const sourcesDiv = document.createElement('div');
                                sourcesDiv.className = 'sources-wrapper';
                                sourcesDiv.innerHTML = sourcesHtml;
                                extrasEl.appendChild(sourcesDiv);
                            }
                        }
                        renderExperimentButton(messageId);
                    }
                } catch (parseErr) {
                    if (parseErr.message && !parseErr.message.startsWith('Unexpected')) {
                        throw parseErr;
                    }
                }
            }
            break;
        }
    }

    currentAbortController = null;
    currentStreamMsgId = null;
    return { answerText, sources };
}

async function streamExperiment(messageId) {
    const state = getAssistantTurnState(messageId);
    // 构建请求体：包含用户在基因编辑器中选定的基因名列表
    const requestBody = {
        query: state.query,
        answer_text: state.answerText,
        skill: 'crispr-experiment',
    };
    // 如果有用户编辑过的基因列表，以 genes_selected 传给后端
    // 后端会调用 LLM 为这些基因名解析物种信息
    if (state.genes && state.genes.length > 0) {
        requestBody.genes_selected = state.genes;
    }

    const response = await fetch('/api/experiment/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getAccessToken(),
        },
        body: JSON.stringify(requestBody),
    });

    if (response.status === 401) {
        showLoginOverlay();
        throw new Error(t('auth.expired'));
    }

    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || t('auth.networkFail'));
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

        const lines = buffer.split('\n');
        buffer = done ? '' : (lines.pop() || '');

        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;

            try {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'experiment_start') {
                    state.experimentRunning = true;
                    state.experimentDone = false;
                    removeExperimentButton(messageId);
                    appendExperimentProgress(messageId, data.genes);
                } else if (data.type === 'progress') {
                    updateExperimentProgress(messageId, data);
                } else if (data.type === 'result' && data.sops) {
                    state.experimentDone = true;
                    state.experimentRunning = false;
                    state.sops = data.sops;
                    const regions = getMessageRegions(messageId);
                    if (regions.extrasEl) renderSOPs(regions.extrasEl, data.sops);
                    // 将 SOP 结果更新到已保存的历史记录中
                    updateLastTurnSops(state.sops, state.genes);
                } else if (data.type === 'error') {
                    state.experimentRunning = false;
                    const msg = data.msg || data.data || t('auth.networkFail');
                    handleExperimentError(messageId, msg);
                    renderExperimentButton(messageId);
                }
            } catch (parseErr) {
                if (parseErr.message && !parseErr.message.startsWith('Unexpected')) {
                    throw parseErr;
                }
            }
        }

        if (done) {
            break;
        }
    }
}

// 格式化答案（使用 marked.js 渲染 Markdown）
function formatAnswer(text) {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true,
        });
        return '<div class="markdown-body">' + marked.parse(text) + '</div>';
    }
    // fallback: 无 marked 时用简单段落
    const formatted = text.replace(
        /\[([^\]]+)\s*\|\s*([^\]]+)\]/g,
        '<span class="source-tag">$1 | $2</span>'
    );
    const paragraphs = formatted.split('\n\n').filter(p => p.trim());
    return paragraphs.map(p => `<p>${p}</p>`).join('');
}

// 来源类型标签（动态取翻译）
function getSourceBadge(sourceType) {
    const map = {
        gene_db:  { key: 'source.gene_db',  cls: 'badge-gene' },
        pubmed:   { key: 'source.pubmed',    cls: 'badge-pubmed' },
        jina_web: { key: 'source.jina_web',  cls: 'badge-web' },
        personal: { key: 'source.personal',  cls: 'badge-personal' },
    };
    const entry = map[sourceType];
    if (entry) return { label: t(entry.key), cls: entry.cls };
    return { label: sourceType, cls: '' };
}

// 渲染来源列表
function renderSources(sources) {
    if (!sources || sources.length === 0) return '';

    const items = sources.slice(0, 15).map((s, i) => {
        const badge = getSourceBadge(s.source_type);
        let title = '';
        let detail = '';

        if (s.source_type === 'gene_db') {
            title = s.gene_name || '';
            detail = s.paper_title || '';
        } else if (s.source_type === 'pubmed') {
            title = s.paper_title || s.title || '';
            detail = s.pmid ? `PMID:${s.pmid}` : '';
        } else if (s.source_type === 'jina_web') {
            title = s.title || '';
            detail = s.url ? `<a href="${s.url}" target="_blank" rel="noopener">${s.url}</a>` : '';
        } else if (s.source_type === 'personal') {
            title = s.filename || '';
            detail = s.page ? `p.${s.page}` : '';
        } else {
            title = s.title || s.paper_title || '';
        }

        const scoreStr = (typeof s.score === 'number') ? s.score.toFixed(3) : '';

        return `
            <div class="source-item">
                <span class="source-badge ${badge.cls}">${badge.label}</span>
                <strong>${i + 1}. ${escapeHtml(title)}</strong>
                ${detail ? ` - ${detail}` : ''}
                ${scoreStr ? `<span style="color:#999;margin-left:6px;">(${scoreStr})</span>` : ''}
            </div>
        `;
    }).join('');

    return `
        <div class="sources-section">
            <div class="sources-title">${t('source.title')} (${sources.length}):</div>
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
                <div class="message-content">
                    <div class="assistant-answer">${content}</div>
                    <div class="assistant-extras"></div>
                </div>
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
        const regions = getMessageRegions(messageId);
        if (regions.answerEl) {
            regions.answerEl.innerHTML = content;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
}

function getAssistantTurnState(messageId) {
    if (!assistantTurnState.has(messageId)) {
        assistantTurnState.set(messageId, {
            query: '',
            answerText: '',
            sources: [],
            experimentRunning: false,
            experimentDone: false,
            genesAvailable: false,
            genes: [],
            streamDone: false,
        });
    }
    return assistantTurnState.get(messageId);
}

function getMessageRegions(messageId) {
    const messageEl = document.getElementById(messageId);
    if (!messageEl) return {};

    let answerEl = messageEl.querySelector('.assistant-answer');
    let extrasEl = messageEl.querySelector('.assistant-extras');

    if (!answerEl) {
        const contentEl = messageEl.querySelector('.message-content');
        if (!contentEl) return {};

        const existing = contentEl.innerHTML;
        contentEl.innerHTML = '<div class="assistant-answer"></div><div class="assistant-extras"></div>';
        answerEl = contentEl.querySelector('.assistant-answer');
        extrasEl = contentEl.querySelector('.assistant-extras');
        answerEl.innerHTML = existing;
    }

    return { messageEl, answerEl, extrasEl };
}

function renderExperimentButton(messageId) {
    const state = getAssistantTurnState(messageId);
    if (!state.answerText || !state.genesAvailable || state.experimentRunning || state.experimentDone) return;

    const { answerEl, extrasEl } = getMessageRegions(messageId);
    if (!extrasEl) return;

    // 避免重复渲染
    const existing = extrasEl.querySelector('.experiment-trigger-area');
    if (existing) return;
    const existingBtn = extrasEl.querySelector('.experiment-btn');
    if (existingBtn) return;
    const progressEl = extrasEl.querySelector('.experiment-progress');
    if (progressEl && !progressEl.querySelector('.experiment-step.error')) return;
    if (extrasEl.querySelector('.experiment-sop')) return;

    // ---- 创建基因编辑器 + SOP 按钮的容器 ----
    const container = document.createElement('div');
    container.className = 'experiment-trigger-area';

    // ---- 渲染基因编辑器（可编辑的基因芯片列表） ----
    if (state.genes && state.genes.length > 0) {
        const geneEditor = renderGeneEditor(messageId, state);
        container.appendChild(geneEditor);
    }

    // ---- 创建 SOP 生成按钮 ----
    const btn = document.createElement('button');
    btn.className = 'experiment-btn';
    btn.type = 'button';
    btn.textContent = '🧬 生成 CRISPR 实验方案 SOP';
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        try {
            await streamExperiment(messageId);
        } catch (error) {
            btn.disabled = false;
            handleExperimentError(messageId, error.message);
        }
    });
    container.appendChild(btn);

    // 始终放到 extrasEl（不插入 answerEl，避免被 updateMessage 覆盖）
    extrasEl.appendChild(container);
}

/**
 * 渲染基因编辑器 —— 可编辑的基因芯片（chip）列表
 *
 * 功能：
 * - 展示后端检测到的基因名，每个基因显示为一个可删除的芯片
 * - 用户可以点击 "×" 移除不需要的基因
 * - 用户可以通过 "+" 按钮添加新的基因名
 * - 编辑结果实时同步到 state.genes，点击 SOP 按钮时传给后端
 *
 * @param {string} messageId - 消息 DOM 元素 ID
 * @param {object} state - assistantTurnState 中的状态对象
 * @returns {HTMLElement} 基因编辑器 DOM 元素
 */
function renderGeneEditor(messageId, state) {
    const editor = document.createElement('div');
    editor.className = 'gene-editor';

    // ---- 标题标签 ----
    const label = document.createElement('div');
    label.className = 'gene-editor-label';
    label.textContent = t('gene.detected');
    editor.appendChild(label);

    // ---- 芯片容器（放置所有基因芯片 + 添加按钮） ----
    const chipsContainer = document.createElement('div');
    chipsContainer.className = 'gene-chips-container';

    /**
     * 重新渲染所有基因芯片（在添加/删除操作后调用）
     */
    function rebuildChips() {
        chipsContainer.innerHTML = '';

        // 为每个基因创建一个可删除的芯片
        state.genes.forEach((geneName, index) => {
            const chip = document.createElement('span');
            chip.className = 'gene-chip';

            // 基因名文本
            const nameSpan = document.createElement('span');
            nameSpan.className = 'gene-chip-name';
            nameSpan.textContent = geneName;
            chip.appendChild(nameSpan);

            // "×" 删除按钮
            const removeBtn = document.createElement('button');
            removeBtn.className = 'gene-chip-remove';
            removeBtn.type = 'button';
            removeBtn.textContent = '\u00d7';  // × 符号
            removeBtn.title = t('gene.removeTitle');
            removeBtn.addEventListener('click', () => {
                // 从 state.genes 中移除该基因并重新渲染
                state.genes.splice(index, 1);
                rebuildChips();
            });
            chip.appendChild(removeBtn);

            chipsContainer.appendChild(chip);
        });

        // ---- "+" 添加基因按钮 ----
        const addBtn = document.createElement('button');
        addBtn.className = 'gene-add-btn';
        addBtn.type = 'button';
        addBtn.textContent = t('gene.addBtn');
        addBtn.addEventListener('click', () => {
            // 替换"+"按钮为输入框
            addBtn.style.display = 'none';

            const inputWrapper = document.createElement('span');
            inputWrapper.className = 'gene-add-wrapper';

            const input = document.createElement('input');
            input.className = 'gene-add-input';
            input.type = 'text';
            input.placeholder = t('gene.inputPlaceholder');
            input.maxLength = 30;

            /**
             * 确认添加基因：去重后加入列表
             */
            function confirmAdd() {
                const name = input.value.trim();
                if (name && !state.genes.includes(name)) {
                    state.genes.push(name);
                }
                // 无论是否添加成功，都重新渲染（移除输入框）
                rebuildChips();
            }

            // 按 Enter 确认添加
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    confirmAdd();
                } else if (e.key === 'Escape') {
                    // 按 Escape 取消输入
                    rebuildChips();
                }
            });

            // 失焦时确认添加
            input.addEventListener('blur', confirmAdd);

            inputWrapper.appendChild(input);
            chipsContainer.appendChild(inputWrapper);

            // 自动聚焦输入框
            input.focus();
        });
        chipsContainer.appendChild(addBtn);
    }

    // 首次渲染芯片
    rebuildChips();

    editor.appendChild(chipsContainer);
    return editor;
}

function removeExperimentButton(messageId) {
    // 移除整个实验触发区域（含基因编辑器 + SOP 按钮）— 仅在 extrasEl 中
    const { extrasEl } = getMessageRegions(messageId);
    extrasEl?.querySelector('.experiment-trigger-area')?.remove();
    extrasEl?.querySelector('.experiment-btn')?.remove();
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function trimSopsForStorage(sops, maxCharsPerSop = 12000, maxTotalChars = 30000) {
    if (!sops || Object.keys(sops).length === 0) return null;

    const trimmed = {};
    let totalChars = 0;

    for (const [accession, text] of Object.entries(sops)) {
        if (totalChars >= maxTotalChars) break;

        const rawText = typeof text === 'string' ? text : String(text || '');
        const remaining = Math.max(maxTotalChars - totalChars, 0);
        const limit = Math.min(maxCharsPerSop, remaining);
        if (limit <= 0) break;

        trimmed[accession] = rawText.length > limit
            ? rawText.slice(0, limit) + '\n\n...(历史记录中已截断)'
            : rawText;
        totalChars += trimmed[accession].length;
    }

    return Object.keys(trimmed).length > 0 ? trimmed : null;
}

function buildPersistableHistory(includeSops = true) {
    return conversationHistory.map(session => ({
        ...session,
        messages: (session.messages || []).map(turn => {
            const nextTurn = { ...turn };
            if (includeSops) {
                const trimmedSops = trimSopsForStorage(nextTurn.sops);
                if (trimmedSops) {
                    nextTurn.sops = trimmedSops;
                } else {
                    delete nextTurn.sops;
                }
            } else {
                delete nextTurn.sops;
            }
            return nextTurn;
        }),
    }));
}

function persistConversationHistory() {
    try {
        const sanitized = buildPersistableHistory(true);
        localStorage.setItem('conversation_history', JSON.stringify(sanitized));
        conversationHistory = sanitized;
    } catch (err) {
        console.warn('保存历史失败，改为不持久化 SOP 全文:', err);
        const fallback = buildPersistableHistory(false);
        localStorage.setItem('conversation_history', JSON.stringify(fallback));
        conversationHistory = fallback;
    }
}

// 保存到历史
function saveToHistory(query, answerText, sources, genes, sops) {
    const turn = { query, answerText, sources, timestamp: Date.now() };
    // 保存基因列表和 SOP 结果（用于切换对话后重新渲染，不会发给 LLM）
    if (genes && genes.length > 0) turn.genes = genes;
    if (sops && Object.keys(sops).length > 0) turn.sops = sops;

    if (currentSessionId) {
        // 追问：追加到当前 session
        const session = conversationHistory.find(s => s.id === currentSessionId);
        if (session) {
            session.messages.push(turn);
            session.timestamp = Date.now();
            // 将该 session 移到列表最前面
            const idx = conversationHistory.indexOf(session);
            if (idx > 0) {
                conversationHistory.splice(idx, 1);
                conversationHistory.unshift(session);
            }
        }
    } else {
        // 新对话：创建新 session
        currentSessionId = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        conversationHistory.unshift({
            id: currentSessionId,
            title: query.slice(0, 50),
            messages: [turn],
            timestamp: Date.now(),
        });
    }

    if (conversationHistory.length > 20) {
        conversationHistory = conversationHistory.slice(0, 20);
    }

    persistConversationHistory();
    loadHistory();
}

// 将 SOP 结果更新到当前 session 最后一轮（按钮触发 SOP 生成后调用）
function updateLastTurnSops(sops, genes) {
    if (!currentSessionId) return;
    const session = conversationHistory.find(s => s.id === currentSessionId);
    if (!session || !session.messages.length) return;
    const lastTurn = session.messages[session.messages.length - 1];
    if (sops && Object.keys(sops).length > 0) lastTurn.sops = sops;
    if (genes && genes.length > 0) lastTurn.genes = genes;
    persistConversationHistory();
}

// 加载历史
function loadHistory() {
    const saved = localStorage.getItem('conversation_history');
    if (saved) {
        try {
            conversationHistory = JSON.parse(saved);
        } catch (err) {
            console.warn('历史记录解析失败，已清空本地缓存:', err);
            conversationHistory = [];
            localStorage.removeItem('conversation_history');
        }

        // 兼容旧格式：将单条 {query, answerText} 迁移为 session 格式
        let migrated = false;
        conversationHistory = conversationHistory.map(item => {
            if (item.messages) return item; // 已经是新格式
            if (!item.answerText) return null; // 过滤无效旧数据
            migrated = true;
            return {
                id: `migrated-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
                title: (item.query || '').slice(0, 50),
                messages: [{
                    query: item.query,
                    answerText: item.answerText,
                    sources: item.sources || [],
                    timestamp: item.timestamp || Date.now(),
                }],
                timestamp: item.timestamp || Date.now(),
            };
        }).filter(Boolean);

        if (migrated) {
            persistConversationHistory();
        }

        const hasStoredSops = conversationHistory.some(
            session => (session.messages || []).some(turn => turn.sops && Object.keys(turn.sops).length > 0)
        );
        if (hasStoredSops) {
            persistConversationHistory();
        }
    }

    historyList.innerHTML = '';

    if (conversationHistory.length === 0) {
        historyList.innerHTML = `<div class="history-loading">${t('sidebar.noHistory')}</div>`;
        return;
    }

    conversationHistory.forEach((session) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        if (session.id === currentSessionId) {
            div.classList.add('active');
        }
        const displayTitle = session.title || (session.messages[0]?.query || '');
        div.textContent = displayTitle.slice(0, 30) + (displayTitle.length > 30 ? '...' : '');
        const msgCount = session.messages.length;
        if (msgCount > 1) {
            const badge = document.createElement('span');
            badge.className = 'history-msg-count';
            badge.textContent = msgCount;
            div.appendChild(badge);
        }
        div.onclick = () => { restoreConversation(session); };
        historyList.appendChild(div);
    });
}

// 还原历史会话
function restoreConversation(session) {
    abortCurrentStream();
    hideWelcomeAndScene();
    hasStartedConversation = true;
    currentSessionId = session.id;

    chatContainer.innerHTML = '';

    // 恢复该 session 内的所有多轮对话
    for (const turn of session.messages) {
        addMessage('user', turn.query);
        const answerHtml = turn.answerText
            ? formatAnswer(turn.answerText)
            : `<p style="color: #999;">${t('history.oldRecord')}</p>`;
        const msgId = addMessage('assistant', answerHtml);

        // 恢复来源、基因、SOP 到 extrasEl
        const { extrasEl } = getMessageRegions(msgId);
        if (extrasEl) {
            // 来源
            if (turn.sources && turn.sources.length > 0) {
                const sourcesHtml = renderSources(turn.sources);
                if (sourcesHtml) {
                    const sourcesDiv = document.createElement('div');
                    sourcesDiv.className = 'sources-wrapper';
                    sourcesDiv.innerHTML = sourcesHtml;
                    extrasEl.appendChild(sourcesDiv);
                }
            }
            // SOP 结果
            if (turn.sops && Object.keys(turn.sops).length > 0) {
                renderSOPs(extrasEl, turn.sops);
            }
        }
    }

    // 更新侧边栏高亮
    loadHistory();
}

// 清空历史
function clearHistory() {
    if (confirm(t('confirm.clearHistory'))) {
        conversationHistory = [];
        localStorage.removeItem('conversation_history');
        loadHistory();
    }
}

// ===== CRISPR 实验方案自动生成（内联 pipeline 进度） =====

const STEP_LABELS = [
    '查询 NCBI Accession',
    '下载基因序列',
    '设计 CRISPR 靶点',
    '生成实验方案 SOP',
];

function appendExperimentProgress(messageId, genes) {
    const { extrasEl } = getMessageRegions(messageId);
    if (!extrasEl) return;

    extrasEl.querySelectorAll('.experiment-progress, .experiment-sop').forEach(el => el.remove());

    const genesStr = genes ? genes.join(', ') : '';

    const progressEl = document.createElement('div');
    progressEl.className = 'experiment-progress';
    progressEl.id = `exp-progress-${messageId}`;
    progressEl.innerHTML = `<div class="experiment-progress-title">\uD83D\uDD2C CRISPR 实验方案生成${genesStr ? '（' + escapeHtml(genesStr) + '）' : ''}</div>` +
        STEP_LABELS.map((label, i) =>
            `<div class="experiment-step" id="exp-step-${messageId}-${i+1}">` +
            `<span class="step-icon">${i+1}</span>` +
            `<span class="step-label">${label}</span>` +
            `</div>`
        ).join('');
    extrasEl.appendChild(progressEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function updateExperimentProgress(messageId, data) {
    const step = data.step;
    // 标记之前的步骤为 done
    for (let i = 1; i < step; i++) {
        const el = document.getElementById(`exp-step-${messageId}-${i}`);
        if (el && !el.classList.contains('done')) {
            el.classList.remove('active');
            el.classList.add('done');
            el.querySelector('.step-icon').textContent = '\u2713';
        }
    }
    // 标记当前步骤为 active
    const curEl = document.getElementById(`exp-step-${messageId}-${step}`);
    if (curEl) {
        curEl.classList.add('active');
        curEl.querySelector('.step-label').textContent = data.msg;
    }
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function handleExperimentError(messageId, msg) {
    if (!document.getElementById(`exp-step-${messageId}-1`)) {
        appendExperimentProgress(messageId, []);
    }

    let targetEl = null;
    // 找到最后一个 active 步骤并标记为 error
    for (let i = STEP_LABELS.length; i >= 1; i--) {
        const el = document.getElementById(`exp-step-${messageId}-${i}`);
        if (el && el.classList.contains('active')) {
            targetEl = el;
            break;
        }
    }
    if (!targetEl) {
        targetEl = document.getElementById(`exp-step-${messageId}-1`);
    }
    if (targetEl) {
        targetEl.classList.remove('active', 'done');
        targetEl.classList.add('error');
        targetEl.querySelector('.step-icon').textContent = '\u2717';
        targetEl.querySelector('.step-label').textContent = msg;
    }
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function renderSOPs(container, sops) {
    container.querySelectorAll('.experiment-sop').forEach(el => el.remove());
    // 标记所有进度步骤为 done
    const progressEl = container.closest('.message-content')?.querySelector('.experiment-progress') || container.querySelector('.experiment-progress');
    if (progressEl) {
        progressEl.querySelectorAll('.experiment-step').forEach(el => {
            el.classList.remove('active');
            el.classList.add('done');
            el.querySelector('.step-icon').textContent = '\u2713';
        });
    }

    for (const [accession, text] of Object.entries(sops)) {
        const sopEl = document.createElement('div');
        sopEl.className = 'experiment-sop';

        const headerEl = document.createElement('div');
        headerEl.className = 'experiment-sop-header';
        headerEl.innerHTML =
            `<span class="experiment-sop-title">\uD83D\uDCCB 实验方案: ${escapeHtml(accession)}</span>` +
            `<span class="experiment-sop-toggle">\u25BC</span>`;

        const bodyEl = document.createElement('div');
        bodyEl.className = 'experiment-sop-body';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'experiment-sop-content';
        contentDiv.textContent = text;

        bodyEl.appendChild(contentDiv);
        sopEl.appendChild(headerEl);
        sopEl.appendChild(bodyEl);
        container.appendChild(sopEl);

        // 默认展开第一个
        const isFirst = container.querySelectorAll('.experiment-sop').length === 1;
        if (isFirst) {
            headerEl.classList.add('expanded');
            bodyEl.classList.add('expanded');
        }

        // 折叠/展开事件
        headerEl.addEventListener('click', () => {
            headerEl.classList.toggle('expanded');
            bodyEl.classList.toggle('expanded');
        });
    }
}
