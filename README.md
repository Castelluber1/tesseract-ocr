## Objetivo

API de OCR/extração de documentos de imigração (passaporte, financeiro, educação, visto/work permit), empacotada em Docker para rodar como "App" no Easypanel, na mesma VPS do n8n (`workflow.upimmigrationconsulting.com`).

## Contexto

Checagem de documentos dos clientes da UP hoje é 100% manual (ver [memória `project_up_crm_doc_check_automation`]). O plano é um workflow n8n rodando diariamente que lê a pasta do Drive de cada case aberto, manda cada arquivo pra essa API, compara o tipo de documento identificado contra o checklist do case, e manda um relatório. Tudo precisa rodar sem depender do PC do Caio estar ligado — por isso vira um serviço na VPS, não um script local.

O código de extração (`app/`) é cópia de `tools/document_parser.py`, `tools/extract_*.py` e `tools/format_output.py` (já existiam, testados localmente antes deste projeto) — Tesseract + Poppler fazem o OCR local (sem custo de API), e cada extrator identifica o tipo de documento por keyword matching + regex (passaporte usa parsing de MRZ). IA generativa (Claude) é fallback pros casos que o Tesseract não classificar, não o caminho principal.

## Deploy

1. Caio cria o repo no GitHub e cria o "App" no Easypanel apontando pra ele, com auto-deploy no push habilitado.
2. Daqui pra frente, ajustes (ex: "não está lendo o passaporte direito") são feitos direto no código, com commit + push — sem passar por configuração manual no Easypanel.
3. Endpoints principais: `POST /upload` (multipart, campo `files[]` + `document_type`), `POST /api/batch` (tenta todos os extratores e usa o de maior confiança), `GET /health`.

## Estrutura

- `app/` — código da API (Flask) + Dockerfile.
- `app/requirements.txt` — dependências Python (pytesseract, pdf2image, opencv, PyPDF2, Flask).
