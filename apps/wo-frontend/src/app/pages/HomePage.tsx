import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, FilePlus, ArrowRight, Edit3 } from 'lucide-react';
import { CreateReportModal } from '../components/CreateReportModal';
import { EditReportSearchModal } from '../components/EditReportSearchModal';
import isqLogo from '../assets/Logo ISQ SVG.svg';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api';

const cards = [
    {
        id: 'search',
        to: '/search',
        icon: Search,
        label: 'Pesquisar Documentos',
        description:
            'Busca semântica em relatórios de análise de falhas, inspeções e documentos técnicos do ISQ.',
        accent: 'from-primary/20 to-primary/5',
        border: 'border-primary/20 hover:border-primary/50',
        iconBg: 'bg-primary/15 border-primary/20 text-primary',
    },
    {
        id: 'edit',
        to: '/edit',
        icon: Edit3,
        label: 'Editar Relatório',
        description:
            'Pesquise e carregue um relatório existente para fazer alterações ou correções.',
        accent: 'from-amber-500/20 to-amber-500/5',
        border: 'border-amber-500/20 hover:border-amber-500/50',
        iconBg: 'bg-amber-500/15 border-amber-500/20 text-amber-500',
    },
    {
        id: 'create',
        icon: FilePlus,
        label: 'Criar Relatório',
        description:
            'Inicie um novo relatório preenchendo os dados básicos para começar a edição.',
        accent: 'from-accent/20 to-accent/5',
        border: 'border-accent/20 hover:border-accent/50',
        iconBg: 'bg-accent/15 border-accent/20 text-accent',
    },
];

export function HomePage() {
    const navigate = useNavigate();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    const [formData, setFormData] = useState({
        numero_relatorio: '',
        cliente: '',
        unidade: '',
        tipo_equipamento: '',
        tag: '',
        numero_ss: '',
        numero_contrato: '',
        csc: ''
    });

    const performSearch = async () => {
        if (!searchQuery.trim()) return;
        setIsSearching(true);
        try {
            const res = await fetch(`${API_BASE}/reports/search?q=${encodeURIComponent(searchQuery)}`);
            if (res.ok) {
                const data = await res.json();
                setSearchResults(data);
            }
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setIsSearching(false);
        }
    };

    const handleCreateReport = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            const res = await fetch(`${API_BASE}/reports`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...formData,
                    revisao: '0',
                    data: new Date().toLocaleDateString('pt-BR'),
                }),
            });

            if (res.ok) {
                const data = await res.json();
                navigate(`/edit/${data.id}`);
            } else {
                alert('Erro ao criar relatório. Tente novamente.');
            }
        } catch (err) {
            console.error(err);
            alert('Erro de conexão com o servidor.');
        } finally {
            setSubmitting(false);
        }
    };

    const updateField = (field: keyof typeof formData, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="min-h-screen bg-background font-sans text-foreground flex flex-col">

            {/* Hero */}
            <div className="gradient-hero relative overflow-hidden flex-1 flex flex-col items-center justify-center">
                {/* Glow orbs */}
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/15 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

                <div className="relative w-full max-w-4xl mx-auto px-6 py-20 flex flex-col items-center text-center">

                    {/* Logo */}
                    <div className="relative mb-8">
                        <div className="absolute inset-0 bg-primary/20 rounded-full blur-2xl scale-150 pointer-events-none" />
                        <img
                            src={isqLogo}
                            alt="ISQ Logo"
                            className="relative w-28 h-28 drop-shadow-[0_0_24px_rgba(214,0,0,0.55)] animate-float"
                        />
                    </div>

                    {/* Brand */}
                    <div className="inline-flex items-center gap-2 glass-card px-4 py-1.5 mb-5 text-xs text-muted-foreground uppercase tracking-widest font-semibold">
                        ISQ · Instituto de Soldadura e Qualidade
                    </div>

                    <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-4 leading-tight">
                        <span className="gradient-text">Plataforma de</span>
                        <br />
                        <span className="text-foreground">Gestão Técnica</span>
                    </h1>

                    <p className="text-lg text-muted-foreground max-w-xl font-light leading-relaxed mb-14">
                        Pesquise em documentos técnicos com busca semântica ou gerencie
                        seus relatórios diretamente pela plataforma.
                    </p>

                    {/* Navigation cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5 w-full">
                        {cards.map((card) => {
                            const { to, icon: Icon, label, description, accent, border, iconBg } = card;
                            const content = (
                                <>
                                    {/* Gradient glow */}
                                    <div className={`absolute inset-0 bg-gradient-to-br ${accent} opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none rounded-2xl`} />

                                    <div className="relative flex items-start justify-between">
                                        <div className={`flex items-center justify-center w-11 h-11 rounded-xl border ${iconBg}`}>
                                            <Icon className="w-5 h-5" />
                                        </div>
                                        <ArrowRight className="w-5 h-5 text-muted-foreground opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
                                    </div>

                                    <div className="relative space-y-1">
                                        <h2 className="text-lg font-bold text-foreground">
                                            {label}
                                        </h2>
                                        <p className="text-sm text-muted-foreground leading-relaxed">
                                            {description}
                                        </p>
                                    </div>
                                </>
                            );

                            if (card.id === 'create') {
                                return (
                                    <button
                                        key={card.id}
                                        onClick={() => setIsModalOpen(true)}
                                        className={`glass-card ${border} border group relative overflow-hidden p-7 text-left flex flex-col gap-4 hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300 w-full`}
                                    >
                                        {content}
                                    </button>
                                );
                            }

                            if (card.id === 'edit') {
                                return (
                                    <button
                                        key={card.id}
                                        onClick={() => setIsEditModalOpen(true)}
                                        className={`glass-card ${border} border group relative overflow-hidden p-7 text-left flex flex-col gap-4 hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300 w-full`}
                                    >
                                        {content}
                                    </button>
                                );
                            }

                            return (
                                <Link
                                    key={card.id}
                                    to={to || '#'}
                                    className={`glass-card ${border} border group relative overflow-hidden p-7 text-left flex flex-col gap-4 hover:scale-[1.02] hover:-translate-y-1 transition-all duration-300`}
                                >
                                    {content}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            </div>

            <CreateReportModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSubmit={handleCreateReport}
                formData={formData}
                updateField={updateField}
                submitting={submitting}
            />

            <EditReportSearchModal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                performSearch={performSearch}
                searchResults={searchResults}
                isSearching={isSearching}
                onSelectReport={(id) => navigate(`/edit/${id}`)}
            />

            {/* Footer */}
            <footer className="border-t border-border py-6">
                <div className="max-w-4xl mx-auto px-6 flex items-center justify-center gap-3">
                    <img src={isqLogo} alt="ISQ" className="w-5 h-5 opacity-50" />
                    <span className="text-xs text-muted-foreground">
                        © ISQ — Instituto de Soldadura e Qualidade
                    </span>
                </div>
            </footer>
        </div>
    );
}

export default HomePage;
