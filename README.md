# IA SEM LIMITES · media

Ficheiros públicos das publicações de @iasemlimites.pt, usados pelo Metricool para agendar.

## Site (link na bio): https://iasemlimites.github.io/
O conteúdo do site vive aqui; quem o publica é o repositório `iasemlimites/iasemlimites.github.io`, que lê este repositório de 30 em 30 minutos.
`site/gerar.py` lê o `info.json` de cada pasta; cada publicação só aparece depois de `publicar_em` (hora de Lisboa).
Bibliotecas em `site/dados/`: `prompts.json` (por setor), `skills.json` e `ferramentas.json`. Cada entrada nova leva `adicionado` (AAAA-MM-DD) e aparece como NOVO durante 14 dias.
O workflow `.github/workflows/site.yml` só verifica que o site gera sem erros.
Pré-visualizar: `python3 site/gerar.py --agora 2026-11-05T13:00` e abrir `_site/index.html`.
