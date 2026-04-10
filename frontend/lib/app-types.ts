export type AgentResponse = {
  task: string
  output: Record<string, any>
  agent_trace?: Record<string, any>
}

export type KbDocument = {
  filename: string
  doc_path: string
  source_type: string
  file_type?: string
  chunk_count: number
  missing: boolean
  created_at?: string
}

export type QueryResultItem = {
  answer: string
  sources: string[]
}
