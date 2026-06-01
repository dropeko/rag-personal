import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { join } from 'path';
import { readFileSync } from 'fs';
import PizZip from 'pizzip';
import Docxtemplater from 'docxtemplater';
import { GenerateReportDto, EnsaioDto, ImageDto } from './generate-report.dto';

@Injectable()
export class ReportGenerateService {
    private readonly logger = new Logger(ReportGenerateService.name);

    private getImageSize(buffer: Buffer) {
        try {
            // PNG
            if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
                return {
                    width: buffer.readInt32BE(16),
                    height: buffer.readInt32BE(20)
                };
            }
            // JPEG
            if (buffer[0] === 0xFF && buffer[1] === 0xD8) {
                let pos = 2;
                while (pos < buffer.length) {
                    if (buffer[pos] !== 0xFF) break;
                    const marker = buffer[pos + 1];
                    const length = buffer.readUInt16BE(pos + 2);
                    // SOF0 (Start Of Frame 0) marker for baseline JPEG
                    if (marker === 0xC0 || marker === 0xC1 || marker === 0xC2) {
                        return {
                            height: buffer.readUInt16BE(pos + 5),
                            width: buffer.readUInt16BE(pos + 7)
                        };
                    }
                    pos += length + 2;
                }
            }
        } catch (e) {
            this.logger.error('Error parsing image dimensions', e);
        }
        return null;
    }

    async generate(dto: GenerateReportDto): Promise<Buffer> {
        try {
            const templatePath = join(
                __dirname,
                '..',
                'src',
                'templates',
                'template_v5.docx',
            );

            const content = readFileSync(templatePath, 'binary');
            const zip = new PizZip(content);

            const ImageModule = require('docxtemplater-image-module-free');
            const fs = require('fs');
            const path = require('path');

            const imageOpts = {
                centered: false,
                getImage: (tagValue: string) => {
                    // Resolve URL to local path
                    // tagValue could be "http://localhost:3000/uploads/report_ID/filename.jpg"
                    // or "/uploads/report_ID/filename.jpg"
                    try {
                        const filenamePart = tagValue.split('/uploads/')[1];
                        if (!filenamePart) return null;

                        const localPath = path.join(process.cwd(), 'apps', 'db-backend', 'data', filenamePart);
                        if (fs.existsSync(localPath)) {
                            return fs.readFileSync(localPath);
                        }
                    } catch (e) {
                        this.logger.error(`Error loading image ${tagValue}`, e);
                    }
                    return null;
                },
                getSize: (img: Buffer) => {
                    const dimensions = this.getImageSize(img);
                    if (!dimensions) return [400, 300];

                    const maxWidth = 480; // Largura máxima no Word (aprox)
                    const width = Math.min(dimensions.width, maxWidth);
                    const ratio = dimensions.width / dimensions.height;
                    const height = width / ratio;

                    return [width, height];
                }
            };

            const doc = new Docxtemplater(zip, {
                paragraphLoop: true,
                linebreaks: true,
                modules: [new ImageModule(imageOpts)],
            });

            const fixedTitles = [
                'DISCUSSÃO DOS RESULTADOS',
                'CONCLUSÃO',
                'RECOMENDAÇÕES',
                'REFERÊNCIAS BIBLIOGRÁFICAS'
            ];

            const standardSectionsDto = (dto.sections ?? []).filter(
                s => !fixedTitles.includes(s.titulo.toUpperCase())
            );

            const mappedSections = standardSectionsDto.map((s, i) => ({
                index: i + 1,
                titulo: s.titulo,
                content: s.content,
            }));

            let currentIndex = mappedSections.length + 1;

            const idxResults = currentIndex++;
            const idxDiscussao = currentIndex++;
            const idxConclusao = currentIndex++;
            const idxRecomendacoes = currentIndex++;
            const idxReferencias = currentIndex++;

            const findContent = (title: string) =>
                (dto.sections ?? []).find(s => s.titulo.toUpperCase() === title.toUpperCase())?.content ?? '';

            doc.render({
                numero_relatorio: dto.numero_relatorio ?? '',
                revisao: dto.revisao ?? '0',
                cliente: dto.cliente ?? '',
                data: dto.data ?? new Date().toLocaleDateString('pt-BR'),
                unidade: dto.unidade ?? '',
                tipo_equipamento: dto.tipo_equipamento ?? '',
                tag: dto.tag ?? '',
                numero_ss: dto.numero_ss ?? '',
                numero_contrato: dto.numero_contrato ?? '',
                elaboracao_nome: dto.elaboracao_nome ?? '',
                elaboracao_cargo: dto.elaboracao_cargo ?? '',
                aprovacao_nome: dto.aprovacao_nome ?? '',
                aprovacao_cargo: dto.aprovacao_cargo ?? '',

                // Seções Dinâmicas (Iniciais)
                sections: mappedSections,

                // RESULTADOS
                idx_resultados: idxResults,
                ensaios: (dto.ensaios ?? []).map((e: EnsaioDto, i) => ({
                    index: `${idxResults}.${i + 1}`,
                    tipo: e.tipo,
                    qnt_amostras: e.qnt_amostras ?? 0,
                    texto: e.texto,
                    imagens: (e.imagens ?? []).map((img: ImageDto) => ({
                        caminho: img.caminho_imagem,
                        legenda: img.legenda
                    }))
                })),

                // Seções Fixas (Finais)
                idx_discussao: idxDiscussao,
                discussao_content: findContent('DISCUSSÃO DOS RESULTADOS'),

                idx_conclusao: idxConclusao,
                conclusao_content: findContent('CONCLUSÃO'),

                idx_recomendacoes: idxRecomendacoes,
                recomendacoes_content: findContent('RECOMENDAÇÕES'),

                idx_referencias: idxReferencias,
                referencias_content: findContent('REFERÊNCIAS BIBLIOGRÁFICAS'),
            });

            const out = doc.getZip().generate({
                type: 'nodebuffer',
                compression: 'DEFLATE',
            });

            return out as Buffer;
        } catch (err) {
            this.logger.error('Failed to generate report', err);
            throw new InternalServerErrorException('Failed to generate report document');
        }
    }
}
