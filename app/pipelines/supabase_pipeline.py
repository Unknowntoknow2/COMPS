import os, json, hmac, hashlib
import boto3
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# Configuration
POSTGRES_DSN = os.getenv("POSTGRES_DSN")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
ANON_HMAC_SECRET = os.getenv("ANON_HMAC_SECRET", "default-key")

def hmac_hash(value: str) -> str:
    return hmac.new(ANON_HMAC_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()

class SupabasePipeline:
    def open_spider(self, spider):
        self.conn = psycopg2.connect(POSTGRES_DSN)
        self.cur = self.conn.cursor()
        self.s3 = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )

    def close_spider(self, spider):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        item = dict(item)
        now = datetime.utcnow().isoformat() + "Z"
        item["exported_at"] = now

        # Anonymize sensitive fields
        if "email" in item:
            item["email_hash"] = hmac_hash(item["email"])
            item.pop("email")
        if "phone" in item:
            item["phone_hash"] = hmac_hash(item["phone"])
            item.pop("phone")

        # Upload images (if any)
        uploaded = []
        for url in item.get("images", []):
            try:
                fname = os.path.basename(urlparse(url).path)
                key = f"craigslist/{fname}"
                self.s3.upload_file(url, S3_BUCKET, key)
                uploaded.append(f"https://{S3_ENDPOINT_URL}/{S3_BUCKET}/{key}")
            except Exception as e:
                spider.logger.warning(f"Image upload failed: {e}")
        item["images"] = uploaded

        # Insert into Postgres
        self.cur.execute(
            """
            INSERT INTO craigslist_listings (craigslist_id, source_city, category, title,
            price_cents, currency, posted_at, url, description, latitude, longitude,
            postal_code, neighborhood, seller_type, attributes, images, exported_at)
            VALUES (%(craigslist_id)s, %(source_city)s, %(category)s, %(title)s,
            %(price_cents)s, %(currency)s, %(posted_at)s, %(url)s, %(description)s,
            %(latitude)s, %(longitude)s, %(postal_code)s, %(neighborhood)s,
            %(seller_type)s, %(attributes)s, %(images)s, %(exported_at)s)
            ON CONFLICT (craigslist_id) DO UPDATE SET
            price_cents = EXCLUDED.price_cents,
            description = EXCLUDED.description,
            images = EXCLUDED.images,
            exported_at = EXCLUDED.exported_at;
            """,
            item,
        )

        self.conn.commit()
        return item
