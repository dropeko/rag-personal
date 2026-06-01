/**
 * This is not a production server yet!
 * This is only a minimal backend to get started.
 */

import { Logger, ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app/app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.enableCors();

  const fs = require('fs');
  const path = require('path');
  const dataDir = path.join(process.cwd(), 'apps', 'db-backend', 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  const express = require('express');
  app.use('/uploads', express.static(dataDir));

  const globalPrefix = 'api';
  app.setGlobalPrefix(globalPrefix);
    app.useGlobalPipes(new ValidationPipe({
        whitelist: true,       // remove campos não declarados no DTO
        forbidNonWhitelisted: true, // rejeita requests com campos extra
        transform: true,       // converte tipos automaticamente (ex: string → number)
    }));

  const port = process.env.PORT || 3000;
  await app.listen(port);
  Logger.log(`🚀 Application is running on: http://localhost:${port}/${globalPrefix}`);
}

bootstrap();
