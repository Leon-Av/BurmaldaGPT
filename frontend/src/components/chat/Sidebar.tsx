/** Боковая панель: новый чат, список чатов, профиль/настройки. */
import { AnimatePresence, motion } from "framer-motion";
import {
  Check,
  LogOut,
  MessageSquarePlus,
  MoreHorizontal,
  Pencil,
  Settings,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { useAuthStore } from "@/store/auth";
import { useChatsStore } from "@/store/chats";

import { Logo } from "@/components/ui/Logo";
import type { Chat } from "@/types";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
}

export function Sidebar({ open, onClose, onOpenSettings }: SidebarProps) {
  const { chats, activeChatId, createChat, selectChat, renameChat, removeChat } = useChatsStore();
  const { user, logout } = useAuthStore();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const editInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingId) editInputRef.current?.focus();
  }, [editingId]);

  const handleNewChat = async () => {
    await createChat();
    onClose();
  };

  const handleSelect = async (id: string) => {
    await selectChat(id);
    onClose();
  };

  const startEdit = (chat: Chat) => {
    setEditingId(chat.id);
    setEditValue(chat.title);
  };

  const commitEdit = async () => {
    if (!editingId) return;
    const title = editValue.trim();
    if (title) await renameChat(editingId, title);
    setEditingId(null);
  };

  const handleDelete = async (id: string) => {
    await removeChat(id);
    setConfirmDeleteId(null);
  };

  return (
    <>
      {/* Затемнение для мобильных */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 bg-black/40 z-30 md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
        )}
      </AnimatePresence>

      <aside
        className={`fixed md:static top-0 left-0 z-40 h-full w-[280px] bg-soft border-r border-app flex flex-col transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Шапка с лого */}
        <div className="h-16 px-4 flex items-center justify-between shrink-0">
          <Logo size={30} />
          <button
            onClick={onClose}
            className="md:hidden text-muted hover:text-main p-1.5 rounded-lg hover:bg-elevated transition-colors"
            aria-label="Закрыть панель"
          >
            <X size={18} />
          </button>
        </div>

        {/* Новый чат */}
        <div className="px-3 pb-2">
          <button
            onClick={handleNewChat}
            className="w-full h-11 rounded-xl border border-app bg-elevated hover:bg-app text-main font-medium text-sm flex items-center gap-2.5 px-3.5 transition-all active:scale-[0.98] shadow-soft"
          >
            <MessageSquarePlus size={18} className="text-brand-500" />
            Новый чат
          </button>
        </div>

        {/* Список чатов */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          <div className="text-xs font-semibold text-faint uppercase tracking-wider px-2 pb-2">
            История
          </div>
          {chats.length === 0 ? (
            <div className="px-2 py-8 text-center text-sm text-faint">
              Нет чатов
            </div>
          ) : (
            <div className="space-y-0.5">
              <AnimatePresence initial={false}>
                {chats.map((chat) => (
                  <motion.div
                    key={chat.id}
                    layout
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -8, height: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <ChatRow
                      chat={chat}
                      active={chat.id === activeChatId}
                      editing={editingId === chat.id}
                      editValue={editValue}
                      editInputRef={editInputRef}
                      onSelect={() => handleSelect(chat.id)}
                      onEdit={() => startEdit(chat)}
                      onEditChange={setEditValue}
                      onCommit={commitEdit}
                      onCancel={() => setEditingId(null)}
                      onDelete={() => setConfirmDeleteId(chat.id)}
                      confirmingDelete={confirmDeleteId === chat.id}
                      onConfirmDelete={() => handleDelete(chat.id)}
                      onAbortDelete={() => setConfirmDeleteId(null)}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Профиль / настройки */}
        <div className="p-2 border-t border-app shrink-0">
          <div className="flex items-center gap-3 p-2 rounded-xl">
            <div className="h-9 w-9 rounded-full bg-brand-500 text-white flex items-center justify-center font-semibold text-sm shrink-0">
              {(user?.display_name || user?.username || "?").charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-main truncate">
                {user?.display_name || user?.username}
              </div>
              <div className="text-xs text-faint truncate">@{user?.username}</div>
            </div>
            <button
              onClick={onOpenSettings}
              className="text-muted hover:text-main p-1.5 rounded-lg hover:bg-elevated transition-colors"
              aria-label="Настройки"
              title="Настройки"
            >
              <Settings size={18} />
            </button>
            <button
              onClick={logout}
              className="text-muted hover:text-red-500 p-1.5 rounded-lg hover:bg-elevated transition-colors"
              aria-label="Выйти"
              title="Выйти"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

interface ChatRowProps {
  chat: Chat;
  active: boolean;
  editing: boolean;
  editValue: string;
  editInputRef: React.RefObject<HTMLInputElement>;
  onSelect: () => void;
  onEdit: () => void;
  onEditChange: (v: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  onDelete: () => void;
  confirmingDelete: boolean;
  onConfirmDelete: () => void;
  onAbortDelete: () => void;
}

function ChatRow(props: ChatRowProps) {
  const {
    chat,
    active,
    editing,
    editValue,
    editInputRef,
    onSelect,
    onEdit,
    onEditChange,
    onCommit,
    onCancel,
    onDelete,
    confirmingDelete,
    onConfirmDelete,
    onAbortDelete,
  } = props;
  const [menuOpen, setMenuOpen] = useState(false);

  if (confirmingDelete) {
    return (
      <div className="flex items-center gap-1 px-2 py-1.5 rounded-lg bg-red-500/10">
        <span className="text-xs text-red-500 flex-1 px-1">Удалить?</span>
        <button
          onClick={onConfirmDelete}
          className="p-1.5 rounded-md text-red-500 hover:bg-red-500/20"
          aria-label="Подтвердить"
        >
          <Check size={14} />
        </button>
        <button
          onClick={onAbortDelete}
          className="p-1.5 rounded-md text-muted hover:bg-elevated"
          aria-label="Отмена"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  return (
    <div
      className={`group relative flex items-center rounded-lg transition-colors ${
        active ? "bg-elevated" : "hover:bg-elevated/60"
      }`}
    >
      {editing ? (
        <input
          ref={editInputRef}
          value={editValue}
          onChange={(e) => onEditChange(e.target.value)}
          onBlur={onCommit}
          onKeyDown={(e) => {
            if (e.key === "Enter") onCommit();
            if (e.key === "Escape") onCancel();
          }}
          className="flex-1 h-9 mx-1 px-2 rounded-md bg-app border border-brand-400 text-sm text-main focus:outline-none focus:ring-2 focus:ring-brand-500/20"
        />
      ) : (
        <button
          onClick={onSelect}
          className={`flex-1 h-9 flex items-center px-3 text-sm text-left truncate ${
            active ? "text-main font-medium" : "text-muted"
          }`}
          title={chat.title}
        >
          {chat.title}
        </button>
      )}

      {!editing && (
        <div className="absolute right-1 top-1/2 -translate-y-1/2">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            onBlur={() => setTimeout(() => setMenuOpen(false), 150)}
            className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-muted hover:text-main hover:bg-app transition-all"
            aria-label="Действия"
          >
            <MoreHorizontal size={16} />
          </button>
          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: -4 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: -4 }}
                transition={{ duration: 0.12 }}
                className="absolute right-0 top-full mt-1 w-36 bg-elevated border border-app rounded-lg shadow-float py-1 z-20"
              >
                <button
                  onMouseDown={(e) => {
                    e.preventDefault();
                    onEdit();
                    setMenuOpen(false);
                  }}
                  className="w-full px-3 py-2 text-sm text-left text-main hover:bg-soft flex items-center gap-2"
                >
                  <Pencil size={14} /> Переименовать
                </button>
                <button
                  onMouseDown={(e) => {
                    e.preventDefault();
                    onDelete();
                    setMenuOpen(false);
                  }}
                  className="w-full px-3 py-2 text-sm text-left text-red-500 hover:bg-soft flex items-center gap-2"
                >
                  <Trash2 size={14} /> Удалить
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
