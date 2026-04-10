import { Card } from "@/components/ui/card"

const TITLE = "\u64cd\u4f5c\u53cd\u9988"

export default function PipelineStatus({ pipelineStatus }: { pipelineStatus: any }) {
  return (
    <div className="space-y-2">
      <h2 className="text-xl font-semibold">{TITLE}</h2>
      <Card>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-md border border-gray-300 bg-gray-100 p-4 text-sm text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white">
          {typeof pipelineStatus === "string"
            ? pipelineStatus
            : JSON.stringify(pipelineStatus, null, 2)}
        </pre>
      </Card>
    </div>
  )
}
