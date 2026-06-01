import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { JwtAuthGuard } from './guards/jwt-auth.guard';

@Module({
    imports: [
        JwtModule.register({
            global: true, // disponibiliza JwtService em toda a aplicação sem reimportar
            secret: process.env.JWT_SECRET,
            signOptions: { expiresIn: '8h' },
        }),
    ],
    controllers: [AuthController],
    providers: [AuthService, JwtAuthGuard],
    exports: [JwtAuthGuard],
})
export class AuthModule {}