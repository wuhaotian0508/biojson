import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BioJSON — 基因提取标注平台",
  description: "植物营养代谢基因文献结构化提取与专家标注平台",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen">
        {/* 顶部导航栏 */}
        <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 font-bold text-lg no-underline">
              <span>🧬</span>
              <span>BioJSON</span>
            </a>
            <nav className="flex items-center gap-4 text-sm text-[var(--muted-foreground)]">
              <a href="/" className="hover:text-[var(--foreground)] no-underline">论文列表</a>
            </nav>
          </div>
        </header>

        {/* 页面内容 */}
        <main>{children}</main>
      </body>
    </html>
  );
}
