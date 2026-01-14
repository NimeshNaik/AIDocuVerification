import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getAuditLogs } from '../lib/api';
import {
    Shield,
    ArrowLeft,
    CheckCircle,
    AlertTriangle,
    XCircle,
    LogOut,
    User,
    Calendar,
    FileText
} from 'lucide-react';
import './Dashboard.css';
import './History.css';

export default function History() {
    const { profile, signOut } = useAuth();
    const navigate = useNavigate();

    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        loadLogs();
    }, [page]);

    async function loadLogs() {
        setLoading(true);
        try {
            const response = await getAuditLogs(page, 20);
            setLogs(response.logs || []);
            setTotalPages(Math.ceil((response.total || 0) / 20));
        } catch (err) {
            setError(err.message || 'Failed to load history');
        } finally {
            setLoading(false);
        }
    }

    async function handleSignOut() {
        await signOut();
        navigate('/login');
    }

    function getDecisionIcon(decision) {
        switch (decision) {
            case 'APPROVE':
                return <CheckCircle size={16} className="text-success" />;
            case 'REVIEW':
                return <AlertTriangle size={16} className="text-warning" />;
            case 'REJECT':
                return <XCircle size={16} className="text-error" />;
            default:
                return <FileText size={16} />;
        }
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    return (
        <div className="dashboard">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <Shield size={28} className="header-logo" />
                    <div>
                        <h1>Verification History</h1>
                        <p>Government of India</p>
                    </div>
                </div>
                <div className="header-right">
                    <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
                        <ArrowLeft size={18} />
                        Back to Dashboard
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
                <div className="card">
                    <div className="card-header">
                        <h2 className="card-title">Audit Logs</h2>
                    </div>

                    {loading ? (
                        <div className="loading-state">
                            <span className="spinner"></span>
                            <p>Loading history...</p>
                        </div>
                    ) : error ? (
                        <div className="error-message">
                            <AlertTriangle size={16} />
                            <span>{error}</span>
                        </div>
                    ) : logs.length === 0 ? (
                        <div className="empty-state">
                            <Calendar size={48} />
                            <p>No verification history yet</p>
                        </div>
                    ) : (
                        <>
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Document Type</th>
                                        <th>Decision</th>
                                        <th>Override</th>
                                        <th>Reason</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log) => (
                                        <tr key={log.id}>
                                            <td>{formatDate(log.created_at)}</td>
                                            <td>
                                                <span className="badge badge-info">
                                                    {log.document_type?.toUpperCase() || 'Unknown'}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`badge badge-${log.officer_decision === 'APPROVE' ? 'success' : log.officer_decision === 'REJECT' ? 'error' : 'warning'}`}>
                                                    {getDecisionIcon(log.officer_decision)}
                                                    {log.officer_decision}
                                                </span>
                                            </td>
                                            <td>
                                                {log.was_overridden ? (
                                                    <span className="badge badge-warning">Yes</span>
                                                ) : (
                                                    <span className="text-muted">No</span>
                                                )}
                                            </td>
                                            <td className="text-muted">
                                                {log.override_reason || '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="pagination">
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                    >
                                        Previous
                                    </button>
                                    <span className="page-info">
                                        Page {page} of {totalPages}
                                    </span>
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                        disabled={page === totalPages}
                                    >
                                        Next
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
