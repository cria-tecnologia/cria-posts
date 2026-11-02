"""Gera as peças da Cria Tecnologia a partir de um post.json.

Uso: python render.py posts/2026-11-02/post.json
Saída: PNGs na mesma pasta do post.json.

Regras da marca aplicadas aqui (Manual da marca v1.0):
- Cores: Grafite #1B1E24, Laranja Sinal #FF5B14, Névoa #F4F5F7, Branco, Cinza Texto #5C6068, Cinza Claro #C3C6CC.
- Fonte Sora. Logo sempre do arquivo da marca (assets/logo-*.png), nunca redigitado.
- Um único destaque em bloco laranja por peça: marcado no texto como [[palavra]].
"""
import html
import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

CSS = """
@font-face { font-family: Sora; src: url('ASSETS/Sora.ttf'); font-weight: 100 800; }
* { box-sizing: border-box; margin: 0; padding: 0; }
:root { --grafite:#1B1E24; --laranja:#FF5B14; --nevoa:#F4F5F7; --branco:#FFFFFF; --cinza:#5C6068; --cinza-claro:#C3C6CC; }
body { font-family: Sora, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
.peca { width: 1080px; height: 1350px; padding: 96px; display: flex; flex-direction: column; background: var(--nevoa); color: var(--grafite); position: relative; overflow: hidden; }
.peca.escura { background: var(--grafite); color: var(--branco); }
.peca.reels { height: 1920px; padding: 0 96px; }
.topo { display: flex; justify-content: space-between; font-size: 26px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase; color: var(--cinza); }
.escura .topo { color: var(--cinza-claro); }
.miolo { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.titulo-capa { font-size: 96px; line-height: 1.16; font-weight: 600; letter-spacing: -.02em; }
.titulo { font-size: 76px; line-height: 1.2; font-weight: 600; letter-spacing: -.015em; }
.texto { font-size: 46px; line-height: 1.45; font-weight: 400; color: var(--cinza); margin-top: 48px; }
.escura .texto { color: var(--cinza-claro); }
.chamada { font-size: 30px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase; color: var(--cinza); margin-bottom: 28px; }
.chamada::after { content: ""; display: block; width: 64px; height: 3px; background: var(--cinza-claro); margin-top: 20px; }
.cta { font-size: 54px; font-weight: 600; margin-top: 56px; }
.hl { background: var(--laranja); color: var(--branco); border-radius: .12em; padding: 0 .16em; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.rodape { display: flex; justify-content: space-between; align-items: center; }
.rodape img { width: 200px; display: block; }
.arraste { display: flex; align-items: center; gap: 20px; font-size: 30px; font-weight: 600; }
.cards { display: grid; gap: 24px; margin-top: 44px; }
.card { border-radius: 16px; padding: 40px 44px; }
.card .rotulo { font-size: 26px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; margin-bottom: 14px; }
.card .conteudo { font-size: 38px; line-height: 1.4; }
.card.antes { background: var(--branco); border: 2px solid var(--cinza-claro); color: var(--cinza); }
.card.antes .rotulo { color: var(--cinza); }
.card.depois { background: var(--grafite); color: var(--branco); }
.card.depois .rotulo { color: var(--cinza-claro); }
.reels .area-segura { position: absolute; left: 96px; right: 96px; top: 285px; height: 1350px; display: flex; flex-direction: column; padding: 96px 0; }
.reels .titulo-capa { font-size: 112px; }
""".replace("ASSETS", ASSETS.as_uri())

SETA = '<svg width="52" height="28" viewBox="0 0 52 28"><path d="M2 14H48M36 2L49 14L36 26" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def rich(texto):
    """Escapa o texto e transforma [[palavra]] no bloco laranja."""
    seguro = html.escape(texto)
    return re.sub(r"\[\[(.+?)\]\]", r'<span class="hl">\1</span>', seguro)


def logo(escura):
    arquivo = "logo-grafite.png" if escura else "logo-nevoa.png"
    return f'<img src="{(ASSETS / arquivo).as_uri()}" alt="Cria Tecnologia">'


def topo(post, n, total):
    contador = f"{n:02d}/{total:02d}" if total > 1 else ""
    return f'<div class="topo"><span>{html.escape(post["tema"])}</span><span>{contador}</span></div>'


def layout_capa(post, s, n, total):
    sub = f'<p class="texto">{rich(s["subtitulo"])}</p>' if s.get("subtitulo") else ""
    arraste = f'<div class="arraste">Arraste para o lado {SETA}</div>' if total > 1 else ""
    return f'''<div class="peca">{topo(post, n, total)}
      <div class="miolo"><h1 class="titulo-capa">{rich(s["titulo"])}</h1>{sub}</div>
      <div class="rodape">{logo(False)}{arraste}</div></div>'''


def layout_interno(post, s, n, total):
    cham = f'<div class="chamada">{html.escape(s["chamada"])}</div>' if s.get("chamada") else ""
    return f'''<div class="peca">{topo(post, n, total)}
      <div class="miolo">{cham}<h2 class="titulo">{rich(s["titulo"])}</h2><p class="texto">{rich(s["texto"])}</p></div>
      <div class="rodape">{logo(False)}</div></div>'''


def layout_cta(post, s, n, total):
    return f'''<div class="peca escura">{topo(post, n, total)}
      <div class="miolo"><h2 class="titulo">{rich(s["titulo"])}</h2><p class="texto">{rich(s["texto"])}</p>
      <p class="cta">{rich(s["cta"])}</p></div>
      <div class="rodape">{logo(True)}</div></div>'''


def layout_estatico(post, s, n, total):
    return f'''<div class="peca">{topo(post, n, total)}
      <div class="miolo"><h2 class="titulo" style="font-size:64px">{rich(s["titulo"])}</h2>
        <div class="cards">
          <div class="card antes"><div class="rotulo">Antes</div><div class="conteudo">{rich(s["antes"])}</div></div>
          <div class="card depois"><div class="rotulo">Depois</div><div class="conteudo">{rich(s["depois"])}</div></div>
        </div>
        <p class="texto" style="font-size:34px;margin-top:32px;margin-bottom:24px">{rich(s["cta"])}</p></div>
      <div class="rodape">{logo(False)}</div></div>'''


def layout_reels_capa(post, s, n, total):
    sub = f'<p class="texto">{rich(s["subtitulo"])}</p>' if s.get("subtitulo") else ""
    return f'''<div class="peca escura reels"><div class="area-segura">{topo(post, 1, 1)}
      <div class="miolo"><h1 class="titulo-capa">{rich(s["titulo"])}</h1>{sub}</div>
      <div class="rodape">{logo(True)}</div></div></div>'''


LAYOUTS = {
    "capa": (layout_capa, 1350),
    "interno": (layout_interno, 1350),
    "cta": (layout_cta, 1350),
    "estatico": (layout_estatico, 1350),
    "reels_capa": (layout_reels_capa, 1920),
}


def validar(post):
    textos = json.dumps(post["pecas"], ensure_ascii=False)
    destaques = len(re.findall(r"\[\[.+?\]\]", textos))
    if destaques != 1:
        raise SystemExit(f"Regra da marca: a peça precisa de exatamente 1 destaque laranja, tem {destaques}.")
    for s in post["pecas"]:
        if s["layout"] not in LAYOUTS:
            raise SystemExit(f"Layout desconhecido: {s['layout']}")


def render(caminho_post):
    caminho_post = pathlib.Path(caminho_post).resolve()
    post = json.loads(caminho_post.read_text(encoding="utf-8"))
    validar(post)
    total = len(post["pecas"])
    saidas = []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        for n, s in enumerate(post["pecas"], 1):
            fn, altura = LAYOUTS[s["layout"]]
            corpo = fn(post, s, n, total)
            doc = f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{corpo}</body></html>"
            tmp = caminho_post.parent / f"_tmp_{n:02d}.html"
            tmp.write_text(doc, encoding="utf-8")
            pagina = nav.new_page(viewport={"width": 1080, "height": altura}, device_scale_factor=1)
            pagina.goto(tmp.as_uri())
            pagina.evaluate("document.fonts.ready")
            saida = caminho_post.parent / f"{post['slug']}-{n:02d}.png"
            pagina.screenshot(path=str(saida), full_page=False)
            pagina.close()
            tmp.unlink()
            saidas.append(saida.name)
        nav.close()
    (caminho_post.parent / "pronto.json").write_text(json.dumps({"arquivos": saidas}, ensure_ascii=False), encoding="utf-8")
    print("\n".join(saidas))


if __name__ == "__main__":
    render(sys.argv[1])
