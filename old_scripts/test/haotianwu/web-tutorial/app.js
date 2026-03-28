/**
 * app.js - 主应用逻辑
 *
 * 这个文件包含页面的所有交互逻辑
 *
 * Web 运作原理：
 * 1. 页面加载完成后，JavaScript 开始运行
 * 2. JavaScript 连接到 Supabase 获取数据
 * 3. JavaScript 将数据渲染到页面上
 * 4. 用户点击时，JavaScript 更新数据并重新渲染
 */

// ===== 全局变量：存储应用状态 =====
let state = {
    papers: [],      // 论文列表
    currentPaper: null,  // 当前查看的论文
    currentAnnotations: [],  // 当前论文的标注数据
    currentUser: null    // 当前登录用户
}

// ===== 页面加载完成时执行 =====
// DOMContentLoaded 是浏览器事件，表示 HTML 结构已经加载完成
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 页面加载完成，开始初始化应用...')

    // 1. 检查本地存储中是否有登录用户
    const savedUser = localStorage.getItem('biojson_username')
    if (savedUser) {
        state.currentUser = savedUser
        updateLoginUI()
    }

    // 2. 从 Supabase 加载论文列表
    await loadPapers()

    // 3. 显示欢迎消息
    showMessage('✅ 数据加载完成！', 'success')
})

// ===== 数据加载：从 Supabase 获取论文 =====
async function loadPapers() {
    const loadingEl = document.getElementById('loading')
    const listEl = document.getElementById('papersList')
    const emptyEl = document.getElementById('emptyState')

    // 显示加载中状态
    loadingEl.style.display = 'block'
    listEl.innerHTML = ''
    emptyEl.style.display = 'none'

    // 调用 supabase-client.js 中定义的函数
    state.papers = await window.supabaseClient.fetchPapers()

    // 隐藏加载中
    loadingEl.style.display = 'none'

    // 根据数据显示相应的内容
    if (state.papers.length === 0) {
        emptyEl.style.display = 'block'
    } else {
        renderPapersList()
    }
}

// ===== 渲染：将数据显示到页面上 =====
function renderPapersList() {
    const listEl = document.getElementById('papersList')

    // 遍历每篇论文，创建 HTML 元素
    listEl.innerHTML = state.papers.map(paper => `
        <div class="paper-card" onclick="openPaperDetail('${paper.id}')">
            <div class="paper-title">${paper.title || paper.slug}</div>
            <div class="paper-meta">
                ${paper.journal || '未知期刊'}
                ${paper.doi ? ` · DOI: ${paper.doi}` : ''}
            </div>
            <div class="paper-stats">
                <span class="stat-badge">🧬 ${paper.gene_count || 0} 个基因</span>
                <span class="stat-badge">📋 ${paper.status || 'pending'}</span>
            </div>
        </div>
    `).join('')

    console.log(`✅ 已渲染 ${state.papers.length} 篇论文`)
}

// ===== 交互：点击论文卡片，打开详情 =====
async function openPaperDetail(paperId) {
    console.log('📖 打开论文详情:', paperId)

    const panel = document.getElementById('detailPanel')
    const content = document.getElementById('detailContent')

    // 显示面板
    panel.classList.add('show')
    content.innerHTML = '<p>⏳ 加载中...</p>'

    // 从 Supabase 获取详情
    const details = await window.supabaseClient.fetchPaperDetails(paperId)

    if (!details) {
        content.innerHTML = '<p>❌ 加载失败</p>'
        return
    }

    state.currentPaper = details

    // 🔥 新增：获取该论文的所有标注数据
    const geneIds = details.genes.map(g => g.id)
    const annotations = await window.supabaseClient.fetchAnnotations(geneIds)
    state.currentAnnotations = annotations

    console.log(`📝 加载了 ${annotations.length} 条标注`)

    // 渲染详情
    renderPaperDetail(details)
}

// ===== 渲染：论文详情页面 =====
function renderPaperDetail({ paper, genes }) {
    const content = document.getElementById('detailContent')

    content.innerHTML = `
        <h3>${paper.title || paper.slug}</h3>
        <p style="color: #666; margin-bottom: 20px;">
            ${paper.journal || '未知期刊'}
            ${paper.doi ? `<br>DOI: ${paper.doi}` : ''}
        </p>

        <div class="annotation-section">
            <h4>📝 标注（${genes.length} 个基因）</h4>
            ${genes.length === 0 ? '<p>暂无基因数据</p>' : ''}
        </div>

        ${genes.map(gene => renderGeneCard(gene)).join('')}
    `
}

// ===== 渲染：单个基因卡片 =====
function renderGeneCard(gene) {
    // gene_data 是一个 JSON 对象，包含各种字段
    const geneData = gene.gene_data || {}
    const geneName = geneData.Gene_Name || geneData.gene_name || `Gene ${gene.gene_index}`

    // 🔥 新增：查找该用户对该基因的已有标注
    const userAnnotations = state.currentAnnotations.filter(a =>
        a.gene_id === gene.id &&
        (!state.currentUser || a.annotator_name === state.currentUser)
    )

    // 创建一个快速查找表：field_name -> verdict
    const annotationMap = {}
    userAnnotations.forEach(a => {
        annotationMap[a.field_name] = a.verdict
    })

    // 生成字段列表
    const fieldsHtml = Object.entries(geneData).map(([key, value]) => {
        if (key === 'Gene_Name' || key === 'gene_name') return ''
        const displayValue = Array.isArray(value) ? value.join(', ') : (value || 'NA')

        // 🔥 新增：获取该字段的已有标注
        const existingVerdict = annotationMap[key] || ''

        return `
            <div class="annotation-row">
                <div class="annotation-label">${key}</div>
                <div class="annotation-value">${displayValue}</div>
                <select class="annotation-select ${existingVerdict}"
                        onchange="handleAnnotationChange('${gene.id}', '${key}', this.value)">
                    <option value="" ${existingVerdict === '' ? 'selected' : ''}>未评分</option>
                    <option value="good" ${existingVerdict === 'good' ? 'selected' : ''}>✅ 好</option>
                    <option value="medium" ${existingVerdict === 'medium' ? 'selected' : ''}>❓ 中</option>
                    <option value="poor" ${existingVerdict === 'poor' ? 'selected' : ''}>❌ 差</option>
                </select>
            </div>
        `
    }).join('')

    return `
        <div class="annotation-section" style="border: 1px solid #eee; padding: 12px; border-radius: 6px;">
            <h5 style="margin-bottom: 12px;">🧬 ${geneName}</h5>
            ${userAnnotations.length > 0 ? `<p style="font-size:12px;color:#666;">已有 ${userAnnotations.length} 条标注</p>` : ''}
            ${fieldsHtml}
        </div>
    `
}

// ===== 交互：处理标注变更 =====
async function handleAnnotationChange(geneId, fieldName, verdict) {
    if (!state.currentUser) {
        showMessage('❌ 请先登录再标注', 'error')
        return
    }

    if (!verdict) return  // 未评分则跳过

    // 更新下拉框颜色
    const select = event.target
    select.className = `annotation-select ${verdict}`

    // 保存到 Supabase
    const success = await window.supabaseClient.saveAnnotation({
        gene_id: geneId,
        field_name: fieldName,
        verdict: verdict,
        comment: null,
        annotator_name: state.currentUser
    })

    if (success) {
        // 🔥 新增：更新本地状态，这样即使切换页面再回来，标注也不会丢失
        // 先移除旧的标注（如果有）
        state.currentAnnotations = state.currentAnnotations.filter(a =>
            !(a.gene_id === geneId && a.field_name === fieldName && a.annotator_name === state.currentUser)
        )
        // 添加新标注
        state.currentAnnotations.push({
            gene_id: geneId,
            field_name: fieldName,
            verdict: verdict,
            annotator_name: state.currentUser
        })

        showMessage('✅ 标注已保存', 'success')
    }
}

// ===== 关闭详情面板 =====
function closeDetail() {
    document.getElementById('detailPanel').classList.remove('show')
    state.currentPaper = null
    state.currentAnnotations = []  // 清空标注数据
}

// ===== 用户登录/退出 =====
function login() {
    const input = document.getElementById('usernameInput')
    const username = input.value.trim()

    if (!username) {
        showMessage('❌ 请输入用户名', 'error')
        return
    }

    state.currentUser = username
    localStorage.setItem('biojson_username', username)
    updateLoginUI()
    showMessage(`✅ 欢迎你，${username}！`, 'success')
}

function logout() {
    state.currentUser = null
    localStorage.removeItem('biojson_username')
    updateLoginUI()
    showMessage('👋 已退出登录', 'success')
}

function updateLoginUI() {
    const loginSection = document.getElementById('loginSection')
    const userInfo = document.getElementById('userInfo')
    const currentUserSpan = document.getElementById('currentUser')

    if (state.currentUser) {
        loginSection.style.display = 'none'
        userInfo.style.display = 'flex'
        userInfo.style.gap = '12px'
        userInfo.style.alignItems = 'center'
        currentUserSpan.textContent = state.currentUser
    } else {
        loginSection.style.display = 'block'
        userInfo.style.display = 'none'
    }
}

// ===== 工具函数：显示消息 =====
function showMessage(text, type = 'success') {
    const msgEl = document.getElementById('message')
    msgEl.textContent = text
    msgEl.className = `message ${type}`

    // 3秒后自动隐藏
    setTimeout(() => {
        msgEl.className = 'message'
    }, 3000)
}

// ===== 页面关闭时清理 =====
window.addEventListener('beforeunload', () => {
    console.log('👋 页面即将关闭')
})
