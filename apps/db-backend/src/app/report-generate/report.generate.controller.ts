import {
    Controller, Post, Body, Res, Logger, HttpCode,
} from '@nestjs/common';
import { Response } from 'express';
import { ReportGenerateService } from './report.generate.service';
import { GenerateReportDto } from './generate-report.dto';

@Controller('report')
export class ReportGenerateController {
    private readonly logger = new Logger(ReportGenerateController.name);

    constructor(private readonly service: ReportGenerateService) { }

    @Post('generate')
    @HttpCode(200)
    async generate(
        @Body() dto: GenerateReportDto,
        @Res() res: Response,
    ) {
        this.logger.log(`Generating report: ${dto.numero_relatorio}`);
        const buffer = await this.service.generate(dto);

        const filename = `${dto.numero_relatorio ?? 'relatorio'}.docx`;
        res.set({
            'Content-Type':
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'Content-Disposition': `attachment; filename="${filename}"`,
            'Content-Length': buffer.length,
        });
        res.end(buffer);
    }
}
