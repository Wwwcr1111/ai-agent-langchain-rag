"use client"

import { useEffect } from "react"
import ErrorBanner from "@/components/ErrorBanner"
import FileUploader from "@/components/FileUploader"
import LoadingSpinner from "@/components/LoadingSpinner"
import PipelineStatus from "@/components/PipelineStatus"
import { Button } from "@/components/ui/button"
import { useKnowledgeBase } from "@/hooks/use-rag"
import type { KbDocument } from "@/lib/app-types"

const TEXT = {
  title: "知识库管理",
  subtitle: "上传、查看和维护知识文档",
  tableTitle: "文档列表",
  filename: "文档名称",
  fileType: "文件类型",
  chunkCount: "分块数量",
  status: "状态",
  createdAt: "创建时间",
  actions: "操作",
  missing: "源文件缺失",
  normal: "正常",
  empty: "暂无文档",
  emptyHint: "请先上传文件以构建知识库",
  refresh: "刷新列表",
  rebuild: "重建索引",
  rebuilding: "重建中...",
  delete: "删除",
  fallback: "--",
} as const

function formatCreatedAt(doc: KbDocument) {
  if (!doc.created_at) return TEXT.fallback
  const date = new Date(doc.created_at)
  if (Number.isNaN(date.getTime())) return doc.created_at
  return date.toLocaleString("zh-CN", { hour12: false })
}

export default function KnowledgePage() {
  const {
    documents,
    loading,
    error,
    pipelineStatus,
    fetchDocuments,
    uploadDocuments,
    rebuildKnowledgeBase,
    deleteDocument,
  } = useKnowledgeBase()

  useEffect(() => {
    void fetchDocuments()
  }, [fetchDocuments])

  return (
    <section className="flex flex-1 flex-col gap-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{TEXT.title}</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">{TEXT.subtitle}</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" disabled={loading} onClick={() => fetchDocuments()}>
            {TEXT.refresh}
          </Button>
          <Button variant="outline" disabled={loading} onClick={() => rebuildKnowledgeBase()}>
            {loading ? (
              <span className="flex items-center gap-2">
                <LoadingSpinner />
                {TEXT.rebuilding}
              </span>
            ) : (
              TEXT.rebuild
            )}
          </Button>
        </div>
      </div>

      <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <FileUploader disabled={loading} multiple={true} mode="ingest" onUpload={uploadDocuments} />
      </div>

      {error && <ErrorBanner message={error} />}
      {pipelineStatus && <PipelineStatus pipelineStatus={pipelineStatus} />}

      <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{TEXT.tableTitle}</h2>
          <span className="text-sm text-gray-500 dark:text-gray-400">{documents.length} 条</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full border-separate border-spacing-0 text-sm">
            <thead>
              <tr className="text-left text-gray-500 dark:text-gray-400">
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.filename}</th>
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.fileType}</th>
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.chunkCount}</th>
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.status}</th>
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.createdAt}</th>
                <th className="border-b border-gray-200 px-4 py-3 font-medium dark:border-gray-800">{TEXT.actions}</th>
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
                    <p>{TEXT.empty}</p>
                    <p className="mt-2 text-xs">{TEXT.emptyHint}</p>
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={`${doc.filename}-${doc.doc_path}`} className="align-top">
                    <td className="border-b border-gray-100 px-4 py-4 dark:border-gray-900">
                      <div className="font-medium text-gray-900 dark:text-white">{doc.filename}</div>
                      <div className="mt-1 text-xs text-gray-400">{doc.doc_path}</div>
                    </td>
                    <td className="border-b border-gray-100 px-4 py-4 dark:border-gray-900">
                      {doc.file_type || doc.source_type || TEXT.fallback}
                    </td>
                    <td className="border-b border-gray-100 px-4 py-4 dark:border-gray-900">{doc.chunk_count}</td>
                    <td className="border-b border-gray-100 px-4 py-4 dark:border-gray-900">
                      {doc.missing ? (
                        <span className="rounded-full bg-red-100 px-3 py-1 text-xs text-red-700 dark:bg-red-950 dark:text-red-300">
                          {TEXT.missing}
                        </span>
                      ) : (
                        <span className="rounded-full bg-green-100 px-3 py-1 text-xs text-green-700 dark:bg-green-950 dark:text-green-300">
                          {TEXT.normal}
                        </span>
                      )}
                    </td>
                    <td className="border-b border-gray-100 px-4 py-4 text-gray-500 dark:border-gray-900 dark:text-gray-400">
                      {formatCreatedAt(doc)}
                    </td>
                    <td className="border-b border-gray-100 px-4 py-4 dark:border-gray-900">
                      <Button variant="destructive" size="sm" disabled={loading} onClick={() => deleteDocument(doc)}>
                        {TEXT.delete}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}
