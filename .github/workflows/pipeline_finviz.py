from finvizfinance.quote import finvizfinance
import pandas as pd
import numpy as np
import os
import time

from datetime import datetime

# Get current date and time
# current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
current_datetime = datetime.now().strftime("%Y-%m-%d")

# Create the gurufocus folder if it doesn't exist
if not os.path.exists('finviz'):
    os.makedirs('finviz')

#get ticker list by filtering only above 1 billion dollar company
DF = pd.read_csv(f'america_2024-03-01.csv')
tickerlst  = list(DF.query('`Market Capitalization`>300e9').Ticker)

#main loop; wait 15 second for every 20 ticker
dfs = []
counter=0
maxiter = len(tickerlst )
for ticker in tickerlst :
  if not '/' in ticker:
    counter+=1
    print(f"{counter} out of {maxiter}  -  {ticker}")
    if counter % 20 ==0:
      time.sleep(15)
    try:
      stock = finvizfinance(ticker)
      mydict = stock.ticker_fundament()
      mydict['Ticker'] =ticker
      dfs.append(mydict)
    except:
      print('***ERROR')
      pass

# Concatenate the DataFrames in the list to create a single DataFrame    
DFtotal = pd.DataFrame(dfs)
DFtotal.to_csv(f'finviz/FinViz_{current_datetime}.csv',index=False)


