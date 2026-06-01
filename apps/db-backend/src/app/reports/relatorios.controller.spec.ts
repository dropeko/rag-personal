import { Test, TestingModule } from '@nestjs/testing';
import { ReportsController } from './reports.controller';
import { ReportsService } from './reports.service';
import { NotFoundException } from '@nestjs/common';

describe('ReportsController', () => {
    let controller: ReportsController;
    let service: ReportsService;

    beforeEach(async () => {
        const module: TestingModule = await Test.createTestingModule({
            controllers: [ReportsController],
            providers: [
                {
                    provide: ReportsService,
                    useValue: {
                        findAll: jest.fn().mockResolvedValue([]),
                        findOne: jest.fn(),
                    },
                },
            ],
        }).compile();

        controller = module.get<ReportsController>(ReportsController);
        service = module.get<ReportsService>(ReportsService);
    });

    it('should be defined', () => {
        expect(controller).toBeDefined();
    });

    describe('findAll', () => {
        it('should return an array of relatorios', async () => {
            await controller.findAll();
            expect(service.findAll).toHaveBeenCalled();
        });
    });

    describe('findOne', () => {
        it('should return a relatorio by id', async () => {
            const mockRelatorio = { id: 1, arquivo_nome: 'test' };
            (service.findOne as jest.Mock).mockResolvedValue(mockRelatorio);

            const result = await controller.findOne(1);
            expect(result).toEqual(mockRelatorio);
            expect(service.findOne).toHaveBeenCalledWith(1);
        });

        it('should throw NotFoundException if relatorio not found', async () => {
            (service.findOne as jest.Mock).mockResolvedValue(null);

            await expect(controller.findOne(999)).rejects.toThrow(NotFoundException);
        });
    });
});
