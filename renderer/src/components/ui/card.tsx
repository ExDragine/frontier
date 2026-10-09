import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const cardVariants = cva(
  "group/card flex min-w-0 flex-col gap-[22px] rounded-2xl border border-card-accent-border text-card-foreground shadow-xs py-[28px] max-[600px]:py-[22px]",
  {
    variants: {
      surface: {
        outline:
          "bg-card [&:not([data-tone=neutral])]:border-t-[3px] [&:not([data-tone=neutral])]:border-t-card-accent",
        muted: "bg-card-accent-surface shadow-none",
        ghost:
          "rounded-none border-0 bg-transparent py-0 shadow-none max-[600px]:py-0",
      },
      tone: {
        neutral: "md-color-neutral",
        blue: "md-color-blue",
        emerald: "md-color-emerald",
        violet: "md-color-violet",
        amber: "md-color-amber",
        rose: "md-color-rose",
        cyan: "md-color-cyan",
      },
    },
    defaultVariants: { surface: "outline", tone: "neutral" },
  },
);

const inset =
  "px-[28px] max-[600px]:px-[22px] group-data-[surface=ghost]/card:px-0";

const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof cardVariants>
>(({ className, surface = "outline", tone = "neutral", ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card"
    data-surface={surface}
    data-tone={tone}
    className={cn(cardVariants({ surface, tone }), className)}
    {...props}
  />
));
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-header"
    className={cn("flex flex-col gap-2.5", inset, className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-title"
    className={cn(
      "font-semibold leading-snug tracking-tight text-card-accent",
      className,
    )}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-description"
    className={cn("text-[20px] text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-content"
    className={cn(inset, className)}
    {...props}
  />
));
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    data-slot="card-footer"
    className={cn(
      "flex items-center border-t border-card-accent-border pt-[18px] text-[18px] text-muted-foreground",
      inset,
      className,
    )}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
};
