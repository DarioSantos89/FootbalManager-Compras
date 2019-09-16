import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
import datetime

def convert_percent(val):
    new_val = val.replace('%', '').replace(",",".")
    return float(new_val) / 100

def convert_data(val):
    new_val=val.replace('.','/').replace('-','08/08/1989')
    format_str = '%d/%m/%Y'
    return datetime.datetime.strptime(new_val, format_str)
    
#calcular a soma dos atributos dos jogador
def somatr (player):
    soma=0
    for po in posicoes:
        soma+=player[po]
    return soma

def lerficheiro(ficheiro):
    data =pd.read_csv(ficheiro,encoding="cp1252", sep=";",thousands="\xa0",
                  header=0, decimal=",",index_col=[0,1,2],
                  converters={"GK Rating":convert_percent,"DL Rating":convert_percent,
                  "DC Rating":convert_percent,"DR Rating":convert_percent,
                  "DM Rating":convert_percent,"MC Rating":convert_percent,
                  "AML Rating":convert_percent,"AMC Rating":convert_percent,
                  "AMR Rating":convert_percent,"FS Rating":convert_percent,
                  "GK Pot Rating":convert_percent,"DL Pot Rating":convert_percent,
                  "DC Pot Rating":convert_percent,"DR Pot Rating":convert_percent,
                  "DM Pot Rating":convert_percent,"MC Pot Rating":convert_percent,
                  "AML Pot Rating":convert_percent,"AMC Pot Rating":convert_percent,
                  "AMR Pot Rating":convert_percent,"FS Pot Rating":convert_percent,
                  "Contract End":convert_data})
    data.dtypes
    data=data.rename(columns={"FS Rating":"FC Rating","FS Pot Rating":"FC Pot Rating"})
    return data

def emprestimos(jogadores):
    emp=jogadores[jogadores['Transfer Status']=='Listed For Loan']
    emp['Sale Value']=0
    jogadores=jogadores[jogadores['Transfer Status']!='Listed For Loan'].append(emp, sort=False)
    return jogadores

def fimcontrato(jogadores,datajogo):
    datajogo=datajogo+datetime.timedelta(days=180)
    contr=jogadores[jogadores['Contract End']<=datajogo]
    contr['Sale Value']=0
    jogadores=jogadores[jogadores['Contract End']>datajogo].append(contr, sort=False)
    return jogadores
    
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

# escolha do plantel
def plantel (jogadores,tatic,club,subida):
    tatica=copy.deepcopy(tatic)
    club=jogadores[jogadores['Club']==club]
    for i in range(len(tatica)):
        tatica[i]['jogador']=pd.DataFrame(columns=list(club.columns))
    posi=list(jogadores.columns[(jogadores.dtypes.values==np.dtype('float64'))])
    jogad=0
    for k in tatica:
        jogad+=k['n']
    clu=len(club.index)
    njogad=0
    while(njogad<clu and njogad<jogad):
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
        if len(tatica[indexaux]['jogador'].index)>=(tatica[indexaux]['n'])/2:
            if (club.loc[bestpla[bigpos[0][0]]]['Age']>subida):
                club.set_value(bestpla[bigpos[0][0]],[bigpos[0][0]],0)
                if(somatr(club.loc[bestpla[bigpos[0][0]]])==0):
                    club=club.drop(bestpla[bigpos[0][0]])
                    clu-=1
            else:
                tatica[indexaux]['jogador']=tatica[indexaux]['jogador'].append(club.loc[bestpla[bigpos[0][0]]])
                club=club.drop(bestpla[bigpos[0][0]])
        else:
            tatica[indexaux]['jogador']=tatica[indexaux]['jogador'].append(club.loc[bestpla[bigpos[0][0]]])
            club=club.drop(bestpla[bigpos[0][0]])
        if len(tatica[indexaux]['jogador'].index)==(tatica[indexaux]['n']):
            posi.remove(bigpos[0][0])
        njogad=0
        for k in tatica:
            njogad+=len(k['jogador'].index)
    return tatica

def resumoplantel (plante):
    equipa=pd.DataFrame(columns=list(plante[0]['jogador'].columns))
    equipa.insert(0,'Pos','')
    for pos in plante:
        joga=pd.DataFrame(columns=list(plante[0]['jogador'].columns))
        joga=pos['jogador'].copy()
        joga.insert(0,'Pos',pos['Position'])
        equipa=equipa.append(joga, sort=False)
    return(equipa)


def compras(jogadoress,tatica,jogadoresimpo,clube,orcamento,salario,subida,ages):
    joga=jogadoress.copy()
    joga=joga.drop(jogadoresimpo)
    joga=joga[(joga['Age']<ages) | (joga['Club']==clube)]
    posi=list(jogadoress.columns[(jogadoress.dtypes.values==np.dtype('float64'))])
    compras=pd.DataFrame(columns=list(jogadoress.columns))
    joga['Wage']+=1
    joga['Sale Value']+=1
    equi=plantel(joga,tatica,clube,subida)
    while(True):
        orc=orcamento-compras['Sale Value'].sum()
        sal=salario-compras['Wage'].sum()
#ver a posição em que o melhor tem a maior dif para o meu ultimo
        bestpos={}
        bestpla={}
        for pos in posi:
            orca=orc
            sala=sal
            indexaux=[j for j,_ in enumerate(equi) if _['Position'] == pos]
            if len(indexaux)==0:
                indexaux=0
            else:
                indexaux=indexaux[0]
            if(equi[indexaux]['jogador'][-1:].index[0] in compras.index):
                orca+=equi[indexaux]['jogador'][-1:]['Sale Value'][0]
                sala+=equi[indexaux]['jogador'][-1:]['Wage'][0]
            jog=joga[(joga['Wage']<=sala) & (joga['Sale Value']<=orca) & (joga['Club']!=clube)]
            jog[pos]=jog[pos]-equi[indexaux]['jogador'][-1:][pos][0]
            jog=jog[jog[pos]>0]
            if(len(jog)>0):
                jog[pos]=(jog[pos])/(((jog['Wage']/sala)+(jog['Sale Value']/orca))/2)
                jog=jog.sort_values(by=[pos], ascending=False)
                bestpos.update({pos:jog.iloc[0][pos]})
                bestpla.update({pos:jog.index[0]})
        if(len(bestpos)>0):
            bestpos=sorted(bestpos.items(), key=lambda p: p[1], reverse=True)
            compras=compras.append(joga.loc[bestpla[bestpos[0][0]]])
            joga.set_value(bestpla[bestpos[0][0]],['Club'],clube)
            equi=plantel(joga,tatica,clube,subida)
            plant=resumoplantel(equi)
            for player in list(compras.index):
                if(player not in plant.index):
                    compras=compras.drop(player)
            print(compras)
        else:
            break
    return (resumoplantel(equi),compras)

def plantelfilter(pla,tatic,outroplantel,club,idade):
    for equ in outroplantel:
        pla=pla.drop(list(equ.index))
    pla=pla[pla['Age']<=idade]
    return(plantel(pla,tatic,club,idade))

def comprasfilter(pla,tatica,outroplantel,jogadoresimpo,clube,orcamento,salario,idade):
    for equ in outroplantel:
        pla=pla.drop(list(equ.index))
    pla=pla[pla['Age']<=idade]
    return(compras(pla,tatica,jogadoresimpo,clube,orcamento,salario,idade,idade-1))

def jogadorescomprados(jogadoress,comprados,clube):
    for jcom in comprados:
        jogadoress.set_value(jcom,['Club'],clube)
    return jogadoress

file="D:\FM\Players\jogadores.csv"
jogadores=lerficheiro(file)
#criar avaliação por posição
#estimar o potencial a acrescentar em cada idade
posicoes=list(jogadores.columns[(jogadores.dtypes.values==np.dtype('float64'))])
posicoes=list(set([pos.replace(' Rating','').replace(' Pot','') for pos in posicoes]))

diajogo= datetime.date(2018, 7, 1)

jogadores_cal=calcular_atributo(fimcontrato(jogadores, diajogo),posicoes)

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
 
nomeclube='Sporting'
idadesuplente=25
transferencias=3350000
salarios=93820
idadecompras=28
    
sporting=resumoplantel(plantel(jogadores_cal,tatica_4_1_1_3_1,nomeclube,idadesuplente))

jogadoresimpo=[]
sportingcomprasfuturas=[('Neto', 55002114, 'Portugal')]
jogadores_comcompras=jogadorescomprados(jogadores_cal,sportingcomprasfuturas,nomeclube)

sporting=resumoplantel(plantel(jogadores_comcompras,tatica_4_1_1_3_1,nomeclube,idadesuplente))
comprassporting=compras(jogadores_comcompras,tatica_4_1_1_3_1,jogadoresimpo,nomeclube,transferencias,salarios,idadesuplente,idadecompras)

sp=[sporting]

transferencias-=sum(comprassporting[1]['Sale Value'])
salarios-=sum(comprassporting[1]['Wage'])
idaderes=23
sportingb=resumoplantel(plantelfilter(jogadores_cal,tatica_4_1_1_3_1,sp,nomeclube,idaderes))
comprasb=comprasfilter(jogadores_cal,tatica_4_1_1_3_1,sp,jogadoresimpo,nomeclube,transferencias,salarios,idaderes)

sp=[sporting,sportingb]
transferencias-=sum(comprasb[1]['Sale Value'])
salarios-=sum(comprasb[1]['Wage'])
idaderes=21
sportingsub23=resumoplantel(plantelfilter(jogadores_cal,tatica_4_1_1_3_1,sp,nomeclube,idaderes))
comprassub23=comprasfilter(jogadores_cal,tatica_4_1_1_3_1,sp,jogadoresimpo,nomeclube,transferencias,salarios,idaderes)

sp=[sporting,sportingb,sportingsub23]
transferencias-=sum(comprassub23[1]['Sale Value'])
salarios-=sum(comprassub23[1]['Wage'])
idaderes=19
sportingjuniores=resumoplantel(plantelfilter(jogadores_cal,tatica_4_1_1_3_1,sp,nomeclube,idaderes))
comprassubjuniores=comprasfilter(jogadores_cal,tatica_4_1_1_3_1,sp,jogadoresimpo,nomeclube,transferencias,salarios,idaderes)
