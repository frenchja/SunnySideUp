#!/usr/bin/env Rscript
# R script to convert and sanitize LA energy consumption data
# for SQL table on consumption.

library(psych)
library(stringr)

la.data <- read.csv(file='~/Downloads/Average_monthly_residential_energy_usage_By_zip_code.csv',
                    header=TRUE)
tmp <- str_split_fixed(la.data$Location.1, "\n", 2)
tmp[,2] <- gsub(pattern="\\(", replacement="",x=tmp[,2])
tmp[,2] <- gsub(pattern="\\)", replacement="",x=tmp[,2])
data <- data.frame(zip=tmp[,1])
tmp_lat <- str_split_fixed(tmp[,2], ",", 2)
data$lat <- tmp_lat[,1]
data$lng <- tmp_lat[,2]
data$kwh_month <- rowMeans(la.data[,c(1:8)],na.rm=TRUE)
data$kwh_day <- data$kwh_month*0.0328549112
write.csv(data,file='~/Documents/m2b/energy.csv',row.names=FALSE)