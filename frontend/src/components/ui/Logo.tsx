/** Логотип БурмалдаGPT с надписью. */
import { motion } from "framer-motion";

interface LogoProps {
  size?: number;
  showText?: boolean;
  animated?: boolean;
  className?: string;
}

export function Logo({ size = 32, showText = true, animated = false, className = "" }: LogoProps) {
  const img = (
    <img
      src="/logo.png"
      alt="БурмалдаGPT"
      width={size}
      height={size}
      className="rounded-xl select-none"
      style={{ width: size, height: size, objectFit: "contain" }}
      draggable={false}
    />
  );

  if (!showText) return <div className={className}>{img}</div>;

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {animated ? (
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        >
          {img}
        </motion.div>
      ) : (
        img
      )}
      <div className="leading-none">
        <span className="font-extrabold tracking-tight text-main text-[1.05rem]">Бурмалда</span>
        <span className="font-semibold text-muted text-[1.05rem]">GPT</span>
      </div>
    </div>
  );
}
