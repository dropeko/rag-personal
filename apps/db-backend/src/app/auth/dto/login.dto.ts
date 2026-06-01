import { IsNotEmpty, IsString } from 'class-validator';

export class LoginDto {
    @IsNotEmpty({ message: 'O utilizador é obrigatório.' })
    @IsString()
    username: string;
    @IsNotEmpty({ message: 'A senha é obrigatória.' })
    @IsString()
    password: string;
}