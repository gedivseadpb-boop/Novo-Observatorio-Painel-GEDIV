"""Pacote OFICIAL do Painel Unificado GEDIV para o GitHub Pages (domínio próprio), sem nenhum dado fictício.

Enquanto não houver dados oficiais aprovados (coleta real comprovada, cobertura validada e conferência da GEDIV),
o pacote publica o estado "Dados oficiais em validação":

- interface aprovada (`observatorio/web/unificado/index.html`, Delicadeza Visual, 240 cores) com as 7 abas, filtros e
  navegação preservados;
- indicadores, gráficos e tabelas INDISPONÍVEIS (nunca zero: zero só pode aparecer com cobertura validada e ausência
  de ocorrências comprovada, o que este pacote não tem);
- nenhum registro, nenhum dado pessoal, nenhum PDF, banco, backup ou credencial; funções que exigem servidor mostram
  aviso.

A validação é fechada: qualquer arquivo fora da lista, marca de carga fictícia (FICTICIO, SAD-PSE-2099, matrícula 950.,
dados-sinteticos), registro, dado pessoal ou credencial reprova o pacote antes da publicação.

A demonstração sintética continua em `scripts/preparar_previa_github_pages.py`, só para testes e homologação local.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HTML_ORIGEM = RAIZ / "observatorio" / "web" / "unificado" / "index.html"
PALETA_JSON = RAIZ / "observatorio" / "web" / "unificado" / "paleta-aprovada.json"

ESTADO_ARQUIVO = "estado-publicacao.json"
PERMITIDOS = {".nojekyll", "index.html", ESTADO_ARQUIVO}
PERMITIDOS_COM_DOMINIO = PERMITIDOS | {"CNAME"}
TITULO_AVISO = "Dados oficiais em validação"
TEXTO_AVISO = ("Indicadores, gráficos e tabelas ficam indisponíveis até a publicação de dados aprovados do "
               "Diário Oficial do Estado da Paraíba, coletados, conferidos e homologados pela GEDIV.")
TEXTO_INDISPONIVEL = "Indisponível · dados oficiais em validação"

# Marcas de carga fictícia ou de demonstração: nenhuma pode aparecer no pacote oficial
MARCAS_FICTICIAS = (
    (re.compile(r"FICT[IÍ]CI", re.I), "nome ou texto fictício"),
    (re.compile(r"SAD-PSE-2099"), "processo sintético (2099)"),
    (re.compile(r"\b950\.\d{3}-\d\b"), "matrícula sintética (950.xxx-x)"),
    (re.compile(r"dados-sinteticos", re.I), "arquivo de dados sintéticos"),
    (re.compile(r"avisoDemonstracao|GEDIV_STATIC_DEMO|modoDemonstracaoEstatica"), "modo demonstração"),
    (re.compile(r"Demonstra[cç][aã]o com dados fict", re.I), "faixa da demonstração"),
)
# Dados pessoais, credenciais e caminhos privados
MARCAS_PRIVADAS = (
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "CPF"),
    (re.compile(r"SAD-PSE-20[0-9]{2}/\d+"), "número de processo"),
    (re.compile(r"\b\d{5,6}-\d\b"), "matrícula"),
    (re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})"), "token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "chave privada"),
    (re.compile(r"(PreviaGediv2026!|previa\.gediv|SenhaAdm#|SenhaGer1#)"), "senha de teste"),
    (re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+", re.I), "caminho local do Windows"),
    (re.compile(r"/api/pdf/"), "rota de PDF privado"),
    (re.compile(r"\.(sqlite3?|db|gedivbak)\b"), "banco ou backup"),
)
EXTENSOES_PROIBIDAS = {".pdf", ".sqlite", ".sqlite3", ".db", ".gedivbak", ".env", ".csv", ".xlsx", ".zip", ".key", ".pem"}

ESTILO = """<style id="estiloValidacao">
#avisoValidacao{background:var(--navy);color:var(--white);border-bottom:4px solid var(--orange);padding:12px max(16px,4vw);font:16px/1.45 system-ui,sans-serif;text-align:center}
#avisoValidacao strong{display:block;font-size:18px;font-weight:800}
#avisoValidacao span{display:block;font-size:14px;opacity:.92;margin-top:2px}
body.estado-validacao #connectionBar,body.estado-validacao #receivedSummaryBar,body.estado-validacao .pending-card,body.estado-validacao .download-main,body.estado-validacao #downloadMenu,body.estado-validacao #coverageOpen,body.estado-validacao #full,body.estado-validacao #toggleZeroGroups,body.estado-validacao .table-pager,body.estado-validacao .table-toolbar{display:none!important}
body.estado-validacao .svc-count,body.estado-validacao .qty,body.estado-validacao .pending-number{visibility:hidden}
body.estado-validacao #kpis .kpi{position:relative;cursor:default}
body.estado-validacao #kpis .kpi .val,body.estado-validacao #kpis .kpi .sub,body.estado-validacao #kpis .kpi .marker{visibility:hidden}
body.estado-validacao #kpis .kpi::after{content:"Indisponível";position:absolute;left:14px;right:14px;bottom:14px;font-weight:700;font-size:14px;color:var(--muted)}
body.estado-validacao #reportRoot .card{position:relative;min-height:140px}
body.estado-validacao #reportRoot .card>:not(.card-heading),body.estado-validacao #reportRoot .card-heading>:not(div),body.estado-validacao #reportRoot .card-heading>div>:not(h3){visibility:hidden}
body.estado-validacao #reportRoot .card::after{content:"Indisponível · dados oficiais em validação";position:absolute;left:16px;right:16px;top:64px;bottom:16px;min-height:56px;display:flex;align-items:center;justify-content:center;text-align:center;padding:8px;border:1px dashed var(--line);border-radius:8px;background:var(--pale);color:var(--muted);font-weight:700;font-size:14px}
</style>"""

AVISO_HTML = (
    f'<div id="avisoValidacao" role="status"><strong>{TITULO_AVISO}</strong>'
    f'<span>{TEXTO_AVISO}</span></div>'
)


def _substituir(html: str, antigo: str, novo: str, rotulo: str) -> str:
    assert html.count(antigo) == 1, f"Trecho esperado não encontrado (ou repetido) na interface aprovada: {rotulo}"
    return html.replace(antigo, novo, 1)


def adaptar_html_oficial_vazio(html_orig: str) -> str:
    """Aplica à interface aprovada o estado 'Dados oficiais em validação', sem tocar no arquivo de origem."""
    html = html_orig

    if '<link rel="icon"' not in html:
        html = _substituir(html, '<meta name="color-scheme" content="light">',
                           '<meta name="color-scheme" content="light"><link rel="icon" href="data:,">', "favicon")

    # Nenhum dado é carregado: o painel parte do esqueleto vazio da interface e lê só o estado da publicação.
    html = _substituir(html, """window.GEDIV_READY=(async()=>{
 let d=window.GEDIV_BOOTSTRAP;
 if(location.protocol!=='file:'&&!location.hostname.endsWith('github.io')){
  try{d=await window.GEDIV_FETCH_DATA();}catch(err){console.warn('Usando esqueleto inicial:',err);}
 }
 window.GEDIV_DATA=d;
 return d;
})();""", """window.GEDIV_OFICIAL_VAZIO=true;
window.GEDIV_FETCH_DATA=async()=>window.GEDIV_BOOTSTRAP;
window.GEDIV_READY=(async()=>{
 const d=window.GEDIV_BOOTSTRAP;
 d.rows=[];d.events=[];d.otherPublications=[];
 d.meta=Object.assign({},d.meta,{coverage:'Dados oficiais em validação: a cobertura das edições ainda não foi validada.',personal:'Nenhum dado individual é publicado neste endereço.'});
 try{const r=await fetch('./estado-publicacao.json',{cache:'no-store',headers:{Accept:'application/json'}});if(r.ok)window.GEDIV_ESTADO_PUBLICACAO=await r.json();}catch(err){console.warn('Estado da publicação indisponível:',err);}
 window.GEDIV_DATA=d;
 return d;
})();""", "GEDIV_READY")

    html = _substituir(html, "const isStaticHost=()=>location.hostname.endsWith('github.io')||location.protocol==='file:';",
                       "const isStaticHost=()=>true;\nconst isOficialVazio=()=>!!window.GEDIV_OFICIAL_VAZIO;", "isStaticHost")

    html = _substituir(html, """ function openLoginModal(){
  $('#loginStatus').textContent='';$('#loginStatus').classList.remove('is-error');$('#loginDialog').showModal();
 }""", """ function openStaticBackendNotice(acao){
  const titulo=acao?`${acao}: recurso da área restrita`:'Dados oficiais em validação';
  const body=`<div class="reconcile-note" style="margin-top:0"><b>Dados oficiais em validação.</b></div>
  <p>Esta é a página pública do Observatório. Os indicadores, gráficos e tabelas serão publicados quando os dados do Diário Oficial do Estado da Paraíba forem coletados, conferidos e aprovados pela GEDIV.</p>
  <p>Acesso da gerência, conferência documental, auditoria e recebimento de lotes funcionam somente no ambiente restrito da GEDIV, com login institucional.</p>`;
  openDialog(titulo,body);
 }
 function openLoginModal(){
  openStaticBackendNotice('Acesso da gerência');
 }""", "openLoginModal")

    for antigo, novo, rotulo in (
        ("function openReviewModal(targetType,items){\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "function openReviewModal(targetType,items){\n if(isOficialVazio()){openStaticBackendNotice('Conferência documental');return;}\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "openReviewModal"),
        ("async function openConflictsDialog(){\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "async function openConflictsDialog(){\n if(isOficialVazio()){openStaticBackendNotice('Conflitos de leitura');return;}\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "openConflictsDialog"),
        ("async function openAuditDialog(){\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "async function openAuditDialog(){\n if(isOficialVazio()){openStaticBackendNotice('Trilha de auditoria');return;}\n if(!data.backend?.autenticado){$('#loginDialog').showModal();return;}",
         "openAuditDialog"),
        ("function exportCsv(){\n if(!data.backend?.autenticado)",
         "function exportCsv(){\n if(isOficialVazio()){toast('Dados oficiais em validação: não há lista para exportar.');return;}\n if(!data.backend?.autenticado)",
         "exportCsv"),
    ):
        html = _substituir(html, antigo, novo, rotulo)

    # Rótulos da conta e da faixa de cobertura: nunca contagens enquanto não houver dados aprovados
    html = _substituir(html, " if(dLbl)dLbl.textContent=isAuth?(usr?.nome||(isAdm?'Admin GEDIV':'Gerência GEDIV')):'Acesso gerencial';",
                       " if(dLbl)dLbl.textContent=isOficialVazio()?'Consulta pública':isAuth?(usr?.nome||(isAdm?'Admin GEDIV':'Gerência GEDIV')):'Acesso gerencial';",
                       "rótulo da conta")
    html = _substituir(html, " if(mm)mm.textContent=isAuth?`${Number(meta.edicoes)||0} edições · perfil ${isAdm?'Administração':'Gerência'}`:'Apenas indicadores agregados';",
                       " if(mm)mm.textContent=isOficialVazio()?'Dados oficiais em validação':isAuth?`${Number(meta.edicoes)||0} edições · perfil ${isAdm?'Administração':'Gerência'}`:'Apenas indicadores agregados';",
                       "meta da conta")
    html = _substituir(html, " if(bt)bt.textContent=edC?`Cobertura parcial (${edC} ${edC===1?'edição':'edições'}) · ${scopeLbl}`:'Cobertura em atualização';",
                       " if(bt)bt.textContent=isOficialVazio()?'Dados oficiais em validação':edC?`Cobertura parcial (${edC} ${edC===1?'edição':'edições'}) · ${scopeLbl}`:'Cobertura em atualização';",
                       "título da faixa de cobertura")
    html = _substituir(html, " if(bx)bx.textContent=isAuth?'Registros extraídos sujeitos a conferência documental.':'Dados públicos agregados (sujeitos a conferência); registros individuais protegidos.';",
                       " if(bx)bx.textContent=isOficialVazio()?'Cobertura das edições ainda não validada. Nenhum número é exibido até a aprovação dos dados.':isAuth?'Registros extraídos sujeitos a conferência documental.':'Dados públicos agregados (sujeitos a conferência); registros individuais protegidos.';",
                       "texto da faixa de cobertura")

    html = _substituir(html, "</head>", ESTILO + "</head>", "</head>")
    html = _substituir(html, "<body>", '<body class="estado-validacao">', "<body>")

    cores_aprovadas = {c.lower() for c in json.loads(PALETA_JSON.read_text(encoding="utf-8"))["cores_hex"]}
    novas = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", html)} - cores_aprovadas
    assert not novas, f"Cores fora da paleta aprovada: {novas}"
    return html


def estado_publicacao(gerado_em: str | None = None) -> dict:
    return {
        "estado": "EM_VALIDACAO",
        "titulo": TITULO_AVISO,
        "mensagem": TEXTO_AVISO,
        "dados_publicados": False,
        "cobertura_validada": False,
        "registros": 0,
        "gerado_em": gerado_em or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "liberacao_de_dados_reais": [
            "coleta real comprovada a partir de ambiente autorizado no Brasil (P0-1)",
            "executor permanente e piloto de 7 dias sem intervenção",
            "homologações e conferência das decisões pela GEDIV",
            "snapshot público agregado promovido com responsável e justificativa",
        ],
    }


def _bootstrap(html: str) -> dict:
    marcador = "window.GEDIV_BOOTSTRAP="
    assert html.count(marcador) == 1, "GEDIV_BOOTSTRAP ausente ou repetido no index.html"
    dados, _ = json.JSONDecoder().raw_decode(html, html.index(marcador) + len(marcador))
    return dados


def validar_pacote_oficial(pasta: Path, permitir_cname: bool = False) -> dict:
    """Validação fechada do pacote oficial. Levanta AssertionError em qualquer violação."""
    arquivos = sorted(p.relative_to(pasta).as_posix() for p in pasta.rglob("*") if p.is_file())
    permitidos = PERMITIDOS_COM_DOMINIO if permitir_cname else PERMITIDOS
    assert PERMITIDOS <= set(arquivos) <= permitidos, f"Arquivos fora da lista autorizada: {arquivos}"
    for nome in arquivos:
        assert Path(nome).suffix.lower() not in EXTENSOES_PROIBIDAS, f"Tipo de arquivo proibido no pacote: {nome}"

    html = (pasta / "index.html").read_text(encoding="utf-8")
    estado_txt = (pasta / ESTADO_ARQUIVO).read_text(encoding="utf-8")
    estado = json.loads(estado_txt)

    for rotulo, texto in (("index.html", html), (ESTADO_ARQUIVO, estado_txt)):
        for padrao, motivo in MARCAS_FICTICIAS:
            assert not padrao.search(texto), f"Carga fictícia recusada ({motivo}) em {rotulo}"
        for padrao, motivo in MARCAS_PRIVADAS:
            if rotulo == "index.html" and padrao.pattern == "/api/pdf/":
                continue  # o código da interface aprovada cita a rota do servidor; o que importa são os DADOS (abaixo)
            assert not padrao.search(texto), f"Dado privado recusado ({motivo}) em {rotulo}"

    boot = _bootstrap(html)
    assert "/api/pdf/" not in json.dumps(boot, ensure_ascii=False), "Rota de PDF privado nos dados embutidos"
    for chave in ("rows", "events", "otherPublications"):
        assert boot.get(chave) == [], f"O pacote oficial vazio não pode trazer registros em {chave}"
    assert estado.get("estado") == "EM_VALIDACAO" and estado.get("dados_publicados") is False, "Estado da publicação inválido"
    assert estado.get("registros") == 0 and estado.get("cobertura_validada") is False, "Estado vazio exige 0 registros e cobertura não validada"
    assert not ({"rows", "linhas", "decisoes", "events"} & set(estado)), "O estado da publicação não pode conter registros"

    # Faixa azul de aviso no topo removida a pedido da responsável (28/11/2026); o estado vazio continua sinalizado
    # pela faixa da própria interface ("Dados oficiais em validação") e pelos cartões "Indisponível".
    assert 'id="avisoValidacao"' not in html, "A faixa azul de aviso no topo foi removida e não deve voltar"
    assert 'GEDIV_OFICIAL_VAZIO' in html, "Estado vazio não sinalizado"
    assert '<body class="estado-validacao">' in html, "Estado vazio não ativado no <body>"
    assert html.count("window.GEDIV_OFICIAL_VAZIO=true") == 1, "Modo oficial vazio não ativado"
    assert html.count('data-view="') >= 7, "Navegação das 7 abas não preservada"
    assert html.count("\r\n") == 0, "CRLF detectado em index.html"
    if permitir_cname and (pasta / "CNAME").exists():
        cname = (pasta / "CNAME").read_text(encoding="utf-8").strip()
        assert re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", cname), f"CNAME inválido: {cname!r}"
    return {"arquivos": arquivos, "registros": 0, "estado": estado["estado"]}


def construir_pacote_oficial(saida: Path, gerado_em: str | None = None) -> Path:
    if saida.exists():
        shutil.rmtree(saida)
    saida.mkdir(parents=True)
    html = adaptar_html_oficial_vazio(HTML_ORIGEM.read_text(encoding="utf-8"))
    (saida / ".nojekyll").write_text("", encoding="utf-8", newline="\n")
    (saida / "index.html").write_text(html, encoding="utf-8", newline="\n")
    (saida / ESTADO_ARQUIVO).write_text(json.dumps(estado_publicacao(gerado_em), ensure_ascii=False, indent=1) + "\n",
                                        encoding="utf-8", newline="\n")
    validar_pacote_oficial(saida)
    print(f"Pacote oficial validado em: {saida} (estado vazio: {TITULO_AVISO}; 0 registros; sem dados fictícios)")
    return saida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--saida", type=Path, help="gera e valida o pacote oficial nesta pasta")
    grupo.add_argument("--validar", type=Path, help="só valida um pacote já gerado (aceita CNAME)")
    a = ap.parse_args(argv)
    if a.saida:
        construir_pacote_oficial(a.saida)
    else:
        print(json.dumps(validar_pacote_oficial(a.validar, permitir_cname=True), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
