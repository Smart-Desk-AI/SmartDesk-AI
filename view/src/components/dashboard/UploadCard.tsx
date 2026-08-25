'use client';

import { useState, useRef } from 'react';
import { api } from '@/lib/api';
import styles from './UploadCard.module.css';

interface Props {
  projectId: number;
  onUploadSuccess: (fileId: string) => void;
  onToast: (msg: string, type: 'success' | 'error' | 'info') => void;
}

export default function UploadCard({ projectId, onUploadSuccess, onToast }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [fileId, setFileId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
      onToast('Only PDF and TXT files are supported.', 'error');
      return;
    }
    setIsUploading(true);
    setUploadedFile(file.name);
    try {
      const res = await api.upload(projectId, file);
      if (res.file_id) {
        setFileId(res.file_id);
        onUploadSuccess(res.file_id);
        onToast(`File uploaded successfully! ID: ${res.file_id}`, 'success');
      } else {
        onToast(`Upload signal: ${res.signal}`, 'error');
      }
    } catch (e: unknown) {
      onToast(`Upload failed: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error');
      setUploadedFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className={`glass-card ${styles.card}`}>
      <div className={styles.header}>
        <div className={styles.stepBadge}>1</div>
        <div>
          <h3 className={styles.title}>Upload Document</h3>
          <p className={styles.desc}>Add a PDF or TXT file to the knowledge base</p>
        </div>
      </div>

      <div
        className={`${styles.dropzone} ${isDragging ? styles.dragging : ''} ${uploadedFile ? styles.hasFile : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept=".pdf,.txt" onChange={onInputChange} style={{ display: 'none' }} />
        {isUploading ? (
          <div className={styles.uploadingState}>
            <div className="spinner spinner-lg" />
            <p>Uploading <strong>{uploadedFile}</strong>…</p>
          </div>
        ) : uploadedFile && fileId ? (
          <div className={styles.successState}>
            <div className={styles.successIcon}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <p className={styles.filename}>{uploadedFile}</p>
            <p className={styles.fileId}>File ID: <code>{fileId}</code></p>
            <p className={styles.reupload}>Click to upload a different file</p>
          </div>
        ) : (
          <div className={styles.idleState}>
            <div className={styles.uploadIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <p className={styles.dropText}>Drag & drop or <span>click to browse</span></p>
            <p className={styles.dropHint}>Supports PDF, TXT</p>
          </div>
        )}
      </div>
    </div>
  );
}
