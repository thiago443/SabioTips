
# SábioTipsBot — Versão Analítica (Seguro)

Este pacote contém um bot analítico desenhado para coletar **dados públicos** (ex.: páginas de estatísticas como FlashScore),
gerar relatórios em português sobre partidas (gols, escanteios, cartões, finalizações) e enviar para um chat/canal do Telegram.

**Importante:** Este bot fornece apenas análises e relatórios para estudo — NÃO RECOMENDA AÇÕES DE APOSTA.

## Arquivos
- `main.py` — script principal (coleta, analisa e envia mensagens).
- `requirements.txt` — dependências Python.

## Como usar (Render com GitHub)
1. Crie um repositório no GitHub (ex.: `sabio-tips`).
2. Adicione `main.py` e `requirements.txt` ao repositório.
3. No Render: **New → Web Service** → conecte ao repositório.
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
5. Configure as variáveis de ambiente no Render:
   - `BOT_TOKEN` — token do seu bot Telegram
   - `CHAT_ID` — chat ID ou @canal onde as mensagens serão enviadas
6. Deploy e verifique os logs — as mensagens de relatório serão enviadas a cada 5 minutos.

## Observações
- O scraping depende do layout do site (FlashScore pode mudar). Ajustes nos seletores podem ser necessários.
- Teste localmente antes de subir em produção.
- Não compartilhe seu token publicamente.
