import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[100px] w-full rounded-2xl border border-gray-300 px-3 py-2 text-sm shadow-sm",
          "focus:outline-none focus:ring-2 focus:ring-accent",
          "bg-white text-black placeholder-gray-500",
          "dark:bg-gray-800 dark:text-white dark:placeholder-gray-400",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Textarea.displayName = "Textarea"
export { Textarea }
