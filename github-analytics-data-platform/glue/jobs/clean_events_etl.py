import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType, LongType

args = getResolvedOptions(sys.argv, [
    "JOB_NAME",
    "SOURCE_S3_PATH",
    "TARGET_S3_PATH",
    "GLUE_DATABASE"
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

source_path = args["SOURCE_S3_PATH"]
target_path = args["TARGET_S3_PATH"]
glue_db = args["GLUE_DATABASE"]

# Read raw NDJSON (gz) - Spark auto decompresses .gz
df = spark.read.json(source_path)

# Select & flatten common fields (schema may vary over time)
df_flat = (
    df.select(
        F.col("id").cast(StringType()).alias("event_id"),
        F.col("type").cast(StringType()).alias("event_type"),
        F.col("actor.id").cast(LongType()).alias("actor_id"),
        F.col("actor.login").cast(StringType()).alias("actor_login"),
        F.col("repo.id").cast(LongType()).alias("repo_id"),
        F.col("repo.name").cast(StringType()).alias("repo_name"),
        F.col("org.login").cast(StringType()).alias("org_login"),
        F.to_timestamp("created_at").cast(TimestampType()).alias("created_at"),
        F.col("payload.action").cast(StringType()).alias("payload_action"),
    )
    .withColumn("event_date", F.to_date("created_at"))
    .withColumn("event_hour", F.hour("created_at"))
)

# Write to Parquet, partitioned by date/hour
(
    df_flat
    .repartition(1)  # demo-friendly; adjust for scale
    .write
    .mode("overwrite")
    .partitionBy("event_date", "event_hour")
    .format("parquet")
    .option("compression", "snappy")
    .save(target_path)
)

job.commit()
