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
LANCAMENTO = "2026-11-01"
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


def cartao(pub, capa):
    tipo = e(pub.get("tipo", "Reel"))
    link_ig = pub.get("instagram_url") or INSTAGRAM
    partes = [f'<p class="resumo">{e(pub.get("resumo", ""))}</p>']
    if pub.get("pontos"):
        partes.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in pub["pontos"]) + "</ul>")
    for p in pub.get("prompts", []):
        partes.append(prompt_html(p))
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


def carregar(nome):
    return json.loads((RAIZ / "site" / "dados" / nome).read_text(encoding="utf-8"))


def e_novo(item, agora):
    d = item.get("adicionado")
    # O que entrou no lançamento não leva "NOVO"; só o que se acrescenta depois.
    return bool(d) and d > LANCAMENTO and (agora.date() - datetime.fromisoformat(d).date()).days <= 14


def selo(item, agora):
    return '<span class="novo">NOVO</span>' if e_novo(item, agora) else ""


def prompt_html(p, agora=None):
    novo = selo(p, agora) if agora else ""
    return (
        '<div class="prompt" data-busca><div class="prompt-topo">'
        f'<strong>{e(p["titulo"])}{novo}</strong>'
        '<button class="copiar" type="button">Copiar</button></div>'
        f'<pre>{e(p["texto"])}</pre></div>'
    )


PAGINAS = [
    ("index.html", "Início"),
    ("prompts.html", "Prompts"),
    ("skills.html", "Skills"),
    ("ferramentas.html", "Ferramentas"),
    ("index.html#contacto", "Parcerias"),
]


def menu(atual):
    return "".join(
        f'<a href="{h}"{" class=\"atual\"" if h == atual else ""}>{e(n)}</a>' for h, n in PAGINAS
    )


def cabecalho(titulo_html, sub, grande=False):
    classe = "topo envolve" if grande else "topo pequeno envolve"
    return f"""<header class="{classe}">
  <a href="index.html"><img src="assets/simbolo.png" alt="IA SEM LIMITES, início"></a>
  <h1>{titulo_html}</h1>
  <p class="slogan">Aprende. Descobre. Transforma.</p>
  <p class="sub">{sub}</p>
  <div class="botoes"><a class="btn principal" href="{INSTAGRAM}" target="_blank" rel="noopener">Seguir no Instagram</a></div>
</header>"""


def pagina(modelo, saida, ficheiro, titulo, descricao, cab, conteudo, agora):
    html_ = modelo
    for chave, valor in {
        "{{TITULO}}": e(titulo),
        "{{DESCRICAO}}": e(descricao),
        "{{CAMINHO}}": "" if ficheiro == "index.html" else ficheiro,
        "{{CABECALHO}}": cab,
        "{{MENU}}": menu(ficheiro),
        "{{CONTEUDO}}": conteudo,
        "{{SITE_URL}}": SITE_URL,
        "{{ATUALIZADO}}": data_pt(agora),
        "{{ANO}}": str(agora.year),
    }.items():
        html_ = html_.replace(chave, valor)
    (saida / ficheiro).write_text(html_, encoding="utf-8")


def gerar(saida, agora):
    if saida.exists():
        shutil.rmtree(saida)
    saida.mkdir(parents=True)
    shutil.copytree(RAIZ / "site" / "assets", saida / "assets")
    modelo = (RAIZ / "site" / "modelo.html").read_text(encoding="utf-8")
    pubs = ler_publicacoes(agora)
    bib = carregar("prompts.json")["setores"]
    skills = carregar("skills.json")["skills"]
    ferr = carregar("ferramentas.json")
    nomes_setor = {s["id"]: s for s in bib}
    n_prompts = sum(len(s["prompts"]) for s in bib)

    # ---------- Início ----------
    cartoes = "".join(cartao(p, copiar_capa(p, saida)) for p in pubs)
    tipos = sorted({p.get("tipo", "Reel") for p in pubs})
    filtros = '<button class="filtro ativo" data-f="*">Tudo</button>' + "".join(
        f'<button class="filtro" data-f="{e(t)}">{e(t)}</button>' for t in tipos
    )
    if not pubs:
        cartoes = '<p class="vazio">As primeiras publicações chegam já hoje. Segue no Instagram para não perderes.</p>'
        filtros = ""
    destaques = f"""<div class="destaques">
  <a class="destaque" href="prompts.html"><div class="num grad">{n_prompts}</div><h3>Prompts por setor</h3><p>Marketing, vendas, finanças, RH, atendimento e mais. Prontos a copiar.</p><span class="ir">Ver prompts →</span></a>
  <a class="destaque" href="skills.html"><div class="num grad">{len(skills)}</div><h3>Skills prontas</h3><p>Instruções que transformam o ChatGPT, o Claude ou o Gemini num assistente teu.</p><span class="ir">Ver skills →</span></a>
  <a class="destaque" href="ferramentas.html"><div class="num grad">{len(ferr["ferramentas"])}</div><h3>Ferramentas de IA</h3><p>As que usamos nos Reels, com o que fazem e se têm plano gratuito.</p><span class="ir">Ver ferramentas →</span></a>
</div>"""
    series_html = "".join(
        f'<div class="serie"><div class="ico">{i}</div><h3>{e(t)}</h3><p>{e(d)}</p></div>' for i, t, d in SERIES
    )
    inicio = f"""
<section id="recursos"><h2>Recursos grátis</h2><p class="intro">Tudo o que é útil partilhar sobre IA, num só sítio e sempre atualizado.</p>{destaques}</section>
<section id="reels"><h2>Últimos Reels</h2><p class="intro">Viste um Reel e queres o link ou o passo a passo? Está aqui.</p>
<div class="filtros">{filtros}</div><div class="grelha">{cartoes}</div></section>
<section id="series"><h2>As nossas séries</h2><p class="intro">Formatos fixos para aprenderes um pouco todos os dias.</p><div class="series">{series_html}</div></section>
<section id="contacto"><div class="contacto"><h2>Parcerias e sugestões</h2>
<p class="intro">Tens uma ferramenta de IA para mostrarmos ou um tema que queres ver explicado? Fala connosco.</p>
<a class="btn principal" href="{MENSAGEM}" target="_blank" rel="noopener">Enviar mensagem no Instagram</a></div></section>"""
    pagina(modelo, saida, "index.html", "IA SEM LIMITES | Dicas de IA em português",
           "Aprende Inteligência Artificial de forma simples, em português: tutoriais, prompts por setor, skills e ferramentas verificadas.",
           cabecalho('IA <span class="grad">SEM LIMITES</span>',
                     "Inteligência Artificial sem complicações, em português. Tudo o que mostramos nos Reels, com as ferramentas, os links e os prompts prontos a copiar.", True),
           inicio, agora)

    # ---------- Prompts ----------
    dos_reels = [p for pub in pubs for p in pub.get("prompts", [])]
    setores = list(bib)
    if dos_reels:
        setores = [{"id": "dos-reels", "nome": "Dos nossos Reels", "icone": "▶️", "prompts": dos_reels}] + setores
    chips = "".join(f'<button class="filtro" data-ir="{s["id"]}">{s["icone"]} {e(s["nome"])}</button>' for s in setores)
    blocos = "".join(
        f'<section class="setor" id="{s["id"]}"><h2>{s["icone"]} {e(s["nome"])}</h2>'
        f'<div class="lista-prompts">{"".join(prompt_html(p, agora) for p in s["prompts"])}</div></section>'
        for s in setores
    )
    conteudo = f"""<section><p class="intro">Copia, cola no ChatGPT, Claude, Gemini ou Copilot e troca o que está entre [ ] pelo teu caso. Prompts originais, pensados para negócios e pessoas em Portugal.</p>
<input class="pesquisa" type="search" placeholder="Pesquisar prompts (ex.: email, Excel, Instagram)" aria-label="Pesquisar prompts">
<div class="filtros">{chips}</div></section>{blocos}"""
    pagina(modelo, saida, "prompts.html", f"{n_prompts} prompts de IA por setor | IA SEM LIMITES",
           "Prompts de IA prontos a copiar para marketing, vendas, conteúdo digital, finanças, recursos humanos, atendimento, gestão, estudo, restauração e imobiliário.",
           cabecalho('Prompts <span class="grad">por setor</span>', "Para o teu trabalho e o teu dia a dia. Novos prompts todas as semanas."),
           conteudo, agora)

    # ---------- Skills ----------
    como = """<div class="passos">
<div class="passo"><h3>No Claude</h3>Escreve "Ajuda-me a criar uma skill com estas instruções", cola o texto e guarda a skill que ele cria. Fica em Personalizar › Skills.</div>
<div class="passo"><h3>No ChatGPT</h3>Cria um projeto (ou um GPT) e cola o texto nas instruções. Todas as conversas lá dentro seguem estas regras.</div>
<div class="passo"><h3>No Gemini</h3>Cria um Gem, dá-lhe um nome e cola o texto nas instruções.</div>
</div>"""
    por_setor = {}
    for k in skills:
        por_setor.setdefault(k["setor"], []).append(k)
    blocos = ""
    for sid, lista in por_setor.items():
        s = nomes_setor.get(sid, {"nome": sid, "icone": "🧩"})
        itens = "".join(
            f'<div class="skill" data-busca><h3>{e(k["nome"])}{selo(k, agora)}</h3><p>{e(k["para_que"])}</p>'
            f'<div class="prompt"><div class="prompt-topo"><strong>Instruções</strong><button class="copiar" type="button">Copiar</button></div><pre>{e(k["instrucoes"])}</pre></div>'
            f'<p class="exemplo">Depois experimenta: <em>{e(k["exemplo"])}</em></p></div>'
            for k in lista
        )
        blocos += f'<section class="setor" id="{sid}"><h2>{s["icone"]} {e(s["nome"])}</h2><div class="lista-prompts">{itens}</div></section>'
    conteudo = f"""<section><h2>Como usar</h2><p class="intro">Uma skill é um conjunto de instruções que a IA segue sempre. Copia o texto, troca o que está entre [ ] e instala uma vez.</p>{como}
<input class="pesquisa" type="search" placeholder="Pesquisar skills" aria-label="Pesquisar skills" style="margin-top:20px"></section>{blocos}"""
    pagina(modelo, saida, "skills.html", f"{len(skills)} skills de IA prontas a usar | IA SEM LIMITES",
           "Skills e instruções prontas para o Claude, ChatGPT e Gemini: emails, atas, propostas, atendimento, Excel, recrutamento e mais.",
           cabecalho('Skills <span class="grad">prontas</span>', "Ensina a IA uma vez e ela trabalha à tua maneira sempre."),
           conteudo, agora)

    # ---------- Ferramentas ----------
    itens = "".join(
        f'<a class="ferr" data-busca href="{e(f["url"])}" target="_blank" rel="noopener"><h3>{e(f["nome"])}</h3>'
        f'<span class="emp">{e(f["empresa"])}</span><p>{e(f["para_que"])}</p><span class="preco">{e(f["preco"])} ↗</span></a>'
        for f in ferr["ferramentas"]
    )
    conteudo = f"""<section><p class="intro">As ferramentas que usamos e recomendamos. Os planos e preços mudam: confirma sempre no site oficial.</p>
<div class="series">{itens}</div><p class="nota">Lista revista a {data_pt(datetime.fromisoformat(ferr["verificado_em"]))}. Sem links de afiliado.</p></section>"""
    pagina(modelo, saida, "ferramentas.html", "Ferramentas de IA recomendadas | IA SEM LIMITES",
           "As melhores ferramentas de Inteligência Artificial para o dia a dia, explicadas em português, com indicação de plano gratuito.",
           cabecalho('Ferramentas <span class="grad">de IA</span>', "O que usar para cada tarefa, sem complicações."),
           conteudo, agora)

    # ---------- SEO ----------
    hoje = agora.date().isoformat()
    urls = "".join(
        f"<url><loc>{SITE_URL}{'' if f == 'index.html' else f}</loc><lastmod>{hoje}</lastmod></url>"
        for f in ("index.html", "prompts.html", "skills.html", "ferramentas.html")
    )
    (saida / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8",
    )
    (saida / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    (saida / ".nojekyll").write_text("")
    print(f"Site gerado em {saida}: {len(pubs)} publicações, {n_prompts} prompts, {len(skills)} skills.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=str(RAIZ / "_site"))
    ap.add_argument("--agora", help="Simular outra data/hora (Lisboa), ex.: 2026-11-05T13:00")
    a = ap.parse_args()
    agora = (
        datetime.fromisoformat(a.agora).replace(tzinfo=LISBOA) if a.agora else datetime.now(LISBOA)
    )
    gerar(Path(a.saida), agora)
