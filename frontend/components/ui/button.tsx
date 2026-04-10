import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
  variant?: "default" | "outline" | "secondary" | "destructive"
  size?: "sm" | "default" | "lg"
}

const variants = {
  default: "bg-black text-white hover:bg-gray-800",
  outline: "border border-gray-300 text-black bg-white hover:bg-gray-100",
  secondary: "bg-gray-100 text-gray-900 hover:bg-gray-200",
  destructive: "bg-red-600 text-white hover:bg-red-700",
}

const sizes = {
  sm: "px-3 py-1.5 text-sm",
  default: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-base",
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, asChild = false, variant = "default", size = "default", ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(
          "inline-flex items-center justify-center rounded-2xl font-medium shadow-sm transition-colors focus:outline-none disabled:opacity-50 disabled:pointer-events-none",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
