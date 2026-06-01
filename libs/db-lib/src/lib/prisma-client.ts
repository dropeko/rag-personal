import { PrismaClient } from '@prisma/client';
import { PrismaBetterSqlite3 } from '@prisma/adapter-better-sqlite3';
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, resolve, isAbsolute } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
config({ path: resolve(__dirname, '../../.env') });

let prisma: PrismaClient;

const dbUrl = process.env.DATABASE_URL;
if (!dbUrl) {
  throw new Error("DATABASE_URL is not defined. Did you forget to load .env?");
}

// Resolve relative SQLite paths (file:./...) relative to the db-lib root,
// not process.cwd(), so the same DB file is used regardless of where the app is started from.
function resolveDbUrl(url: string): string {
  const match = url.match(/^file:(.+)$/);
  if (!match) return url;
  const filePath = match[1];
  if (isAbsolute(filePath)) return url;
  const dbLibRoot = resolve(__dirname, '../..');
  return 'file:' + resolve(dbLibRoot, filePath);
}

export function getPrismaClient(): PrismaClient {
    if (!prisma) {
        const adapter = new PrismaBetterSqlite3({
            url: resolveDbUrl(dbUrl!),
        });
        prisma = new PrismaClient({ adapter });
    }
    return prisma;
}