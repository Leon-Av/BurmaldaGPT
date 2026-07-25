/** Одно сообщение в чате (user/assistant) с markdown и копированием. */
import { motion } from "framer-motion";
import { Check, Copy, User as UserIcon } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { imageUrl } from "@/api/chats";
import { Logo } from "@/components/ui/Logo";
import type { Message as MessageType } from "@/types";

interface MessageProps {
  message: MessageType;
  chatId: string;
  streaming?: boolean; // это сообщение сейчас стримится
  isLastAssistant?: boolean;
}

export function Message({ message, chatId, streaming, isLastAssistant }: MessageProps) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className={`group flex gap-3 md:gap-4 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Аватар */}
      <div className="shrink-0">
        {isUser ? (
          <div className="h-8 w-8 md:h-9 md:w-9 rounded-xl bg-brand-100 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300 flex items-center justify-center">
            <UserIcon size={16} />
          </div>
        ) : (
          <div className="h-8 w-8 md:h-9 md:w-9 rounded-xl overflow-hidden bg-soft border border-app flex items-center justify-center">
            <Logo size={26} showText={false} />
          </div>
        )}
      </div>

      {/* Содержимое */}
      <div className={`flex-1 min-w-0 ${isUser ? "flex flex-col items-end" : ""}`}>
        <div
          className={`inline-block max-w-full ${
            isUser
              ? "bg-brand-600 text-white rounded-2xl rounded-tr-md px-4 py-2.5"
              : "bg-elevated border border-app rounded-2xl rounded-tl-md px-4 py-3"
          }`}
        >
          {/* Изображения */}
          {message.images && message.images.length > 0 && (
            <div className={`flex flex-wrap gap-2 ${message.content ? "mb-2" : ""}`}>
              {message.images
                .slice()
                .sort((a, b) => a.order_index - b.order_index)
                .map((img) =>
                  img.id.startsWith("pending-") ? (
                    img.id
                  ) : (
                    <a
                      key={img.id}
                      href={imageUrl(chatId, message.id, img.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="block"
                    >
                      <img
                        src={imageUrl(chatId, message.id, img.id)}
                        alt="Прикреплённое"
                        className="h-28 w-28 object-cover rounded-lg border border-black/10"
                        loading="lazy"
                      />
                    </a>
                  )
                )
                .filter(Boolean)}
            </div>
          )}

          {message.content ? (
            isUser ? (
              <div className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
                {message.content}
              </div>
            ) : (
              <div className={`markdown ${streaming ? "stream-caret" : ""}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )
          ) : streaming ? (
            <div className="flex items-center gap-1.5 py-1">
              <span className="inline-flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="h-2 w-2 rounded-full bg-brand-400 animate-pulse-soft"
                    style={{ animationDelay: `${i * 0.18}s` }}
                  />
                ))}
              </span>
            </div>
          ) : null}
        </div>

        {/* Кнопка копирования (только assistant, не при стриминге) */}
        {!isUser && message.content && !streaming && isLastAssistant && (
          <div className="mt-1.5 flex items-center">
            <button
              onClick={copy}
              className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1.5 text-xs text-faint hover:text-main px-2 py-1 rounded-md hover:bg-soft"
              title="Копировать ответ"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              {copied ? "Скопировано" : "Копировать"}
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
