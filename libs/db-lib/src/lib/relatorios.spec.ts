import { getRelatorios } from './relatorios.js';
import { getPrismaClient } from './prisma-client.js';

// Mocking Prisma Client
jest.mock('./prisma-client', () => ({
    getPrismaClient: jest.fn(),
}));

describe('getRelatorios', () => {
    it('should call prisma.relatorio.findMany', async () => {
        const mockFindMany = jest.fn().mockResolvedValue([]);
        (getPrismaClient as jest.Mock).mockReturnValue({
            relatorio: {
                findMany: mockFindMany,
            },
        });

        await getRelatorios();

        expect(mockFindMany).toHaveBeenCalledWith({
            include: {
                imagens: true,
            },
        });
    });
});