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
import shutil
import subprocess
import sys
import tempfile

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


# ---------------------------------------------------------------- vídeo motion (Reels)
VIDEO_CSS = """
.v { width:1080px; height:1920px; position:relative; overflow:hidden; font-family:Sora, Arial, sans-serif; }
.cena { position:absolute; inset:0; padding:300px 96px 480px; display:flex; flex-direction:column; justify-content:center; background:var(--nevoa); color:var(--grafite); opacity:0; }
.cena.escura { background:var(--grafite); color:var(--branco); }
.cena .logo-topo { position:absolute; top:150px; left:96px; width:220px; }
.cena .titulo-capa { font-size:104px; line-height:1.15; }
.cena .titulo { font-size:84px; line-height:1.2; }
.cena .texto { font-size:50px; }
.cena .chamada { font-size:32px; }
.cena .itens { margin-top:56px; display:grid; gap:36px; }
.cena .item { display:flex; gap:28px; align-items:baseline; font-size:52px; line-height:1.3; font-weight:500; }
.cena .item .num { font-size:30px; font-weight:600; color:var(--cinza); letter-spacing:.1em; min-width:56px; }
.cena .cta { font-size:64px; }
.v .hlv { background-image:linear-gradient(var(--laranja),var(--laranja)); background-repeat:no-repeat; background-size:0% 100%; border-radius:.12em; padding:0 .16em; }
.v .barra { position:absolute; z-index:5; left:96px; right:96px; top:96px; height:6px; border-radius:3px; background:var(--cinza-claro); opacity:.6; }
.v .barra i { display:block; height:100%; width:0; border-radius:3px; background:var(--grafite); }
"""

VIDEO_JS = """
const cenas=[...document.querySelectorAll('.cena')];
const durs=cenas.map(c=>parseFloat(c.dataset.dur));
const total=durs.reduce((a,b)=>a+b,0);
const ease=p=>1-Math.pow(1-p,3);
const clamp=x=>Math.max(0,Math.min(1,x));
window.setT=function(t){
  let ini=0;
  cenas.forEach((c,i)=>{
    const d=durs[i], lt=t-ini, ativa=(lt>=0 && lt<d) || (i===cenas.length-1 && t>=total);
    let op=0;
    if(ativa){ op=clamp(lt/0.25); if(i<cenas.length-1) op=Math.min(op, clamp((d-lt)/0.3)); }
    c.style.opacity=op;
    c.querySelectorAll('[data-in]').forEach(el=>{
      const p=ease(clamp((lt-parseFloat(el.dataset.in))/0.55));
      el.style.opacity=p; el.style.transform='translateY('+((1-p)*56)+'px)';
    });
    c.querySelectorAll('.hlv').forEach(el=>{
      const p=ease(clamp((lt-parseFloat(el.dataset.wipe))/0.5));
      el.style.backgroundSize=(p*100)+'% 100%';
      el.style.color = p>0.55 ? '#FFFFFF' : '';
    });
    ini+=d;
  });
  document.querySelector('.barra i').style.width=(Math.min(t/total,1)*100)+'%';
};
"""


def rich_video(texto, atraso):
    seguro = html.escape(texto)
    return re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span class="hlv" data-wipe="{atraso}">{m.group(1)}</span>', seguro)


def cena_html(c):
    escura = c["tipo"] == "cta"
    lg = (ASSETS / ("logo-grafite.png" if escura else "logo-nevoa.png")).as_uri()
    partes = [f'<img class="logo-topo" src="{lg}" alt="Cria Tecnologia">']
    t = 0.25
    if c.get("chamada"):
        partes.append(f'<div class="chamada" data-in="{t}">{html.escape(c["chamada"])}</div>'); t += 0.25
    classe = "titulo-capa" if c["tipo"] == "gancho" else "titulo"
    partes.append(f'<h2 class="{classe}" data-in="{t}">{rich_video(c["titulo"], t + 0.7)}</h2>'); t += 0.6
    if c.get("texto"):
        partes.append(f'<p class="texto" data-in="{t}">{rich_video(c["texto"], t + 0.7)}</p>'); t += 0.5
    if c.get("itens"):
        itens = "".join(
            f'<div class="item" data-in="{t + 0.7 * k:.2f}"><span class="num">{k + 1:02d}</span><span>{html.escape(x)}</span></div>'
            for k, x in enumerate(c["itens"]))
        partes.append(f'<div class="itens">{itens}</div>')
    if c.get("cta"):
        partes.append(f'<p class="cta" data-in="{t + 0.3}">{html.escape(c["cta"])}</p>')
    return f'<div class="cena{" escura" if escura else ""}" data-dur="{c["dur"]}">{"".join(partes)}</div>'


def achar_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"], check=True)
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_video(nav, post, s, pasta, n, fps=30):
    corpo = '<div class="v"><div class="barra"><i></i></div>' + "".join(cena_html(c) for c in s["cenas"]) + "</div>"
    doc = (f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><style>{CSS}{VIDEO_CSS}</style></head>"
           f"<body>{corpo}<script>{VIDEO_JS}</script></body></html>")
    tmp = pasta / f"_tmp_{n:02d}.html"
    tmp.write_text(doc, encoding="utf-8")
    pagina = nav.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
    pagina.goto(tmp.as_uri())
    pagina.evaluate("document.fonts.ready")
    total = sum(c["dur"] for c in s["cenas"])
    quadros = int(round(total * fps))
    with tempfile.TemporaryDirectory() as d:
        for i in range(quadros):
            pagina.evaluate(f"setT({i / fps})")
            pagina.screenshot(path=f"{d}/q{i:05d}.jpg", type="jpeg", quality=92)
        saida = pasta / f"{post['slug']}-{n:02d}.mp4"
        subprocess.run([achar_ffmpeg(), "-y", "-loglevel", "error",
                        "-framerate", str(fps), "-i", f"{d}/q%05d.jpg",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
                        "-preset", "medium", "-crf", "20", "-r", str(fps),
                        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(saida)], check=True)
    pagina.close()
    tmp.unlink()
    return saida.name


def contar_destaques(obj):
    return len(re.findall(r"\[\[.+?\]\]", json.dumps(obj, ensure_ascii=False)))


def validar(post):
    # Reels: capa e vídeo são peças separadas, cada uma com 1 destaque.
    grupos = post["pecas"] if post.get("formato") == "reels" else [post["pecas"]]
    for g in grupos:
        n = contar_destaques(g)
        if n != 1:
            raise SystemExit(f"Regra da marca: cada peça precisa de exatamente 1 destaque laranja, encontrei {n}.")
    for s in post["pecas"]:
        if s["layout"] not in LAYOUTS and s["layout"] != "reels_video":
            raise SystemExit(f"Layout desconhecido: {s['layout']}")
    for s in post["pecas"]:
        if s["layout"] == "reels_video":
            total = sum(c["dur"] for c in s["cenas"])
            if not 15 <= total <= 30:
                raise SystemExit(f"O vídeo precisa ter de 15 a 30 segundos, tem {total}.")


def render(caminho_post):
    caminho_post = pathlib.Path(caminho_post).resolve()
    post = json.loads(caminho_post.read_text(encoding="utf-8"))
    validar(post)
    total = len(post["pecas"])
    saidas = []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        for n, s in enumerate(post["pecas"], 1):
            if s["layout"] == "reels_video":
                saidas.append(render_video(nav, post, s, caminho_post.parent, n))
                continue
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
