import requests
import os
from app.queries.shopify_graphql_queries import QUERIES

ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP_URL = os.getenv("SHOPIFY_STORE_URL")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION")
SHOPIFY_GRAPHQL_URL = f"{SHOP_URL}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

def shopify_headers():
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN,
    }

def graphql_request(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(SHOPIFY_GRAPHQL_URL, json=payload, headers=shopify_headers())
    return response.json()

class ShopifyGIDBuilder:
    def __init__(self, object_type: str):
        self.object_type = object_type

    def build(self, object_id: str) -> str:
        return f"gid://shopify/{self.object_type}/{object_id}"
    
def transform_filename(url):
    return url.split("/")[-1].replace("%20", "_20")

def create_media_from_url(originalSource_url):
    try:
        result = graphql_request(QUERIES["file_create"], {"originalSource": originalSource_url})
        file_data = result.get("data", {}).get("fileCreate", {})

        user_errors = file_data.get("userErrors", [])
        if user_errors:
            print(f"[WARN] fileCreate userErrors for {originalSource_url}: {user_errors}")
            return None

        files = file_data.get("files", [])
        if not files:
            print(f"[WARN] No files returned from fileCreate for {originalSource_url}")
            return None

        created_file = files[0]
        return {
            "id": created_file.get("id"),
            "fileStatus": created_file.get("fileStatus")
            # No URL is returned here, we cannot guess it
        }

    except Exception as e:
        print(f"[ERROR] Exception while creating media for {originalSource_url}: {e}")
        return None
