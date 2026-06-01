import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ChromaModule } from './chroma/chroma.module';
import { ReportsModule } from './reports/reports.module';
import { ReportGenerateModule } from './report-generate/report.generate.module';
import { AuthModule } from './auth/auth.module';

@Module({
    imports: [AuthModule, ChromaModule, ReportsModule, ReportGenerateModule],
    controllers: [AppController],
    providers: [AppService],
})
export class AppModule {}