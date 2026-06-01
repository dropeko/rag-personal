import React from 'react';
import { FilePlus, X, Hash, Building2, Wrench, Tag } from 'lucide-react';
import { Button } from '@data-platforms/ui-lib/ui';
import { FieldGroup, inputCls } from './FieldGroup';

interface CreateReportModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (e: React.FormEvent) => void;
    formData: {
        numero_relatorio: string;
        cliente: string;
        unidade: string;
        tipo_equipamento: string;
        tag: string;
        numero_ss: string;
        numero_contrato: string;
        csc: string;
    };
    updateField: (field: any, value: string) => void;
    submitting: boolean;
}

export function CreateReportModal({
    isOpen,
    onClose,
    onSubmit,
    formData,
    updateField,
    submitting
}: CreateReportModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="glass-card w-full max-w-2xl max-h-[90vh] overflow-y-auto border-border shadow-2xl animate-in zoom-in-95 duration-200">
                <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-md border-b border-border p-6 flex items-center justify-between">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <FilePlus className="w-5 h-5 text-primary" />
                        Novo Relatório
                    </h2>
                    <button onClick={onClose} className="p-2 hover:bg-secondary rounded-full transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={onSubmit} className="p-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <FieldGroup icon={Hash} label="Número do Relatório">
                            <input required className={inputCls} placeholder="Ex: ISQ-AF-2024-..." value={formData.numero_relatorio} onChange={e => updateField('numero_relatorio', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Building2} label="Cliente">
                            <input required className={inputCls} placeholder="Nome do cliente" value={formData.cliente} onChange={e => updateField('cliente', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Building2} label="Unidade">
                            <input required className={inputCls} placeholder="Unidade/Planta" value={formData.unidade} onChange={e => updateField('unidade', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Wrench} label="Tipo de Equipamento">
                            <input required className={inputCls} placeholder="Ex: Trocador de Calor" value={formData.tipo_equipamento} onChange={e => updateField('tipo_equipamento', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Tag} label="TAG">
                            <input required className={inputCls} placeholder="Tag do equipamento" value={formData.tag} onChange={e => updateField('tag', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Hash} label="Número SS">
                            <input required className={inputCls} placeholder="Nº da Solicitação" value={formData.numero_ss} onChange={e => updateField('numero_ss', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Tag} label="CSC">
                            <input required className={inputCls} placeholder="Controle de Serviço" value={formData.csc} onChange={e => updateField('csc', e.target.value)} />
                        </FieldGroup>
                        <FieldGroup icon={Hash} label="Nº Contrato">
                            <input required className={inputCls} placeholder="Número do contrato" value={formData.numero_contrato} onChange={e => updateField('numero_contrato', e.target.value)} />
                        </FieldGroup>
                    </div>

                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancelar</Button>
                        <Button type="submit" variant="primary" loading={submitting}>Criar e Editar</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
