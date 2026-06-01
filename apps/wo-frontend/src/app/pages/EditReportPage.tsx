import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Plus, Trash2, FileText, ArrowLeft, AlignLeft, Tag,
    User, Building2, Hash, Wrench, CalendarDays, CheckSquare,
    Loader2, Beaker, Save, Download, Upload, Image as ImageIcon
} from 'lucide-react';
import { useParams } from 'react-router-dom';
import { Button } from '@data-platforms/ui-lib/ui';
import { FieldGroup, inputCls } from '../components/FieldGroup';
import isqLogo from '../assets/Logo ISQ SVG.svg';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3000/api';

interface Section {
    id: string;
    title: string;
    content: string;
}

interface Imagem {
    id: string;
    caminho_imagem: string;
    legenda: string;
}

interface Ensaio {
    id: string;
    tipo: string;
    qnt_amostras: number;
    texto: string;
    imagens: Imagem[];
}

function generateId() {
    return Math.random().toString(36).slice(2, 9);
}



export function EditReportPage() {
    const { id: urlId } = useParams<{ id: string }>();
    const [currentReportId, setCurrentReportId] = useState<number | null>(urlId ? parseInt(urlId) : null);

    // Metadata
    const [meta, setMeta] = useState({
        numero_relatorio: '',
        revisao: '0',
        cliente: '',
        data: new Date().toLocaleDateString('pt-BR'),
        unidade: '',
        tipo_equipamento: '',
        tag: '',
        numero_ss: '',
        numero_contrato: '',
        csc: '',
        elaboracao_nome: '',
        elaboracao_cargo: '',
        aprovacao_nome: '',
        aprovacao_cargo: '',
    });

    const [sections, setSections] = useState<Section[]>([
        { id: generateId(), title: '', content: '' },
    ]);

    const [ensaios, setEnsaios] = useState<Ensaio[]>([]);

    const [submitting, setSubmitting] = useState(false);

    const updateMeta = (field: keyof typeof meta, value: string) =>
        setMeta(prev => ({ ...prev, [field]: value }));

    const addSection = () => setSections(prev => [...prev, { id: generateId(), title: '', content: '' }]);
    const removeSection = (id: string) => setSections(prev => prev.filter(s => s.id !== id));
    const updateSection = (id: string, field: 'title' | 'content', value: string) =>
        setSections(prev => prev.map(s => s.id === id ? { ...s, [field]: value } : s));

    const addEnsaio = () => setEnsaios(prev => [...prev, { id: generateId(), tipo: '', qnt_amostras: 0, texto: '', imagens: [] }]);
    const removeEnsaio = (id: string) => setEnsaios(prev => prev.filter(e => e.id !== id));
    const updateEnsaio = (id: string, field: 'tipo' | 'texto' | 'qnt_amostras', value: string | number) =>
        setEnsaios(prev => prev.map(e => e.id === id ? { ...e, [field]: value } : e));

    const addImagemToEnsaio = (ensaioId: string) => {
        setEnsaios(prev => prev.map(e => {
            if (e.id === ensaioId) {
                return { ...e, imagens: [...e.imagens, { id: generateId(), caminho_imagem: '', legenda: '' }] };
            }
            return e;
        }));
    };

    const removeImagemFromEnsaio = (ensaioId: string, imagemId: string) => {
        setEnsaios(prev => prev.map(e => {
            if (e.id === ensaioId) {
                return { ...e, imagens: e.imagens.filter(img => img.id !== imagemId) };
            }
            return e;
        }));
    };

    const updateImagemInEnsaio = (ensaioId: string, imagemId: string, field: keyof Imagem, value: string) => {
        setEnsaios(prev => prev.map(e => {
            if (e.id === ensaioId) {
                return {
                    ...e,
                    imagens: e.imagens.map(img => img.id === imagemId ? { ...img, [field]: value } : img)
                };
            }
            return e;
        }));
    };

    const handleFileUpload = async (ensaioId: string, imagemId: string, file: File) => {
        if (!currentReportId) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch(`${API_BASE}/reports/upload/${currentReportId}`, {
                method: 'POST',
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                const serverUrl = API_BASE.replace('/api', '');
                updateImagemInEnsaio(ensaioId, imagemId, 'caminho_imagem', `${serverUrl}${data.url}`);
            } else {
                alert('Erro ao fazer upload da imagem.');
            }
        } catch (err) {
            console.error('Upload failed:', err);
            alert('Falha na conexão ao enviar imagem.');
        }
    };

    useEffect(() => {
        const fetchReport = async (id: number) => {
            try {
                const res = await fetch(`${API_BASE}/reports/${id}`);
                if (res.ok) {
                    const data = await res.json();
                    loadReport(data);
                }
            } catch (err) {
                console.error('Failed to fetch report:', err);
            }
        };

        if (urlId) {
            const id = parseInt(urlId);
            if (!isNaN(id)) {
                fetchReport(id);
            }
        }
    }, [urlId]);

    const loadReport = (report: any) => {
        const equipamento = report.equipamento;
        const ss = equipamento?.ss;
        const contrato = ss?.contrato;
        const cliente = contrato?.cliente;

        setCurrentReportId(report.id);
        setMeta({
            numero_relatorio: report.numero_relatorio || '',
            revisao: report.revisao || '0',
            cliente: cliente?.nome || '',
            data: report.data || new Date().toLocaleDateString('pt-BR'),
            unidade: cliente?.unidades?.[0]?.nome || '',
            tipo_equipamento: equipamento?.nome || '',
            tag: equipamento?.dados || '',
            numero_ss: ss?.numero || '',
            numero_contrato: contrato?.numero || '',
            csc: ss?.csc || '',
            elaboracao_nome: report.elaboracao_nome || '',
            elaboracao_cargo: report.elaboracao_cargo || '',
            aprovacao_nome: report.aprovacao_nome || '',
            aprovacao_cargo: report.aprovacao_cargo || '',
        });

        if (report.secoes && report.secoes.length > 0) {
            setSections(report.secoes.map((s: { nome: string; conteudo: string }) => ({
                id: generateId(),
                title: s.nome,
                content: s.conteudo
            })));
        } else {
            setSections([{ id: generateId(), title: '', content: '' }]);
        }

        if (report.equipamento?.ensaios) {
            setEnsaios(report.equipamento.ensaios.map((e: { tipo: string; qnt_amostras?: number; texto: string; imagens?: any[] }) => ({
                id: generateId(),
                tipo: e.tipo,
                qnt_amostras: e.qnt_amostras || 0,
                texto: e.texto,
                imagens: e.imagens?.map((img: { caminho_imagem: string; legenda?: string }) => ({
                    id: generateId(),
                    caminho_imagem: img.caminho_imagem,
                    legenda: img.legenda || ''
                })) || []
            })));
        } else {
            setEnsaios([]);
        }
    };

    const handleSave = async () => {
        setSubmitting(true);
        try {
            const payload = {
                id: currentReportId,
                ...meta,
                sections: sections.map(s => ({ titulo: s.title, content: s.content })),
                ensaios: ensaios.map(e => ({
                    tipo: e.tipo,
                    qnt_amostras: Number(e.qnt_amostras),
                    texto: e.texto,
                    imagens: e.imagens.map(img => ({
                        caminho_imagem: img.caminho_imagem,
                        legenda: img.legenda
                    }))
                }))
            };

            const saveRes = await fetch(`${API_BASE}/reports`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!saveRes.ok) throw new Error('Failed to save to database');
            alert('Relatório salvo com sucesso!');
        } catch (err) {
            console.error('Failed to save report:', err);
            alert('Erro ao salvar o relatório.');
        } finally {
            setSubmitting(false);
        }
    };

    const handleExport = async () => {
        setSubmitting(true);
        try {
            const payload = {
                id: currentReportId,
                ...meta,
                sections: sections.map(s => ({ titulo: s.title, content: s.content })),
                ensaios: ensaios.map(e => ({
                    tipo: e.tipo,
                    qnt_amostras: Number(e.qnt_amostras),
                    texto: e.texto,
                    imagens: e.imagens.map(img => ({
                        caminho_imagem: img.caminho_imagem,
                        legenda: img.legenda
                    }))
                }))
            };

            const res = await fetch(`${API_BASE}/report/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error(`Server error: ${res.status}`);

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${meta.numero_relatorio || 'relatorio'}.docx`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to generate report:', err);
            alert('Erro ao gerar o relatório. Verifique o backend.');
        } finally {
            setSubmitting(false);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleSave();
    };

    return (
        <div className="min-h-screen bg-background font-sans text-foreground pb-20">
            {/* Sticky Navbar */}
            <div className="sticky top-0 z-10 backdrop-blur-md bg-background/80 border-b border-border">
                <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
                    <Link to="/" className="inline-flex items-center text-muted-foreground hover:text-primary transition-colors group text-sm font-medium">
                        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
                        Voltar
                    </Link>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <FileText className="w-4 h-4 text-primary" />
                        <span className="font-semibold text-foreground">
                            {`Editando Relatório: ${meta.numero_relatorio}`}
                        </span>
                    </div>
                    <img src={isqLogo} alt="ISQ" className="w-7 h-7 opacity-80" />
                </div>
            </div>

            <div className="gradient-hero relative overflow-hidden">
                <div className="absolute top-0 left-1/4 w-96 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
                <div className="relative max-w-4xl mx-auto px-6 py-10 text-center">
                    <h1 className="text-4xl font-black tracking-tight">
                        <span className="gradient-text">Gerenciar Relatório</span>
                    </h1>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-6 py-4 space-y-8">
                {currentReportId ? (
                    <form onSubmit={handleSubmit} className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {/* ── Metadados ─────────────────────────────────────── */}
                        <div className="glass-card p-6 space-y-5">
                            <h2 className="font-bold text-foreground flex items-center gap-2">
                                <Hash className="w-4 h-4 text-primary" />
                                Dados do Relatório
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <FieldGroup icon={Hash} label="Número do Relatório">
                                    <input className={inputCls} value={meta.numero_relatorio} onChange={e => updateMeta('numero_relatorio', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Hash} label="Revisão">
                                    <input className={inputCls} value={meta.revisao} onChange={e => updateMeta('revisao', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Building2} label="Cliente">
                                    <input className={inputCls} value={meta.cliente} onChange={e => updateMeta('cliente', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={CalendarDays} label="Data">
                                    <input className={inputCls} value={meta.data} onChange={e => updateMeta('data', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Building2} label="Unidade">
                                    <input className={inputCls} value={meta.unidade} onChange={e => updateMeta('unidade', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Wrench} label="Tipo de Equipamento">
                                    <input className={inputCls} value={meta.tipo_equipamento} onChange={e => updateMeta('tipo_equipamento', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Tag} label="TAG">
                                    <input className={inputCls} value={meta.tag} onChange={e => updateMeta('tag', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Hash} label="Número SS">
                                    <input className={inputCls} value={meta.numero_ss} onChange={e => updateMeta('numero_ss', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Hash} label="Nº Contrato" >
                                    <input className={inputCls} value={meta.numero_contrato} onChange={e => updateMeta('numero_contrato', e.currentTarget.value)} />
                                </FieldGroup>
                                <FieldGroup icon={Tag} label="CSC">
                                    <input className={inputCls} value={meta.csc} onChange={e => updateMeta('csc', e.currentTarget.value)} />
                                </FieldGroup>
                            </div>
                        </div>

                        {/* ── Ensaios ───────────────────────────────────────── */}
                        <div className="space-y-4">
                            <h2 className="font-bold text-foreground flex items-center gap-2 px-1">
                                <Beaker className="w-4 h-4 text-primary" />
                                Ensaios do Equipamento
                            </h2>

                            {ensaios.map((ensaio, index) => (
                                <div key={ensaio.id} className="glass-card relative overflow-hidden group">
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-amber-500 rounded-l-2xl opacity-70" />
                                    <div className="p-6 pl-7 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                                <span className="font-medium text-foreground">Ensaio {index + 1}</span>
                                            </div>
                                            <button type="button" onClick={() => removeEnsaio(ensaio.id)}
                                                className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-all duration-200 opacity-0 group-hover:opacity-100">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <FieldGroup icon={Tag} label="Tipo de Ensaio">
                                                <input type="text" value={ensaio.tipo}
                                                    onChange={e => updateEnsaio(ensaio.id, 'tipo', e.currentTarget.value)}
                                                    placeholder="Ex: Inspeção Visual, Ultrassom..."
                                                    className={inputCls + ' font-medium'} />
                                            </FieldGroup>
                                            <FieldGroup icon={Hash} label="Qtd. Amostras">
                                                <input type="number" value={ensaio.qnt_amostras}
                                                    onChange={e => updateEnsaio(ensaio.id, 'qnt_amostras', parseInt(e.currentTarget.value) || 0)}
                                                    className={inputCls + ' font-medium'} />
                                            </FieldGroup>
                                        </div>
                                        <FieldGroup icon={AlignLeft} label="Detalhes/Texto">
                                            <textarea value={ensaio.texto}
                                                onChange={e => updateEnsaio(ensaio.id, 'texto', e.currentTarget.value)}
                                                placeholder="Detalhes do ensaio..."
                                                rows={2}
                                                className={inputCls + ' font-serif leading-relaxed resize-y'} />
                                        </FieldGroup>

                                        {/* Imagens do Ensaio */}
                                        <div className="pt-2 border-t border-border mt-4 space-y-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                                    Imagens do Ensaio
                                                </span>
                                                <Button variant="ghost" type="button" onClick={() => addImagemToEnsaio(ensaio.id)} className="h-7 text-xs px-2">
                                                    <Plus className="w-3 h-3 mr-1" /> Adicionar Imagem
                                                </Button>
                                            </div>
                                            {ensaio.imagens.map((img, imgIndex) => (
                                                <div key={img.id} className="flex flex-col sm:flex-row gap-2 bg-secondary/20 p-3 rounded-xl border border-border">
                                                    <div className="flex-1 space-y-3">
                                                        <div className="flex items-center gap-3">
                                                            {img.caminho_imagem ? (
                                                                <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-border bg-secondary/30">
                                                                    <img src={img.caminho_imagem} alt="Preview" className="w-full h-full object-cover" />
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => updateImagemInEnsaio(ensaio.id, img.id, 'caminho_imagem', '')}
                                                                        className="absolute top-1 right-1 p-1 bg-black/50 text-white rounded-full hover:bg-black/70 transition-colors"
                                                                    >
                                                                        <Trash2 className="w-3 h-3" />
                                                                    </button>
                                                                </div>
                                                            ) : (
                                                                <label className="flex flex-col items-center justify-center w-24 h-24 rounded-lg border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all duration-200 group/label">
                                                                    <Upload className="w-6 h-6 text-muted-foreground group-hover/label:text-primary transition-colors" />
                                                                    <span className="text-[10px] mt-1 text-muted-foreground group-hover/label:text-primary">Upload</span>
                                                                    <input
                                                                        type="file"
                                                                        className="hidden"
                                                                        accept="image/*"
                                                                        onChange={(e) => {
                                                                            const file = e.target.files?.[0];
                                                                            if (file) handleFileUpload(ensaio.id, img.id, file);
                                                                        }}
                                                                    />
                                                                </label>
                                                            )}
                                                            <div className="flex-1">
                                                                <FieldGroup icon={ImageIcon} label="Legenda da Imagem">
                                                                    <input type="text" value={img.legenda}
                                                                        onChange={e => updateImagemInEnsaio(ensaio.id, img.id, 'legenda', e.target.value)}
                                                                        placeholder="Descreva o que aparece na imagem..."
                                                                        className={inputCls + ' py-2'} />
                                                                </FieldGroup>
                                                                {/* {img.caminho_imagem && (
                                                                    <p className="text-[10px] text-muted-foreground mt-2 truncate w-full">
                                                                        {img.caminho_imagem}
                                                                    </p> */}
                                                                {/* )} */}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <button type="button" onClick={() => removeImagemFromEnsaio(ensaio.id, img.id)}
                                                        className="p-2 self-start rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-all">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ))}

                            <button type="button" onClick={addEnsaio}
                                className="w-full glass-card border-2 border-dashed border-amber-500/30 hover:border-amber-500/60 hover:bg-amber-500/5 py-4 rounded-2xl flex items-center justify-center gap-2 text-muted-foreground hover:text-amber-500 transition-all duration-300 group">
                                <Plus className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Adicionar Ensaio</span>
                            </button>
                        </div>

                        {/* ── Secções de Texto ──────────────────────────────── */}
                        <div className="space-y-4">
                            <h2 className="font-bold text-foreground flex items-center gap-2 px-1">
                                <AlignLeft className="w-4 h-4 text-primary" />
                                Secções do Relatório
                            </h2>

                            {sections.map((section, index) => (
                                <div key={section.id} className="glass-card relative overflow-hidden group">
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-l-2xl opacity-70" />
                                    <div className="p-6 pl-7 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium text-foreground">Secção {index + 1}</span>
                                            <button type="button" onClick={() => removeSection(section.id)}
                                                className="p-1.5 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-400/10 transition-all duration-200 opacity-0 group-hover:opacity-100">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <FieldGroup icon={Tag} label="Título da secção">
                                            <input type="text" value={section.title}
                                                onChange={e => updateSection(section.id, 'title', e.currentTarget.value)}
                                                className={inputCls + ' font-medium'} />
                                        </FieldGroup>
                                        <FieldGroup icon={AlignLeft} label="Conteúdo">
                                            <textarea value={section.content}
                                                onChange={e => updateSection(section.id, 'content', e.currentTarget.value)}
                                                rows={5}
                                                className={inputCls + ' font-serif leading-relaxed resize-y'} />
                                        </FieldGroup>
                                    </div>
                                </div>
                            ))}

                            <button type="button" onClick={addSection}
                                className="w-full glass-card border-2 border-dashed border-border hover:border-primary/40 hover:bg-primary/5 py-5 rounded-2xl flex items-center justify-center gap-2 text-muted-foreground hover:text-primary transition-all duration-300 group">
                                <Plus className="w-5 h-5 group-hover:scale-110 transition-transform" />
                                <span className="font-medium text-sm">Adicionar Secção</span>
                            </button>
                        </div>

                        {/* ── Responsáveis ─────────────────────────────────── */}
                        <div className="glass-card p-6 space-y-5">
                            <h2 className="font-bold text-foreground flex items-center gap-2">
                                <CheckSquare className="w-4 h-4 text-primary" />
                                Responsáveis
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div className="space-y-3">
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Elaboração</p>
                                    <FieldGroup icon={User} label="Nome">
                                        <input className={inputCls} value={meta.elaboracao_nome} onChange={e => updateMeta('elaboracao_nome', e.currentTarget.value)} />
                                    </FieldGroup>
                                    <FieldGroup icon={Wrench} label="Cargo / Registro">
                                        <input className={inputCls} value={meta.elaboracao_cargo} onChange={e => updateMeta('elaboracao_cargo', e.currentTarget.value)} />
                                    </FieldGroup>
                                </div>
                                <div className="space-y-3">
                                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Aprovação</p>
                                    <FieldGroup icon={User} label="Nome">
                                        <input className={inputCls} value={meta.aprovacao_nome} onChange={e => updateMeta('aprovacao_nome', e.currentTarget.value)} />
                                    </FieldGroup>
                                    <FieldGroup icon={Wrench} label="Cargo / Registro">
                                        <input className={inputCls} value={meta.aprovacao_cargo} onChange={e => updateMeta('aprovacao_cargo', e.currentTarget.value)} />
                                    </FieldGroup>
                                </div>
                            </div>
                        </div>
                        {/* ── Submit ───────────────────────────────────────── */}
                        <div className="flex justify-end gap-3 pt-2">
                            <Button type="button" variant="ghost" loading={submitting} onClick={handleExport} className="px-6 py-3 text-base">
                                <Download className="w-4 h-4 mr-2" />
                                Exportar docx
                            </Button>
                            <Button type="submit" variant="primary" loading={submitting} className="px-8 py-3 text-base">
                                <Save className="w-4 h-4 mr-2" />
                                Salvar Alterações
                            </Button>
                        </div>
                    </form>
                ) : (
                    <div className="glass-card p-12 text-center space-y-4">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-secondary text-muted-foreground mb-2">
                            <Loader2 className="w-8 h-8 animate-spin" />
                        </div>
                        <h3 className="text-xl font-bold">Carregando relatório...</h3>
                        <p className="text-muted-foreground max-w-sm mx-auto">
                            Buscando os dados do relatório solicitado.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default EditReportPage;
