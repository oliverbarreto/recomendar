"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileDropzone } from '@/components/shared/file-dropzone';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, ArrowRight, Upload, CheckCircle2, AlertCircle, FileAudio, RefreshCw } from 'lucide-react';
import { useUploadEpisode } from '@/hooks/use-episodes';
import { formatFileSize, formatDuration } from '@/lib/validation';

interface UploadEpisodeFormProps {
    channelId: number;
    onSuccess?: () => void;
    onCancel?: () => void;
}

enum UploadStep {
    FILE_SELECTION = 1,
    EPISODE_DETAILS = 2,
    UPLOADING = 3,
    COMPLETE = 4,
}

export function UploadEpisodeForm({ channelId, onSuccess, onCancel }: UploadEpisodeFormProps) {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState<UploadStep>(UploadStep.FILE_SELECTION);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [fileError, setFileError] = useState<string | null>(null);

    // Form data
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [publicationDate, setPublicationDate] = useState(
        new Date().toISOString().split('T')[0]
    );
    const [tags, setTags] = useState<string[]>([]);
    const [tagInput, setTagInput] = useState('');

    const uploadMutation = useUploadEpisode((progress) => {
        setUploadProgress(progress);
    });

    const handleFileSelect = (file: File) => {
        setSelectedFile(file);
        setFileError(null); // Clear any previous error
        // Auto-populate title from filename if empty
        if (!title) {
            const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
            setTitle(nameWithoutExt);
        }
    };

    const handleFileRemove = () => {
        setSelectedFile(null);
        setFileError(null); // Clear any previous error
    };

    const handleFileError = (error: string | null) => {
        setFileError(error);
    };

    const handleNext = () => {
        if (currentStep === UploadStep.FILE_SELECTION && selectedFile) {
            setCurrentStep(UploadStep.EPISODE_DETAILS);
        }
    };

    const handleBack = () => {
        if (currentStep === UploadStep.EPISODE_DETAILS) {
            setCurrentStep(UploadStep.FILE_SELECTION);
        }
    };

    const handleAddTag = () => {
        const trimmedTag = tagInput.trim();
        if (trimmedTag && !tags.includes(trimmedTag) && tags.length < 10) {
            setTags([...tags, trimmedTag]);
            setTagInput('');
        }
    };

    const handleRemoveTag = (tagToRemove: string) => {
        setTags(tags.filter(tag => tag !== tagToRemove));
    };

    const handleSubmit = async () => {
        if (!selectedFile || !title.trim()) return;

        setCurrentStep(UploadStep.UPLOADING);

        try {
            await uploadMutation.mutateAsync({
                channelId,
                title: title.trim(),
                description: description.trim() || undefined,
                publicationDate,
                tags: tags.length > 0 ? tags : undefined,
                audioFile: selectedFile,
            });

            setCurrentStep(UploadStep.COMPLETE);

            // Call onSuccess callback after a short delay
            setTimeout(() => {
                if (onSuccess) {
                    onSuccess();
                } else {
                    router.push(`/channels/${channelId}/episodes`);
                }
            }, 2000);
        } catch (error) {
            // Error is handled by the mutation's onError callback
            setCurrentStep(UploadStep.EPISODE_DETAILS);
        }
    };

    const renderStepIndicator = () => {
        const steps = [
            { number: 1, label: 'Select File' },
            { number: 2, label: 'Episode Details' },
            { number: 3, label: 'Upload' },
        ];

        return (
            <div className="flex items-center justify-center mb-8">
                {steps.map((step, index) => (
                    <React.Fragment key={step.number}>
                        <div className="flex items-center">
                            <div
                                className={`
                  w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium
                  ${currentStep >= step.number
                                        ? 'bg-primary text-primary-foreground'
                                        : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                                    }
                `}
                            >
                                {currentStep > step.number ? (
                                    <CheckCircle2 className="w-5 h-5" />
                                ) : (
                                    step.number
                                )}
                            </div>
                            <span
                                className={`
                  ml-2 text-sm font-medium
                  ${currentStep >= step.number
                                        ? 'text-gray-900 dark:text-gray-100'
                                        : 'text-gray-500 dark:text-gray-400'
                                    }
                `}
                            >
                                {step.label}
                            </span>
                        </div>
                        {index < steps.length - 1 && (
                            <div
                                className={`
                  w-16 h-0.5 mx-4
                  ${currentStep > step.number
                                        ? 'bg-primary'
                                        : 'bg-gray-200 dark:bg-gray-700'
                                    }
                `}
                            />
                        )}
                    </React.Fragment>
                ))}
            </div>
        );
    };

    const renderFileSelection = () => (
        <div className="space-y-6">
            <FileDropzone
                onFileSelect={handleFileSelect}
                onFileRemove={handleFileRemove}
                selectedFile={selectedFile}
                onError={handleFileError}
                externalError={fileError}
            />

            <div className="flex justify-end gap-3">
                {onCancel && (
                    <Button variant="outline" onClick={onCancel}>
                        Cancel
                    </Button>
                )}
                {fileError ? (
                    <Button
                        onClick={() => setFileError(null)}
                    >
                        <RefreshCw className="mr-2 w-4 h-4" />
                        Try Again
                    </Button>
                ) : (
                    <Button
                        onClick={handleNext}
                        disabled={!selectedFile}
                    >
                        Next
                        <ArrowRight className="ml-2 w-4 h-4" />
                    </Button>
                )}
            </div>
        </div>
    );

    const renderEpisodeDetails = () => (
        <div className="space-y-6">
            {/* File Summary */}
            {selectedFile && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm">Selected File</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-sm space-y-1">
                            <p><span className="font-medium">Name:</span> {selectedFile.name}</p>
                            <p><span className="font-medium">Size:</span> {formatFileSize(selectedFile.size)}</p>
                            <p><span className="font-medium">Type:</span> {selectedFile.type}</p>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Episode Details Form */}
            <div className="space-y-4">
                <div>
                    <Label htmlFor="title">Title *</Label>
                    <Input
                        id="title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter episode title"
                        maxLength={500}
                        required
                    />
                </div>

                <div>
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Enter episode description (optional)"
                        rows={4}
                        maxLength={5000}
                    />
                </div>

                <div>
                    <Label htmlFor="publicationDate">Publication Date</Label>
                    <Input
                        id="publicationDate"
                        type="date"
                        value={publicationDate}
                        onChange={(e) => setPublicationDate(e.target.value)}
                    />
                </div>

                <div>
                    <Label htmlFor="tags">Tags</Label>
                    <div className="flex gap-2">
                        <Input
                            id="tags"
                            value={tagInput}
                            onChange={(e) => setTagInput(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    e.preventDefault();
                                    handleAddTag();
                                }
                            }}
                            placeholder="Add a tag (press Enter)"
                            maxLength={50}
                            disabled={tags.length >= 10}
                        />
                        <Button
                            type="button"
                            onClick={handleAddTag}
                            disabled={!tagInput.trim() || tags.length >= 10}
                            variant="outline"
                        >
                            Add
                        </Button>
                    </div>
                    {tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                            {tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-primary/10 text-primary rounded-full text-sm"
                                >
                                    {tag}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveTag(tag)}
                                        className="hover:text-primary/70"
                                    >
                                        ×
                                    </button>
                                </span>
                            ))}
                        </div>
                    )}
                    <p className="text-xs text-gray-500 mt-1">
                        {tags.length}/10 tags
                    </p>
                </div>
            </div>

            <div className="flex justify-between gap-3">
                <Button variant="outline" onClick={handleBack}>
                    <ArrowLeft className="mr-2 w-4 h-4" />
                    Back
                </Button>
                <div className="flex gap-3">
                    {onCancel && (
                        <Button variant="outline" onClick={onCancel}>
                            Cancel
                        </Button>
                    )}
                    <Button
                        onClick={handleSubmit}
                        disabled={!title.trim() || uploadMutation.isPending}
                    >
                        <Upload className="mr-2 w-4 h-4" />
                        Upload Episode
                    </Button>
                </div>
            </div>
        </div>
    );

    const renderUploading = () => (
        <div className="space-y-6 text-center">
            <div className="flex justify-center">
                <div className="p-4 bg-primary/10 rounded-full">
                    <Upload className="w-12 h-12 text-primary animate-pulse" />
                </div>
            </div>

            <div>
                <h3 className="text-lg font-medium mb-2">Uploading Episode...</h3>
                <p className="text-sm text-gray-500">
                    Please wait while we upload and process your audio file
                </p>
            </div>

            {selectedFile && (
                <div className="max-w-md mx-auto space-y-3">
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded">
                                <FileAudio className="w-5 h-5 text-primary" />
                            </div>
                            <div className="flex-1 text-left min-w-0">
                                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                    {selectedFile.name}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                    {formatFileSize(selectedFile.size)}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center justify-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        <span>Uploading to server...</span>
                    </div>
                </div>
            )}

            <p className="text-xs text-gray-400">
                Please don&apos;t close this window. This may take a few moments depending on file size.
            </p>
        </div>
    );

    const renderComplete = () => (
        <div className="space-y-6 text-center">
            <div className="flex justify-center">
                <div className="p-4 bg-green-100 dark:bg-green-900/20 rounded-full">
                    <CheckCircle2 className="w-12 h-12 text-green-600 dark:text-green-400" />
                </div>
            </div>

            <div>
                <h3 className="text-lg font-medium mb-2">Upload Complete!</h3>
                <p className="text-sm text-gray-500">
                    Your episode has been successfully uploaded and is ready to be published.
                </p>
            </div>

            <Button
                onClick={() => {
                    if (onSuccess) {
                        onSuccess();
                    } else {
                        router.push(`/channels/${channelId}/episodes`);
                    }
                }}
            >
                View Episodes
            </Button>
        </div>
    );

    return (
        <div className="max-w-3xl mx-auto">
            {currentStep !== UploadStep.COMPLETE && currentStep !== UploadStep.UPLOADING && renderStepIndicator()}

            <Card>
                <CardHeader>
                    <CardTitle>
                        {currentStep === UploadStep.FILE_SELECTION && 'Upload Audio File'}
                        {currentStep === UploadStep.EPISODE_DETAILS && 'Episode Details'}
                        {currentStep === UploadStep.UPLOADING && 'Uploading'}
                        {currentStep === UploadStep.COMPLETE && 'Success'}
                    </CardTitle>
                    <CardDescription>
                        {currentStep === UploadStep.FILE_SELECTION && 'Select an audio file to upload (MP3, M4A, WAV, OGG, FLAC)'}
                        {currentStep === UploadStep.EPISODE_DETAILS && 'Provide details about your episode'}
                        {currentStep === UploadStep.UPLOADING && 'Processing your audio file'}
                        {currentStep === UploadStep.COMPLETE && 'Your episode is ready'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {currentStep === UploadStep.FILE_SELECTION && renderFileSelection()}
                    {currentStep === UploadStep.EPISODE_DETAILS && renderEpisodeDetails()}
                    {currentStep === UploadStep.UPLOADING && renderUploading()}
                    {currentStep === UploadStep.COMPLETE && renderComplete()}
                </CardContent>
            </Card>
        </div>
    );
}


