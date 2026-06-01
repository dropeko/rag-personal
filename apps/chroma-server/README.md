# chroma-server

App Python que sobe o servidor [ChromaDB](https://www.trychroma.com/) via CLI.

## Requisitos

- Python 3.9+
- `chromadb` e `python-dotenv` instalados (veja abaixo)

## Configuração

1. Copie o arquivo de exemplo e preencha o caminho do banco de dados:
   ```bash
   cp apps/chroma-server/.env.example apps/chroma-server/.env
   ```

2. Edite `apps/chroma-server/.env`:
   ```
   CHROMA_DB_PATH=C:\caminho\para\seu\chromadb\data
   ```

## Como rodar

### Via Nx (recomendado)

```bash
# Instalar dependências Python
npx nx run chroma-server:install

# Subir o servidor (porta 8000)
npx nx run chroma-server:serve
```

### Diretamente com Python

```bash
cd apps/chroma-server
pip install -r requirements.txt
python server.py
```

## Verificar se está rodando

Acesse: [http://localhost:8000/api/v1/heartbeat](http://localhost:8000/api/v1/heartbeat)

Resposta esperada: `{"nanosecond heartbeat": ...}`
