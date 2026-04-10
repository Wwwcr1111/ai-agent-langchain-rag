"use client"

import { useRef, useState } from "react"
import { Button } from "@/components/ui/button"

type Props = {
  onUpload: (files: File[]) => void
  disabled?: boolean
  multiple?: boolean
  mode?: "classify" | "ingest"
}

const TEXT = {
  dropHint: "\u5c06\u6587\u4ef6\u62d6\u62fd\u5230\u8fd9\u91cc\uff0c\u6216\u70b9\u51fb\u9009\u62e9\u6587\u4ef6",
  ingestHint: "\u4e0a\u4f20\u540e\u7684\u6587\u4ef6\u5c06\u88ab\u5199\u5165\u77e5\u8bc6\u5e93\u5e76\u53c2\u4e0e\u95ee\u7b54",
  classifyHint: "\u4e0a\u4f20\u540e\u4f1a\u5148\u63d0\u53d6\u6587\u672c\uff0c\u4ee5\u4fbf\u7ee7\u7eed\u6267\u884c\u5206\u7c7b\u4e0e\u5206\u6790",
  browse: "\u9009\u62e9\u6587\u4ef6",
} as const

export default function FileUploader({ onUpload, disabled, multiple = true, mode = "classify" }: Props) {
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files || [])
    if (files.length > 0) onUpload(files)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length > 0) onUpload(files)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition ${
        dragOver
          ? "border-blue-500 bg-blue-100 dark:border-blue-400 dark:bg-blue-900"
          : "border-gray-300 bg-white dark:border-gray-600 dark:bg-gray-800"
      }`}
      onClick={() => fileInputRef.current?.click()}
    >
      <p className="mb-1 text-sm text-gray-500 dark:text-gray-300">{TEXT.dropHint}</p>
      <p className="mb-3 text-xs text-gray-400 dark:text-gray-500">
        {mode === "ingest" ? TEXT.ingestHint : TEXT.classifyHint}
      </p>
      <Button type="button" disabled={disabled} variant="secondary">
        {TEXT.browse}
      </Button>
      <input
        type="file"
        accept=".txt,.pdf,.docx"
        multiple={multiple}
        hidden
        ref={fileInputRef}
        onChange={handleFileSelect}
      />
    </div>
  )
}
