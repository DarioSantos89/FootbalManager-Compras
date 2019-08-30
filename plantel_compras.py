import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def convert_percent(val):
    new_val = val.replace('%', '').replace(",",".")
    return float(new_val) / 100

data =pd.read_csv("jogadores.csv",encoding="cp1252", sep=";",thousands="\xa0",
                  header=0, decimal=",",index_col=[0,1],
                  converters={"GK Rating":convert_percent,"DL Rating":convert_percent,
                  "DC Rating":convert_percent,"DR Rating":convert_percent,
                  "DM Rating":convert_percent,"MC Rating":convert_percent,
                  "AML Rating":convert_percent,"AMC Rating":convert_percent,
                  "AMR Rating":convert_percent,"FS Rating":convert_percent,
                  "GK Pot Rating":convert_percent,"DL Pot Rating":convert_percent,
                  "DC Pot Rating":convert_percent,"DR Pot Rating":convert_percent,
                  "DM Pot Rating":convert_percent,"MC Pot Rating":convert_percent,
                  "AML Pot Rating":convert_percent,"AMC Pot Rating":convert_percent,
                  "AMR Pot Rating":convert_percent,"FS Pot Rating":convert_percent})
data.dtypes
jogadores=data.rename(columns={"FS Rating":"FC Rating","FS Pot Rating":"FC Pot Rating"})
#dados importados

#criar avaliação por posição
#estimar o potencial a acrescentar em cada idade
posicoes=list(jogadores.columns[(jogadores.dtypes.values==np.dtype('float64'))])
posicoes=list(set([pos.replace(' Rating','').replace(' Pot','') for pos in posicoes]))
def calcular_atributo(jogadores,posicoes):
    Idades=pd.DataFrame(index=list(set(jogadores['Age'])))
    for pos in posicoes:
        letras=list(pos)
        aux=jogadores
        #filtar jogadores cuja melhor posição tem as letras da posição
        for l in letras:
            aux[aux.columns[0]]=aux[aux.columns[0]].astype(str)
            aux=aux[aux[aux.columns[0]].str.contains(l)]
        #ter dataframe só com as colunas da idade e da posiçao
        aux=pd.merge(aux.filter(regex='Age'),aux.filter(regex='^'+pos),left_index=True, right_index=True)            
        aux['Perct']=aux[aux.columns[1]]/aux[aux.columns[2]]
        aux2=aux.groupby(['Age']).mean().filter(regex='Perct')
        plt.plot(aux2)
        aux2=-aux2.diff(periods=-1)
        aux2=aux2.rename(columns={"Perct":pos})
        Idades=pd.merge(Idades,aux2,left_index=True, right_index=True, how="outer").fillna(0)
#Aplicar estas taxas para calcular nova avaliação
    jogadores_cal=pd.merge(jogadores,Idades,right_index=True,left_on='Age', how="left")
    jogadores_cal.fillna(0)
    for pos in posicoes:
        aux3=jogadores_cal.filter(regex='^'+pos)
        jogadores_cal[aux3.columns[2]]=aux3[aux3.columns[0]]+aux3[aux3.columns[1]]*aux3[aux3.columns[2]]
    jogadores_cal=jogadores_cal[jogadores_cal.columns.drop(list(jogadores_cal.filter(regex='Rating')))]
    return jogadores_cal

'''
ver se alterou a posição na lista dos melhores jogadores
jogadores_cal['rankini']=jogadores_cal['GK Rating'].rank(ascending=False)
jogadores_cal['rankcal']=jogadores_cal['GK'].rank(ascending=False)
jogadores_cal['rankdiff']=jogadores_cal['rankcal']-jogadores_cal['rankini']
jog=jogadores_cal.groupby(['Age']).mean().filter(regex='rankdiff')
'''
jogadores_cal=calcular_atributo(jogadores,posicoes)
# escolha do plantel

def plantel (jogadores,tatica,club):
    club=jogadores[jogadores['Club']==club]
    for i in range(len(tatica)):
        tatica[i]['jogador']=pd.DataFrame(columns=list(club.columns))
    posi=list(jogadores.columns[(jogadores.dtypes.values==np.dtype('float64'))])
    for i in range(22):
#ver a posição em que o melhor tem a maior dif para o 2º
        bigpos={}
        bestpla={}
        for pos in posi:
            jog=club.sort_values(by=[pos], ascending=False).filter(regex=pos).diff(periods=-1)
            bigpos.update({pos:jog.iloc[0][pos]})
            bestpla.update({pos:jog.index[0]})
        bigpos=sorted(bigpos.items(), key=lambda p: p[1], reverse=True)
#index dessa posição
        indexaux=[t for t,_ in enumerate(tatica) if _['Position'] == bigpos[0][0]]
        if len(indexaux)==0:
            indexaux=0
        else:
            indexaux=indexaux[0]
#adicionar o jogador
        tatica[indexaux]['jogador']=tatica[indexaux]['jogador'].append(club.loc[bestpla[bigpos[0][0]]])
        club=club.drop(bestpla[bigpos[0][0]])
        if len(tatica[indexaux]['jogador'].index)==(tatica[indexaux]['n']):
            posi.remove(bigpos[0][0])
    return tatica

def resumoplantel (plantel):
    equipa=pd.DataFrame(columns=list(plantel[0]['jogador'].columns))
    equipa.insert(0,'Pos','')    
    for pos in plantel:
        pos['jogador'].insert(0,'Pos',pos['Position'])
        equipa=equipa.append(pos['jogador'], sort=False)
    return equipa


tatica_4_1_1_3_1=([{'Position':'GR','n':2},
        {'Position':'DR','n':2},
        {'Position':'DC','n':4},
        {'Position':'DL','n':2},
        {'Position':'DM','n':2},
        {'Position':'MC','n':2},
        {'Position':'AMR','n':2},
        {'Position':'AMC','n':2},
        {'Position':'AML','n':2},
        {'Position':'FC','n':2}])

sporting=resumoplantel(plantel(jogadores_cal,tatica_4_1_1_3_1,club='Sporting'))

def compras(jogadores,tatica,clube,orcamento,salario):
    aux=0
    joga=jogadores.copy()
    posi=list(jogadores.columns[(jogadores.dtypes.values==np.dtype('float64'))])
    compras=pd.DataFrame(columns=list(jogadores.columns))
    joga['Wage']+=1
    joga['Sale Value']+=1
    equipa=plantel(joga,tatica,clube)
    while(True):
        orc=orcamento-compras['Sale Value'].sum()
        sal=salario-compras['Wage'].sum()
#ver a posição em que o melhor tem a maior dif para o meu ultimo
        bestpos={}
        bestpla={}
        for pos in posi:
            if(equipa['Position'==pos]['jogador'][-1:].index[0] in compras.index):
                orc+=equipa['Position'==pos]['jogador'][-1:]['Sale Value']
                sal+=equipa['Position'==pos]['jogador'][-1:]['Wage']
            jog=joga[(joga['Wage']<=sal) & (joga['Sale Value']<=orc)& (joga['Club']!=clube)]
            jog[pos]=jog[pos]-equipa['Position'==pos]['jogador'][-1:][pos][0]
            jog=jog[jog[pos]>0]
            if(len(jog)>0):
                jog[pos]=(jog[pos])/(((jog['Wage']/salario)+(jog['Sale Value']/orcamento))/2)
                jog=jog.sort_values(by=[pos], ascending=False)
                bestpos.update({pos:jog.iloc[0][pos]})
                bestpla.update({pos:jog.index[0]})
        if(len(bestpos)>0):
            bestpos=sorted(bestpos.items(), key=lambda p: p[1], reverse=True)
            compras=compras.append(joga.loc[bestpla[bestpos[0][0]]])
            print(bestpos[0][0])
            print(compras)
            joga.loc[bestpla[bestpos[0][0]]]['Club']=clube
            print(joga.loc[bestpla[bestpos[0][0]]])
            equipa=plantel(joga,tatica,clube)
            plant=resumoplantel(equipa)
            for player in list(compras.index):
                if(player not in plant.index):
                    compras=compras.drop(player)                    
            aux+=1
        else:
            break
        if(len(compras.index)>22 or (aux>22)):
            break
    return (resumoplantel(equipa),compras)

comprassporting=compras(jogadores_cal,tatica_4_1_1_3_1,clube='Sporting',orcamento=100000000,salario=1000000)
