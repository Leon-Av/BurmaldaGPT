/** Поле ввода сообщения с поддержкой изображений и авто-ростом. */
import { AnimatePresence, motion } from "framer-motion";
import { ArrowUp, ImageIcon, Loader2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useCapabilities } from "@/hooks/useCapabilities";

interface MessageInputProps {
  onSubmit: (content: string, images?: File[]) => void;
  streaming: boolean;
  autoFocus?: boolean;
}

const ACCEPTED = "image/png,image/jpeg,image/webp,image/gif";

export function MessageInput({ onSubmit, streaming, autoFocus }: MessageInputProps) {
  const caps = useCapabilities(true);
  const [text, setText] = useState("");
  const [images, setImages] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus) taRef.current?.focus();
  }, [autoFocus]);

  // Авто-рост textarea
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
  }, [text]);

  // Очистка object-URL
  useEffect(() => {
    return () => previews.forEach((u) => URL.revokeObjectURL(u));
  }, [previews]);

  const canSend = (text.trim() || images.length > 0) && !streaming;
  const visionOk = caps.vision_enabled;
  const maxImgs = caps.max_images_per_message;

  const submit = () => {
    if (!canSend) return;
    onSubmit(text.trim(), images.length ? images : undefined);
    setText("");
    setImages([]);
    previews.forEach((u) => URL.revokeObjectURL(u));
    setPreviews([]);
    // Сброс высоты
    requestAnimationFrame(() => {
      if (taRef.current) taRef.current.style.height = "auto";
    });
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onFiles = (files: FileList | null) => {
    if (!files || !visionOk) return;
    const next = [...images];
    const nextPreviews = [...previews];
    for (const f of Array.from(files)) {
      if (!f.type.startsWith("image/")) continue;
      if (next.length >= maxImgs) break;
      next.push(f);
      nextPreviews.push(URL.createObjectURL(f));
    }
    setImages(next);
    setPreviews(nextPreviews);
    if (fileRef.current) fileRef.current.value = "";
  };

  const removeImage = (idx: number) => {
    URL.revokeObjectURL(previews[idx]);
    setImages(images.filter((_, i) => i !== idx));
    setPreviews(previews.filter((_, i) => i !== idx));
  };

  const onPaste = (e: React.ClipboardEvent) => {
    if (!visionOk) return;
    const files = Array.from(e.clipboardData.files).filter((f) => f.type.startsWith("image/"));
    if (files.length) {
      e.preventDefault();
      const dt = new DataTransfer();
      files.forEach((f) => dt.items.add(f));
      onFiles(dt.files);
    }
  };

  return (
    <div className="w-full">
      {/* Превью изображений */}
      <AnimatePresence>
        {previews.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap gap-2 mb-2"
          >
            {previews.map((src, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="relative group"
              >
                <img
                  src={src}
                  alt={`Прикреплённое ${i + 1}`}
                  className="h-16 w-16 object-cover rounded-lg border border-app"
                />
                <button
                  onClick={() => removeImage(i)}
                  className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-red-500 text-white flex items-center justify-center shadow-soft opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="Удалить изображение"
                >
                  <X size={12} />
                </button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative flex items-end gap-2 bg-elevated border border-app rounded-2xl shadow-float px-2 py-1.5 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-500/15 transition-all">
        {/* Кнопка вложений */}
        {visionOk && (
          <button
            onClick={() => fileRef.current?.click()}
            disabled={streaming}
            className="h-9 w-9 shrink-0 rounded-xl text-muted hover:text-main hover:bg-soft flex items-center justify-center transition-colors disabled:opacity-40"
            title={`Прикрепить изображение (до ${maxImgs})`}
          >
            <ImageIcon size={20} />
          </button>
        )}
        <input
          ref={fileRef}
          type="file"
          accept={ACCEPTED}
          multiple
          className="hidden"
          onChange={(e) => onFiles(e.target.files)}
        />

        <textarea
          ref={taRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          onPaste={onPaste}
          rows={1}
          placeholder="Напишите сообщение…"
          className="flex-1 resize-none bg-transparent border-0 outline-none text-main placeholder:text-faint py-2 text-[15px] leading-relaxed max-h-[200px]"
        />

        <button
          onClick={submit}
          disabled={!canSend}
          className="h-9 w-9 shrink-0 rounded-xl bg-brand-600 hover:bg-brand-700 text-white flex items-center justify-center transition-all active:scale-95 disabled:bg-soft disabled:text-faint disabled:pointer-events-none"
          title={streaming ? "Дождитесь ответа…" : "Отправить (Enter)"}
        >
          {streaming ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={18} />}
        </button>
      </div>
      <p className="text-center text-xs text-faint mt-2">
        Enter — отправить · Shift+Enter — новая строка
      </p>
    </div>
  );
}
