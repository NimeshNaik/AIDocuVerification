import { useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { verifyDocument, submitDecision, upscaleDocument } from '../lib/api';
import {
    Shield,
    Upload,
    FileText,
    CheckCircle,
    AlertTriangle,
    XCircle,
    LogOut,
    History,
    User,
    ChevronRight,
    Sparkles
} from 'lucide-react';
import './Dashboard.css';

export default function Dashboard() {
    const { profile, signOut } = useAuth();
    const navigate = useNavigate();
    const fileInputRef = useRef(null);

    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [isUpscaling, setIsUpscaling] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [overrideReason, setOverrideReason] = useState('');

    function handleFileSelect(e) {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            setFile(selectedFile);
            setResult(null);
            setError('');

            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result);
            reader.readAsDataURL(selectedFile);
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files?.[0];
        if (droppedFile) {
            setFile(droppedFile);
            setResult(null);
            setError('');

            const reader = new FileReader();
            reader.onload = (e) => setPreview(e.target.result);
            reader.readAsDataURL(droppedFile);
        }
    }

    async function handleUpscale() {
        if (!file) return;

        setIsUpscaling(true);
        setError('');

        try {
            const upscaledBlob = await upscaleDocument(file);
            const upscaledFile = new File([upscaledBlob], `enhanced_${file.name}`, {
                type: 'image/jpeg'
            });

            setFile(upscaledFile);
            setPreview(URL.createObjectURL(upscaledBlob));
            setResult(null); // Reset results as image changed
            // alert("Image enhanced successfully!");
        } catch (err) {
            setError(err.message || 'Upscaling failed');
        } finally {
            setIsUpscaling(false);
        }
    }

    async function handleVerify() {
        if (!file) return;

        setLoading(true);
        setError('');

        try {
            const verificationResult = await verifyDocument(file);
            setResult(verificationResult);
        } catch (err) {
            setError(err.message || 'Verification failed');
        } finally {
            setLoading(false);
        }
    }

    async function handleDecision(decision) {
        if (!result) return;

        setSubmitting(true);

        try {
            const needsReason = result.recommendation !== decision;
            await submitDecision(
                result.request_id,
                decision,
                needsReason ? overrideReason : null
            );

            // Reset for next document
            setFile(null);
            setPreview(null);
            setResult(null);
            setOverrideReason('');

            alert(`Document ${decision.toLowerCase()}ed successfully!`);
        } catch (err) {
            setError(err.message || 'Failed to submit decision');
        } finally {
            setSubmitting(false);
        }
    }

    async function handleSignOut() {
        await signOut();
        navigate('/login');
    }

    function getRecommendationStyle(recommendation) {
        switch (recommendation) {
            case 'APPROVE':
                return { icon: CheckCircle, color: 'success', text: 'Recommended: Approve' };
            case 'REVIEW':
                return { icon: AlertTriangle, color: 'warning', text: 'Manual Review Required' };
            case 'REJECT':
                return { icon: XCircle, color: 'error', text: 'Recommended: Reject' };
            default:
                return { icon: FileText, color: 'info', text: 'Processing' };
        }
    }

    function getConfidenceLevel(score) {
        if (score >= 0.8) return 'high';
        if (score >= 0.5) return 'medium';
        return 'low';
    }

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <Shield size={28} className="header-logo" />
                    <div>
                        <h1>Document Verification</h1>
                        <p>Government of India</p>
                    </div>
                </div>
                <div className="header-right">
                    <button className="btn btn-secondary" onClick={() => navigate('/history')}>
                        <History size={18} />
                        History
                    </button>
                    <div className="user-menu">
                        <User size={18} />
                        <span>{profile?.full_name || 'Officer'}</span>
                    </div>
                    <button className="btn btn-secondary" onClick={handleSignOut}>
                        <LogOut size={18} />
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="dashboard-main">
                <div className="dashboard-grid">
                    {/* Upload Panel */}
                    <div className="card upload-panel">
                        <div className="card-header">
                            <h2 className="card-title">Upload Document</h2>
                        </div>

                        {!preview ? (
                            <div
                                className="upload-zone"
                                onClick={() => fileInputRef.current?.click()}
                                onDrop={handleDrop}
                                onDragOver={(e) => e.preventDefault()}
                            >
                                <Upload size={48} className="upload-zone-icon" />
                                <p className="upload-zone-text">
                                    Drag & drop or click to upload
                                </p>
                                <p className="upload-zone-hint">
                                    Supports: JPEG, PNG
                                </p>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/jpeg,image/png"
                                    onChange={handleFileSelect}
                                    hidden
                                />
                            </div>
                        ) : (
                            <div className="preview-container">
                                <img src={preview} alt="Document preview" className="document-preview" />
                                <div className="preview-actions">
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => {
                                            setFile(null);
                                            setPreview(null);
                                            setResult(null);
                                        }}
                                    >
                                        Remove
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={handleUpscale}
                                        disabled={loading || isUpscaling}
                                        title="Enhance image quality using AI"
                                    >
                                        {isUpscaling ? (
                                            <span className="spinner"></span>
                                        ) : (
                                            <Sparkles size={18} />
                                        )}
                                        Enhance
                                    </button>
                                    <button
                                        className="btn btn-primary"
                                        onClick={handleVerify}
                                        disabled={loading || isUpscaling}
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner"></span>
                                                Analyzing...
                                            </>
                                        ) : (
                                            <>
                                                <ChevronRight size={18} />
                                                Verify Document
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        )}

                        {error && (
                            <div className="error-message mt-md">
                                <AlertTriangle size={16} />
                                <span>{error}</span>
                            </div>
                        )}
                    </div>

                    {/* Results Panel */}
                    <div className="card results-panel">
                        <div className="card-header">
                            <h2 className="card-title">Verification Results</h2>
                        </div>

                        {!result ? (
                            <div className="empty-state">
                                <FileText size={48} />
                                <p>Upload a document to see results</p>
                            </div>
                        ) : (
                            <div className="results-content">
                                {/* Recommendation Banner */}
                                {(() => {
                                    const rec = getRecommendationStyle(result.recommendation);
                                    const Icon = rec.icon;
                                    return (
                                        <div className={`recommendation-banner ${rec.color}`}>
                                            <Icon size={24} />
                                            <div>
                                                <strong>{rec.text}</strong>
                                                <p>{result.explanation}</p>
                                            </div>
                                        </div>
                                    );
                                })()}

                                {/* Document Type */}
                                <div className="result-section">
                                    <h3>Document Type</h3>
                                    <div className="document-type-badge">
                                        {result.document_type?.toUpperCase()}
                                    </div>
                                </div>

                                {/* Extracted Fields */}
                                <div className="result-section">
                                    <h3>Extracted Fields</h3>
                                    <div className="fields-list">
                                        {Object.entries(result.fields || {}).map(([key, field]) => (
                                            <div key={key} className="field-item">
                                                <span className="field-label">{key.replace(/_/g, ' ')}</span>
                                                <span className="field-value">{field.value || '-'}</span>
                                                <div className="confidence-meter">
                                                    <div className="confidence-bar">
                                                        <div
                                                            className={`confidence-fill ${getConfidenceLevel(field.confidence)}`}
                                                            style={{ width: `${field.confidence * 100}%` }}
                                                        />
                                                    </div>
                                                    <span className="confidence-value">
                                                        {Math.round(field.confidence * 100)}%
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Validation Errors */}
                                {result.validation_errors?.length > 0 && (
                                    <div className="result-section">
                                        <h3>Validation Issues</h3>
                                        <ul className="issues-list">
                                            {result.validation_errors.map((error, i) => (
                                                <li key={i} className="issue-item warning">
                                                    <AlertTriangle size={14} />
                                                    {error}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Fraud Signals */}
                                {result.fraud_signals?.length > 0 && (
                                    <div className="result-section">
                                        <h3>Fraud Signals</h3>
                                        <ul className="issues-list">
                                            {result.fraud_signals.map((signal, i) => (
                                                <li key={i} className={`issue-item ${signal.severity.toLowerCase()}`}>
                                                    <AlertTriangle size={14} />
                                                    {signal.description}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Override Reason */}
                                {result.recommendation !== 'APPROVE' && (
                                    <div className="result-section">
                                        <label className="form-label">Override Reason (if any)</label>
                                        <textarea
                                            className="form-input"
                                            placeholder="Explain if overriding the recommendation..."
                                            value={overrideReason}
                                            onChange={(e) => setOverrideReason(e.target.value)}
                                            rows={2}
                                        />
                                    </div>
                                )}

                                {/* Decision Buttons */}
                                <div className="decision-actions">
                                    <button
                                        className="btn btn-success btn-lg"
                                        onClick={() => handleDecision('APPROVE')}
                                        disabled={submitting}
                                    >
                                        <CheckCircle size={18} />
                                        Approve
                                    </button>
                                    <button
                                        className="btn btn-warning btn-lg"
                                        onClick={() => handleDecision('REVIEW')}
                                        disabled={submitting}
                                    >
                                        <AlertTriangle size={18} />
                                        Review Later
                                    </button>
                                    <button
                                        className="btn btn-danger btn-lg"
                                        onClick={() => handleDecision('REJECT')}
                                        disabled={submitting}
                                    >
                                        <XCircle size={18} />
                                        Reject
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
