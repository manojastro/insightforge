"use client";

import { useRef, useState } from "react";

interface Props {
  onFile: (f: File) => void;
  busy?: boolean;
  accept?: string;
}

export default function UploadDropzone({ onFile, busy, accept = ".csv,.parquet,.xlsx" }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDrag(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-lg border border-dashed p-6 text-center text-sm ${
        drag ? "border-blue-500 bg-blue-50 dark:bg-blue-950" : "border-slate-300 dark:border-slate-700"
      } ${busy ? "opacity-60" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
      {busy ? "Uploading to POST /datasets/upload…" : `Drop a file here or click to upload (${accept})`}
    </div>
  );
}
