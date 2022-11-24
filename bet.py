import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import poisson

st.set_page_config(
    page_title='Apostas na Copa do Mundo 2022',
    page_icon='⚽',
)
st.title("Previsão dos jogos da Copa do Mundo 2022")

teamsStats = pd.read_excel(
    "data/DadosCopaDoMundoQatar2022.xlsx", sheet_name="selecoes", index_col=0)
matches = pd.read_excel(
    "data/DadosCopaDoMundoQatar2022.xlsx", sheet_name="jogos")
rankFifa = teamsStats["PontosRankingFIFA"]

rankMin, rankMax = min(rankFifa), max(rankFifa)
valueRankMin, valueRankMax = 0.15, 1

beta1 = (valueRankMax - valueRankMin)/(rankMax - rankMin)
beta0 = valueRankMax - (rankMax * beta1)

strength = beta0 + beta1*rankFifa


def AvgPoisson(team1, team2):
    strengthTeam1 = strength[team1]
    strengthTeam2 = strength[team2]
    avgGoasl = 2.83
    avgGoaslTeam1 = (avgGoasl * strengthTeam1)/(strengthTeam1 + strengthTeam2)
    avgGoaslTeam2 = avgGoasl - avgGoaslTeam1

    return [avgGoaslTeam1, avgGoaslTeam2]


def PoissonDist(avg):
    probabilities = []
    for i in range(10):
        probabilities.append(poisson.pmf(i, avg))
    probabilities.append(1-sum(probabilities))

    return pd.Series(probabilities, index=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])


def ProbabilitiesMatch(team1, team2):
    avgTeam1, avgTeam2 = AvgPoisson(team1, team2)
    distTeam1, distTeam2 = PoissonDist(avgTeam1), PoissonDist(avgTeam2)
    matriz = np.outer(distTeam1, distTeam2)
    victoryTeam1 = np.tril(matriz).sum()-np.trace(matriz)
    loseTeam1 = np.triu(matriz).sum()-np.trace(matriz)
    drawTeam1 = 1 - (victoryTeam1 + loseTeam1)
    probabilities = np.around([victoryTeam1, drawTeam1, loseTeam1], 3)
    probabilitiesPercent = [f"{100*i:.1f}" for i in probabilities]

    results = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    matriz = pd.DataFrame(matriz, columns=results, index=results)
    matriz.index = pd.MultiIndex.from_product([[team1], matriz.index])
    matriz.columns = pd.MultiIndex.from_product([[team2], matriz.columns])

    output = {"Seleção 1": team1, "Gols Seleção 1": avgTeam1,
              "Seleção 2": team2, "Gols Seleção 2": avgTeam2,
              "probabilidades": probabilitiesPercent}

    return output


def Match(team1, team2):
    avgGoaslTeam1, avgGoalsTeam2 = AvgPoisson(team1, team2)
    goalsTeam1 = int(np.random.poisson(lam=avgGoaslTeam1, size=1))
    goalsTeam2 = int(np.random.poisson(lam=avgGoalsTeam2, size=1))
    score = "{}x{}". format(goalsTeam1, goalsTeam2)

    return score


matches["Vitória"] = None
matches["Empate"] = None
matches["Derrota"] = None

for i in range(matches.shape[0]):
    team1 = matches["seleção1"][i]
    team2 = matches["seleção2"][i]
    v, d, l = ProbabilitiesMatch(team1, team2)["probabilidades"]
    matches.at[i, "Vitória"] = v
    matches.at[i, "Empate"] = d
    matches.at[i, "Derrota"] = l


listTeamHome = teamsStats.index.tolist()
listTeamHome.sort()
listTeamAway = listTeamHome.copy()

j1, j2 = st.columns(2)
team1 = j1.selectbox('Escolha a primeira Seleção', listTeamHome)
listTeamAway.remove(team1)
team2 = j2.selectbox('Escolha a segunda Seleção', listTeamAway, index=1)
st.markdown('---')

matches = ProbabilitiesMatch(team1, team2)
prob = matches['probabilidades']

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.image(teamsStats.loc[team1, 'LinkBandeiraGrande'])
with col2:
    st.metric(team1, prob[0])
    st.metric("Odd", round((100/float(prob[0])), 2))
with col3:
    st.metric("Empate", prob[1])
    st.metric("Odd", round((100/float(prob[1])), 2))
with col4:
    st.metric(team2, prob[0])
    st.metric("Odd", round((100/float(prob[2])), 2))
col5.image(teamsStats.loc[team2, 'LinkBandeiraGrande'])
st.markdown('---')
