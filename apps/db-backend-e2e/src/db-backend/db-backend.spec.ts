import axios from 'axios';

describe('Reports API (e2e)', () => {
  let createdReportId: number;

  it('POST /api/reports should create a new report', async () => {
    const reportData = {
      numero_relatorio: 'REL-2026-001',
      revisao: '0',
      cliente: 'Empresa Teste',
      unidade: 'Unidade Alpha',
      numero_ss: 'SS-999',
      numero_contrato: 'CONT-123',
      tipo_equipamento: 'Reator',
      tag: 'R-01',
      sections: [
        { title: 'Introdução', content: 'Conteúdo de teste.' }
      ],
      ensaios: [
        {
          tipo: 'Visual',
          texto: 'Ensaio visual realizado.',
          imagens: [
            { caminho_imagem: 'http://example.com/img.jpg', legenda: 'Legenda 1' }
          ]
        }
      ]
    };

    const res = await axios.post(`/api/reports`, reportData);

    expect(res.status).toBe(201);
    expect(res.data).toHaveProperty('id');
    expect(res.data.numero_relatorio).toBe('REL-2026-001');
    createdReportId = res.data.id;
  });

  it('GET /api/reports should return a list of reports', async () => {
    const res = await axios.get(`/api/reports`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    expect(res.data.length).toBeGreaterThan(0);
  });

  it('GET /api/reports/:id should return a specific report', async () => {
    const res = await axios.get(`/api/reports/${createdReportId}`);

    expect(res.status).toBe(200);
    expect(res.data.id).toBe(createdReportId);
    expect(res.data.cliente.nome).toBe('Empresa Teste');
  });

  it('GET /api/reports/search should find reports by query', async () => {
    const res = await axios.get(`/api/reports/search?q=REL-2026-001`);

    expect(res.status).toBe(200);
    expect(Array.isArray(res.data)).toBe(true);
    expect(res.data.some(r => r.numero_relatorio === 'REL-2026-001')).toBe(true);
  });
});

