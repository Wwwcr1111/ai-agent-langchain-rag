"use client"

type Props = {
  message: string
}

export default function ErrorBanner({ message }: Props) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
      {message}
    </div>
  )
}
