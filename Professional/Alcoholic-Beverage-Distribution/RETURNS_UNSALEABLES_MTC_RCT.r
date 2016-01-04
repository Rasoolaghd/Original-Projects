library(dplyr)
library(xlsx)
library(lubridate)
library(ggplot2)

print('Define functions necessary for analysis.')
headTail = function(x) {
  h <- head(x)
  t <- tail(x)
  print(h)
  print(t)
}

as400Date <- function(x) {
  date <- as.character(x)
  date <- substrRight(date, 6)
  date <- as.character((strptime(date, "%y%m%d")))
  date
}

substrRight <- function(x, n){
  substr(x, nchar(x)-n+1, nchar(x))
}

substrLeft <- function(x, n){
  substr(x, 1, n)
}


print('Beer returns & spoilage. Based on RCT1 and mtc1 files in AS400.')
setwd("C:/Users/pmwash/Desktop/R_files/Data Input")


print('Be sure to re-run both queries. Gain access to query before replacing these file objects in memory.')
rct = read.csv('rct1.csv', header=TRUE, na.strings='NA')
mtc = read.csv('mtc1.csv', header=TRUE, na.strings=NA) #make sure change file name to mtc
headTail(rct)
headTail(mtc)

print('Create dates in both files.')
rct$DATE = as400Date(rct$X.RDATE)
rct$MONTH = month(rct$DATE, label=TRUE)
mtc$DATE = as400Date(mtc$X.MIVDT)
mtc$MONTH = month(mtc$DATE, label=TRUE)

print('Create cases from cases & bottles using QPC.')
cs = rct$X.RCASE
btl = rct$X.RBOTT
qpc = rct$X.RQPC
rct$CASES = cs + round(btl/qpc, 2)


print('Put in Class codes.')
class = rct$X.RCLA.
rct$CLASS = ifelse(class==10, 'Liquor & Spirits', 
                   ifelse(class==25, 'Liquor & Spirits',
                          ifelse(class==50, 'Wine', 
                                 ifelse(class==51, 'Wine', 
                                        ifelse(class==53, 'Wine', 
                                               ifelse(class==55, 'Wine', 
                                                      ifelse(class==58, 'Beer & Cider', 
                                                             ifelse(class==59, 'Beer & Cider', 
                                                                    ifelse(class==70, 'Wine', 
                                                                           ifelse(class==80, 'Beer & Cider', 
                                                                                  ifelse(class==84, 'Beer & Cider', 
                                                                                         ifelse(class==85, 'Beer & Cider', 
                                                                                                ifelse(class==86, 'Beer & Cider', 
                                                                                                       ifelse(class==87, 'Beer & Cider',
                                                                                                              ifelse(class==88, 'Beer & Cider', 
                                                                                                                     ifelse(class>=90, 'Non-Alcoholic', 'XXXXXXXXXXXXX'))))))))))))))))

print('Put in Cases for mtcfile.')
qpc = mtc$X.MQPC 
qty = mtc$X.MQTYS
code = mtc$X.MQTY.
btl = ifelse(code=='B', qty, 0)
btlCs = round(as.numeric(btl)/as.numeric(qpc), 2)
cs = ifelse(code=='C', as.numeric(qty), 0)
mtc$CASES = btlCs + cs


print('Check names.')
headTail(mtc);headTail(rct)

#################################################################################################

print('Sum inventory adjustments/dumps, returns, & total unsaleables by Supplier;
      Units are CASES derived from case + bottle using QPC.')
supplierItem = aggregate(CASES ~ PSUPPL + X.SSUNM + X.RPRD. + X.RDESC + CLASS, data=rct, FUN=sum)#inventory adjustments
supplierItem = arrange(supplierItem, CASES)
names(supplierItem) = c('SUPPLIER', 'SUPPLIER.NO', 'ITEM.NO', 'DESCRIPTION', 'CLASS', 'CASES.DUMPED.ADJUSTED') 
headTail(supplierItem)

print('Sum cases returned from mtc1 by MINP product number.')
itemReturns = aggregate(CASES ~ X.MINP., data=mtc, FUN=sum)
itemReturns = arrange(itemReturns, CASES)
names(itemReturns) = c('ITEM.NO', 'CASES.RETURNED')
headTail(itemReturns)

supplierItem = merge(supplierItem, itemReturns, by='ITEM.NO')
supplierItem$TOT.CASES.UNSALEABLE = supplierItem$CASES.DUMPED.ADJUSTED + supplierItem$CASES.RETURNED
supplierItem = arrange(supplierItem, TOT.CASES.UNSALEABLE)
print('Here is the BY ITEM moneyshot.')
headTail(supplierItem)


print('Now get info by supplier only.')
suppliers = aggregate(CASES.DUMPED.ADJUSTED ~ SUPPLIER + SUPPLIER.NO + CLASS, data=supplierItem, FUN=sum)
suppliers = arrange(suppliers, CASES.DUMPED.ADJUSTED)
headTail(suppliers)

returned = aggregate(CASES.RETURNED ~ SUPPLIER + SUPPLIER.NO, data=supplierItem, FUN=sum)
returned = arrange(returned, CASES.RETURNED)
headTail(returned)

suppliers = merge(suppliers, returned, by=c('SUPPLIER', 'SUPPLIER.NO'))
suppliers$TOT.CASES.UNSALEABLE = suppliers$CASES.DUMPED.ADJUSTED + suppliers$CASES.RETURNED
suppliers = arrange(suppliers, TOT.CASES.UNSALEABLE)
print('Here is the BY SUPPLIER moneyshot')
headTail(suppliers)

print('Check returns by customer number XMCUS.')
customers = aggregate(CASES ~ X.MCUS., data=mtc, FUN=sum)
names(customers) = c('CUSTOMER.NO', 'CASES.RETURNED')
setwd("C:/Users/pmwash/Desktop/R_files/Data Input")
cust = read.csv('active_customers_dive.csv', header=TRUE)
names(cust) = c('CUSTOMER', 'CUSTOMER.NO')
customers = merge(cust, customers, by='CUSTOMER.NO')
customers = arrange(customers, CASES.RETURNED)
headTail(customers)

print('Generate a time series of returns and inventory adjustments/dumps.')
monthReturns = aggregate(CASES ~ MONTH + X.MINP., data=mtc, FUN=sum)
names(monthReturns) = c('MONTH', 'ITEM.NO', 'CASES.RETURNED')
headTail(monthReturns)

monthAdjustments = aggregate(CASES ~ MONTH + PSUPPL + X.SSUNM + X.RPRD. + X.RDESC + CLASS, data=rct, FUN=sum)
names(monthAdjustments) = c('MONTH', 'SUPPLIER', 'SUPPLIER.NO', 'ITEM.NO', 'DESCRIPTION', 'CLASS', 'CASES.DUMPED.ADJUSTED')
headTail(monthAdjustments)

monthly = merge(monthAdjustments, monthReturns, by=c('ITEM.NO', 'MONTH'))
monthly$TOT.CASES.UNSALEABLE = monthly$CASES.DUMPED.ADJUSTED + monthly$CASES.RETURNED
headTail(monthly)

monthly = arrange(monthly, TOT.CASES.UNSALEABLE)
monthly = arrange(monthly, MONTH)
headTail(monthly)


#################################################################################################


print('Create a plot of time series for suppliers.')
g = ggplot(data=monthly, aes(x=MONTH, y=abs(TOT.CASES.UNSALEABLE)))
g + geom_boxplot(aes(group=MONTH)) +
  theme(legend.position='none') 

#################################################################################################


print('Write items and suppliers to Excel document.')
setwd("C:/Users/pmwash/Desktop/R_files/Data Output")
write.xlsx(supplierItem, file='returned_dumped_2015.xlsx', sheet='Item Summary')
write.xlsx(suppliers, file='returned_dumped_2015.xlsx', sheet='Supplier Summary', append=TRUE)
write.xlsx(customers, file='returned_dumped_2015.xlsx', sheet='Customer Returns Summary', append=TRUE)
write.xlsx(monthly, file='returned_dumped_2015.xlsx', sheet='Time Series', append=TRUE)














