import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, LogIn } from 'lucide-react';
import { FieldGroup, inputCls } from '../components/FieldGroup';
import isqLogo from '../assets/Logo ISQ SVG.svg';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api';

export function LoginPage() {
    const navigate = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSubmitting(true);

        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            if (res.ok) {
                navigate('/');
            } else {
                setError('Utilizador ou senha inválidos. Tente novamente.');
            }
        } catch {
            setError('Erro de conexão com o servidor.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background font-sans text-foreground flex flex-col">
            <div className="gradient-hero relative overflow-hidden flex-1 flex flex-col items-center justify-center">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/15 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

                <div className="relative w-full max-w-sm mx-auto px-6 py-20 flex flex-col items-center text-center">
                    <div className="relative mb-8">
                        <div className="absolute inset-0 bg-primary/20 rounded-full blur-2xl scale-150 pointer-events-none" />
                        <img
                            src={isqLogo}
                            alt="ISQ Logo"
                            className="relative w-20 h-20 drop-shadow-[0_0_24px_rgba(214,0,0,0.55)] animate-float"
                        />
                    </div>

                    <div className="inline-flex items-center gap-2 glass-card px-4 py-1.5 mb-5 text-xs text-muted-foreground uppercase tracking-widest font-semibold">
                        ISQ · Instituto de Soldadura e Qualidade
                    </div>

                    <h2 className="text-2xl font-black tracking-tight mb-2 leading-tight">
                        <span className="gradient-text">Acesso ao</span>
                        {' '}
                        <span className="text-foreground">Data-Platforms</span>
                    </h2>

                    <p className="text-sm text-muted-foreground font-light leading-relaxed mb-8">
                        Introduza as suas credenciais para continuar.
                    </p>

                    <form
                        onSubmit={handleSubmit}
                        className="glass-card border border-border w-full p-8 flex flex-col gap-5"
                    >
                        <FieldGroup icon={User} label="Utilizador">
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Usuário"
                                autoComplete="username"
                                required
                                className={inputCls}
                            />
                        </FieldGroup>

                        <FieldGroup icon={Lock} label="Senha">
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                autoComplete="current-password"
                                required
                                className={inputCls}
                            />
                        </FieldGroup>

                        {error && (
                            <p className="text-xs text-primary font-medium text-center -mt-1">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={submitting}
                            className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-primary-foreground font-semibold py-3 px-6 rounded-xl transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed mt-1"
                        >
                            <LogIn className="w-4 h-4" />
                            {submitting ? 'A entrar…' : 'Entrar'}
                        </button>
                    </form>
                </div>
            </div>

            <footer className="border-t border-border py-6">
                <div className="max-w-sm mx-auto px-6 flex items-center justify-center gap-3">
                    <img src={isqLogo} alt="ISQ" className="w-5 h-5 opacity-50" />
                    <span className="text-xs text-muted-foreground">
                        © ISQ — Instituto de Soldadura e Qualidade
                    </span>
                </div>
            </footer>
        </div>
    );
}

export default LoginPage;