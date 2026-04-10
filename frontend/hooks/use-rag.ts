"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { API_BASE_URL } from "@/lib/api"
import type { AgentResponse, KbDocument, QueryResultItem } from "@/lib/app-types"

const TEXT = {
  genericError: "发生了一些问题",
  queryFailed: "智能问答请求失败",
  uploadFailed: "上传失败",
  agentError: "智能体执行失败",
  kbDeleteFailed: "删除文档失败",
  kbRebuildFailed: "重建索引失败",
  kbListFailed: "获取知识库文档失败",
  kbRebuildSuccess: "知识库索引重建完成",
  kbDeleteSuccess: "文档已从知识库删除：",
  ingestSuccess: "已成功导入：",
} as const

function ensureThreadId() {
  const saved = localStorage.getItem("rag_thread_id")
  if (saved) return saved
  const created = crypto.randomUUID()
  localStorage.setItem("rag_thread_id", created)
  return created
}

async function parseErrorMessage(response: Response, fallback: string) {
  try {
    const data = await response.json()
    return data?.detail || fallback
  } catch {
    return fallback
  }
}

export function useChatQuery() {
  const threadIdRef = useRef<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<QueryResultItem[]>([])

  useEffect(() => {
    threadIdRef.current = ensureThreadId()
  }, [])

  const askQuestion = useCallback(async (question: string) => {
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion) return null

    setLoading(true)
    setError(null)

    try {
      const threadId = threadIdRef.current ?? ensureThreadId()
      const response = await fetch(
        `${API_BASE_URL}/api/query?question=${encodeURIComponent(trimmedQuestion)}&namespace=default&thread_id=${threadId}`
      )

      if (!response.ok) {
        throw new Error(await parseErrorMessage(response, TEXT.queryFailed))
      }

      const data = await response.json()
      const answers = Array.isArray(data.results) ? data.results : []
      const sources = Array.isArray(data.sources) ? data.sources : []
      setResults(
        answers.map((answer: string) => ({
          answer,
          sources,
        }))
      )
      return answers.map((answer: string) => ({
        answer,
        sources,
      })) as QueryResultItem[]
    } catch (err) {
      setError(err instanceof Error ? err.message : TEXT.queryFailed)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    error,
    results,
    askQuestion,
  }
}

export function useKnowledgeBase() {
  const [documents, setDocuments] = useState<KbDocument[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null)

  const fetchDocuments = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/kb/documents`)
      if (!response.ok) {
        throw new Error(await parseErrorMessage(response, TEXT.kbListFailed))
      }

      const data = await response.json()
      setDocuments(Array.isArray(data.documents) ? data.documents : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : TEXT.kbListFailed)
    } finally {
      setLoading(false)
    }
  }, [])

  const uploadDocuments = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return

      setLoading(true)
      setError(null)
      setPipelineStatus(null)

      try {
        for (const file of files) {
          const formData = new FormData()
          formData.append("files", file)

          const response = await fetch(`${API_BASE_URL}/api/ingest`, {
            method: "POST",
            body: formData,
          })

          if (!response.ok) {
            throw new Error(await parseErrorMessage(response, TEXT.uploadFailed))
          }

          await response.json()
          setPipelineStatus(`${TEXT.ingestSuccess}${file.name}`)
        }

        await fetchDocuments()
      } catch (err) {
        setError(err instanceof Error ? err.message : TEXT.uploadFailed)
      } finally {
        setLoading(false)
      }
    },
    [fetchDocuments]
  )

  const rebuildKnowledgeBase = useCallback(async () => {
    setLoading(true)
    setError(null)
    setPipelineStatus(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/kb/rebuild`, { method: "POST" })
      if (!response.ok) {
        throw new Error(await parseErrorMessage(response, TEXT.kbRebuildFailed))
      }

      const data = await response.json()
      setPipelineStatus(JSON.stringify({ message: TEXT.kbRebuildSuccess, ...data }, null, 2))
      await fetchDocuments()
    } catch (err) {
      setError(err instanceof Error ? err.message : TEXT.kbRebuildFailed)
    } finally {
      setLoading(false)
    }
  }, [fetchDocuments])

  const deleteDocument = useCallback(
    async (doc: KbDocument) => {
      setLoading(true)
      setError(null)
      setPipelineStatus(null)

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/kb/documents/${encodeURIComponent(doc.filename)}?doc_path=${encodeURIComponent(doc.doc_path)}`,
          { method: "DELETE" }
        )

        if (!response.ok) {
          throw new Error(await parseErrorMessage(response, TEXT.kbDeleteFailed))
        }

        const data = await response.json()
        setPipelineStatus(JSON.stringify({ message: `${TEXT.kbDeleteSuccess}${doc.filename}`, ...data }, null, 2))
        await fetchDocuments()
      } catch (err) {
        setError(err instanceof Error ? err.message : TEXT.kbDeleteFailed)
      } finally {
        setLoading(false)
      }
    },
    [fetchDocuments]
  )

  return {
    documents,
    loading,
    error,
    pipelineStatus,
    fetchDocuments,
    uploadDocuments,
    rebuildKnowledgeBase,
    deleteDocument,
  }
}

export function useClassifyAgent({
  onAppendText,
}: {
  onAppendText: (value: string) => void
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AgentResponse | null>(null)

  const uploadFiles = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return

      setLoading(true)
      setError(null)
      setResult(null)

      try {
        for (const file of files) {
          const formData = new FormData()
          formData.append("files", file)

          const response = await fetch(`${API_BASE_URL}/upload-docs`, {
            method: "POST",
            body: formData,
          })

          if (!response.ok) {
            throw new Error(await parseErrorMessage(response, `${TEXT.uploadFailed}.`))
          }

          const data = await response.json()
          const extractedText = data.uploaded?.[0]?.extracted_text || ""
          if (extractedText) {
            onAppendText(`--- ${file.name} ---\n\n${extractedText}`)
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : TEXT.uploadFailed)
      } finally {
        setLoading(false)
      }
    },
    [onAppendText]
  )

  const runAgent = useCallback(async (text: string) => {
    const trimmedText = text.trim()
    if (!trimmedText) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/run-agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmedText }),
      })

      if (!response.ok) {
        throw new Error(await parseErrorMessage(response, TEXT.agentError))
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : TEXT.genericError)
    } finally {
      setLoading(false)
    }
  }, [])

  const clearResult = useCallback(() => {
    setResult(null)
    setError(null)
  }, [])

  const exportResult = useCallback(() => {
    if (!result) return

    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement("a")
    anchor.href = url
    anchor.download = `agent-output-${result.task}.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }, [result])

  return {
    loading,
    error,
    result,
    uploadFiles,
    runAgent,
    clearResult,
    exportResult,
  }
}
