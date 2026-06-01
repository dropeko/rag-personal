import { Injectable } from '@nestjs/common';
import { getPrismaClient } from '@data-platforms/db-lib';

@Injectable()
export class ReportsService {
    private prisma = getPrismaClient();

    async findAll() {
        return this.prisma.relatorio.findMany({
            orderBy: { created_at: 'desc' },
            include: {
                equipamento: {
                    include: {
                        ss: {
                            include: {
                                contrato: {
                                    include: {
                                        cliente: {
                                            include: { unidades: true }
                                        }
                                    }
                                }
                            }
                        },
                        ensaios: { include: { imagens: true } }
                    }
                },
                secoes: true,
            }
        });
    }

    async findOne(id: number) {
        return this.prisma.relatorio.findUnique({
            where: { id },
            include: {
                equipamento: {
                    include: {
                        ss: {
                            include: {
                                contrato: {
                                    include: {
                                        cliente: {
                                            include: { unidades: true }
                                        }
                                    }
                                }
                            }
                        },
                        ensaios: { include: { imagens: true } }
                    }
                },
                secoes: true,
            }
        });
    }

    async search(query: string) {
        return this.prisma.relatorio.findMany({
            where: {
                OR: [
                    { equipamento: { ss: { numero: { contains: query } } } },
                    { equipamento: { ss: { csc: { contains: query } } } },
                    { numero_relatorio: { contains: query } }
                ]
            },
            include: {
                equipamento: {
                    include: {
                        ss: {
                            include: {
                                contrato: {
                                    include: {
                                        cliente: {
                                            include: { unidades: true }
                                        }
                                    }
                                }
                            }
                        },
                        ensaios: { include: { imagens: true } }
                    }
                },
                secoes: true
            }
        });
    }

    async createOrUpdate(data: any) {
        const {
            id,
            numero_relatorio, revisao, cliente, data: metaData, unidade,
            csc,
            tipo_equipamento, tag, numero_ss, numero_contrato,
            elaboracao_nome, elaboracao_cargo, aprovacao_nome, aprovacao_cargo,
            sections, ensaios
        } = data;

        // Helper to find or create
        let clienteId = null;
        if (cliente) {
            let c = await this.prisma.cliente.findFirst({ where: { nome: cliente } });
            if (!c) c = await this.prisma.cliente.create({ data: { nome: cliente } });
            clienteId = c.id;
        }

        if (unidade && clienteId) {
            const u = await this.prisma.unidade.findFirst({ where: { nome: unidade, clienteId } });
            if (!u) await this.prisma.unidade.create({ data: { nome: unidade, clienteId } });
        }

        let contratoId = null;
        if (numero_contrato && clienteId) {
            let cont = await this.prisma.contrato.findFirst({ where: { numero: numero_contrato, clienteId } });
            if (!cont) cont = await this.prisma.contrato.create({ data: { numero: numero_contrato, clienteId } });
            contratoId = cont.id;
        }

        let ssId = null;
        if (numero_ss && contratoId) {
            let sess = await this.prisma.sS.findFirst({ where: { numero: numero_ss, contratoId } });
            if (!sess) {
                sess = await this.prisma.sS.create({ data: { numero: numero_ss, csc, contratoId } });
            } else if (csc && sess.csc !== csc) {
                sess = await this.prisma.sS.update({ where: { id: sess.id }, data: { csc } });
            }
            ssId = sess.id;
        }

        let equipamentoId = null;
        if ((tipo_equipamento || tag) && ssId) {
            let eq = await this.prisma.equipamento.findFirst({ where: { nome: tipo_equipamento || 'Equipamento', ssId } });
            if (!eq) eq = await this.prisma.equipamento.create({ data: { nome: tipo_equipamento || 'Equipamento', dados: tag, ssId } });
            equipamentoId = eq.id;
        }

        const relatorioData = {
            numero_relatorio,
            revisao,
            data: metaData,
            elaboracao_nome,
            elaboracao_cargo,
            aprovacao_nome,
            aprovacao_cargo,
            equipamentoId
        };

        let result;
        if (id) {
            // Update
            result = await this.prisma.relatorio.update({
                where: { id },
                data: relatorioData
            });

            // Update sections (recreate them)
            if (sections) {
                await this.prisma.secaoTexto.deleteMany({ where: { relatorioId: id } });
                await this.prisma.secaoTexto.createMany({
                    data: sections.map((s: any) => ({
                        nome: s.titulo || s.title || 'Secao',
                        conteudo: s.content,
                        relatorioId: id
                    }))
                });
            }

            // Update ensaios for the equipamento if provided
            if (ensaios && equipamentoId) {
                // To support nested insertion simply loop:
                await this.prisma.ensaio.deleteMany({ where: { equipamentoId } });
                for (const e of ensaios) {
                    await this.prisma.ensaio.create({
                        data: {
                            tipo: e.tipo,
                            qnt_amostras: e.qnt_amostras || 0,
                            texto: e.texto,
                            equipamentoId,
                            imagens: e.imagens ? {
                                create: e.imagens.map((i: any) => ({
                                    caminho_imagem: i.caminho_imagem,
                                    legenda: i.legenda
                                }))
                            } : undefined
                        }
                    });
                }
            }

        } else {
            // Create
            result = await this.prisma.relatorio.create({
                data: {
                    ...relatorioData,
                    secoes: sections ? {
                        create: sections.map((s: any) => ({
                            nome: s.titulo || s.title || 'Secao',
                            conteudo: s.content,
                        }))
                    } : undefined
                }
            });

            if (ensaios && equipamentoId) {
                for (const e of ensaios) {
                    await this.prisma.ensaio.create({
                        data: {
                            tipo: e.tipo,
                            qnt_amostras: e.qnt_amostras || 0,
                            texto: e.texto,
                            equipamentoId,
                            imagens: e.imagens ? {
                                create: e.imagens.map((i: any) => ({
                                    caminho_imagem: i.caminho_imagem,
                                    legenda: i.legenda
                                }))
                            } : undefined
                        }
                    });
                }
            }
        }

        return this.findOne(result.id);
    }
}
