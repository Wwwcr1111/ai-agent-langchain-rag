"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"

type Props = {
  task: string
  output: Record<string, any>
  trace?: Record<string, any>
}

const TEXT = {
  task: "\u4efb\u52a1\uff1a",
  tool: "\u5de5\u5177\uff1a",
} as const

export default function AgentResultCard({ task, output, trace }: Props) {
  return (
    <Card className="mt-6 space-y-4">
      <div className="flex items-center justify-between">
        <Badge>{TEXT.task}{task}</Badge>
        {trace?.routed_tool && <Badge>{TEXT.tool}{trace.routed_tool}</Badge>}
      </div>

      <ScrollArea className="max-h-[400px] pr-4">
        <pre className="whitespace-pre-wrap text-sm">{JSON.stringify(output, null, 2)}</pre>
      </ScrollArea>
    </Card>
  )
}
