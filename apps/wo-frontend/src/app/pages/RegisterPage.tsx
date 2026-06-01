import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, User, Mail, Phone, Briefcase, Lock } from 'lucide-react';
import { FieldGroup, inputCls } from '../components/FieldGroup';
import isqLogo from '../assets/Logo ISQ SVG.svg';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api';

interface RegisterForm {
    name: string;
    email: string;
    phone: string;
    position: string;
    password: string;
}

const INITIAL_FORM: RegisterForm = {
    name: '',
    email: '',
    phone: '',
    position: '',
    password: '',
};

export function RegisterPage() {
    const navigate = useNavigate();
    const [form, setForm] = useState<RegisterForm>(INITIAL_FORM);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateField = (field: keyof RegisterForm, value: string) => {
        setForm(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSubmitting(true);

        try {
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });

            if (res.ok) {
                navigate('/login');
            } else {
                const data = await res.json().catch(() => null);
                setError(data?.message ?? 'Erro ao criar conta. Tente novamente.');
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

                <div className="relative w-full max-w-sm mx-auto px-6 py-16 flex flex-col items-center text-center">
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
                        <span className="gradient-text">Criar</span>
                        {' '}
                        <span className="text-foreground">Conta</span>
                    </h2>

                    <p className="text-sm text-muted-foreground font-light leading-relaxed mb-4">
                        Preencha os dados abaixo para solicitar acesso à plataforma.
                    </p>

                    <form
                        onSubmit={handleSubmit}
                        className="glass-card border border-border w-full p-8 flex flex-col gap-5"
                    >
                        <FieldGroup icon={User} label="Nome">
                            <input
                                type="text"
                                value={form.name}
                                onChange={(e) => updateField('name', e.target.value)}
                                placeholder="Nome completo"
                                autoComplete="name"
                                required
                                className={inputCls}
                            />
                        </FieldGroup>

                        <FieldGroup icon={Mail} label="Email">
                            <input
                                type="email"
                                value={form.email}
                                onChange={(e) => updateField('email', e.target.value)}
                                placeholder="nome@isqbrasil.com.br"
                                autoComplete="email"
                                required
                                className={inputCls}
                            />
                        </FieldGroup>

                        <FieldGroup icon={Lock} label="Senha">
                            <input
                                type="password"
                                value={form.password}
                                onChange={(e) => updateField('password', e.target.value)}
                                placeholder="Mínimo 8 caracteres"
                                autoComplete="new-password"
                                required
                                minLength={8}
                                className={inputCls}
                            />
                        </FieldGroup>

                        <FieldGroup icon={Phone} label="Telefone">
                            <input
                                type="tel"
                                value={form.phone}
                                onChange={(e) => updateField('phone', e.target.value)}
                                placeholder="+55 11 9000 0000"
                                autoComplete="tel"
                                className={inputCls}
                            />
                        </FieldGroup>

                        <FieldGroup icon={Briefcase} label="Cargo">
                            <input
                                type="text"
                                value={form.position}
                                onChange={(e) => updateField('position', e.target.value)}
                                placeholder="Ex: Inspetor, Engenheiro…"
                                autoComplete="organization-title"
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
                            <UserPlus className="w-4 h-4" />
                            {submitting ? 'A registar…' : 'Criar conta'}
                        </button>

                        <p className="text-xs text-muted-foreground text-center">
                            Já tem conta?{' '}
                            <Link to="/login" className="text-primary font-semibold hover:underline">
                                Entrar
                            </Link>
                        </p>
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

export default RegisterPage;