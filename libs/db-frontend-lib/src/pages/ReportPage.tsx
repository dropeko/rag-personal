import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, ReportResult } from '../api';
import { ArrowLeft, Calendar, User, MapPin, Hash, FileText, BookOpen, FileDown, ChevronDown } from 'lucide-react';
import isqLogo from '../assets/Logo ISQ SVG.svg';
import { InfoItem, LoadingSpinner } from '@data-platforms/ui-lib/ui';

export function ReportPage() {
    const { id } = useParams<{ id: string }>();
    const [data, setData] = useState<ReportResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [pdfOpen, setPdfOpen] = useState(false);
    const [pdfLoaded, setPdfLoaded] = useState(false);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            api.getReport(id)
                .then(setData)
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [id]);

    if (loading) {
        return <LoadingSpinner fullScreen message="Carregando documento..." />;
    }

    if (!data || data.ids.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="text-center max-w-md px-6">
                    <div className="glass-card w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                        <FileText className="w-9 h-9 text-muted-foreground" />
                    </div>
                    <h2 className="text-2xl font-bold text-foreground mb-2">Relatório não encontrado</h2>
                    <p className="text-muted-foreground mb-6">Não conseguimos localizar o relatório solicitado.</p>
                    <Link
                        to="/"
                        className="inline-flex items-center gap-2 text-primary font-medium hover:text-accent transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Voltar para busca
                    </Link>
                </div>
            </div>
        );
    }

    const reportMeta = data.metadatas[0];

    const sections: Record<string, string> = {};
    data.metadatas.forEach((meta, idx) => {
        if (meta.secao) {
            sections[meta.secao] = data.documents[idx];
        }
    });

    const sortedSections = Object.entries(sections).sort((a, b) => {
        const order = ['INTRODUÇÃO', 'OBJETIVO', 'METODOLOGIA', 'RESULTADOS', 'DISCUSSÃO', 'CONCLUSÃO', 'RECOMENDAÇÕES'];
        const getIndex = (s: string) => {
            const found = order.findIndex(k => s.toUpperCase().includes(k));
            return found === -1 ? 99 : found;
        };
        return getIndex(a[0]) - getIndex(b[0]);
    });

    return (
        <div className="min-h-screen bg-background pb-20">
            {/* Sticky Navbar */}
            <div className="sticky top-0 z-10 backdrop-blur-md bg-background/80 border-b border-border">
                <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
                    <Link
                        to="/"
                        className="inline-flex items-center text-muted-foreground hover:text-primary transition-colors group text-sm font-medium"
                    >
                        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                        Voltar para resultados
                    </Link>
                    {/* Logo no navbar */}
                    <img src={isqLogo} alt="ISQ" className="w-7 h-7 opacity-80" />
                </div>
            </div>

            <div className="max-w-5xl mx-auto px-6 py-8">
                {/* Header Card */}
                <div className="glass-card overflow-hidden mb-8">
                    <div className="relative overflow-hidden" style={{
                        background: 'linear-gradient(160deg, #fff0f0 0%, #ffe0e0 40%, #ffffff 100%)'
                    }}>
                        <div className="absolute -top-10 -right-10 w-64 h-64 bg-primary/20 rounded-full blur-3xl pointer-events-none" />

                        <div className="relative p-8 md:p-10">
                            <div className="flex items-start justify-between gap-6">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
                                        <BookOpen className="w-4 h-4 text-primary" />
                                        <span>Relatório Técnico</span>
                                    </div>
                                    <h1 className="text-3xl md:text-4xl font-black tracking-tight text-gray-900 mb-2">
                                        {reportMeta.numero_relatorio}
                                    </h1>
                                    <p className="text-gray-500 text-lg font-light max-w-2xl">
                                        {reportMeta.arquivo}
                                    </p>
                                </div>
                                {/* Logo no header do relatório */}
                                <div className="relative shrink-0">
                                    <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl" />
                                    <img
                                        src={isqLogo}
                                        alt="ISQ"
                                        className="relative w-16 h-16 drop-shadow-[0_0_15px_rgba(214,0,0,0.5)]"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Info strip */}
                    <div className="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-border">
                        <InfoItem icon={<Calendar className="w-4 h-4" />} label="Data" value={reportMeta.data} />
                        <InfoItem icon={<User className="w-4 h-4" />} label="Cliente" value={reportMeta.cliente} />
                        <InfoItem icon={<MapPin className="w-4 h-4" />} label="Unidade" value={reportMeta.unidade} />
                        <InfoItem icon={<Hash className="w-4 h-4" />} label="Tag" value={reportMeta.tag} />
                    </div>
                </div>

                {/* PDF Viewer Section */}
                <section className="glass-card overflow-hidden mb-8">
                    <button
                        onClick={() => {
                            if (!pdfUrl && id) {
                                setPdfUrl(api.getPdfUrl(id));
                            }
                            setPdfOpen(prev => !prev);
                        }}
                        className="w-full flex items-center justify-between p-8 text-left group relative overflow-hidden"
                    >
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-2xl opacity-70" />

                        <div className="flex items-center gap-4 pl-2">
                            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary/15 border border-primary/20 text-primary">
                                <FileDown className="w-5 h-5" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-foreground tracking-tight">Documento Original</h2>
                                <p className="text-sm text-muted-foreground mt-0.5">
                                    {pdfOpen ? 'Clique para fechar o PDF' : 'Clique para visualizar o PDF do relatório'}
                                </p>
                            </div>
                        </div>

                        <ChevronDown
                            className={`w-5 h-5 text-muted-foreground transition-transform duration-300 ${pdfOpen ? 'rotate-180' : ''}`}
                        />
                    </button>

                    {pdfOpen && (
                        <div className="relative border-t border-border">
                            {!pdfLoaded && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-background/80 z-10">
                                    <LoadingSpinner size="md" message="A carregar PDF..." />
                                </div>
                            )}
                            <iframe
                                key={pdfUrl}
                                src={pdfUrl ?? undefined}
                                title="Documento PDF"
                                className="w-full"
                                style={{ height: '80vh' }}
                                onLoad={() => setPdfLoaded(true)}
                            />
                        </div>
                    )}
                </section>

                <div className="space-y-6">
                    {sortedSections.map(([title, content], idx) => (
                        <section
                            key={idx}
                            className="glass-card glass-card-hover p-8 scroll-mt-24 relative overflow-hidden"
                            id={`section-${idx}`}
                        >
                            <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-2xl opacity-70" />

                            <div className="flex items-center gap-4 mb-6 pb-4 border-b border-border">
                                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary/15 text-primary text-sm font-bold shrink-0 border border-primary/20">
                                    {idx + 1}
                                </div>
                                <h2 className="text-2xl font-bold text-foreground tracking-tight">
                                    {title}
                                </h2>
                            </div>

                            <div className="pl-12 text-muted-foreground leading-relaxed font-serif text-lg space-y-4">
                                {content.split('\n').map((paragraph, pIdx) =>
                                    paragraph.trim() ? <p key={pIdx}>{paragraph}</p> : null
                                )}
                            </div>
                        </section>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default ReportPage;
