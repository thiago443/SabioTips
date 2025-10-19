
"""
SábioTipsBot — Versão Analítica (dados reais)
------------------------------------------------
Este script coleta dados públicos de sites de estatísticas (ex: FlashScore),
gera relatórios analíticos (gols, escanteios, cartões, finalizações) e
envia mensagens em português ao Telegram (canal/usuário configurado).

IMPORTANTES:
- Projetado para *análise esportiva* e estudo — NÃO fornece instruções de aposta.
- Configure variáveis de ambiente BOT_TOKEN e CHAT_ID no host (Render/GitHub Secrets).
- Execute em ambiente que permita requisições HTTP (internet).
- Scraping depende do layout do site — pode ser necessário ajustar seletores se o site mudar.
"""
import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from threading import Thread

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SEND_TO = os.getenv("SEND_TO") or CHAT_ID  # canal ou chat id

# Ligas alvo (páginas iniciais do Flashscore BR para exemplo)
LEAGUE_URLS = {
    "Brasileirão Série A": "https://www.flashscore.com.br/futebol/brasil/serie-a/",
    "Premier League": "https://www.flashscore.com.br/futebol/inglaterra/premier-league/",
    "Champions League": "https://www.flashscore.com.br/futebol/champions-league/",
    "La Liga": "https://www.flashscore.com.br/futebol/espanha/la-liga/"
}

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"}

def send_telegram(text):
    """Envia texto (HTML) para o chat/canal configurado no Telegram."""
    if not BOT_TOKEN or not SEND_TO:
        print("BOT_TOKEN ou CHAT_ID não configurados. Mensagem não enviada.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": SEND_TO, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

def scrape_league_page(url):
    """
    Pega partidas ao vivo e agendadas de uma página de liga do FlashScore.
    Retorna lista de dicionários com dados básicos: home, away, status, score, link (se disponível).
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print("Erro ao acessar liga:", e)
        return []

    matches = []
    # Seletores podem variar — procuramos por elementos que contenham times e status
    # FlashScore costuma usar classes como event__match, event__participant, event__scores, event__time
    rows = soup.find_all(lambda tag: tag.name=="div" and "event__match" in " ".join(tag.get("class", [])))
    for row in rows:
        try:
            teams = row.find_all("div", class_="event__participant")
            if len(teams) < 2:
                continue
            home = teams[0].get_text(strip=True)
            away = teams[1].get_text(strip=True)
            score_tag = row.find("div", class_="event__scores")
            time_tag = row.find("div", class_="event__time")
            score = score_tag.get_text(strip=True) if score_tag else ""
            status = time_tag.get_text(strip=True) if time_tag else ""
            link_tag = row.find("a", class_="event__match--link")
            link = None
            if link_tag and link_tag.get("href"):
                href = link_tag.get("href")
                if href.startswith("/"):
                    link = "https://www.flashscore.com.br" + href
                else:
                    link = href
            matches.append({
                "home": home,
                "away": away,
                "score": score,
                "status": status,
                "link": link
            })
        except Exception:
            continue
    return matches

def scrape_match_details(match_url):
    """
    Acessa a página da partida e tenta extrair estatísticas (escanteios, cartões, chutes).
    Retorna dicionário com estatísticas (valores inteiros ou 'N/D' se não encontrado).
    """
    stats = {"corners_home": "N/D", "corners_away": "N/D", "yellow_home": "N/D", "yellow_away": "N/D",
             "shots_home": "N/D", "shots_away": "N/D"}
    if not match_url:
        return stats
    try:
        r = requests.get(match_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # O layout do FlashScore é dinâmico — procuramos por blocos com indicador textual
        # Procuramos por linhas com "Corners" ou "Escanteios" e "Yellow cards" ou "Amarelos"
        text = soup.get_text(separator="|", strip=True)
        # heurística simples: procurar por "Corners" em inglês ou "Escanteios" em pt-br
        if "Corners" in text or "Escanteios" in text:
            # tentar extrair números próximos — heurística fraca; ajustar conforme necessário
            # vamos buscar elementos específicos
            stat_rows = soup.find_all(lambda t: t.name in ["div","tr","span"] and ("Corner" in t.get_text() or "Escanteio" in t.get_text() or "Yellow" in t.get_text() or "Amarelo" in t.get_text() or "Shots" in t.get_text() or "Finalizações" in t.get_text()))
            for sr in stat_rows:
                txt = sr.get_text(" ", strip=True)
                if "Corner" in txt or "Escanteio" in txt:
                    # extrair dígitos na string
                    import re
                    nums = re.findall(r"\d+", txt)
                    if len(nums) >= 2:
                        stats["corners_home"] = int(nums[0])
                        stats["corners_away"] = int(nums[1])
                if "Yellow" in txt or "Amarelo" in txt:
                    import re
                    nums = re.findall(r"\d+", txt)
                    if len(nums) >= 2:
                        stats["yellow_home"] = int(nums[0])
                        stats["yellow_away"] = int(nums[1])
                if "Shots" in txt or "Finaliza" in txt:
                    import re
                    nums = re.findall(r"\d+", txt)
                    if len(nums) >= 2:
                        stats["shots_home"] = int(nums[0])
                        stats["shots_away"] = int(nums[1])
    except Exception as e:
        print("Erro em detalhes da partida:", e)
    return stats

def build_report(match):
    """Gera texto em português com análise resumida — estilo profissional, sem recomendar apostas."""
    home = match.get("home")
    away = match.get("away")
    score = match.get("score") or ""
    status = match.get("status") or ""
    link = match.get("link")
    details = scrape_match_details(link) if link else {}
    # Montar relatório
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report = f"⚽ <b>{home} x {away}</b>\n"
    if status:
        report += f"⏱️ <i>{status}</i>\n"
    if score:
        report += f"🟢 Placar: {score}\n"
    report += "\n📊 <b>Estatísticas (quando disponíveis)</b>:\n"
    report += f"• Escanteios — Casa: {details.get('corners_home')} | Fora: {details.get('corners_away')}\n"
    report += f"• Cartões amarelos — Casa: {details.get('yellow_home')} | Fora: {details.get('yellow_away')}\n"
    report += f"• Finalizações — Casa: {details.get('shots_home')} | Fora: {details.get('shots_away')}\n"
    # Tendências simples (exemplo): presença de escanteios altos se corners sum > 8
    try:
        ch = details.get('corners_home') if isinstance(details.get('corners_home'), int) else 0
        cf = details.get('corners_away') if isinstance(details.get('corners_away'), int) else 0
        total_corners = (ch or 0) + (cf or 0)
    except Exception:
        total_corners = 0
    trend = "baixa"
    if total_corners >= 10:
        trend = "alta"
    elif total_corners >= 6:
        trend = "moderada"
    report += f"\n🔎 Tendência de escanteios: <b>{trend}</b> (total atual: {total_corners})\n"
    report += f"\n🔁 Atualizado: {now}\n"
    report += "\n---\n"
    report += "ℹ️ Este é um relatório analítico para estudo — não é recomendação de aposta."
    return report

def worker_loop():
    """Loop principal: varre ligas, coleta partidas e envia relatórios ao Telegram."""
    while True:
        try:
            found = False
            for league, url in LEAGUE_URLS.items():
                matches = scrape_league_page(url)
                if matches:
                    found = True
                    for m in matches[:8]:  # limitar envio por rodada para evitar spam
                        report = build_report(m)
                        send_telegram(report)
                        time.sleep(1.5)
            if not found:
                print("Nenhuma partida encontrada nas ligas monitoradas no momento.")
        except Exception as e:
            print("Erro no loop principal:", e)
        print("Aguardando 5 minutos para próxima verificação...")
        time.sleep(300)

if __name__ == "__main__":
    print("SábioTipsBot (versão analítica) iniciando...")
    # start background worker (when running on Render, use process management)
    try:
        worker_loop()
    except KeyboardInterrupt:
        print("Encerrando.")
# --- Servidor Flask para manter o Render ativo ---
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Dicas Sabio está rodando corretamente!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port) 
