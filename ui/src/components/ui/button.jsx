import { forwardRef } from "react"

import { cn } from "@/lib/utils"

const VARIANT_CLASSES = {
  primary: "bg-accent text-white hover:bg-accent-ink",
  outline:
    "border border-border-strong bg-surface text-ink hover:bg-surface-hover hover:border-border-strong",
  ghost: "text-ink-muted hover:text-ink hover:bg-surface-hover",
  destructive: "bg-bad text-white hover:bg-bad/90",
}

const SIZE_CLASSES = {
  xs: "h-6 px-2 text-[11.5px] gap-1",
  sm: "h-7 px-2.5 text-[12.5px] gap-1.5",
  md: "h-8 px-3 text-[13px] gap-1.5",
  lg: "h-9 px-3.5 text-[13.5px] gap-2",
  "icon-xs": "h-6 w-6 justify-center text-[11.5px]",
  "icon-sm": "h-7 w-7 justify-center text-[13px]",
  "icon-lg": "h-9 w-9 justify-center text-[13.5px]",
}

const Button = forwardRef(function Button(
  { className, variant = "primary", size = "md", ...props },
  ref
) {
  return (
    <button
      ref={ref}
      data-slot="button"
      className={cn(
        "inline-flex shrink-0 items-center rounded-sm font-semibold whitespace-nowrap transition-all duration-150 outline-none active:translate-y-px disabled:pointer-events-none disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-accent/50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className
      )}
      {...props}
    />
  )
})

export { Button }
