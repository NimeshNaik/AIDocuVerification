import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Mail, Lock, AlertCircle } from 'lucide-react';
import './Login.css';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { signIn } = useAuth();
    const navigate = useNavigate();

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await signIn(email, password);
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Failed to sign in');
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <div className="login-logo">
                        <Shield size={40} />
                    </div>
                    <h1>Document Verification</h1>
                    <p>Government of India</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {error && (
                        <div className="error-message">
                            <AlertCircle size={16} />
                            <span>{error}</span>
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <div className="input-wrapper">
                            <Mail size={18} className="input-icon" />
                            <input
                                type="email"
                                className="form-input with-icon"
                                placeholder="officer@gov.in"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <div className="input-wrapper">
                            <Lock size={18} className="input-icon" />
                            <input
                                type="password"
                                className="form-input with-icon"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? <span className="spinner"></span> : 'Sign In'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Don't have an account? <Link to="/signup">Register</Link></p>
                </div>
            </div>

            <div className="login-branding">
                <p>Secure Document Verification Platform</p>
            </div>
        </div>
    );
}
