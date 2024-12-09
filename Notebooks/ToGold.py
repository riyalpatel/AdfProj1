# Databricks notebook source
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

mount_point = "/mnt/silver"
source = "abfss://silver@riyassignadls.dfs.core.windows.net"
Mounting(mount_point,source,configs)

# COMMAND ----------

silver_df = spark.read.parquet("/mnt/silver/data/silverdata/*.parquet")

# transformed_df = silver_df.withColumn("AverageAQI").isNull((col("AverageAQI")+col("AverageAQI"))/2)

# COMMAND ----------

# MAGIC %md
# MAGIC - if AverageAQI 0 DROP
# MAGIC - if CoveragePercentage is Below 90 Drop
# MAGIC - if AverageAQI < 50 it's healthy air
# MAGIC - if AverageAQI > 50 it's unhealthy air 
# MAGIC

# COMMAND ----------

from pyspark.sql.functions import when, max, min, avg, col, format_number, round

def MapQuality(aqi_col):
    return when(aqi_col <= 50, "Good") \
        .when((aqi_col > 50) & (aqi_col <= 100), "Moderate") \
        .when((aqi_col > 100) & (aqi_col <= 150), "Unhealthy for Sensitive Groups") \
        .when((aqi_col > 150) & (aqi_col <= 200), "Unhealthy") \
        .when((aqi_col > 200) & (aqi_col <= 300), "Very Unhealthy") \
        .otherwise("Hazardous")

# def format_number(num):
    # num = num.cast(float)
    # return "round({num}, 2)".format(col("{num}"))

# COMMAND ----------

transformed_df = silver_df.filter( (col("AverageAQI")!=0 ) & (col("PercentageCoverage")>90) )\
    .withColumn("id",col("id").alias("sesorId"))\
    .withColumn("AirQuality", MapQuality(col("AverageAQI")))\
   .withColumn("AverageAQI", round(col("AverageAQI"), 2))\
    .drop("name")
display(transformed_df)

# COMMAND ----------

result = transformed_df.groupBy("sesorId").agg(max("AverageAQI").alias("MaxValue")\
    , min("AverageAQI").alias("MinValue")\
    , avg("AverageAQI").alias("AvgValue"))\
    .withColumn("AvgValue", round(col("AvgValue"), 2))

display(result)

# COMMAND ----------

# Alias the DataFrames to avoid ambiguity
transformed_df_alias = transformed_df.alias("transformed")
result_alias = result.alias("result")

max_date = transformed_df_alias.join(
    result_alias,
    (transformed_df_alias["sesorId"] == result_alias["sesorId"]) & 
    (transformed_df_alias["AverageAQI"] == result_alias["MaxValue"])
).select(
    transformed_df_alias["sesorId"].alias("sesorId"),
    transformed_df_alias["DateRecorded"].alias("MaxValueDate")
)

min_date = transformed_df_alias.join(
    result_alias,
    (transformed_df_alias["sesorId"] == result_alias["sesorId"]) & 
    (transformed_df_alias["AverageAQI"] == result_alias["MinValue"])
).select(
    transformed_df_alias["sesorId"].alias("sesorId"),
    transformed_df_alias["DateRecorded"].alias("MinValueDate")
)

final_result = result_alias.join(max_date, on="sesorId", how="left") \
                           .join(min_date, on="sesorId", how="left")

display(final_result)


# COMMAND ----------

#trasformation
display(transformed_df)

# COMMAND ----------

mount_point2 = "/mnt/gold"
source2 = "abfss://gold@riyassignadls.dfs.core.windows.net"
Mounting(mount_point2,source2,configs)

# COMMAND ----------

# Transformed_Df.write.format('csv').mode("overwrite").save('/mnt/gold/data')
transformed_df.write.format('parquet').mode("overwrite").save('/mnt/gold/data/maindata.parquet')
transformed_df.write.format('parquet').mode("overwrite").save('/mnt/gold/data/aggdata.parquet')

# COMMAND ----------

