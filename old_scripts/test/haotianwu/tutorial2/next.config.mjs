/** @type {import('next').NextConfig} */
const nextConfig = {
  // 允许从环境变量读取 Supabase 配置
  env: {
    SUPABASE_URL: process.env.SUPABASE_URL,
    SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY,
  },
}

export default nextConfig
