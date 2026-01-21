import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const severityBadgeVariants = cva(
  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
  {
    variants: {
      severity: {
        critical: "bg-red-500/20 text-red-400 border-red-500/50",
        high: "bg-orange-500/20 text-orange-400 border-orange-500/50",
        medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
        low: "bg-green-500/20 text-green-400 border-green-500/50",
      },
      size: {
        sm: "text-xs px-2 py-0.5",
        md: "text-xs px-2.5 py-1",
        lg: "text-sm px-3 py-1.5",
      }
    },
    defaultVariants: {
      severity: "medium",
      size: "md",
    },
  }
);

interface SeverityBadgeProps extends VariantProps<typeof severityBadgeVariants> {
  className?: string;
  children?: React.ReactNode;
  showDot?: boolean;
}

export function SeverityBadge({ 
  severity, 
  size, 
  className, 
  children,
  showDot = true 
}: SeverityBadgeProps) {
  const dotColor = {
    critical: "bg-red-400",
    high: "bg-orange-400",
    medium: "bg-yellow-400",
    low: "bg-green-400",
  };

  return (
    <span className={cn(severityBadgeVariants({ severity, size }), className)}>
      {showDot && (
        <span className={cn("w-1.5 h-1.5 rounded-full pulse-marker", dotColor[severity || "medium"])} />
      )}
      {children || severity?.charAt(0).toUpperCase() + severity?.slice(1)}
    </span>
  );
}
