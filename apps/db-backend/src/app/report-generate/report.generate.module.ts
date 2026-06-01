import { Module } from '@nestjs/common';
import { ReportGenerateController } from './report.generate.controller';
import { ReportGenerateService } from './report.generate.service';

@Module({
    controllers: [ReportGenerateController],
    providers: [ReportGenerateService],
})
export class ReportGenerateModule { }
