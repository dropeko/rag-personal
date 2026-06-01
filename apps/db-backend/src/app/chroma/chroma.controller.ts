import { Controller, Get, Post, Body, Param, Res, NotFoundException } from '@nestjs/common';
import type { Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { ChromaService } from './chroma.service';

@Controller('chroma')
export class ChromaController {
    constructor(private readonly chromaService: ChromaService) { }

    @Get()
    async healthCheck() {
        return { status: 'ok' };
    }

    @Post('query')
    async query(@Body() body: { query: string; nResults?: number }) {
        return this.chromaService.query(body.query, body.nResults);
    }

    @Get('report/:id')
    async getReport(@Param('id') id: string) {
        return this.chromaService.getReport(id);
    }

    @Get('pdf/:id')
    async getPdf(@Param('id') id: string, @Res() res: Response) {
        const filePath = await this.chromaService.getPdfPath(id);
        const resolved = path.resolve(filePath);

        if (!fs.existsSync(resolved)) {
            throw new NotFoundException(`PDF file not found at path: ${resolved}`);
        }

        const filename = path.basename(resolved);
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `inline; filename="${filename}"`);
        fs.createReadStream(resolved).pipe(res);
    }
}
