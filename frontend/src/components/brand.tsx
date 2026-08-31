import { cn } from "@/lib/utils";

export function Logo({ className, showText = true }: { className?: string; showText?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="relative grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm">
        <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round">
          <path d="M12 3v18M5 8l7-5 7 5M4 12h16M6 16h12" />
        </svg>
        <span className="absolute -bottom-1 left-1/2 h-1 w-6 -translate-x-1/2 rounded-full gov-stripe" />
      </div>
      {showText ? (
        <div className="leading-tight">
          <div className="font-display text-[15px] font-bold tracking-tight">
            Kaush<span className="text-accent">AI</span>
          </div>
          <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            PM-AJAY · SIH26097
          </div>
        </div>
      ) : null}
    </div>
  );
}
