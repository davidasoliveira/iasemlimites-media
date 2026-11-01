# IA SEM LIMITES · media

Ficheiros públicos das publicações de @iasemlimites.pt, usados pelo Metricool para agendar.

## Site (link na bio)
`site/gerar.py` lê o `info.json` de cada pasta e gera o site; cada publicação só aparece depois de `publicar_em` (hora de Lisboa). O GitHub Actions (`.github/workflows/site.yml`) volta a gerar e publica no GitHub Pages a cada push no `main` e de 30 em 30 minutos.
Para uma publicação nova aparecer no site: criar `info.json` na pasta (copiar o de outra pasta como modelo).
Bibliotecas em `site/dados/`: `prompts.json` (por setor), `skills.json` e `ferramentas.json`. Cada entrada nova leva `adicionado` (AAAA-MM-DD) e aparece como NOVO durante 14 dias.
Páginas geradas: `index.html`, `prompts.html`, `skills.html`, `ferramentas.html`, mais `sitemap.xml` e `robots.txt`.
Pré-visualizar: `python3 site/gerar.py --agora 2026-11-05T13:00` e abrir `_site/index.html`.
