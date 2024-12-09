# AQI Data Analysis - Data Engineering Poject

## Overview
This project is focused on ETL for data of Air Qulaity of Index in canada using Azure Data Fectory Pipelinesa and Azure Data Bricks and Azure Data Lake Storage. The Goal is to transform and aggrigate data into actionable data for use of analysis.

# Architecture for data storage
> Storage Account : riyassignadls 
>> bronze
>> silver
>> gold
>> metadata

![ADF Storage Account](Linke to be come)

##Ingetion
for ingetion it uses ADF that copy data from API and Azure SQL, as it reads data from multiple endpoints to get data in bronze folder it uses meta data from which get list id from which wanted to read the data

Activities :
1. Lookup Activity [LookupSensorList] - Read data from metadata container
2. Foreach Activty [ForEachSensorList] - Itrate throuch list of `SensorId` and copy data for each `sensorId` from API
  2.1 Copy Data [APItoAdls] - Activity for Fatching Data From Each of the SensorId in List
3. Copy Data [SqlToAdls] - Copy Data From Azure SQL Database to ADLS
4. Notebook Activity [ToSilver] - Trigger Notebook from Azure Data Bricks
5. Notebook Activity [ToGold] - Trigger Notebook from Axure Data Bricks

List of sensorid From Metadata
```
SensorId,Id,LocationName,LocationId
6554967,1,Kitchener,1275795
791,2,Beaverlodge,456
24896,4,FORT ST JOHN LEARNIN,8567
```
