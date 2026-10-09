import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit max-w-full items-center self-start rounded-md border px-2.5 py-[3px] text-[17px] font-semibold leading-normal",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-muted text-foreground",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80",
        outline: "text-foreground",
      },
      tone: {
        neutral: "",
        success: "bg-success-surface text-success",
        warning: "bg-warning-surface text-warning",
        danger: "bg-danger-surface text-danger",
      },
    },
    compoundVariants: [
      {
        variant: "outline",
        tone: "success",
        className: "border-success/30 bg-transparent",
      },
      {
        variant: "outline",
        tone: "warning",
        className: "border-warning/30 bg-transparent",
      },
      {
        variant: "outline",
        tone: "danger",
        className: "border-danger/30 bg-transparent",
      },
      {
        variant: "default",
        tone: "success",
        className: "bg-success text-primary-foreground",
      },
      {
        variant: "default",
        tone: "warning",
        className: "bg-warning text-primary-foreground",
      },
      {
        variant: "default",
        tone: "danger",
        className: "bg-danger text-primary-foreground",
      },
    ],
    defaultVariants: {
      variant: "default",
      tone: "neutral",
    },
  },
);

export interface BadgeProps
  extends
    React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, tone, ...props }: BadgeProps) {
  return (
    <div
      data-slot="badge"
      className={cn(badgeVariants({ variant, tone }), className)}
      {...props}
    />
  );
}

export { Badge, badgeVariants };
