/// <reference types='vitest' />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dts from 'vite-plugin-dts';
import * as path from 'path';

export default defineConfig(() => ({
    root: import.meta.dirname,
    cacheDir: '../../node_modules/.vite/libs/db-frontend-lib',
    plugins: [
        react(),
        dts({
            entryRoot: 'src',
            tsconfigPath: path.join(import.meta.dirname, 'tsconfig.lib.json'),
            outDir: path.join(import.meta.dirname, 'dist'),
        }),
    ],

    build: {
        outDir: './dist',
        emptyOutDir: true,
        reportCompressedSize: true,
        commonjsOptions: {
            transformMixedEsModules: true,
        },
        lib: {
            entry: {
                pages: 'src/pages.ts',
                api: 'src/api.ts',
            },
            name: '@data-platforms/db-frontend-lib',
            formats: ['es' as const],
        },
        rollupOptions: {
            external: ['react', 'react-dom', 'react/jsx-runtime', 'react-router-dom'],
        },
    },

    test: {
        name: '@data-platforms/db-frontend-lib',
        watch: false,
        globals: true,
        environment: 'jsdom',
        include: ['{src,tests}/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
        reporters: ['default'],
        coverage: {
            reportsDirectory: './test-output/vitest/coverage',
            provider: 'v8' as const,
        },
    },
}));
