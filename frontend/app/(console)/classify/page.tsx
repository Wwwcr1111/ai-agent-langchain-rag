"use client"

import { useState } from "react"
import AgentResultCard from "@/components/AgentResultCard"
import ErrorBanner from "@/components/ErrorBanner"
import FileUploader from "@/components/FileUploader"
import LoadingSpinner from "@/components/LoadingSpinner"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useClassifyAgent } from "@/hooks/use-rag"

const TEXT = {
  title: "问题分类",
  subtitle: "保留原有分类与智能体执行能力，当前仅隐藏导航入口。",
  inputLabel: "待分析文本",
  placeholder: "请粘贴需要分析的文档内容...",
  runAgent: "运行智能体",
  running: "处理中...",
  clearResult: "清空结果",
  exportJson: "导出 JSON",
} as const

export default function ClassifyPage() {
  const [text, setText] = useState("")
  const { loading, error, result, uploadFiles, runAgent, clearResult, exportResult } = useClassifyAgent({
    onAppendText: (value) => {
      setText((previous) => `${previous}${previous ? "\n\n" : ""}${value}`)
    },
  })

  return (
    <section className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">{TEXT.title}</h1>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">{TEXT.subtitle}</p>
      </div>

      <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <FileUploader disabled={loading} multiple={true} mode="classify" onUpload={uploadFiles} />
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-200">{TEXT.inputLabel}</label>
        <Textarea placeholder={TEXT.placeholder} value={text} onChange={(event) => setText(event.target.value)} />

        <div className="mt-4 flex flex-wrap gap-3">
          <Button disabled={loading || !text.trim()} onClick={() => runAgent(text)}>
            {loading ? (
              <span className="flex items-center gap-2">
                <LoadingSpinner />
                {TEXT.running}
              </span>
            ) : (
              TEXT.runAgent
            )}
          </Button>

          {result && (
            <>
              <Button variant="secondary" onClick={clearResult}>
                {TEXT.clearResult}
              </Button>
              <Button variant="secondary" onClick={exportResult}>
                {TEXT.exportJson}
              </Button>
            </>
          )}
        </div>
      </div>

      {result && <AgentResultCard task={result.task} output={result.output} trace={result.agent_trace} />}
    </section>
  )
}
