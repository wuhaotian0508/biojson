/**
 * supabase-client.js
 *
 * 这个文件负责创建 Supabase 连接
 *
 * 关键概念：
 * 1. Supabase 是一个云端数据库服务
 * 2. 需要用 URL 和 API Key 来连接
 * 3. 连接后可以执行 CRUD 操作（创建、读取、更新、删除）
 */

// ===== 第一步：获取配置 =====
// 从环境变量或配置文件读取 Supabase 的连接信息
// 注意：在真实项目中，这些应该从 .env 文件读取，不要硬编码！

async function loadConfig() {
    try {
        // 尝试从本地配置文件读取
        const response = await fetch('./config.json')
        if (response.ok) {
            return await response.json()
        }
    } catch (e) {
        console.log('配置文件不存在，使用环境变量')
    }

    // 回退到环境变量
    return {
        supabaseUrl: localStorage.getItem('SUPABASE_URL') || '',
        supabaseKey: localStorage.getItem('SUPABASE_KEY') || ''
    }
}

// ===== 第二步：创建客户端 =====
let supabase = null
let config = null

async function initSupabase() {
    if (supabase) return supabase

    config = await loadConfig()

    if (!config.supabaseUrl || !config.supabaseKey) {
        showMessage('❌ 缺少 Supabase 配置！请在 config.json 中设置 SUPABASE_URL 和 SUPABASE_KEY', 'error')
        return null
    }

    // 使用 Supabase 官方客户端库
    // 这个函数来自 CDN：https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2
    supabase = window.supabase.createClient(config.supabaseUrl, config.supabaseKey)

    console.log('✅ Supabase 客户端已初始化')
    return supabase
}

// ===== 第三步：定义数据库操作函数 =====

/**
 * 读取所有论文
 * 对应 SQL: SELECT * FROM papers ORDER BY created_at DESC
 */
async function fetchPapers() {
    const client = await initSupabase()
    if (!client) return []

    // Supabase 查询语法：链式调用
    const { data, error } = await client
        .from('papers')           // 从 papers 表
        .select('*')              // 选择所有字段
        .order('created_at', { ascending: false })  // 按创建时间倒序

    if (error) {
        console.error('读取论文失败:', error)
        showMessage('❌ 读取数据失败: ' + error.message, 'error')
        return []
    }

    return data
}

/**
 * 读取单个论文的详细信息（包括基因）
 * 对应 SQL: SELECT * FROM genes WHERE paper_id = ?
 */
async function fetchPaperDetails(paperId) {
    const client = await initSupabase()
    if (!client) return null

    // 同时读取论文和基因数据
    const [paperResult, genesResult] = await Promise.all([
        client.from('papers').select('*').eq('id', paperId).single(),
        client.from('genes').select('*').eq('paper_id', paperId)
    ])

    if (paperResult.error) {
        console.error('读取论文详情失败:', paperResult.error)
        return null
    }

    return {
        paper: paperResult.data,
        genes: genesResult.data || []
    }
}

/**
 * 获取某篇论文的所有标注数据
 * 对应 SQL: SELECT * FROM field_annotations WHERE gene_id IN (...)
 */
async function fetchAnnotations(geneIds) {
    const client = await initSupabase()
    if (!client) return []

    if (!geneIds || geneIds.length === 0) return []

    const { data, error } = await client
        .from('field_annotations')
        .select('*')
        .in('gene_id', geneIds)

    if (error) {
        console.error('读取标注失败:', error)
        return []
    }

    return data || []
}

/**
 * 保存标注到数据库
 * 对应 SQL: INSERT OR UPDATE INTO field_annotations ...
 */
async function saveAnnotation(annotationData) {
    const client = await initSupabase()
    if (!client) return false

    const { error } = await client
        .from('field_annotations')
        .upsert(annotationData)

    if (error) {
        console.error('保存标注失败:', error)
        showMessage('❌ 保存失败: ' + error.message, 'error')
        return false
    }

    return true
}

// ===== 导出函数供 app.js 使用 =====
// 将函数挂载到 window 对象上，这样其他文件也能访问
window.supabaseClient = {
    init: initSupabase,
    fetchPapers,
    fetchPaperDetails,
    fetchAnnotations,  // 新增：获取标注数据
    saveAnnotation
}
