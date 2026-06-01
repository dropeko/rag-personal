# template_web_dev

Este é um monorepo de desenvolvimento web moderno, projetado para facilitar a criação de multiplas aplicações web escaláveis e robustas.

## Stack Utilizada

- **Linguagem**: TypeScript v5
- **Backend**: NestJS (framework Node.js), Prisma ORM para gerenciamento de banco de dados
- **Frontend**: React 19 com Vite para build, TanStack Query para gerenciamento de APIs e Tailwind CSS v4 para estilização
- **Banco de Dados**: PostgreSQL com Prisma ORM
- **Arquitetura**: BFF (Backend for Frontend)
- **Testes**: Vitest (frontend) e Jest (backend)
- **Validação**: Zod

## Getting Started

1. Configurar banco de dados vetorizado no chroma-server:

    1. Baixar a pasta [chroma_db_finetune](https://isqbrasillt.sharepoint.com/:f:/s/NIT-Dev/IgD_Lu6SpnsCS6qA-gBdoBRrAV9oFBAXRVC7IDsUwoAukpI?e=IvHqw0) e colocar em apps/chroma-server/chroma_db_finetune

2. Configurar o .env de todas as pastas:

    1. Entrar dentro de apps/chroma-server/.env e inserir CHROMA_DB_PATH como no example.env

    2. Entrar dentro de apps/db-backend/.env e inserir CHROMA_PATH como no example.env

    3. Entrar dentro de libs/db-lib/.env e inserir DATABASE_URL (use o caminho absoluto do arquivo) e VITE_BACKEND_URL como no example.env

    4. Entrar dentro de apps/wo-frontend/.env e VITE_API_BASE como no example.env

3. Instale tudo: 
    ```
    npm install
    ```

4. Dê build em todas as aplicações:
    ```
    npx nx run-many -t build
    ```

5. Rode a aplicação
    ```
    npm run dev
    ```

## Organização do Projeto (Monorepo Nx)

```
├── apps/                       <- Aplicações executáveis
│   ├── db-backend/             <- API para visualização de banco de dados (NestJS)
│   ├── db-frontend/            <- Aplicação Web para DB (React + Vite)
│   ├── wo-backend/             <- API para relatórios de laboratório (NestJS)
│   └── wo-frontend/            <- Aplicação Web para Lab (React + Vite)
│
├── libs/                       <- Bibliotecas compartilhadas
│   ├── db-lib/                 <- Logica de acesso a dados e Prisma Client (Compartilhado)
|   ├── db-frontend-lib/        <- Componentes de UI e Estilos (Compartilhado)
│   └── ui-lib/                 <- Componentes de UI e Estilos (Compartilhado)
│
├── package.json                <- Dependências globais do Monorepo
├── nx.json                     <- Configuração do Nx
└── tsconfig.base.json          <- Configuração base do TypeScript
```

## Comandos Úteis

- **Criar nova lib**: `npx nx g @nx/js:lib nome-da-lib`
- **Rodar testes**: `npx nx test db-backend`
- **Visualizar grafo de dependências**: `npx nx graph`

You can enforce that the TypeScript project references are always in the correct state when running in CI by adding a step to your CI job configuration that runs the following command:

```sh
npx nx sync:check
```

```sh
npx nx graph
```


Você pode rodar aplicações individualmente:
    ```bash
    npx nx serve db-frontend
    npx nx serve db-backend
    ```

    Ou rodar vários projetos simultaneamente:
    ```bash
    npx nx run-many -t serve
    npx nx run-many -t serve -p db-backend,db-frontend,wo-backend,wo-frontend
    npx nx run-many -t build
    ```


[Learn more about nx sync](https://nx.dev/reference/nx-commands#sync)


## Links úteis

Learn more:

- [Learn more about this workspace setup](https://nx.dev/nx-api/js?utm_source=nx_project&amp;utm_medium=readme&amp;utm_campaign=nx_projects)
- [Learn about Nx on CI](https://nx.dev/ci/intro/ci-with-nx?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [Releasing Packages with Nx release](https://nx.dev/features/manage-releases?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [What are Nx plugins?](https://nx.dev/concepts/nx-plugins?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

And join the Nx community:
- [Discord](https://go.nx.dev/community)
- [Follow us on X](https://twitter.com/nxdevtools) or [LinkedIn](https://www.linkedin.com/company/nrwl)
- [Our Youtube channel](https://www.youtube.com/@nxdevtools)
- [Our blog](https://nx.dev/blog?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
