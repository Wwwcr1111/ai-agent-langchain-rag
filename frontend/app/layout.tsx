import "@/app/globals.css"
import { ThemeProvider } from "@/components/ThemeProvider"

export const metadata = {
  title: "\u6587\u6863\u667a\u80fd\u4f53",
  description: "\u7528\u4e8e\u6587\u6863\u5206\u7c7b\u3001\u5bfc\u5165\u4e0e\u77e5\u8bc6\u5e93\u95ee\u7b54\u7684\u4e2d\u6587\u754c\u9762",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
