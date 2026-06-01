/**
 * run-queries.ts — Executa o golden set contra cada variante e mede latência.
 *
 * Uso:
 *   npx ts-node run-queries.ts --golden-set golden-set.csv --out results.csv
 *   npx ts-node run-queries.ts --variants v1,v2,v3 --top-k 10 --repeats 5
 *
 * V1 (MPNet) usa @xenova/transformers (mesmo runtime da produção).
 * V2/V3/V4 (OpenAI) usam fetch() direto na API (sem SDK extra).
 * V5 (BGE-m3) é pulado neste runner — para medir V5 use o helper Python.
 */
import { ChromaClient } from 'chromadb';
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.join(__dirname, '.env') });

const CHROMA_URL = process.env.CHROMA_URL ?? 'http://localhost:8000';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY ?? '';
const TOP_K_DEFAULT = Number(process.env.TOP_K ?? 10);
const REPEATS_DEFAULT = Number(process.env.QUERY_REPEATS ?? 5);

type Provider = 'mpnet-xenova' | 'openai' | 'skip';

interface Variant {
    id: string;
    collection: string;
    provider: Provider;
    model?: string;
    dim?: number;
}

const VARIANTS: Record<string, Variant> = {
    v1: { id: 'v1_mpnet_768', collection: 'report_texts', provider: 'mpnet-xenova' },
    v2: { id: 'v2_openai_small_768', collection: 'bench_v2_openai_small_768', provider: 'openai', model: 'text-embedding-3-small', dim: 768 },
    v3: { id: 'v3_openai_small_1536', collection: 'bench_v3_openai_small_1536', provider: 'openai', model: 'text-embedding-3-small', dim: 1536 },
    v4: { id: 'v4_openai_large_3072', collection: 'bench_v4_openai_large_3072', provider: 'openai', model: 'text-embedding-3-large' },
    v5: { id: 'v5_bge_m3_1024', collection: 'bench_v5_bge_m3_1024', provider: 'skip' },
};

interface Args {
    goldenSet: string;
    out: string;
    variants: string[];
    topK: number;
    repeats: number;
}

function parseArgs(argv: string[]): Args {
    const get = (flag: string, fallback?: string) => {
        const i = argv.indexOf(flag);
        return i >= 0 ? argv[i + 1] : fallback;
    };
    return {
        goldenSet: get('--golden-set', 'golden-set.csv')!,
        out: get('--out', 'results.csv')!,
        variants: (get('--variants', 'v1,v2,v3,v4')!).split(','),
        topK: Number(get('--top-k', String(TOP_K_DEFAULT))),
        repeats: Number(get('--repeats', String(REPEATS_DEFAULT))),
    };
}

interface GoldenRow {
    queryId: number;
    question: string;
    expectedReportId: string;
}

function parseCSV(filePath: string): GoldenRow[] {
    // Parser minimalista — não suporta vírgula dentro de campo não-quotado.
    const lines = fs.readFileSync(filePath, 'utf-8').split(/\r?\n/).filter(Boolean);
    const [header, ...rows] = lines;
    const cols = parseCsvLine(header);
    const idxQuestion = cols.indexOf('question');
    const idxExpected = cols.indexOf('expected_report_id');
    if (idxQuestion < 0 || idxExpected < 0) {
        throw new Error(`golden-set precisa ter colunas question, expected_report_id. Achei: ${cols.join(', ')}`);
    }
    return rows.map((line, i) => {
        const parts = parseCsvLine(line);
        return {
            queryId: i + 1,
            question: parts[idxQuestion],
            expectedReportId: parts[idxExpected],
        };
    });
}

function parseCsvLine(line: string): string[] {
    const out: string[] = [];
    let cur = '';
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
        const c = line[i];
        if (c === '"' && line[i + 1] === '"' && inQ) { cur += '"'; i++; continue; }
        if (c === '"') { inQ = !inQ; continue; }
        if (c === ',' && !inQ) { out.push(cur); cur = ''; continue; }
        cur += c;
    }
    out.push(cur);
    return out;
}

// ---------- Embedders ----------

class XenovaEmbedder {
    private pipe: any;
    async init() {
        const { pipeline } = await import('@xenova/transformers');
        this.pipe = await pipeline('feature-extraction', 'Xenova/paraphrase-multilingual-mpnet-base-v2');
    }
    async embed(text: string): Promise<number[]> {
        const out = await this.pipe(text, { pooling: 'mean', normalize: true });
        return Array.from(out.data as Float32Array);
    }
}

async function openaiEmbed(text: string, model: string, dim?: number): Promise<number[]> {
    if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY ausente');
    const body: Record<string, unknown> = { model, input: text };
    if (dim) body.dimensions = dim;
    const res = await fetch('https://api.openai.com/v1/embeddings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${OPENAI_API_KEY}`,
        },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`OpenAI ${res.status}: ${await res.text()}`);
    const json: any = await res.json();
    return json.data[0].embedding;
}

// ---------- Runner ----------

interface ResultRow {
    query_id: number;
    variant: string;
    repeat: number;
    rank: number;
    retrieved_id: string;
    retrieved_report_id: string;
    score: number;
    embed_latency_ms: number;
    search_latency_ms: number;
}

async function runVariant(
    variant: Variant,
    chroma: ChromaClient,
    golden: GoldenRow[],
    topK: number,
    repeats: number,
): Promise<ResultRow[]> {
    if (variant.provider === 'skip') {
        console.log(`[${variant.id}] pulado (rode via Python helper).`);
        return [];
    }

    console.log(`[${variant.id}] conectando à coleção '${variant.collection}'...`);
    const collection = await chroma.getCollection({ name: variant.collection });

    let xenova: XenovaEmbedder | null = null;
    if (variant.provider === 'mpnet-xenova') {
        xenova = new XenovaEmbedder();
        console.log(`[${variant.id}] carregando modelo Xenova (cold start)...`);
        await xenova.init();
        // Warm-up: 1ª inferência é sempre mais lenta.
        await xenova.embed('warmup');
    }

    const rows: ResultRow[] = [];
    for (const q of golden) {
        for (let r = 1; r <= repeats; r++) {
            const tEmbed0 = performance.now();
            let queryEmbedding: number[];
            try {
                if (variant.provider === 'mpnet-xenova') {
                    queryEmbedding = await xenova!.embed(q.question);
                } else {
                    queryEmbedding = await openaiEmbed(q.question, variant.model!, variant.dim);
                }
            } catch (e) {
                console.error(`[${variant.id}] erro embedding query ${q.queryId}: ${e}`);
                continue;
            }
            const embedMs = performance.now() - tEmbed0;

            const tSearch0 = performance.now();
            const res = await collection.query({
                queryEmbeddings: [queryEmbedding],
                nResults: topK,
                include: ['metadatas', 'distances'],
            });
            const searchMs = performance.now() - tSearch0;

            const ids = res.ids?.[0] ?? [];
            const distances = res.distances?.[0] ?? [];
            const metadatas = res.metadatas?.[0] ?? [];

            for (let k = 0; k < ids.length; k++) {
                const meta = metadatas[k] as Record<string, unknown> | null;
                rows.push({
                    query_id: q.queryId,
                    variant: variant.id,
                    repeat: r,
                    rank: k + 1,
                    retrieved_id: ids[k],
                    retrieved_report_id: String(meta?.id_relatorio ?? ''),
                    score: typeof distances[k] === 'number' ? 1 - distances[k] : 0,
                    embed_latency_ms: r === 1 ? embedMs : embedMs, // todas as repetições registradas
                    search_latency_ms: searchMs,
                });
            }
        }
        if (q.queryId % 10 === 0) console.log(`[${variant.id}] ${q.queryId}/${golden.length}`);
    }
    return rows;
}

function writeCSV(filePath: string, rows: ResultRow[]) {
    const cols: (keyof ResultRow)[] = [
        'query_id', 'variant', 'repeat', 'rank',
        'retrieved_id', 'retrieved_report_id', 'score',
        'embed_latency_ms', 'search_latency_ms',
    ];
    const header = cols.join(',');
    const body = rows.map(r => cols.map(c => {
        const v = r[c];
        if (typeof v === 'number') return v.toFixed(4);
        const s = String(v ?? '');
        return /[,"\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(',')).join('\n');
    fs.writeFileSync(filePath, header + '\n' + body + '\n');
}

async function main() {
    const args = parseArgs(process.argv.slice(2));
    const goldenPath = path.resolve(args.goldenSet);
    if (!fs.existsSync(goldenPath)) {
        console.error(`golden set não encontrado: ${goldenPath}`);
        process.exit(1);
    }
    const golden = parseCSV(goldenPath);
    console.log(`golden set: ${golden.length} queries`);

    const chroma = new ChromaClient({ path: CHROMA_URL });

    const allRows: ResultRow[] = [];
    for (const vKey of args.variants) {
        const v = VARIANTS[vKey.trim()] ?? Object.values(VARIANTS).find(x => x.id === vKey.trim());
        if (!v) { console.error(`variant desconhecida: ${vKey}`); continue; }
        const rows = await runVariant(v, chroma, golden, args.topK, args.repeats);
        allRows.push(...rows);
    }

    writeCSV(path.resolve(args.out), allRows);
    console.log(`\nResultados em ${args.out} (${allRows.length} linhas)`);
}

main().catch(e => { console.error(e); process.exit(1); });
