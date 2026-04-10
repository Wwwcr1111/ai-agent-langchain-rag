"use client"

import { useEffect, useRef, useState } from "react"
import ErrorBanner from "@/components/ErrorBanner"
import LoadingSpinner from "@/components/LoadingSpinner"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useChatQuery } from "@/hooks/use-rag"

type ChatMessage = {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: string[]
  isMock?: boolean
}

type QuickPrompt = {
  label: string
  userMessage: string
  reply: string
}

const QUICK_PROMPTS: QuickPrompt[] = [
  {
    label: "选购指南",
    userMessage: "我想了解扫地机器人的选购指南",
    reply:
      "选购扫地机器人时，建议重点关注清洁能力、续航时间、避障能力、建图能力以及是否支持扫拖一体。如果您有宠物、地毯或大户型等特殊需求，也可以告诉我，我可以进一步为您推荐合适的产品方向。",
  },
  {
    label: "新品速递",
    userMessage: "想看看最近有什么新品",
    reply:
      "目前我们已上线多款新型号扫地机器人，部分产品升级了激光导航、自动集尘、拖布自清洁等功能。如果您更关注清洁能力、智能程度或性价比，我可以继续为您介绍适合的新品方向。",
  },
  {
    label: "维护保养",
    userMessage: "扫地机器人平时要怎么维护保养？",
    reply:
      "建议您定期清理尘盒、滚刷、边刷和滤网，并检查传感器和万向轮是否有灰尘堆积。如果设备支持拖地功能，也建议及时清洗水箱和拖布，以保持清洁效果和设备使用寿命。",
  },
  {
    label: "常见故障",
    userMessage: "扫地机器人常见故障有哪些？",
    reply:
      "常见问题包括无法回充、吸力变弱、地图异常、滚刷卡住、设备离线等。您可以先检查电量、网络连接、滚刷是否缠绕异物，以及传感器是否被遮挡。如果您愿意，也可以直接告诉我具体现象，我帮您一步步排查。",
  },
  {
    label: "售后政策",
    userMessage: "你们的售后政策是怎样的？",
    reply:
      "不同产品的售后政策会略有差异，一般包括质保期内的维修支持、配件更换说明以及退换货规则。您可以提供具体型号或购买渠道，我可以进一步帮您查询更准确的售后信息。",
  },
  {
    label: "联系客服",
    userMessage: "我想联系人工客服",
    reply:
      "如果您需要进一步帮助，可以通过官方客服热线、在线客服入口或售后服务渠道联系我们。若您告诉我您的问题类型，我也可以先帮您快速判断是否可以在线解决。",
  },
]

const INITIAL_MESSAGE: ChatMessage = {
  id: "welcome-message",
  role: "assistant",
  content: "您好，我是智能客服助手，请问有什么可以帮您？",
}

const TEXT = {
  title: "智能客服",
  subtitle: "面向产品的智能问答助手",
  clear: "清空对话",
  welcomeTitle: "智能客服助手",
  welcomeCopy: "您好，我可以帮助您解答选购、保养、故障排查和售后问题。",
  placeholder: "请输入您的问题",
  send: "发送",
  sending: "发送中...",
  sourceToggle: "参考依据",
  sourceEmpty: "当前回复暂未返回来源，后续接入知识库引用后会展示在这里。",
  sourceMock: "当前回复来自前端预置演示问答内容。",
} as const

function buildMessage(role: ChatMessage["role"], content: string, extra?: Partial<ChatMessage>): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    ...extra,
  }
}

function SourceDisclosure({ message }: { message: ChatMessage }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="text-xs text-gray-500 transition hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        {TEXT.sourceToggle}
      </button>
      {open && (
        <div className="mt-2 rounded-2xl border border-gray-200 bg-white/80 px-3 py-2 text-xs leading-6 text-gray-500 dark:border-gray-700 dark:bg-gray-900/80 dark:text-gray-300">
          {message.sources && message.sources.length > 0 ? (
            <ul className="space-y-1">
              {message.sources.map((source) => (
                <li key={source}>{source}</li>
              ))}
            </ul>
          ) : (
            <p>{message.isMock ? TEXT.sourceMock : TEXT.sourceEmpty}</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE])
  const { loading, error, askQuestion } = useChatQuery()
  const viewportRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!viewportRef.current) return
    viewportRef.current.scrollTop = viewportRef.current.scrollHeight
  }, [messages, loading])

  const appendMockConversation = (prompt: QuickPrompt) => {
    setMessages((current) => [
      ...current,
      buildMessage("user", prompt.userMessage, { isMock: true }),
      buildMessage("assistant", prompt.reply, { isMock: true, sources: [] }),
    ])
  }

  const handleSend = async () => {
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || loading) return

    const userMessage = buildMessage("user", trimmedQuestion)
    setMessages((current) => [...current, userMessage])
    setQuestion("")

    const response = await askQuestion(trimmedQuestion)
    if (!response) return

    const firstReply = response[0]
    setMessages((current) => [
      ...current,
      buildMessage("assistant", firstReply?.answer || "暂时没有获取到回复。", {
        sources: firstReply?.sources || [],
      }),
    ])
  }

  const clearConversation = () => {
    setQuestion("")
    setMessages([INITIAL_MESSAGE])
  }

  return (
    <section className="flex h-[calc(100vh-4rem)] flex-1 flex-col">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{TEXT.title}</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">{TEXT.subtitle}</p>
        </div>
        <Button variant="secondary" onClick={clearConversation}>
          {TEXT.clear}
        </Button>
      </div>

      {error && <div className="mb-4"><ErrorBanner message={error} /></div>}

      <div className="flex min-h-0 flex-1 flex-col rounded-[28px] border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <div ref={viewportRef} className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
          <div className="rounded-3xl border border-gray-200 bg-gray-50 px-5 py-4 dark:border-gray-800 dark:bg-gray-950">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{TEXT.welcomeTitle}</h2>
            <p className="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{TEXT.welcomeCopy}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt.label}
                  type="button"
                  onClick={() => appendMockConversation(prompt)}
                  className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-gray-700 transition hover:border-gray-300 hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200 dark:hover:border-gray-600 dark:hover:bg-gray-800"
                >
                  {prompt.label}
                </button>
              ))}
            </div>
          </div>

          {messages.map((message) => (
            <div
              key={message.id}
              className={cn("flex", message.role === "user" ? "justify-end" : "justify-start")}
            >
              <div
                className={cn(
                  "max-w-[85%] rounded-3xl px-4 py-3 text-sm leading-7 shadow-sm sm:max-w-[75%]",
                  message.role === "user"
                    ? "bg-gray-900 text-white dark:bg-white dark:text-gray-900"
                    : "border border-gray-200 bg-gray-50 text-gray-800 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
                )}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.role === "assistant" && <SourceDisclosure message={message} />}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-3xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600 shadow-sm dark:border-gray-700 dark:bg-gray-950 dark:text-gray-200">
                <span className="flex items-center gap-2">
                  <LoadingSpinner />
                  {TEXT.sending}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center gap-3 rounded-3xl bg-gray-50 p-3 dark:bg-gray-950">
            <input
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.nativeEvent.isComposing) {
                  event.preventDefault()
                  void handleSend()
                }
              }}
              placeholder={TEXT.placeholder}
              className="flex-1 bg-transparent px-2 text-sm text-gray-900 outline-none placeholder:text-gray-400 dark:text-white"
            />
            <Button disabled={loading || !question.trim()} onClick={() => void handleSend()}>
              {TEXT.send}
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
