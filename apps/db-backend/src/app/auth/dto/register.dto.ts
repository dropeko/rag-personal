import { IsEmail, IsNotEmpty, IsOptional, IsString, MinLength } from 'class-validator';

export class RegisterDto {
    @IsNotEmpty({ message: 'O nome é obrigatório.' })
    @IsString()
    name: string;

    @IsEmail({}, { message: 'Formato de email inválido.' })
    email: string;

    @IsNotEmpty({ message: 'A senha é obrigatória.' })
    @IsString()
    @MinLength(8, { message: 'A senha deve ter no mínimo 8 caracteres.' })
    password: string;

    @IsOptional()
    @IsString()
    phone?: string;

    @IsOptional()
    @IsString()
    position?: string;
}