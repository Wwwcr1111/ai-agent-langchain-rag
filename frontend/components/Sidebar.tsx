"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/chat", label: "智能客服", description: "面向产品的智能问答助手" },
  { href: "/knowledge", label: "知识库管理", description: "上传、查看和维护产品知识文档" },
] as const

const HIDDEN_ROUTE_META = {
  "/classify": {
    label: "智能分类",
    description: "面向产品内容的自动分类与整理能力",
  },
} as const

const TEXT = {
  title: "智能客服助手",
  brand: "Demo Console",
  currentMode: "当前模式",
  modeHint: "模式说明",
  navigation: "功能导航",
  switchLight: "切换到浅色模式",
  switchDark: "切换到深色模式",
  switchTheme: "切换主题",
} as const

export default function Sidebar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const currentItem =
    NAV_ITEMS.find((item) => pathname === item.href) ??
    HIDDEN_ROUTE_META[pathname as keyof typeof HIDDEN_ROUTE_META] ??
    NAV_ITEMS[0]

  return (
    <aside className="sticky top-0 flex h-screen w-72 shrink-0 flex-col border-r border-gray-200/80 bg-white/92 px-5 py-5 backdrop-blur-xl dark:border-gray-800/80 dark:bg-gray-950/92">
      <div className="rounded-[28px] border border-gray-200/80 bg-gradient-to-b from-white to-gray-50 px-4 py-4 shadow-[0_10px_30px_rgba(15,23,42,0.06)] dark:border-gray-800 dark:from-gray-950 dark:to-gray-900">
        <div className="inline-flex items-center rounded-full border border-gray-200 bg-white/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-gray-500 dark:border-gray-700 dark:bg-gray-900/80 dark:text-gray-400">
          {TEXT.brand}
        </div>
        <div className="mt-4 space-y-1">
          <h1 className="text-[21px] font-semibold leading-tight tracking-tight text-gray-950 dark:text-white">{TEXT.title}</h1>
          <p className="text-sm leading-6 text-gray-500 dark:text-gray-400">产品问答与知识管理</p>
        </div>
      </div>

      <div className="mt-5 rounded-[28px] border border-gray-200/80 bg-gray-50/90 p-4 shadow-[0_8px_24px_rgba(15,23,42,0.04)] dark:border-gray-800 dark:bg-gray-900/70">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400">{TEXT.currentMode}</p>
        <p className="mt-3 text-lg font-semibold text-gray-900 dark:text-white">{currentItem.label}</p>
        <div className="mt-4 border-t border-gray-200/80 pt-3 dark:border-gray-800">
          <p className="text-[11px] font-medium tracking-[0.16em] text-gray-400 dark:text-gray-500">{TEXT.modeHint}</p>
          <p className="mt-1.5 text-sm leading-6 text-gray-600 dark:text-gray-300">{currentItem.description}</p>
        </div>
      </div>

      <nav className="mt-6 flex-1">
        <p className="mb-3 px-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-gray-500 dark:text-gray-400">{TEXT.navigation}</p>
        <div className="space-y-2">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group block rounded-2xl border px-4 py-3 transition-all duration-200",
                  active
                    ? "border-gray-900 bg-gray-900 text-white shadow-[0_8px_20px_rgba(17,24,39,0.18)] dark:border-white dark:bg-white dark:text-gray-900"
                    : "border-transparent bg-transparent text-gray-600 hover:border-gray-200 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:border-gray-800 dark:hover:bg-gray-900/80 dark:hover:text-white"
                )}
              >
                <span className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium">{item.label}</span>
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full transition",
                      active
                        ? "bg-white/90 dark:bg-gray-900"
                        : "bg-gray-300 group-hover:bg-gray-500 dark:bg-gray-700 dark:group-hover:bg-gray-400"
                    )}
                  />
                </span>
              </Link>
            )
          })}
        </div>
      </nav>

      <div className="border-t border-gray-200/80 pt-4 dark:border-gray-800">
        <Button
          variant="secondary"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-full justify-start rounded-2xl border border-gray-200/80 bg-gray-50 px-4 py-3 text-gray-700 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          {mounted ? (theme === "dark" ? TEXT.switchLight : TEXT.switchDark) : TEXT.switchTheme}
        </Button>
      </div>
    </aside>
  )
}
