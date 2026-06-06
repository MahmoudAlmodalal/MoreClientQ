"use client";

import * as React from "react";
import { UploadCloud, FileText, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";

interface FileUploadProps {
  assistantId: string;
  onSuccess: (document: any) => void;
  onError: (error: string) => void;
}

export default function FileUpload({ assistantId, onSuccess, onError }: FileUploadProps) {
  const [isDragActive, setIsDragActive] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const allowedExtensions = ["pdf", "docx", "txt"];
  const maxSizeBytes = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): boolean => {
    setErrorMsg(null);
    setSuccessMsg(null);
    const suffix = file.name.split(".").pop()?.toLowerCase() || "";
    
    if (!allowedExtensions.includes(suffix)) {
      setErrorMsg("Unsupported file type. Allowed: PDF, DOCX, TXT.");
      return false;
    }
    
    if (file.size > maxSizeBytes) {
      setErrorMsg("File size exceeds maximum limit of 10MB.");
      return false;
    }
    
    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append("assistant_id", assistantId);
      formData.append("file", selectedFile);

      const response = await fetchApi("/documents/upload", {
        method: "POST",
        body: formData,
      });

      setSuccessMsg(`Successfully uploaded "${selectedFile.name}"! Starting background ingestion...`);
      setSelectedFile(null);
      onSuccess(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload document.";
      setErrorMsg(msg);
      onError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
        className={`relative p-8 rounded-2xl border-2 border-dashed transition duration-300 flex flex-col items-center justify-center cursor-pointer min-h-[180px] text-center ${
          isDragActive
            ? "border-indigo-500 bg-indigo-500/5"
            : "border-slate-800 bg-slate-900/20 hover:border-slate-700 hover:bg-slate-900/30"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          disabled={isUploading}
        />

        <div className="p-3.5 bg-slate-950/80 rounded-2xl border border-slate-800 text-slate-400 mb-4 group-hover:text-indigo-400 group-hover:border-indigo-500/20 transition-all">
          <UploadCloud className="h-6 w-6 animate-pulse" />
        </div>

        {selectedFile ? (
          <div className="space-y-2">
            <p className="text-white text-sm font-semibold flex items-center justify-center gap-2">
              <FileText className="h-4 w-4 text-indigo-400" />
              {selectedFile.name}
            </p>
            <p className="text-slate-500 text-xs">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            <p className="text-white text-sm font-bold tracking-tight">
              Drag & drop document here, or <span className="text-indigo-400">browse</span>
            </p>
            <p className="text-slate-500 text-xs font-semibold">
              Supports PDF, DOCX, TXT up to 10MB
            </p>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold flex items-start gap-2.5 animate-in fade-in duration-200">
          <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-start gap-2.5 animate-in fade-in duration-200">
          <CheckCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />
          <span>{successMsg}</span>
        </div>
      )}

      {selectedFile && (
        <div className="flex justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFile(null);
            }}
            disabled={isUploading}
            className="border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            Clear
          </Button>
          <Button
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleUpload();
            }}
            disabled={isUploading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4"
          >
            {isUploading ? "Uploading..." : "Upload File"}
          </Button>
        </div>
      )}
    </div>
  );
}
