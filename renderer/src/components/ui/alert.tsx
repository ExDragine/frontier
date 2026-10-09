import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const alertVariants = cva(
  "relative w-full rounded-xl border border-border px-6 py-[22px] text-[20px] leading-relaxed max-[600px]:p-[18px] [&:has(>svg)]:grid [&:has(>svg)]:grid-cols-[24px_minmax(0,1fr)] [&:has(>svg)]:gap-3.5 [&>svg]:mt-[3px] [&>svg]:size-6",
  {
    variants: {
      variant: {
        default: "bg-background text-foreground",
        destructive:
          "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
        neutral: "bg-secondary text-foreground",
        muted: "border-dashed bg-secondary text-muted-foreground",
        success: "border-success/20 bg-success-surface text-success",
        warning: "border-warning/20 bg-warning-surface text-warning",
        danger: "border-danger/20 bg-danger-surface text-danger",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="alert"
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
));
Alert.displayName = "Alert";

const AlertTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    data-slot="alert-title"
    className={cn(
      "m-0 text-[22px] font-semibold leading-snug tracking-tight text-inherit",
      className,
    )}
    {...props}
  />
));
AlertTitle.displayName = "AlertTitle";

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="alert-description"
    className={cn(
      "text-[20px] whitespace-pre-wrap [&_p]:leading-relaxed",
      className,
    )}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertTitle, AlertDescription };
