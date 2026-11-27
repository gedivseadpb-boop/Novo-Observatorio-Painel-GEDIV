# Diário de trabalho — Observatório GEDIV

Registro curto de cada etapa de trabalho, para que qualquer pessoa ou agente de IA
retome de onde parou. Complementa o `docs/CHECKPOINT.md` (último estado verificado).

## Regras de preenchimento

- **Sem dados pessoais.** Não escreva nomes de servidores, CPF, matrícula, e-mail,
  telefone, senhas, tokens nem caminhos de pastas com dados (ex.: `C:\GEDIV\dados`).
- Em "Quem fez", use só o **papel**: `Responsável pelo projeto`, `Agente de IA (Claude)`,
  `Agente de IA (Codex)`, etc.
- Datas no formato `AAAA-MM-DD`.
- Registro mais recente **no topo**.
- Se citar um commit, use o código curto (ex.: `d276c21`).

## Modelo (copie e preencha)

```markdown
### AAAA-MM-DD — título curto da etapa

- **Quem fez:** papel (ex.: Agente de IA (Claude))
- **O que mudou:** o que foi feito, em poucas linhas; commit, se houver
- **Evidência:** testes rodados e resultado, ou "não verificado"
- **Próximo passo:** o que falta e quem precisa agir
```

---

## Registros

### 2026-11-27 — revisão pela planilha (etapa B)

- **Quem fez:** Agente de IA (Claude), a pedido da responsável pelo projeto
- **O que mudou:** comandos `configurar-revisao`, `gerar-revisao` e `aplicar-revisao`; etapas na rotina diária; trava de versão por impressão digital da linha
- **Evidência:** 6 testes novos aprovados (edição simulada como no Excel); suíte 736 aprovados, 1 falha conhecida só na nuvem (sem Tesseract)
- **Próximo passo:** responsável roda `git pull` e `configurar-revisao` no PC; depois, etapa C (grifos)

### 2026-11-26 — planilha CSV diária e coluna de alertas

- **Quem fez:** Agente de IA (Claude), a pedido da responsável pelo projeto
- **O que mudou:** CSV diário completo e público (D-12, `8761a95`); coluna `Motivo_Alerta` (D-13 etapa A, `6448158`)
- **Evidência:** 9 testes do CSV aprovados; gerado no PC da responsável (3.821 linhas no completo, 0 no público)
- **Próximo passo:** etapa B, revisão pela planilha no Drive (Agente de IA)

### 2026-11-26 — criação do diário

- **Quem fez:** Agente de IA (Claude), a pedido da responsável pelo projeto
- **O que mudou:** criado este arquivo `docs/DIARIO.md` com o modelo de registro
- **Evidência:** só documentação; nenhuma regra ou interface alterada
- **Próximo passo:** registrar aqui cada nova etapa, junto com a atualização do `docs/CHECKPOINT.md`
