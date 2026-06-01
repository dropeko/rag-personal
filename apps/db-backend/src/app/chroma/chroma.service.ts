import { Injectable, OnModuleInit, Logger, NotFoundException } from '@nestjs/common';
import { ChromaClient, Collection } from 'chromadb';
import * as dotenv from 'dotenv';

dotenv.config();

@Injectable()
export class ChromaService implements OnModuleInit {
    private client!: ChromaClient;
    private collection!: Collection;
    private readonly logger = new Logger(ChromaService.name);
    private readonly COLLECTION_NAME = 'report_texts';

    async onModuleInit() {
        try {
            this.client = new ChromaClient({
                path: process.env.CHROMA_PATH ?? 'http://localhost:8000',
            });

            const embedder = new XenovaEmbeddingFunction();
            await embedder.init();

            // Verify connection by getting the collection
            this.collection = await this.client.getCollection({
                name: this.COLLECTION_NAME,
                embeddingFunction: embedder
            });

            this.logger.log(`Connected to ChromaDB collection: ${this.COLLECTION_NAME}`);
        } catch (error) {
            this.logger.error('Failed to connect to ChromaDB', error);
        }
    }

    async query(text: string, nResults = 5) {
        if (!this.collection) {
            throw new Error('ChromaDB collection not initialized');
        }
        this.logger.log(`Querying ChromaDB for text: ${text}`);

        const results = await this.collection.query({
            queryTexts: [text],
            nResults: nResults,
        });

        return results;
    }

    async getReport(reportId: string | number) {
        if (!this.collection) {
            throw new Error('ChromaDB collection not initialized');
        }
        this.logger.log(`Getting report with ID: ${reportId}`);

        const results = await this.collection.get({
            where: {
                id_relatorio: Number(reportId),
            },
            include: ['metadatas', 'documents'],
        });

        // Strip internal filesystem path from metadata before sending to client
        const sanitizedMetadatas = results.metadatas?.map((meta) => {
            if (!meta) return meta;
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { caminho, ...safeMeta } = meta as Record<string, unknown>;
            return safeMeta;
        });

        return { ...results, metadatas: sanitizedMetadatas };
    }

    async getPdfPath(reportId: string | number): Promise<string> {
        if (!this.collection) {
            throw new Error('ChromaDB collection not initialized');
        }
        this.logger.log(`Getting PDF path for report ID: ${reportId}`);

        const results = await this.collection.get({
            where: { id_relatorio: Number(reportId) },
            include: ['metadatas' as any],
            limit: 1,
        });

        const meta = results.metadatas?.[0];
        if (!meta || !meta['caminho']) {
            throw new NotFoundException(`PDF path not found for report ${reportId}`);
        }

        return meta['caminho'] as string;
    }
}

import { pipeline } from '@xenova/transformers';

class XenovaEmbeddingFunction {
    private pipe: any;

    async init() {
        this.pipe = await pipeline('feature-extraction', 'Xenova/paraphrase-multilingual-mpnet-base-v2');
    }

    async generate(texts: string[]): Promise<number[][]> {
        if (!this.pipe) {
            await this.init();
        }
        const embeddings: number[][] = [];
        for (const text of texts) {
            const output = await this.pipe(text, { pooling: 'mean', normalize: true });
            embeddings.push(Array.from(output.data));
        }
        return embeddings;
    }
}

