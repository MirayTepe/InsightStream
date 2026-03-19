"use client";

import { useState, useCallback } from "react";
import { PDFUploadZone } from "@/components/upload/pdf-upload-zone";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { Sidebar } from "@/components/sidebar";
import { ErrorBoundary } from "@/components/error-boundary";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChat } from "@/hooks/use-chat";
import { uploadPDF } from "@/lib/api";
import { toast } from "sonner";

export default function Home() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [chatSessions, setChatSessions] = useState<
    { id: string; title: string }[]
  >([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);

  const handleError = useCallback((err: Error) => {
    toast.error(err.message);
  }, []);

  const { messages, sendMessage, clearMessages, isLoading, isStreaming } =
    useChat({ documentId, onError: handleError });

  const handleUpload = useCallback(async (file: File) => {
    const res = await uploadPDF(file);
    setDocumentId(res.document_id);
    toast.success(`PDF processed: ${res.num_chunks} chunks`);
  }, []);

  const handleNewChat = useCallback(() => {
    clearMessages();
    const id = `session-${Date.now()}`;
    setChatSessions((s) => [...s, { id, title: "New chat" }]);
    setCurrentSession(id);
  }, [clearMessages]);

  const handleSelectSession = useCallback((id: string) => {
    setCurrentSession(id);
    clearMessages();
  }, [clearMessages]);

  const handleSend = useCallback(
    (content: string, mode: "summary" | "deep_dive" | "explain_to_kid") => {
      if (chatSessions.length === 0) {
        handleNewChat();
      }
      sendMessage(content, mode, true);
    },
    [sendMessage, chatSessions.length, handleNewChat]
  );

  const showUpload = !documentId;
  const showChat = !!documentId;

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        documentId={documentId}
        chatSessions={chatSessions}
        currentSession={currentSession}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
      />

      <main className="flex-1 flex flex-col min-w-0">
        {showUpload && (
          <div className="flex-1 flex items-center justify-center p-8">
            <ErrorBoundary>
              <div className="w-full max-w-xl">
                <h1 className="text-2xl font-bold text-center mb-2">
                  InsightStream
                </h1>
                <p className="text-muted-foreground text-center mb-8">
                  Upload a PDF to start asking questions
                </p>
                <PDFUploadZone onUpload={handleUpload} />
              </div>
            </ErrorBoundary>
          </div>
        )}

        {showChat && (
          <>
            <ScrollArea className="flex-1">
              <ErrorBoundary>
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
                    <h2 className="text-xl font-semibold mb-2">
                      Ask about your document
                    </h2>
                    <p className="text-muted-foreground text-sm max-w-md">
                      Choose a mode and type your question. Responses stream in
                      real time.
                    </p>
                  </div>
                ) : (
                  <div className="pb-4">
                    {messages.map((msg, i) => (
                      <ChatMessage
                        key={i}
                        role={msg.role as "user" | "assistant"}
                        content={msg.content}
                        isStreaming={
                          isStreaming &&
                          i === messages.length - 1 &&
                          msg.role === "assistant"
                        }
                      />
                    ))}
                  </div>
                )}
              </ErrorBoundary>
            </ScrollArea>
            <ChatInput
              onSend={handleSend}
              disabled={isLoading}
            />
          </>
        )}
      </main>
    </div>
  );
}
