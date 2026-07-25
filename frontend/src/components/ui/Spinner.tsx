/** Спиннер загрузки. */
import { Loader2 } from "lucide-react";

interface SpinnerProps {
  size?: number;
  className?: string;
}

export function Spinner({ size = 18, className = "" }: SpinnerProps) {
  return (
    <Loader2
      size={size}
      className={`animate-spin text-brand-500 ${className}`}
      aria-label="Загрузка"
    />
  );
}
