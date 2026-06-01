import { Controller, Get, Param, ParseIntPipe, NotFoundException, Logger, Query, Post, Body, UseInterceptors, UploadedFile } from '@nestjs/common';
import { ReportsService } from './reports.service';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { extname, join } from 'path';
import { existsSync, mkdirSync } from 'fs';

@Controller('reports')
export class ReportsController {
    private readonly logger = new Logger(ReportsController.name);
    constructor(private readonly reportsService: ReportsService) { }

    @Get()
    async findAll() {
        this.logger.log('Finding all reports');
        return this.reportsService.findAll();
    }

    @Get('search')
    async search(@Query('q') query: string) {
        this.logger.log(`Searching reports with query: ${query}`);
        if (!query) return this.reportsService.findAll();
        return this.reportsService.search(query);
    }

    @Post()
    async createOrUpdate(@Body() data: any) {
        this.logger.log(`Creating or updating report...`);
        return this.reportsService.createOrUpdate(data);
    }

    @Post('upload/:reportId')
    @UseInterceptors(FileInterceptor('file', {
        storage: diskStorage({
            destination: (req, file, cb) => {
                const reportId = req.params.reportId;
                const uploadPath = join(process.cwd(), 'apps', 'db-backend', 'data', `report_${reportId}`);
                if (!existsSync(uploadPath)) {
                    mkdirSync(uploadPath, { recursive: true });
                }
                cb(null, uploadPath);
            },
            filename: (req, file, cb) => {
                const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
                cb(null, `${uniqueSuffix}${extname(file.originalname)}`);
            },
        }),
    }))
    uploadFile(@Param('reportId') reportId: string, @UploadedFile() file: Express.Multer.File) {
        this.logger.log(`Uploading file for report ${reportId}: ${file.filename}`);
        return {
            url: `/uploads/report_${reportId}/${file.filename}`,
            filename: file.filename
        };
    }

    @Get(':id')
    async findOne(@Param('id', ParseIntPipe) id: number) {
        this.logger.log(`Finding report with ID ${id}`);
        const relatorio = await this.reportsService.findOne(id);
        if (!relatorio) {
            throw new NotFoundException(`Relatorio with ID ${id} not found`);
        }
        return relatorio;
    }
}
