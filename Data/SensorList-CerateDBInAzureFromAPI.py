# Databricks notebook source
#Access/Read File
file_location = "/FileStore/tables/son"

df = spark.read.option("multiline", True) \
  .json(file_location)

display(df)

# COMMAND ----------

#Imports

from pyspark.sql.functions import from_json, col,explode,posexplode
from pyspark.sql.types import StructType, StructField, StringType


# COMMAND ----------

# MAGIC %md
# MAGIC RULE IF I WANT TO FLATTERM THE JSON FILE
# MAGIC
# MAGIC
# MAGIC 0. DON'T GET EXCITED
# MAGIC 1. NOTE ALL COLUMN YOU WANT
# MAGIC 2. NOTE EVERY ARRAY YOU WANT TO EXPLODE FROM SCHEMA USING : withColumn('aliasName',explode('structurename.arrayname'))
# MAGIC 3. SELECT EVERYTHING YOU WANT BY USING THE NOTES FROM POINT 1.
# MAGIC 4. CELEBRATE 
# MAGIC
# MAGIC

# COMMAND ----------



# COMMAND ----------

temp_df = df.withColumn("results",explode('results'))\
            .select("results.")

display(temp_df)

# COMMAND ----------

#flattning JSON File

new_df = df.withColumn("new_results",explode('results'))\
    .withColumn('sensor', explode('new_results.sensors'))\
    .select('*','new_results.coordinates.latitude','new_results.coordinates.longitude','sensor.id','sensor.name')\
    .drop('meta').drop('results').drop('new_results').drop('sensor')
display(new_df)

# COMMAND ----------

new_df

# COMMAND ----------

jdbc_url = "jdbc:sqlserver://riyaldbsrvr.database.windows.net:1433;database=dbAssignment1" # JDBC url 
table_name = "CanadaSensors"
connection_properties = {
    "user": "username@dbserver", # db User name
    "password": "password@123", # db Password
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

# COMMAND ----------

new_df.write.jdbc(url=jdbc_url, table=table_name, mode="overwrite", properties=connection_properties)

# COMMAND ----------


