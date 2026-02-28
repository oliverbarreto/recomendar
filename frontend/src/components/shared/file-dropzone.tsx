"use client";

import React, { useCallback, useState, useEffect, useRef } from 'react';
import { Upload, FileAudio, X, RefreshCw, AlertCircle, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { validateAudioFile, formatFileSize, getAllowedExtensionsString } from '@/lib/validation';

interface FileDropzoneProps {
    onFileSelect: (file: File) => void;
    onFileRemove: () => void;
    selectedFile: File | null;
    disabled?: boolean;
    maxSizeMB?: number;
    onError?: (error: string | null) => void;
    externalError?: string | null;
}

export function FileDropzone({
    onFileSelect,
    onFileRemove,
    selectedFile,
    disabled = false,
    maxSizeMB = 500,
    onError,
    externalError,
}: FileDropzoneProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [dragCounter, setDragCounter] = useState(0);
    const [isValidating, setIsValidating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Clear internal error when external error is cleared
    useEffect(() => {
        if (!externalError) {
            setError(null);
        }
    }, [externalError]);

    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setDragCounter(prev => prev + 1);
            setIsDragging(true);
        }
    }, [disabled]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragCounter(prev => {
            const newCount = prev - 1;
            if (newCount === 0) {
                setIsDragging(false);
            }
            return newCount;
        });
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const processFile = async (file: File) => {
        setError(null);
        setIsValidating(true);
        onError?.(null); // Clear parent error

        try {
            // Validate file
            const validation = await validateAudioFile(file);

            if (!validation.valid) {
                const errorMessage = validation.error || 'Invalid file';
                setError(errorMessage);
                onError?.(errorMessage); // Notify parent of error
                return;
            }

            onFileSelect(file);
        } finally {
            setIsValidating(false);
        }
    };

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        setDragCounter(0);

        if (disabled) return;

        const files = Array.from(e.dataTransfer.files);
        if (files.length === 0) return;

        const file = files[0];
        await processFile(file);
    }, [disabled, processFile]);

    const handleRemove = () => {
        setError(null);
        onError?.(null); // Clear parent error
        onFileRemove();
    };

    const handleBrowseClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled && fileInputRef.current) {
            fileInputRef.current.click();
        }
    }, [disabled]);

    const handleFileInputChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            await processFile(file);
        }
        // Reset input value to allow re-selecting the same file
        e.target.value = '';
    }, [processFile]);

    return (
        <div className="w-full">
            {/* Hidden file input for OS file picker */}
            <input
                ref={fileInputRef}
                type="file"
                accept="audio/mpeg,audio/mp3,audio/mp4,audio/x-m4a,audio/wav,audio/x-wav,audio/wave,audio/ogg,audio/flac,audio/x-flac"
                onChange={handleFileInputChange}
                className="hidden"
                disabled={disabled}
                aria-label="Upload audio file"
            />
            {!selectedFile ? (
                <div
                    onDragEnter={handleDragEnter}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`
            relative border-2 border-dashed rounded-lg p-8 text-center
            transition-colors duration-200
            ${isDragging
                            ? 'border-primary bg-primary/5'
                            : 'border-gray-300 dark:border-gray-700 hover:border-primary/50'
                        }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
                >
                    <div className="flex flex-col items-center gap-4">
                        <div className={`
              p-4 rounded-full 
              ${isDragging
                                ? 'bg-primary/10'
                                : 'bg-gray-100 dark:bg-gray-800'
                            }
            `}>
                            <Upload className={`
                w-8 h-8 
                ${isDragging
                                    ? 'text-primary'
                                    : 'text-gray-400 dark:text-gray-500'
                                }
              `} />
                        </div>

                        <div>
                            <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                                Drag and drop your audio file here
                            </p>
                        </div>

                        {/* OR divider */}
                        <div className="flex items-center gap-3 w-full max-w-xs mx-auto my-2">
                            <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
                            <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">OR</span>
                            <div className="flex-1 border-t border-gray-300 dark:border-gray-600"></div>
                        </div>

                        {/* Browse Files Button */}
                        <Button
                            type="button"
                            variant="outline"
                            size="lg"
                            onClick={handleBrowseClick}
                            disabled={disabled || isValidating}
                            className="w-full max-w-xs mx-auto"
                        >
                            <FolderOpen className="mr-2 h-4 w-4" />
                            Browse Files
                        </Button>

                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-4">
                            <p>Supported formats: {getAllowedExtensionsString()}</p>
                            <p className="mt-1">Maximum file size: {maxSizeMB}MB</p>
                        </div>
                    </div>

                    {isValidating && (
                        <div className="mt-4 flex items-center justify-center gap-2 text-sm text-primary">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                            <span>Validating file...</span>
                        </div>
                    )}

                    {(externalError || error) && (
                        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                            <div className="flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-red-600 dark:text-red-400 flex-1">{externalError || error}</p>
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <div className="border-2 border-gray-300 dark:border-gray-700 rounded-lg p-6">
                    <div className="flex items-start gap-4">
                        <div className="p-3 bg-primary/10 rounded-lg">
                            <FileAudio className="w-6 h-6 text-primary" />
                        </div>

                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                {selectedFile.name}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {formatFileSize(selectedFile.size)}
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={handleRemove}
                            disabled={disabled}
                            className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            aria-label="Remove file"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {(externalError || error) && (
                        <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
                            <div className="flex items-start gap-2">
                                <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-red-600 dark:text-red-400 flex-1">{externalError || error}</p>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

