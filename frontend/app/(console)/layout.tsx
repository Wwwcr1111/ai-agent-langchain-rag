import Sidebar from "@/components/Sidebar"

export default function ConsoleLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-gray-100 text-gray-900 dark:bg-gray-950 dark:text-white">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col p-6 sm:p-8">{children}</div>
      </main>
    </div>
  )
}
