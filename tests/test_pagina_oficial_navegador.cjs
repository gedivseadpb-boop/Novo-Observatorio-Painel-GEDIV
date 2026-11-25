// Teste no navegador do pacote OFICIAL do GitHub Pages (estado "Dados oficiais em validação").
// Uso: python scripts/preparar_pacote_oficial_pages.py --saida /tmp/site
//      node tests/test_pagina_oficial_navegador.cjs --static-dir /tmp/site
// Verifica, no computador (1440x900) e no celular (iPhone 13): aviso visível, as 7 abas navegáveis, nenhum número de
// dados visível (só rótulos de período e a data do dia), indicadores e cartões "Indisponível", nenhum registro
// fictício, nenhuma requisição externa, nenhum erro de script e nenhuma rolagem lateral.
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium, devices } = require('playwright');

const arg = process.argv.indexOf('--static-dir');
const DIR = arg > -1 ? path.resolve(process.argv[arg + 1]) : null;
if (!DIR || !fs.existsSync(path.join(DIR, 'index.html'))) { console.error('Informe --static-dir PASTA_DO_PACOTE'); process.exit(2); }
const VISTAS = ['geral', 'vertical', 'horizontal', 'tempo', 'outras', 'hoje', 'historico'];
// rótulos de período, a data do dia e o contador de filtros ATIVOS da navegação (não são dados)
const PERMITIDOS = [/^\d+ dias$/, /\d{2}\/\d{2}\/\d{4}/, /^FILTROS \(\d+\)$/];

const tipos = { '.html': 'text/html; charset=utf-8', '.json': 'application/json' };
const servidor = http.createServer((req, res) => {
  const alvo = path.join(DIR, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  if (!alvo.startsWith(DIR) || !fs.existsSync(alvo)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': tipos[path.extname(alvo)] || 'application/octet-stream' });
  fs.createReadStream(alvo).pipe(res);
});

(async () => {
  await new Promise(r => servidor.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${servidor.address().port}/`;
  const navegador = await chromium.launch(process.env.GEDIV_CHROMIUM ? { executablePath: process.env.GEDIV_CHROMIUM } : {});
  const falhas = [];
  for (const [nome, opcoes] of [['computador', { viewport: { width: 1440, height: 900 } }], ['celular', { ...devices['iPhone 13'] }]]) {
    const ctx = await navegador.newContext(opcoes);
    const p = await ctx.newPage();
    const erros = [], externos = [];
    p.on('pageerror', e => erros.push(e.message));
    p.on('console', m => { if (m.type() === 'error') erros.push(m.text()); });
    p.on('request', r => { if (!r.url().startsWith(base) && !r.url().startsWith('data:')) externos.push(r.url()); });
    await p.goto(base, { waitUntil: 'networkidle' });
    await p.waitForTimeout(800);
    const aviso = await p.locator('#avisoValidacao').innerText();
    if (!aviso.includes('Dados oficiais em validação')) falhas.push(`${nome}: aviso ausente`);
    if (await p.evaluate(() => document.documentElement.scrollWidth - innerWidth) > 0) falhas.push(`${nome}: rolagem lateral`);
    for (const v of VISTAS) {
      await p.evaluate(v => document.querySelector(`nav.tabs [data-view="${v}"]`).click(), v);
      await p.waitForTimeout(250);
      const r = await p.evaluate(() => {
        const textos = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
        while ((n = w.nextNode())) {
          const el = n.parentElement; if (!el || el.closest('script,style,dialog')) continue;
          const s = getComputedStyle(el); if (s.visibility === 'hidden' || s.display === 'none' || !el.getClientRects().length) continue;
          const t = n.textContent.trim(); if (t) textos.push(t);
        }
        const kpis = [...document.querySelectorAll('#kpis .kpi')].map(k => getComputedStyle(k, '::after').content);
        const cards = [...document.querySelectorAll('#reportRoot .card')].filter(c => c.getClientRects().length)
          .map(c => getComputedStyle(c, '::after').content);
        return { textos, kpis, cards, ativa: document.querySelector('nav.tabs .active')?.dataset.view, corpo: document.body.innerText };
      });
      if (r.ativa !== v) falhas.push(`${nome}/${v}: aba não navegou`);
      const numeros = r.textos.filter(t => /\d/.test(t) && !PERMITIDOS.some(re => re.test(t)));
      if (numeros.length) falhas.push(`${nome}/${v}: números visíveis ${JSON.stringify(numeros.slice(0, 5))}`);
      if (!r.kpis.length || r.kpis.some(c => !c.includes('Indisponível'))) falhas.push(`${nome}/${v}: indicador sem "Indisponível"`);
      if (!r.cards.length || r.cards.some(c => !c.includes('Indisponível'))) falhas.push(`${nome}/${v}: cartão sem "Indisponível"`);
      if (/FICT[IÍ]CI|2099|sintétic/i.test(r.corpo)) falhas.push(`${nome}/${v}: texto fictício visível`);
    }
    if (erros.length) falhas.push(`${nome}: erros de script ${JSON.stringify(erros.slice(0, 3))}`);
    if (externos.length) falhas.push(`${nome}: requisições externas ${JSON.stringify(externos.slice(0, 3))}`);
    await ctx.close();
  }
  await navegador.close();
  servidor.close();
  if (falhas.length) { console.error('FALHOU:\n- ' + falhas.join('\n- ')); process.exit(1); }
  console.log(`OK: pacote oficial vazio aprovado em computador e celular (${VISTAS.length} abas).`);
})().catch(e => { console.error(e); process.exit(1); });
