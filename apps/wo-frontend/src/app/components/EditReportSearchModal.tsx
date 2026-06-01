import { Edit3, X, Hash, Building2, Wrench } from 'lucide-react';
import { Button } from '@data-platforms/ui-lib/ui';
import { inputCls } from './FieldGroup';

interface EditReportSearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    searchQuery: string;
    onSearchChange: (value: string) => void;
    performSearch: () => void;
    searchResults: any[];
    isSearching: boolean;
    onSelectReport: (id: number) => void;
}

export function EditReportSearchModal({
    isOpen,
    onClose,
    searchQuery,
    onSearchChange,
    performSearch,
    searchResults,
    isSearching,
    onSelectReport
}: EditReportSearchModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="glass-card w-full max-w-2xl max-h-[90vh] overflow-y-auto border-border shadow-2xl animate-in zoom-in-95 duration-200">
                <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-md border-b border-border p-6 flex items-center justify-between">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <Edit3 className="w-5 h-5 text-amber-500" />
                        Editar Relatório Existente
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-secondary rounded-full transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    <div className="space-y-4">
                        <p className="text-sm text-muted-foreground">
                            Busque por Número de SS, CSC, Número do Relatório ou Cliente.
                        </p>
                        <div className="flex gap-2">
                            <input
                                className={inputCls}
                                placeholder="Digite para buscar..."
                                value={searchQuery}
                                onChange={e => onSearchChange(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && performSearch()}
                                autoFocus
                            />
                            <Button variant="primary" onClick={performSearch} loading={isSearching}>
                                Buscar
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                        {searchResults.length > 0 ? (
                            searchResults.map((report) => (
                                <div
                                    key={report.id}
                                    className="flex items-center justify-between p-4 bg-secondary/30 rounded-xl border border-border hover:border-amber-500/50 hover:bg-secondary/50 transition-all group"
                                >
                                    <div className="space-y-1">
                                        <div className="font-bold flex items-center gap-2">
                                            <span className="text-foreground">{report.numero_relatorio || 'S/N'}</span>
                                            {report.revisao && <span className="bg-primary/20 text-primary text-[10px] px-1.5 py-0.5 rounded font-black tracking-wider uppercase">REV {report.revisao}</span>}
                                        </div>
                                        <div className="text-xs text-muted-foreground grid grid-cols-2 gap-x-4 gap-y-1">
                                            <span className="flex items-center gap-1"><Hash className="w-3 h-3" /> SS: {report.ss?.numero || report.equipamento?.ss?.numero || '-'}</span>
                                            <span className="flex items-center gap-1"><Building2 className="w-3 h-3" /> Cliente: {report.cliente?.nome || report.equipamento?.ss?.contrato?.cliente?.nome || '-'}</span>
                                            <span className="flex items-center gap-1 col-span-2"><Wrench className="w-3 h-3" /> Equp: {report.equipamento?.nome || '-'}</span>
                                        </div>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        onClick={() => onSelectReport(report.id)}
                                        className="group-hover:bg-amber-500 group-hover:text-white transition-colors"
                                    >
                                        Editar
                                    </Button>
                                </div>
                            ))
                        ) : searchQuery && !isSearching ? (
                            <div className="text-center py-8 text-muted-foreground">
                                Nenhum relatório encontrado para "{searchQuery}"
                            </div>
                        ) : null}
                    </div>
                </div>

                <div className="flex justify-end p-6 border-t border-border">
                    <Button variant="ghost" onClick={onClose}>Fechar</Button>
                </div>
            </div>
        </div>
    );
}
