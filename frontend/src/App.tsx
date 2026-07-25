/** Корневой компонент: роутинг по auth-состоянию. */
import { useEffect } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { AuthScreen } from "@/components/auth/AuthScreen";
import { ChatLayout } from "@/components/chat/ChatLayout";
import { useAuthStore } from "@/store/auth";

export default function App() {
  const { user, loading, init } = useAuthStore();

  useEffect(() => {
    init();
  }, [init]);

  if (loading && user === null && localStorage.getItem("burmalda-token")) {
    return (
      <div className="h-screen flex items-center justify-center bg-app">
        <Spinner size={28} />
      </div>
    );
  }

  // Прямой условный рендер без AnimatePresence — последний вызывает
  // «застревание» exit-анимации при переключении auth↔app и блокирует UI.
  if (!user) return <AuthScreen />;
  return <ChatLayout />;
}
