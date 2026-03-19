"use client";

import { FileText, MessageSquare, Sun, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  documentId: string | null;
  chatSessions: { id: string; title: string }[];
  currentSession: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  className?: string;
}

export function Sidebar({
  documentId,
  chatSessions,
  currentSession,
  onNewChat,
  onSelectSession,
  className,
}: SidebarProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <aside
      className={cn(
        "flex flex-col w-64 border-r bg-card shrink-0",
        className
      )}
    >
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg flex items-center gap-2">
          <FileText className="h-5 w-5" />
          InsightStream
        </h2>
        <Button
          variant="outline"
          className="w-full mt-4"
          onClick={onNewChat}
          disabled={!documentId}
        >
          <MessageSquare className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {chatSessions.length > 0 && (
        <div className="flex-1 overflow-auto p-2">
          <p className="text-xs font-medium text-muted-foreground px-2 mb-2">
            Chat History
          </p>
          {chatSessions.map((s) => (
            <button
              key={s.id}
              onClick={() => onSelectSession(s.id)}
              className={cn(
                "w-full text-left px-3 py-2 rounded-md text-sm truncate",
                currentSession === s.id
                  ? "bg-primary/10 text-primary"
                  : "hover:bg-muted"
              )}
            >
              {s.title}
            </button>
          ))}
        </div>
      )}

      <div className="p-4 border-t">
        <Button variant="ghost" size="icon" onClick={toggleTheme}>
          {resolvedTheme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </aside>
  );
}
