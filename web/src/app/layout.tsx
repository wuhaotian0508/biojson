import type { Metadata } from "next";
import "./globals.css";
import { UserProvider } from "@/lib/UserContext";
import Header from "@/components/Header";

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
        <UserProvider>
          <Header />
          <main>{children}</main>
        </UserProvider>
      </body>
    </html>
  );
}
