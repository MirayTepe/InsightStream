"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface PDFUploadZoneProps {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
}

export function PDFUploadZone({ onUpload, disabled }: PDFUploadZoneProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file || disabled || uploading) return;

      setError(null);
      setUploading(true);
      setProgress(10);

      try {
        setProgress(50);
        await onUpload(file);
        setProgress(100);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Upload failed");
      } finally {
        setUploading(false);
        setTimeout(() => setProgress(0), 500);
      }
    },
    [onUpload, disabled, uploading]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
    disabled: disabled || uploading,
  });

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors",
          isDragActive && "border-primary bg-primary/5",
          !isDragActive && "border-muted-foreground/25 hover:border-primary/50",
          (disabled || uploading) && "opacity-60 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="space-y-2">
            <Loader2 className="h-12 w-12 mx-auto animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Processing PDF...</p>
            <div className="w-48 h-1.5 mx-auto bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <>
            <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm font-medium">
              {isDragActive ? "Drop PDF here" : "Drag & drop a PDF or click to upload"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Max 50MB</p>
          </>
        )}
      </div>
      {error && (
        <p className="text-sm text-destructive text-center">{error}</p>
      )}
    </div>
  );
}
