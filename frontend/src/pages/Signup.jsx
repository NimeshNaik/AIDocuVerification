import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Mail, Lock, User, Building, AlertCircle } from 'lucide-react';
import './Login.css';

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [department, setDepartment] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { signUp } = useAuth();
    const navigate = useNavigate();

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await signUp(email, password, fullName, department);
            navigate('/dashboard');
        } catch (err) {
            setError(err.message || 'Failed to create account');
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
                    <h1>Create Account</h1>
                    <p>Register as Verification Officer</p>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    {error && (
                        <div className="error-message">
                            <AlertCircle size={16} />
                            <span>{error}</span>
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Full Name</label>
                        <div className="input-wrapper">
                            <User size={18} className="input-icon" />
                            <input
                                type="text"
                                className="form-input with-icon"
                                placeholder="Your full name"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                required
                            />
                        </div>
                    </div>

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
                        <label className="form-label">Department (Optional)</label>
                        <div className="input-wrapper">
                            <Building size={18} className="input-icon" />
                            <input
                                type="text"
                                className="form-input with-icon"
                                placeholder="e.g., Revenue Department"
                                value={department}
                                onChange={(e) => setDepartment(e.target.value)}
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
                                placeholder="Minimum 6 characters"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                minLength={6}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary btn-lg w-full"
                        disabled={loading}
                    >
                        {loading ? <span className="spinner"></span> : 'Create Account'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Already have an account? <Link to="/login">Sign In</Link></p>
                </div>
            </div>

            <div className="login-branding">
                <p>Secure Document Verification Platform</p>
            </div>
        </div>
    );
}
