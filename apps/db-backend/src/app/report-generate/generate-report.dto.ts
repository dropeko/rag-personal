export class SectionDto {
    titulo!: string;
    content!: string;
}

export class ImageDto {
    caminho_imagem!: string;
    legenda!: string;
}

export class EnsaioDto {
    tipo!: string;
    qnt_amostras!: number;
    texto!: string;
    imagens?: ImageDto[];
}

export class GenerateReportDto {
    numero_relatorio!: string;
    revisao!: string;
    cliente!: string;
    data!: string;
    unidade!: string;
    tipo_equipamento!: string;
    tag!: string;
    numero_ss!: string;
    numero_contrato!: string;
    elaboracao_nome!: string;
    elaboracao_cargo!: string;
    aprovacao_nome!: string;
    aprovacao_cargo!: string;
    sections!: SectionDto[];
    ensaios?: EnsaioDto[];
}
