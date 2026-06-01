import { getPrismaClient } from './prisma-client.js';

export async function getRelatorios() {
    const prisma = getPrismaClient();
    return prisma.relatorio.findMany();
}

export async function getRelatorioById(id: number) {
    const prisma = getPrismaClient();
    return prisma.relatorio.findUnique({
        where: { id },
    });
}
