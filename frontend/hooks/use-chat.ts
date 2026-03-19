"use client";

import { useState, useCallback } from "react";
import type { Message, RAGMode } from "@/lib/api";
import { askChat, streamChat } from "@/lib/api";

interface UseChatOptions {
  documentId: string | null;
  onError?: (err: Error) => void;
}

export function useChat({ documentId, onError }: UseChatOptions) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(
    async (content: string, mode: RAGMode, stream = true) => {
      if (!documentId) {
        onError?.(new Error("No document loaded"));
        return;
      }

      const userMessage: Message = { role: "user", content };
      setMessages((m) => [...m, userMessage]);
      setIsLoading(true);

      if (stream) {
        setIsStreaming(true);
        const assistantMessage: Message = { role: "assistant", content: "" };
        setMessages((m) => [...m, assistantMessage]);

        try {
          const msgHistory = [...messages, userMessage];
          for await (const { event, data } of streamChat(documentId, msgHistory, mode)) {
            if (event === "token") {
              setMessages((m) => {
                const next = [...m];
                const last = next[next.length - 1];
                if (last?.role === "assistant") {
                  next[next.length - 1] = { ...last, content: last.content + data };
                }
                return next;
              });
            } else if (event === "error") {
              const parsed = JSON.parse(data).error;
              throw new Error(parsed);
            }
          }
        } catch (e) {
          const err = e instanceof Error ? e : new Error(String(e));
          onError?.(err);
          setMessages((m) => {
            const next = [...m];
            const last = next[next.length - 1];
            if (last?.role === "assistant") {
              next[next.length - 1] = {
                ...last,
                content: last.content || `Error: ${err.message}`,
              };
            }
            return next;
          });
        } finally {
          setIsStreaming(false);
        }
      } else {
        try {
          const res = await askChat(documentId, [...messages, userMessage], mode);
          setMessages((m) => [...m, { role: "assistant", content: res.answer }]);
        } catch (e) {
          const err = e instanceof Error ? e : new Error(String(e));
          onError?.(err);
          setMessages((m) => [
            ...m,
            { role: "assistant", content: `Error: ${err.message}` },
          ]);
        }
      }

      setIsLoading(false);
    },
    [documentId, messages, onError]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, sendMessage, clearMessages, isLoading, isStreaming };
}
