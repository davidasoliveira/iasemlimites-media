#!/usr/bin/env python3
"""Gera o site da IA SEM LIMITES (link na bio) a partir das pastas de publicações.

Cada pasta AAAA-MM-DD-nome com um info.json aparece no site depois de
`publicar_em` (hora de Lisboa). Sem dependências obrigatórias; usa o Pillow
para reduzir as capas, se estiver instalado.

Uso: python3 site/gerar.py [--saida _site] [--agora 2026-11-05T13:00]
"""
import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
LISBOA = ZoneInfo("Europe/Lisbon")
INSTAGRAM = "https://www.instagram.com/iasemlimites.pt/"
MENSAGEM = "https://ig.me/m/iasemlimites.pt"
SITE_URL = "https://davidasoliveira.github.io/iasemlimites-media/"

SERIES = [
    ("⚡", "Truque de 30 s", "Um truque rápido em apps que já usas: Gmail, WhatsApp, Excel, Canva."),
    ("📶", "Nível 1, 2, 3", "A mesma tarefa com três ferramentas, do básico ao profissional."),
    ("🤔", "Real ou IA?", "Consegues distinguir? Diz nos comentários e vê a resposta."),
    ("🆕", "Novidades verificadas", "O que saiu esta semana e se já está disponível em Portugal."),
]

e = html.escape


def ler_publicacoes(agora):
    pubs = []
    for info in sorted(RAIZ.glob("20??-??-??-*/info.json")):
        dados = json.loads(info.read_text(encoding="utf-8"))
        quando = datetime.fromisoformat(dados["publicar_em"]).replace(tzinfo=LISBOA)
        if quando > agora:
            continue
        dados["_pasta"] = info.parent
        dados["_quando"] = quando
        pubs.append(dados)
    pubs.sort(key=lambda p: p["_quando"], reverse=True)
    return pubs


def copiar_capa(pub, saida):
    origem = pub["_pasta"] / pub["capa"]
    destino = saida / "capas" / f"{pub['_pasta'].name}.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image

        im = Image.open(origem).convert("RGB")
        im.thumbnail((540, 960))
        im.save(destino, quality=82, optimize=True)
    except ImportError:
        destino = destino.with_suffix(origem.suffix)
        shutil.copy(origem, destino)
    return f"capas/{destino.name}"


MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]


def data_pt(d):
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def bloco_prompt(p):
    return (
        '<div class="prompt"><div class="prompt-topo">'
        f'<strong>{e(p["titulo"])}</strong>'
        '<button class="copiar" type="button">Copiar</button></div>'
        f'<pre>{e(p["texto"])}</pre></div>'
    )


def cartao(pub, capa):
    tipo = e(pub.get("tipo", "Reel"))
    link_ig = pub.get("instagram_url") or INSTAGRAM
    partes = [f'<p class="resumo">{e(pub.get("resumo", ""))}</p>']
    if pub.get("pontos"):
        partes.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in pub["pontos"]) + "</ul>")
    for p in pub.get("prompts", []):
        partes.append(bloco_prompt(p))
    if pub.get("ferramentas"):
        links = "".join(
            f'<a class="chip" href="{e(f["url"])}" target="_blank" rel="noopener">{e(f["nome"])} ↗</a>'
            for f in pub["ferramentas"]
        )
        partes.append(f'<div class="ferramentas"><span>Ferramentas:</span>{links}</div>')
    if pub.get("fonte"):
        f = pub["fonte"]
        partes.append(f'<p class="fonte">Fonte: <a href="{e(f["url"])}" target="_blank" rel="noopener">{e(f["nome"])}</a></p>')
    partes.append(f'<a class="ver-ig" href="{e(link_ig)}" target="_blank" rel="noopener">Ver no Instagram →</a>')
    return f"""
<article class="cartao" data-tipo="{tipo}">
  <img src="{capa}" alt="Capa: {e(pub['titulo'])}" loading="lazy" width="540" height="960">
  <div class="corpo">
    <div class="meta"><span class="etiqueta">{tipo}</span><time datetime="{pub['_quando'].date()}">{data_pt(pub['_quando'])}</time></div>
    <h3>{e(pub['titulo'])}</h3>
    <details><summary>Ver o que aprendes</summary>{''.join(partes)}</details>
  </div>
</article>"""


def gerar(saida, agora):
    if saida.exists():
        shutil.rmtree(saida)
    saida.mkdir(parents=True)
    shutil.copytree(RAIZ / "site" / "assets", saida / "assets")
    pubs = ler_publicacoes(agora)

    cartoes = "".join(cartao(p, copiar_capa(p, saida)) for p in pubs)
    tipos = sorted({p.get("tipo", "Reel") for p in pubs})
    filtros = '<button class="filtro ativo" data-f="*">Tudo</button>' + "".join(
        f'<button class="filtro" data-f="{e(t)}">{e(t)}</button>' for t in tipos
    )
    if not pubs:
        cartoes = '<p class="vazio">As primeiras publicações chegam já hoje. Segue no Instagram para não perderes.</p>'
        filtros = ""

    todos_prompts = [(p, pub) for pub in pubs for p in pub.get("prompts", [])]
    prompts_html = "".join(bloco_prompt(p) for p, _ in todos_prompts) or (
        '<p class="vazio">Em breve: prompts prontos a copiar.</p>'
    )
    series_html = "".join(
        f'<div class="serie"><div class="ico">{i}</div><h3>{e(t)}</h3><p>{e(d)}</p></div>' for i, t, d in SERIES
    )
    atualizado = data_pt(agora)

    pagina = (RAIZ / "site" / "modelo.html").read_text(encoding="utf-8")
    for chave, valor in {
        "{{CARTOES}}": cartoes,
        "{{FILTROS}}": filtros,
        "{{PROMPTS}}": prompts_html,
        "{{N_PROMPTS}}": str(len(todos_prompts)),
        "{{SERIES}}": series_html,
        "{{INSTAGRAM}}": INSTAGRAM,
        "{{MENSAGEM}}": MENSAGEM,
        "{{SITE_URL}}": SITE_URL,
        "{{ATUALIZADO}}": atualizado,
        "{{ANO}}": str(agora.year),
    }.items():
        pagina = pagina.replace(chave, valor)
    (saida / "index.html").write_text(pagina, encoding="utf-8")
    (saida / ".nojekyll").write_text("")
    print(f"Site gerado em {saida} com {len(pubs)} publicações e {len(todos_prompts)} prompts.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(RAIZ / "_site"))
    ap.add_argument("--agora", help="Simular outra data/hora (Lisboa), ex.: 2026-11-05T13:00")
    a = ap.parse_args()
    agora = (
        datetime.fromisoformat(a.agora).replace(tzinfo=LISBOA) if a.agora else datetime.now(LISBOA)
    )
    gerar(Path(a.saida), agora)
