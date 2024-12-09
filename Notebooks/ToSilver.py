# Databricks notebook source
#dbutils.secrets.list("AzureConnection")


# COMMAND ----------

service_credential = dbutils.secrets.get("AzureConnection","ServiceCerdential2")
directory_id = dbutils.secrets.get("AzureConnection","DirectoryID2")
application_id = dbutils.secrets.get("AzureConnection","ApplicationID2")

configs = {"fs.azure.account.auth.type": "OAuth",
          "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
          "fs.azure.account.oauth2.client.id":application_id,
          "fs.azure.account.oauth2.client.secret": service_credential,
          "fs.azure.account.oauth2.client.endpoint": f"https://login.microsoftonline.com/{directory_id}/oauth2/token"}


# COMMAND ----------

def Mounting(m_point,src,conf):
    if any(m_point in m.mountPoint for m in dbutils.fs.mounts()):
        dbutils.fs.unmount(m_point)
        print(f"Unmounted {m_point}")
    try:
        dbutils.fs.mount(
            source=src,
            mount_point=m_point,
            extra_configs=conf)
        print(f"Mounted {m_point}")
    except Exception as e:
        print(f"Error mounting {m_point}: {e}")

# COMMAND ----------

mount_point = "/mnt/bronze"
source = "abfss://bronze@riyassignadls.dfs.core.windows.net"
Mounting(mount_point,source,configs)

# COMMAND ----------

mount_point2 = "/mnt/silver"
source2 = "abfss://silver@riyassignadls.dfs.core.windows.net"
Mounting(mount_point2,source2,configs)

# COMMAND ----------

sensor_df = spark.read.format("json").option("header","true").option("inferschema","true").load("/mnt/bronze/SensorData/*.json")

# COMMAND ----------

from pyspark.sql.functions import explode, col, date_format, input_file_name, regexp_extract

sensor_id_regex = r"/(\d+)\.json$"

Transformed_sensor_df = sensor_df.select(explode("results").alias("new_results"))\
    .withColumn("sesorId", regexp_extract(input_file_name(),sensor_id_regex,1))\
    .drop("results")\
    .select(date_format(col("new_results.coverage.datetimeTo.local"),"yyyy-MM-dd").alias("DateRecorded"),\
        col("new_results.summary.avg").alias("AverageAQI"),\
        col("new_results.coverage.percentCoverage").alias("PercentageCoverage"),\
        col("sesorId"))


#display(Transformed_sensor_df)

# COMMAND ----------

#create list of sensorids

column_list = [row["sesorId"] for row in Transformed_sensor_df.select("sesorId").collect()]

# COMMAND ----------

df_sensor_list =spark.read.format("csv").option("header","true").option("inferschema","true").load("/mnt/bronze/SensorList/*.csv")
df_sensor_list.printSchema()


# COMMAND ----------

df_sensrolist_forJoin = df_sensor_list.filter(col("id").isin(column_list))
#display(df_sensrolist_forJoin)

# COMMAND ----------

final_data = Transformed_sensor_df.join(df_sensrolist_forJoin, Transformed_sensor_df.sesorId == df_sensrolist_forJoin.id,"inner")


# COMMAND ----------

#display(final_data)

# COMMAND ----------

#Transformed_Df.write.format('csv').mode("overwrite").save('/mnt/silver/data')
final_data.write.format('parquet').mode('overwrite').save('/mnt/silver/data/silverdata')