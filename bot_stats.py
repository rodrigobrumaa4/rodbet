import requests
import pandas as pd
from scipy.stats import poisson
import numpy as np
import telegram
from telegram.ext import Updater, CommandHandler

# ----------------------------------------------------
# 1. FUNÇÃO DE SCRAPING (Baseada no vídeo e na inspecao de rede)
# ----------------------------------------------------

def get_match_stats(match_id):
    """Realiza o Web Scraping do Sofascore para um ID de jogo específico."""
    # ⚠️ ATENÇÃO: Use a estrutura da API que você encontrou na inspeção de rede
    url = f'https://api.sofascore.com/api/v1/event/{match_id}/statistics'
    headers = {'User-Agent': 'Mozilla/5.0'} 

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Simplificando a extração: focando apenas nas estatísticas importantes
        stats_list = []
        for match_stats in data.get('statistics', []):
            if match_stats.get('period') == 'ALL': # Foco no jogo completo
                for group in match_stats.get('groups', []):
                    for item in group.get('statisticItems', []):
                        stats_list.append({
                            'Statistic': item.get('name'),
                            'Home': item.get('home'),
                            'Away': item.get('away')
                        })
        return stats_list
    except Exception as e:
        return f"Erro ao coletar dados: {e}"

# ----------------------------------------------------
# 2. FÓRMULA DE PROBABILIDADE (Distribuição de Poisson)
# ----------------------------------------------------

def calcular_prob_placar(lambda_casa, lambda_fora, gols_casa, gols_fora):
    """Calcula a probabilidade de um placar específico."""
    prob_casa = poisson.pmf(gols_casa, lambda_casa)
    prob_fora = poisson.pmf(gols_fora, lambda_fora)
    return prob_casa * prob_fora

def calcular_prob_1x2(lambda_casa, lambda_fora, max_gols=5):
    """Calcula as probabilidades totais de 1 (Casa), X (Empate) e 2 (Fora)."""
    prob_1, prob_X, prob_2 = 0, 0, 0
    
    for i in range(max_gols + 1):
        for j in range(max_gols + 1):
            prob_placar = calcular_prob_placar(lambda_casa, lambda_fora, i, j)
            
            if i > j:
                prob_1 += prob_placar  # Vitória Casa
            elif i == j:
                prob_X += prob_placar # Empate
            else:
                prob_2 += prob_placar # Vitória Fora

    # Normalizando as probabilidades
    total = prob_1 + prob_X + prob_2
    return {
        'Casa': prob_1 / total, 
        'Empate': prob_X / total, 
        'Fora': prob_2 / total
    }

# ----------------------------------------------------
# 3. LÓGICA DO BOT (Função de Comando)
# ----------------------------------------------------

# (Você precisará de um banco de dados ou histórico estático para calcular Lambdas reais)
# Para fins de demonstração, usaremos Lambdas fixos.
def analisar(update, context):
    """Recebe o comando /analisar e retorna as probabilidades."""
    
    # Exemplo: O usuário digita /analisar 1205364
    if not context.args:
        update.message.reply_text("Por favor, forneça o ID do jogo. Ex: /analisar 1205364")
        return
        
    match_id = context.args[0]
    
    # ⚠️ ESTE É UM PONTO CHAVE! 
    # Em um bot real, você usaria o histórico de gols/xG do time para calcular
    # o lambda_casa e o lambda_fora. Aqui, estamos usando valores simulados:
    
    lambda_casa_simulado = 1.5 
    lambda_fora_simulado = 0.8
    
    # 1. Coleta dos Dados do Jogo (Scraping)
    stats = get_match_stats(match_id)
    
    # 2. Cálculo das Probabilidades (Poisson)
    probs = calcular_prob_1x2(lambda_casa_simulado, lambda_fora_simulado)
    
    # 3. Montagem da Mensagem de Saída
    if isinstance(stats, str):
         output = f"Erro na análise: {stats}"
    else:
        odds_justas = {k: round(1 / v, 2) for k, v in probs.items()}
        output = (
            f"⚽ **Análise Estatística (ID: {match_id})**\n"
            f"------------------------------------\n"
            f"🏠 **Casa** ({probs['Casa']:.1%}) | Odd Justa: {odds_justas['Casa']:.2f}\n"
            f"🤝 **Empate** ({probs['Empate']:.1%}) | Odd Justa: {odds_justas['Empate']:.2f}\n"
            f"✈️ **Fora** ({probs['Fora']:.1%}) | Odd Justa: {odds_justas['Fora']:.2f}\n\n"
            f"🔎 *Estatística Coletada:* {len(stats)} itens (xG, Posse, etc.)"
        )
    
    update.message.reply_text(output, parse_mode=telegram.ParseMode.MARKDOWN)

# ----------------------------------------------------
# 4. INICIALIZAÇÃO DO BOT
# ----------------------------------------------------
def main():
    # ⚠️ SUBSTITUA PELO SEU TOKEN DO BOTFATHER
    token = "SEU_TOKEN_DO_TELEGRAM" 
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    # Conecta a função 'analisar' ao comando /analisar
    dp.add_handler(CommandHandler("analisar", analisar))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
