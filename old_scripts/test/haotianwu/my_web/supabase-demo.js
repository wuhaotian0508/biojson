// ══════════════════════════════════════════════
//  Step 1: 连接 Supabase
//  createClient(URL, KEY) → 返回一个 supabase 客户端对象
// ══════════════════════════════════════════════
const SUPABASE_URL = 'https://vqcfjnwyxvayygxtaons.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxY2Zqbnd5eHZheXlneHRhb25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MDE0ODQsImV4cCI6MjA4OTM3NzQ4NH0.0oErR07B644NmWX2ck48po9LQNVXgpxlQkXT8Y1aquI';

// window.supabase 是从 CDN 加载进来的库，createClient 创建连接
// 注意：变量名不能叫 supabase，因为 CDN 库已经占用了 window.supabase
const db = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);


// ══════════════════════════════════════════════
//  Step 2: 查询数据
//  async function → 这个函数是异步的（会等待网络请求完成）
// ══════════════════════════════════════════════
async function fetchPapers() {
    // 显示加载状态
    document.getElementById('status').textContent = '⏳ 正在查询...';
    document.getElementById('result').innerHTML = '';

    // ── 核心查询 ──────────────────────────────
    // await → 等待 Supabase 返回结果，期间页面不会卡住
    // .from('papers')   → 选择 papers 表
    // .select(...)      → 选择要读取的列
    // 返回 { data, error } 两个值
    const { data, error } = await db
        .from('papers')
        .select('slug, title, status, gene_count, created_at');

    // ── 错误处理 ──────────────────────────────
    if (error) {
        document.getElementById('status').textContent = '❌ 查询失败';
        document.getElementById('result').innerHTML = `
            <div class="error-box">
                <strong>错误信息：</strong> ${error.message}
            </div>
        `;
        console.error('Supabase 错误：', error);
        return;  // 出错就停在这里，不往下执行
    }

    // ── 成功：渲染数据 ─────────────────────────
    document.getElementById('status').textContent = `✅ 查询成功，共找到 ${data.length} 篇论文`;
    renderPapers(data);

    // 同时在控制台打印原始数据，方便学习查看
    console.log('原始返回数据（JSON）：', data);
}


// ══════════════════════════════════════════════
//  Step 3: 把数据渲染到页面
//  papers → 是一个数组，每个元素是一篇论文的对象
// ══════════════════════════════════════════════
function renderPapers(papers) {
    const container = document.getElementById('result');

    // 如果没有数据
    if (papers.length === 0) {
        container.innerHTML = '<p>数据库里还没有论文数据。</p>';
        return;
    }

    // 用 map() 把每篇论文变成一张 HTML 卡片，再用 join('') 拼成字符串
    container.innerHTML = papers.map(paper => `
        <div class="paper-card">
            <h3>
                ${paper.title || '（无标题）'}
                <span class="badge badge-${paper.status}">${paper.status}</span>
            </h3>
            <div class="slug">
                slug: ${paper.slug}
                &nbsp;|&nbsp;
                基因数: ${paper.gene_count ?? 0}
                &nbsp;|&nbsp;
                创建时间: ${new Date(paper.created_at).toLocaleDateString('zh-CN')}
            </div>
        </div>
    `).join('');
}
