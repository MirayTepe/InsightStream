const API_BASE = "/api/v1";

export type RAGMode = "summary" | "deep_dive" | "explain_to_kid";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface PDFUploadResponse {
  document_id: string;
  num_pages: number;
  num_chunks: number;
}

export interface PDFUploadAsyncResponse {
  document_id: string;
  job_id: string;
  status: "pending";
  message: string;
}

export interface ChatResponse {
  answer: string;
  mode: RAGMode;
  used_chunks: number;
}

export interface JobStatusResponse {
  status: string;
  result?: { status: string; num_chunks?: number };
  error?: string;
}

export async function uploadPDF(file: File): Promise<PDFUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/pdf/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function uploadPDFAsync(
  file: File,
  token: string
): Promise<PDFUploadAsyncResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/pdf/upload/async`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/pdf/job/${jobId}`);
  if (!res.ok) throw new Error("Failed to get job status");
  return res.json();
}

export async function askChat(
  documentId: string,
  messages: Message[],
  mode: RAGMode = "summary"
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, messages, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Chat failed");
  }
  return res.json();
}

export async function* streamChat(
  documentId: string,
  messages: Message[],
  mode: RAGMode = "summary"
): AsyncGenerator<{ event: string; data: string }> {
  const res = await fetch(`${API_BASE}/chat/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, messages, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Stream failed");
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith("data:") && currentEvent) {
        const data = line.slice(5).trim();
        yield { event: currentEvent, data };
        currentEvent = "";
      }
    }
  }
}
