import { useState } from 'react';
import { api, SearchResult } from '../api';
import { Search, FileText, ArrowRight, Database } from 'lucide-react';
import { Link } from 'react-router-dom';
import isqLogo from '../assets/Logo ISQ SVG.svg';
import { Badge, LoadingSpinner, Button } from '@data-platforms/ui-lib/ui';

export function SearchPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setHasSearched(true);

        try {
            const data = await api.search(query);
            setResults(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background font-sans text-foreground">
            {/* Hero Section */}
            <div className="gradient-hero relative overflow-hidden">
                {/* Decorative glow orbs */}
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

                <div className="relative max-w-5xl mx-auto px-6 py-16 text-center">
                    {/* ISQ Logo em destaque */}
                    <div className="flex justify-center mb-8">
                        <div className="relative">
                            <div className="absolute inset-0 bg-primary/20 rounded-full blur-2xl scale-150" />
                            <img
                                src={isqLogo}
                                alt="ISQ Logo"
                                className="relative w-24 h-24 drop-shadow-[0_0_20px_rgba(214,0,0,0.6)] animate-float"
                            />
                        </div>
                    </div>

                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 glass-card px-4 py-2 mb-6 text-sm text-muted-foreground">
                        <Database className="w-4 h-4 text-primary" />
                        <span>Busca semântica em documentos técnicos</span>
                    </div>

                    <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-3">
                        <span className="gradient-text">Base de Conhecimento</span>
                    </h1>
                    <p className="text-lg text-muted-foreground mb-10 max-w-2xl mx-auto font-light">
                        Pesquise em relatórios de análise de falhas, inspeções e documentos técnicos.
                    </p>

                    {/* Search Bar */}
                    <form onSubmit={handleSearch} className="max-w-2xl mx-auto relative group">
                        <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                            <Search className="w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                        </div>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.currentTarget.value)}
                            placeholder="O que você está procurando?"
                            disabled={loading}
                            className="w-full bg-card/80 backdrop-blur-xl pl-5 pr-36 py-5 rounded-2xl border border-border text-foreground placeholder:text-muted-foreground outline-none transition-all duration-300 glow-ring focus:glow-ring-focus disabled:opacity-70 disabled:cursor-not-allowed"
                        />
                        <Button
                            type="submit"
                            variant="primary"
                            loading={loading}
                            className="absolute right-2 top-2 bottom-2 px-6 rounded-xl text-gray-100"
                        >
                            <Search className="w-4 h-4" />
                            Buscar
                        </Button>
                    </form>
                </div>
            </div>

            {/* ISQ branding strip */}
            <div className="bg-primary/10 border-y border-primary/20 py-2">
                <div className="max-w-5xl mx-auto px-6 flex items-center justify-center gap-3">
                    <img src={isqLogo} alt="ISQ" className="w-5 h-5 opacity-70" />
                    <span className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">
                        ISQ · Instituto de Soldadura e Qualidade
                    </span>
                </div>
            </div>

            {/* Results Section */}
            <div className="max-w-5xl mx-auto px-6 py-12">
                {loading && (
                    <LoadingSpinner message="Buscando resultados..." />
                )}

                {!loading && hasSearched && (!results || results.ids.length === 0 || results.ids[0].length === 0) && (
                    <div className="text-center py-20">
                        <div className="glass-card w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse-glow">
                            <Search className="w-9 h-9 text-muted-foreground" />
                        </div>
                        <h3 className="text-2xl font-bold text-foreground mb-2">Nenhum resultado encontrado</h3>
                        <p className="text-muted-foreground">Tente refinar sua busca com outros termos.</p>
                    </div>
                )}

                {!loading && results && results.ids[0]?.length > 0 && (
                    <div className="mb-6 flex items-center gap-3">
                        <div className="w-1 h-5 bg-primary rounded-full" />
                        <p className="text-sm text-muted-foreground">
                            <span className="font-semibold text-foreground">{results.ids[0].length}</span> resultados encontrados
                        </p>
                    </div>
                )}

                <div className="grid gap-5">
                    {!loading && results?.ids[0]?.map((id, index) => {
                        const metadata = results.metadatas[0][index];
                        const document = results.documents[0][index];
                        const distance = results.distances[0][index];
                        const relevance = Math.round((1 - distance) * 100);

                        const barColor =
                            relevance >= 80 ? 'bg-primary' :
                                relevance >= 60 ? 'bg-accent' :
                                    'bg-muted-foreground';

                        return (
                            <article
                                key={`${id}-${index}`}
                                className="glass-card glass-card-hover group relative overflow-hidden hover:scale-[1.01] hover:-translate-y-0.5 transition-all duration-300"
                            >
                                {/* Left accent bar */}
                                <div className={`absolute left-0 top-0 bottom-0 w-1 ${barColor} rounded-l-2xl`} />

                                <div className="p-6 pl-7">
                                    <div className="flex items-start justify-between mb-3 gap-4">
                                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                            <FileText className="w-4 h-4 text-primary" />
                                            <span className="font-semibold text-foreground">
                                                {metadata.numero_relatorio || 'Relatório sem ID'}
                                            </span>
                                            <span className="text-border">•</span>
                                            <span>{metadata.data}</span>
                                        </div>

                                        <div className="flex items-center gap-3 shrink-0">
                                            <div className="text-xs font-bold uppercase tracking-wider text-primary">
                                                {relevance}%
                                            </div>
                                            <div className="w-16 h-1.5 bg-secondary rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${barColor} rounded-full transition-all duration-500`}
                                                    style={{ width: `${relevance}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <Link
                                        to={`/report/${metadata.id_relatorio}`}
                                        className="block group-hover:text-primary transition-colors duration-200"
                                    >
                                        <h2 className="text-xl font-bold text-foreground mb-3 flex items-center gap-2">
                                            {metadata.secao ? metadata.secao : 'Trecho do Relatório'}
                                            <ArrowRight className="w-4 h-4 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all duration-300 text-primary" />
                                        </h2>
                                    </Link>

                                    <p className="text-muted-foreground leading-relaxed line-clamp-3 mb-4 font-serif text-lg">
                                        "{document}"
                                    </p>

                                    <div className="flex flex-wrap gap-2">
                                        <Badge label={metadata.cliente} />
                                        <Badge label={metadata.unidade} />
                                    </div>
                                </div>
                            </article>
                        );
                    })}
                </div>
            </div>

            {/* Footer */}
            <footer className="border-t border-border py-8 mt-8">
                <div className="max-w-5xl mx-auto px-6 flex items-center justify-center gap-3">
                    <img src={isqLogo} alt="ISQ" className="w-6 h-6 opacity-60" />
                    <span className="text-xs text-muted-foreground">
                        © ISQ — Instituto de Soldadura e Qualidade
                    </span>
                </div>
            </footer>
        </div>
    );
}

export default SearchPage;
