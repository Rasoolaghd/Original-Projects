'''
Off Day and Additional Deliveries
Re-engineered September/October 2016
'''

from pandas import Series, DataFrame, read_csv
import numpy as np
import pandas as pd
from datetime import datetime as dt
import itertools

pd.set_option('display.height', 100)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 100)


pw_offday = read_csv('C:/Users/pmwash/Desktop/Re-Engineered Reports/Off Day Deliveries/pw_offday.csv')
weeklookup = read_csv('C:/Users/pmwash/Desktop/Re-Engineered Reports/Off Day Deliveries/pw_offday_weeklookup.csv')#change htese paths



def clean_pw_offday(pw_offday, weeklookup):
    '''
    Clean pw_offday query without filtering out non-off-days
    invoice-level => day level => customer level
    '''
    deliveries = pw_offday
    
    def as400_date(dat):
        '''Accepts date as formatted in AS400'''
        dat = str(dat)
        dat = dat[-6:]
        dat = str(dt.date(dt.strptime(dat, '%y%m%d')))
        return dat
        
    def sum_digits_in_string(digit):
        return sum(int(x) for x in digit if x.isdigit())
        
    deliveries.columns = ['Date', 'Division', 'Invoice', 'CustomerId', 'Call', 'Priority', 
               'Warehouse', 'Cases', 'Dollars', 'Ship', 'Salesperson', 
               'ShipWeekPlan', 'Merchandising', 'OnPremise', 
               'CustomerSetup', 'CustomerType', 'Customer']
    
    typ = deliveries.CustomerType
    typ_map = {'A':'Bar/Tavern','C':'Country Club','E':'Transportation/Airline','G':'Gambling',\
                'J':'Hotel/Motel','L':'Restaurant','M':'Military','N':'Fine Dining','O':'Internal',\
                'P':'Country/Western','S':'Package Store','T':'Supermarket/Grocery','V':'Drug Store',\
                'Y':'Convenience Store','Z':'Catering','3':'Night Club','5':'Adult Entertainment','6':'Sports Bar',\
                'I':'Church','F':'Membership Club','B':'Mass Merchandiser','H':'Fraternal Organization',\
                '7':'Sports Venue'}
    deliveries.CustomerType = deliveries.CustomerType.astype(str).map(typ_map)    
    
    whs_map = {1:'Kansas City',2:'Saint Louis',3:'Columbia',4:'Cape Girardeau', 5:'Springfield'}
    deliveries.Warehouse = deliveries.Warehouse.map(whs_map)          
    
    deliveries.Date = [as400_date(d) for d in deliveries.Date.astype(str).tolist()]    
    deliveries = deliveries.merge(weeklookup, on='Date')
    
    dat = Series(deliveries.Date.tolist())
    dat_f = Series([dt.strptime(d, '%Y-%m-%d') for d in dat])
    deliveries['Weekday'] = Series([dt.strftime(d, '%A') for d in dat_f])
    
    week_plan = deliveries.ShipWeekPlan.tolist()
    week_shipped = deliveries.ShipWeek.tolist()
    
    month = deliveries.Month
    year = deliveries.Year
    
    deliveries.Ship = del_days = [str('%07d'% int(str(day).zfill(0))) for day in deliveries.Ship.astype(str).tolist()]
    
    mon = Series([d[-7:][:1] for d in del_days]).map({'1':'M','0':'_'})
    tue = Series([d[-6:][:1] for d in del_days]).map({'1':'T','0':'_'})
    wed = Series([d[-5:][:1] for d in del_days]).map({'1':'W','0':'_'})
    thu = Series([d[-4:][:1] for d in del_days]).map({'1':'R','0':'_'})
    fri = Series([d[-3:][:1] for d in del_days]).map({'1':'F','0':'_'})
    sat = Series([d[-2:][:1] for d in del_days]).map({'1':'S','0':'_'})
    sun = Series([d[-1:][:1] for d in del_days]).map({'1':'U','0':'_'})
    
    deliveries['DeliveryDays'] = del_days = list(itertools.chain.from_iterable([mon + tue + wed + thu + fri + sat + sun]))
    
    weekday = deliveries.Weekday = [d[:3] for d in deliveries.Weekday.astype(str).tolist()]
    _days = DataFrame(data={'Weekday':weekday, 'WeekPlanned':week_plan, 'WeekShipped':week_shipped, 'DelDays':del_days}) #'Monday':mon, 'Tuesday':tue, 'Wednesday':wed, 'Thursday':thu, 'Friday':fri, 'Saturday':sat, 'Sunday':sun,
    day_list = _days['WeekPlanned'].tolist()
    _days['WeekPlanned'] = [d if d in ['A','B'] else '' for d in day_list]
    
    _week_actual = _days.WeekShipped.tolist()
    _week_plan = _days['WeekPlanned'] = [ship_week if plan_week == '' else plan_week for ship_week, plan_week in zip(_week_actual,_days.WeekPlanned.tolist())]
    _days['OffWeek'] = _off_week = [p != a for p, a in zip(_week_plan, _week_actual)]
    
    off_mon = [str('M' not in d and w == 'Mon')[:1] for d, w in zip(del_days, weekday)]
    off_tue = [str('T' not in d and w == 'Tue')[:1] for d, w in zip(del_days, weekday)]
    off_wed = [str('W' not in d and w == 'Wed')[:1] for d, w in zip(del_days, weekday)]
    off_thu = [str('R' not in d and w == 'Thu')[:1] for d, w in zip(del_days, weekday)]
    off_fri = [str('F' not in d and w == 'Fri')[:1] for d, w in zip(del_days, weekday)]
    off_sat = [str('S' not in d and w == 'Sat')[:1] for d, w in zip(del_days, weekday)]
    off_sun = [str('U' not in d and w == 'Sun')[:1] for d, w in zip(del_days, weekday)]
    
    _off_days = DataFrame({'Mon':off_mon, 'Tue':off_tue, 'Wed':off_wed, 'Thu':off_thu, 
                           'Fri':off_fri, 'Sat':off_sat, 'Sun':off_sun, 'OffWeek':_off_week, 'Weekday':weekday})
    _off_days = _off_days[['Mon','Tue','Wed','Thu','Fri','Sat','Sun','Weekday','OffWeek']]                           
    _off_days['OffDayDelivery'] = (_off_days['Mon'] == 'T') | (_off_days['Tue'] == 'T') | (_off_days['Wed'] == 'T') | (_off_days['Thu'] == 'T') | (_off_days['Fri'] == 'T') | (_off_days['Sat'] == 'T') | (_off_days['Sun'] == 'T') | (_off_days['OffWeek'] == True)                
                           
    check_later = _off_days[_off_days['OffDayDelivery'] == True]
    
    deliveries = pd.concat([deliveries,_off_days[['OffWeek','OffDayDelivery']]], axis=1)
    deliveries.Call = deliveries.Call.map({1:'Customer Call', 2:'ROE/EDI', 3:'Salesperson Call', 4:'Telesales'})
    
    setup_date = deliveries.CustomerSetup.astype(str).tolist()
    setup_month = Series([d.zfill(4)[:2] for d in setup_date])
    this_century = [int(d[-2:]) < 20 for d in setup_date]
    setup_year = Series(["20" + s[-2:] if int(s[-2:]) < 20 else "19" + s[-2:] for s in setup_date])
    
    deliveries['CustomerSetup'] = c_setup = [str(mon) + '-' + str(yr) for mon, yr in zip(setup_month, setup_year)]
    
    last_month = str(dt.now().month - 1).zfill(2)
    this_year = str(dt.now().year)
    m_y_cutoff = last_month + '-' + this_year
    
    transaction_month = [d[5:7] for d in deliveries.Date.tolist()]
    transaction_year = [d[:4] for d in deliveries.Date.tolist()]
    m_y_transaction = [m + '-' + y for m, y in zip(transaction_month, transaction_year)]
    
    deliveries['NewCustomer'] = _new_cust = [1 if m_y_cutoff == setup else 0 for setup in c_setup]
    deliveries['OffDayDeliveries'] =  deliveries.OffDayDelivery.astype(int)
    
    _n_days = deliveries.Ship.astype(str).tolist()
    deliveries['AllottedWeeklyDeliveryDays'] = [sum_digits_in_string(n) for n in _n_days]
    _allot = deliveries['AllottedWeeklyDeliveryDays'].tolist()
    _week_ind = deliveries['ShipWeekPlan'].tolist()
    deliveries['AllottedWeeklyDeliveryDays'] = [a if w not in ['A','B'] else 0.5 for a, w in zip(_allot, _week_ind)]
    _n_days = deliveries.set_index('CustomerId')['AllottedWeeklyDeliveryDays'].to_dict()
        
    print(deliveries.head(),'\n\n\n\n',deliveries.tail())
    
    
    # Aggregate by day 
    len_unique = lambda x: len(pd.unique(x))
    agg_funcs_day = {'OffDayDeliveries' : {'Count':max}, 
                 'Date' : {'Count':len_unique},
                 'Cases' : {'Sum':sum, 'Avg':np.mean},
                 'Dollars' : {'Sum':sum, 'Avg':np.mean},
                 'NewCustomer': lambda x: min(x)}
    
    pass_through_cols = ['CustomerId','Customer','Week','Date']
    _agg_byday = DataFrame(deliveries.groupby(pass_through_cols).agg(agg_funcs_day)).reset_index(drop=False)
    _agg_byday = DataFrame(_agg_byday[['CustomerId','Customer','Week','Date','OffDayDeliveries','NewCustomer','Cases','Dollars']])
    _agg_byday.columns = ['%s%s' % (a, '|%s' % b if b else '') for a, b in _agg_byday.columns]
    _agg_byday.columns = ['CustomerId','Customer','Week','Date','Delivery','OffDayDelivery','NewCustomer','Cases|Sum','Cases|Avg','Dollars|Sum','Dollars|Avg']
    _agg_byday['AllottedWeeklyDeliveryDays|Count'] = _agg_byday['CustomerId'].astype(int)
    _agg_byday['AllottedWeeklyDeliveryDays|Count'] = _agg_byday['AllottedWeeklyDeliveryDays|Count'].map(_n_days)
    
    
    
    # Aggregate by week for use later on
    agg_funcs_week = {'OffDayDelivery' : {'Count':sum},
                      'Delivery' : {'Count':sum},
                      'NewCustomer' : lambda x: min(x)}
    
    _agg_byweek = DataFrame(_agg_byday.groupby(['CustomerId','Week']).agg(agg_funcs_week)).reset_index(drop=False)
    _agg_byweek.columns = ['%s%s' % (a, '|%s' % b if b else '') for a, b in _agg_byweek.columns]
    
        
    # Map number of total deliveries each week by customer
    # to determine whether a customer with TWR deliveries 
    # got TWF deliveries -- which is an off-day delivery
    # but not an additional delivery. Use a dictionary {(cust#, week) : n_deliveries_total}
    _c = _agg_byweek['CustomerId'].astype(str).tolist()
    _w = _agg_byweek['Week'].astype(str).tolist()
    _agg_byweek['_X'] = [c + ',' + w for c,w in zip(_c,_w)]
    by_week_map = _agg_byweek.set_index('_X')['Delivery|Count'].to_dict()
    
    cid = _agg_byday['CustomerId'].astype(str).tolist()
    wkk = _agg_byday['Week'].astype(str).tolist()
    _agg_byday['N_DeliveriesThisWeek'] = [c + ',' + w for c, w in zip(cid, wkk)]
    _agg_byday['N_DeliveriesThisWeek'] = _agg_byday['N_DeliveriesThisWeek'].map(Series(by_week_map))
    
    
    
    addl_day_criteria_1 = ( _agg_byday.shift(1)['CustomerId'] == _agg_byday['CustomerId'] )
    addl_day_criteria_2 = ( _agg_byday.shift(1)['Week'] == _agg_byday['Week'] )
    addl_day_criteria_3 = ( _agg_byday['OffDayDelivery'] == 1 )
    addl_day_criteria_4 = ( _agg_byday['NewCustomer'] != 1 )
    addl_day_criteria_5 = ( _agg_byday['N_DeliveriesThisWeek'] > _agg_byday['AllottedWeeklyDeliveryDays|Count'] )
    
    _agg_byday['AdditionalDeliveryDays'] = Series(addl_day_criteria_1 & addl_day_criteria_2 & addl_day_criteria_3 & addl_day_criteria_4 & addl_day_criteria_5).astype(int)
    
    
    
    ### CHECK CALCULATION FOR ADDITIONAL DEL DAYS THERE IS A BUG
    # Aggregate by customer to see how each customer did during the time period specified
    agg_funcs_cust = {'OffDayDelivery' : {'Count':sum},
                      'Delivery' : {'Count':sum},
                      'NewCustomer' : lambda x: min(x),
                      'AllottedWeeklyDeliveryDays|Count': lambda x: max(x),
                      'AdditionalDeliveryDays': lambda x: sum(x),
                      'Dollars|Sum':lambda x: int(sum(x)),
                      'Cases|Sum':lambda x: sum(x) }                                           
    
    _agg_bycust = DataFrame(_agg_byday.groupby(['CustomerId','Customer']).agg(agg_funcs_cust)).reset_index(drop=False)
    _agg_bycust.columns = ['%s%s' % (a, '|%s' % b if b else '') for a, b in _agg_bycust.columns]
    _agg_bycust = _agg_bycust.reindex_axis(sorted(_agg_bycust.columns), axis=1)
    
    _agg_bycust.columns = ['AdditionalDeliveries','AllottedDeliveryDays','Cases',
                           'Customer','CustomerId','Deliveries','Dollars',
                           'NewCustomer','OffDayDeliveries']
    _agg_bycust = _agg_bycust[['CustomerId','Customer','NewCustomer','AllottedDeliveryDays','Deliveries',
                               'OffDayDeliveries','AdditionalDeliveries','Cases','Dollars']]
    
    
    # Map customer attributes from the deliveries raw dataframe
    attr = ['CustomerId','Warehouse','OnPremise','CustomerSetup','CustomerType','ShipWeekPlan','DeliveryDays']
    customer_attributes = deliveries[attr].drop_duplicates().reset_index(drop=True)
    
    _agg_bycust = _agg_bycust.merge(customer_attributes, on='CustomerId', how='inner').drop_duplicates()
    _agg_bycust = _agg_bycust.sort_values(by=['AdditionalDeliveries','OffDayDeliveries'], ascending=False).reset_index(drop=True)
    
    _agg_bycust['CasesPerDelivery'] = _agg_bycust['Cases'] / _agg_bycust['Deliveries']
    _agg_bycust['DollarsPerDelivery'] = round(_agg_bycust['Dollars'] / _agg_bycust['Deliveries'],2)
    
    _agg_bycust['OffDayDeliveries/Deliveries'] = round(_agg_bycust['OffDayDeliveries'] / _agg_bycust['Deliveries'],2)
    _agg_bycust['AdditionalDeliveries/Deliveries'] = round(_agg_bycust['AdditionalDeliveries'] / _agg_bycust['Deliveries'],2)
    
    
    # Map tiers to customers
    tier_map = {0:'No Delivery Days Assigned',0.5:'Tier 4', 1:'Tier 3', 2:'Tier 2', 3:'Tier 1', 4:'Tier 1', 5:'Tier 1', 6:'Tier 1', 7:'Tier 1'}
    _agg_bycust['Tier'] = _agg_bycust['AllottedDeliveryDays'].map(tier_map)
    
    addl_deliv = _agg_bycust['AdditionalDeliveries'].tolist()
    tier = _agg_bycust['Tier'].tolist()
    
    _agg_bycust['AdditionalDeliveries'] = [addl if t != 'No Delivery Days Assigned' else 0 for addl, t in zip(addl_deliv, tier)]
    
    _agg_bycust['ShipWeekPlan'] = _agg_bycust['ShipWeekPlan'].replace(np.nan, '')
    
    
    # Create summary
    agg_funcs_summary = {'Deliveries':sum,
                         'OffDayDeliveries':sum,
                         'AdditionalDeliveries':sum,
                         'Dollars':{'Avg':np.mean},
                         'Cases':{'Avg':np.mean},
                         'CasesPerDelivery':{'Avg':np.mean},
                         'NewCustomer':sum,
                         'Customer':len,
                         'AllottedDeliveryDays':lambda x: round(np.mean(x),1)}                                           
    
    overall_summary = DataFrame(_agg_bycust.groupby(['Tier','Warehouse']).agg(agg_funcs_summary))
    overall_summary.columns = ['%s%s' % (a, '|%s' % b if b else '') for a, b in overall_summary.columns]
    overall_summary = overall_summary[['NewCustomer|sum','Customer|len','AllottedDeliveryDays|<lambda>',
                                       'Deliveries|sum','OffDayDeliveries|sum','AdditionalDeliveries|sum',
                                       'Cases|Avg','CasesPerDelivery|Avg','Dollars|Avg']]
    overall_summary.columns = ['NewCustomers','Customers','AvgAllottedDeliveryDays','Deliveries','OffDayDeliveries','AdditionalDeliveries',
                                       'Cases|mean','CasesPerDelivery|mean','Dollars|mean']
    
    
    
    
    
    return overall_summary, _agg_bycust, _agg_byday


summary, by_customer, by_day = clean_pw_offday(pw_offday, weeklookup)

summary
by_customer.tail()
by_day.tail()







def write_offday_report_to_excel(summary, by_customer, by_day, month='September 2016'):
    '''
    Write report to Excel with formatting
    '''
    pass
file_out = pd.ExcelWriter('N:/Operations Intelligence/Monthly Reports/Off Day Deliveries/Delivery Audit -'+month+'.xlsx', engine='xlsxwriter')
workbook = file_out.book

summary.to_excel(file_out, sheet_name='Summary', index=True)
by_customer.to_excel(file_out, sheet_name='By Customer', index=False)
by_day.to_excel(file_out, sheet_name='By Delivery Day', index=False)

# Declare formats
format_thousands = workbook.add_format({'num_format': '#,##0'})
format_dollars = workbook.add_format({'num_format': '$#,##0'})
format_percent = workbook.add_format({'num_format': '0%'})


# Set column widths
summary_tab = file_out.sheets['Summary']
summary_tab.set_column('A:A',25)
summary_tab.set_column('B:B',14)
summary_tab.set_column('C:C',14)
summary_tab.set_column('D:D',10)
summary_tab.set_column('E:E',23)
summary_tab.set_column('F:F',10)
summary_tab.set_column('G:G',16)
summary_tab.set_column('H:H',19)
summary_tab.set_column('I:I',12, format_thousands)
summary_tab.set_column('J:J',22.5, format_thousands)
summary_tab.set_column('K:K',13, format_dollars)

# Set column widths
customer_tab = file_out.sheets['By Customer']
customer_tab.set_column('A:A',11)
customer_tab.set_column('B:B',37)
customer_tab.set_column('C:C',13.5)
customer_tab.set_column('D:D',19.5)
customer_tab.set_column('E:E',9.3)
customer_tab.set_column('F:G',19)
customer_tab.set_column('H:K',12)
customer_tab.set_column('J:K',12)
customer_tab.set_column('H:H',12, format_thousands)
customer_tab.set_column('L:O',15)
customer_tab.set_column('M:M',21)
customer_tab.set_column('P:Q',17, format_thousands)
customer_tab.set_column('R:T',28)

# Set column widths
day_tab = file_out.sheets['By Delivery Day']
day_tab.set_column('A:A',11)
day_tab.set_column('B:B',37)
day_tab.set_column('C:C',6)
day_tab.set_column('D:D',10)
day_tab.set_column('E:E',8)
day_tab.set_column('F:H',13.2, format_thousands)
day_tab.set_column('I:K',12, format_thousands)
day_tab.set_column('L:L',33)
day_tab.set_column('M:N',21)





file_out.save()









from ggplot import *
g = ggplot(by_customer, aes('Tier', 'AdditionalDeliveries', colour='CustomerType'))
g + geom_bar() + facet_wrap('Warehouse') 










