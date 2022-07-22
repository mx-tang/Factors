#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 16:34:05 2022

@author: daizytang
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

daily_return=pd.read_csv('DailyReturns.csv')
daily_return=daily_return.set_index('Unnamed: 0')


tradefilter=pd.read_csv('TradeFilter.csv')
tradefilter=tradefilter.set_index('Unnamed: 0')


def generate_pos(MA = 5, percentage=0.2, Return = daily_return, Trade_or_not = tradefilter):
    position=pd.DataFrame(data=np.zeros(Return.shape), index=Return.index, columns=Return.columns)
    mom=Return.rolling(window=MA).mean()
    ### do loops for every day
    for i in range(MA-1, len(Return.index)):
        # drop nan data
        try1=mom.iloc[i,:].dropna().index
        # confirm trade filter
        valid1=Trade_or_not.loc[Trade_or_not.index[i], try1]
        # get valid MA return
        valid_mom=mom.loc[Return.index[i], valid1[valid1==True].index]
        
        # conform the valid asset number in portfolio
        num=int(np.floor(len(valid_mom) * percentage))
    
        # generate position
        lower_item=valid_mom.sort_values(ascending=False).index[-num:]
        upper_item=valid_mom.sort_values(ascending=False).index[0:num]
        position.loc[position.index[i], lower_item]=-1/(2*num)
        position.loc[position.index[i], upper_item]=1/(2*num)
    return position

position=generate_pos(MA = 5, percentage=0.2, Return = daily_return, Trade_or_not = tradefilter)
'''
Specially attention here!!!
position.iloc[5:,:].replace(0, np.nan, inplace=True)
position=position.fillna(method='ffill')
'''

# get daily investment return, pay attention to the delay 1 day
invest_return = daily_return * position.shift(1)
p_return = invest_return.sum(axis=1)
p_return.index=pd.to_datetime(p_return.index) ### change the index to datetime

# get accumulative portfolio return and draw the picture
p_return.cumsum().plot()
plt.xlabel('date')
plt.ylabel('acc_return')
plt.title('short term momentum for CTA')


# daily turnover rate
daily_turnover=abs(position.diff(1)).sum(axis=1) / abs(position).sum(axis=1)
daily_turnover.index=pd.to_datetime(daily_turnover.index) ### change the index to datetime

'''
deal with the performace metric:
    total return
    annual return
    sharp ratio
    max drawdown
    daily turnover

'''
def performance_metric(freq='Q', p_return=p_return, daily_turnover=daily_turnover):
    # get group data according to freq
    p_group=p_return.resample(freq)
    turnover_group=daily_turnover.resample(freq)
    date=p_group.last().index
    date1=date.strftime('%Y-%m-%d').tolist()
    date1.append('total')
    
    total_return=[]
    annual_return=[]
    sharp_ratio=[]
    max_drawdown=[]
    turnover=[]

# get freq results

    for item in p_group: ### initial item is a tuple
        item=item[1]
        total_return.append(item.sum())
        annual_return.append(item.mean() * 252)
        sharp_ratio.append(item.mean() / item.std() * np.sqrt(252))
        
        cumr=item.cumsum()
        curr_max=cumr.cummax()
        drawdown=curr_max - cumr
        max_drawdown.append(drawdown.max())
        
        
    for item in turnover_group:
        item=item[1]
        turnover.append(item.mean())

# get whole period result
    total_return.append(p_return.sum())
    annual_return.append(p_return.mean() * 252)
    sharp_ratio.append(p_return.mean() / p_return.std() * np.sqrt(252))
    
    
    cumr=p_return.cumsum()
    curr_max=cumr.cummax()
    drawdown=curr_max - cumr
    max_drawdown.append(drawdown.max())
    
    turnover.append(daily_turnover.mean())
    
    ### generate result dataframe
    diction={'period':date1,'total_return':total_return, 'annual_return':annual_return, 'sharp_ratio': sharp_ratio, 'max_drawdown':max_drawdown, 'daily_turnover':turnover}
    metrics=pd.DataFrame(diction)
    metrics=metrics.set_index('period',drop=True)
    return metrics

res=performance_metric(freq='Q', p_return=p_return, daily_turnover=daily_turnover)
res.to_csv('CTA_MM_performance_result.csv')
