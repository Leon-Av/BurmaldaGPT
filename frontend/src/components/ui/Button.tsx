/** Переиспользуемая кнопка. */
import { forwardRef } from "react";

type Variant = "primary" | "ghost" | "outline" | "danger";
type Size = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-brand-600 hover:bg-brand-700 text-white shadow-soft disabled:bg-brand-400",
  ghost: "text-muted hover:text-main hover:bg-soft",
  outline:
    "border border-app bg-elevated hover:bg-soft text-main",
  danger:
    "bg-red-600 hover:bg-red-700 text-white shadow-soft",
};

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-sm rounded-lg gap-1.5",
  md: "h-10 px-4 text-sm rounded-xl gap-2",
  lg: "h-12 px-6 text-base rounded-xl gap-2",
  icon: "h-9 w-9 rounded-lg justify-center",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "outline", size = "md", className = "", children, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center font-medium transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/40 ${variants[variant]} ${sizes[size]} ${className}`}
        {...rest}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
