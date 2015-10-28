"""MC2-P1: Market simulator."""

import pandas as pd
import numpy as np
import os
import csv

from util import get_data, plot_data
from portfolio.analysis import get_portfolio_value, get_portfolio_stats, plot_normalized_data

def compute_portvals(start_date, end_date, orders_file, start_val):
    """Compute daily portfolio value given a sequence of orders in a CSV file.

    Parameters
    ----------
        start_date: first date to track
        end_date: last date to track
        orders_file: CSV file to read orders from
        start_val: total starting cash available

    Returns
    -------
        portvals: portfolio value for each trading day from start_date to end_date (inclusive)
    """
    # TODO: Your code here
    #create df_prices
    df_temp = pd.read_csv(orders_file, index_col='Date', parse_dates=True)
    symbols = []
    for index,row in df_temp.iterrows():		
    	symbols.append(row['Symbol'])
    symbols = list(set(symbols))
    dates = pd.date_range(start_date, end_date)
    df_prices = get_data(symbols, dates)
    df_prices = df_prices.drop('SPY',1)
    df_prices['CASH'] = 1.0
    #print df_prices
    
    #Create df_trade.
    #Check for leverage by create a curr_list that save the cumulative holding.
    #When a new order comes, create a temp_list with update holding and multiply it with current prices, 
    #then check to see if leverage exceeds 2 or not. If it's not, then process the order,
    #change curr_list to temp_list and update df_trade
    #If it exceeds 2, then don't process the order and do nothing 
    df_trade = df_prices.copy()
    df_trade[df_trade != 0] = 0
    df_trade.ix[start_date,'CASH'] = start_val
    curr_list = df_trade.ix[start_date].copy()
    for index, row in df_temp.iterrows():
    	temp_list = curr_list.copy()
    	temp_list.ix[row['Symbol']] += (1 if row['Order'] == 'BUY' else -1)*float(row['Shares'])
    	temp_list.ix['CASH'] += (-1 if row['Order'] == 'BUY' else 1)*float(row['Shares'])*df_prices.ix[index,row['Symbol']]
    	sum_abs_all  = abs(temp_list).dot(df_prices.ix[index])
    	sum_cash = abs(temp_list['CASH'])
    	sum_all = temp_list.dot(df_prices.ix[index])
    	leverage = (sum_abs_all-sum_cash)/sum_all
    	#print df_prices.ix[index,row['Symbol']], sum_abs_all , sum_cash, sum_all, leverage
    	if (leverage <= 2.0):
    		curr_list = temp_list.copy()
    		df_trade.ix[index,row['Symbol']] += (1 if row['Order'] == 'BUY' else -1)*float(row['Shares'])
    		df_trade.ix[index,'CASH'] += (-1 if row['Order'] == 'BUY' else 1)*float(row['Shares'])*df_prices.ix[index,row['Symbol']]
    #print df_trade
    
    #calculate holding from df_trade and portvals
    portvals = pd.Series(index = df_prices.index)
    portvals.ix[0] = df_prices.ix[0].dot(df_trade.ix[0])
    for i in range(1,df_trade.shape[0]):
    	df_trade.ix[i] += df_trade.ix[i-1]
    	portvals.ix[i] = df_prices.ix[i].dot(df_trade.ix[i])
    print portvals
    return portvals


def test_run():
    """Driver function."""
    # Define input parameters
    start_date = '2011-01-05'
    end_date = '2011-01-20'
    orders_file = os.path.join("orders", "orders-short.csv")
    start_val = 1000000

    # Process orders
    portvals = compute_portvals(start_date, end_date, orders_file, start_val)
    if isinstance(portvals, pd.DataFrame):
        portvals = portvals[portvals.columns[0]]  # if a DataFrame is returned select the first column to get a Series

    # Get portfolio stats
    cum_ret, avg_daily_ret, std_daily_ret, sharpe_ratio = get_portfolio_stats(portvals)
    

    # Simulate a $SPX-only reference portfolio to get stats
    prices_SPX = get_data(['$SPX'], pd.date_range(start_date, end_date))
    prices_SPX = prices_SPX[['$SPX']]  # remove SPY
    portvals_SPX = get_portfolio_value(prices_SPX, [1.0])
    cum_ret_SPX, avg_daily_ret_SPX, std_daily_ret_SPX, sharpe_ratio_SPX = get_portfolio_stats(portvals_SPX)




    # Compare portfolio against $SPX
    print "Data Range: {} to {}".format(start_date, end_date)
    print
    print "Sharpe Ratio of Fund: {}".format(sharpe_ratio)
    print "Sharpe Ratio of $SPX: {}".format(sharpe_ratio_SPX)
    print
    print "Cumulative Return of Fund: {}".format(cum_ret)
    print "Cumulative Return of $SPX: {}".format(cum_ret_SPX)
    print
    print "Standard Deviation of Fund: {}".format(std_daily_ret)
    print "Standard Deviation of $SPX: {}".format(std_daily_ret_SPX)
    print
    print "Average Daily Return of Fund: {}".format(avg_daily_ret)
    print "Average Daily Return of $SPX: {}".format(avg_daily_ret_SPX)
    print
    print "Final Portfolio Value: {}".format(portvals[-1])

    # Plot computed daily portfolio value
    df_temp = pd.concat([portvals, prices_SPX['$SPX']], keys=['Portfolio', '$SPX'], axis=1)
    plot_normalized_data(df_temp, title="Daily portfolio value and $SPX")


if __name__ == "__main__":
    test_run()
