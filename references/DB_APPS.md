# ARQUIVO LEGADO, IREI ANALISAR SE APAGO - PIETRO

# DB Apps — Guia de Execução

Este documento descreve como executar as aplicações `db-backend` (NestJS) e `db-frontend` (Vite/React).

## Visão Geral da Arquitetura

```
ChromaDB (porta 8000)  ←→  db-backend / NestJS (porta 3000)  ←→  db-frontend / Vite (porta 4200)
```

> **Ordem de inicialização obrigatória:** ChromaDB → db-backend → db-frontend

---

## 1. ChromaDB (servidor vetorial)

O ChromaDB deve ser executado **separadamente** como um servidor HTTP. O backend consome sua API REST.

### Pré-requisitos

- Python 3.8+
- `pip install chromadb`

### Iniciar o servidor

```bash
chroma run --path ./chroma_db --port 8000
```

> O diretório `./chroma_db` é onde os dados vetoriais ficam persistidos. Ajuste o caminho conforme necessário.

O ChromaDB ficará disponível em: `http://localhost:8000`

---

## 2. db-backend (NestJS)

### Configuração do `.env`

Crie o arquivo `apps/db-backend/.env` com o seguinte conteúdo:

```env
# Porta em que o backend irá rodar
PORT=3000

# URL do servidor ChromaDB
CHROMA_PATH=http://localhost:8000
```

### Instalar dependências

```bash
cd apps/db-backend
npm install
```

### Executar em modo desenvolvimento

```bash
npx nx serve db-backend
```

O backend ficará disponível em: `http://localhost:3000/api`

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/query` | Busca semântica por texto |
| `GET` | `/api/report/:id` | Retorna um relatório pelo ID |

---

## 3. db-frontend (Vite / React)

### Configuração do `.env`

Crie o arquivo `apps/db-frontend/.env` com o seguinte conteúdo:

```env
# URL base da API do backend
VITE_API_BASE=http://localhost:3000/api
```

> **Importante:** No Vite, todas as variáveis expostas ao browser **precisam** ter o prefixo `VITE_`.
> Após criar ou alterar o `.env`, reinicie o servidor de dev para as variáveis serem carregadas.

### Instalar dependências

```bash
cd apps/db-frontend
npm install
```

### Executar em modo desenvolvimento

```bash
npx nx serve db-frontend
```

O frontend ficará disponível em: `http://localhost:4200`

---

## Resumo — Ordem de execução

Abra **3 terminais** e execute nessa ordem:

**Terminal 1 — ChromaDB**
```bash
chroma run --path ./chroma_db --port 8000
```

**Terminal 2 — Backend**
```bash
npx nx serve db-backend
```

**Terminal 3 — Frontend**
```bash
npx nx serve db-frontend
```

---

## Variáveis de Ambiente — Referência rápida

| App | Arquivo | Variável | Valor padrão |
|-----|---------|----------|--------------|
| `db-backend` | `apps/db-backend/.env` | `PORT` | `3000` |
| `db-backend` | `apps/db-backend/.env` | `CHROMA_PATH` | `http://localhost:8000` |
| `db-frontend` | `apps/db-frontend/.env` | `VITE_API_BASE` | `http://localhost:3000/api` |
