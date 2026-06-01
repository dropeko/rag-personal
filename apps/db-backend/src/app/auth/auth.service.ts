import {
    BadRequestException,
    Injectable,
    NotFoundException,
    UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { getPrismaClient } from '@data-platforms/db-lib';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';

const BCRYPT_SALT_ROUNDS = 12;

@Injectable()
export class AuthService {
    private readonly prisma = getPrismaClient();

    constructor(private readonly jwtService: JwtService) {}

    async register(dto: RegisterDto) {
        const existing = await this.prisma.user.findUnique({
            where: { email: dto.email },
        });

        if (existing) {
            throw new BadRequestException('Já existe uma conta com este email.');
        }

        const [firstName, ...rest] = dto.name.trim().split(' ');
        const lastName = rest.join(' ') || '';
        const hashedPassword = await bcrypt.hash(dto.password, BCRYPT_SALT_ROUNDS);

        const user = await this.prisma.user.create({
            data: {
                firstName,
                lastName,
                email: dto.email,
                password: hashedPassword,
                phone: dto.phone,
                position: dto.position,
                isConfirmed: true,
            },
        });

        return {
            message: 'Conta criada com sucesso.',
            id: user.id,
            email: user.email,
        };
    }

    async login(dto: LoginDto) {
        const user = await this.prisma.user.findUnique({
            where: { email: dto.username },
        });

        if (!user) {
            throw new NotFoundException('Utilizador não encontrado.');
        }

        if (!user.isConfirmed) {
            throw new UnauthorizedException('Conta ainda não confirmada. Contacte o administrador.');
        }

        if (!user.password) {
            throw new UnauthorizedException('Password não definida. Contacte o administrador.');
        }

        const passwordMatches = await bcrypt.compare(dto.password, user.password);
        if (!passwordMatches) {
            throw new UnauthorizedException('Credenciais inválidas.');
        }

        const payload = { sub: user.id, email: user.email, role: user.role };
        const token = await this.jwtService.signAsync(payload);

        return {
            access_token: token,
            user: {
                id: user.id,
                email: user.email,
                firstName: user.firstName,
                lastName: user.lastName,
                role: user.role,
            },
        };
    }
}