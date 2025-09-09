from urllib.parse import urlparse, unquote
from flask import json
import requests
import os
from app.graphql_queries.query_builders.query_builders import ImageMutationBuilder, MetafieldMutationBuilder
from app.models import Product, Shop, Variant
from app import db

SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION")

# Store credentials
STORES = {
    "shop1": {"name": os.getenv("SHOP1_NAME"), "url": os.getenv("SHOP1_URL"), "token": os.getenv("SHOP1_TOKEN")},
    "shop2": {"name": os.getenv("SHOP2_NAME"), "url": os.getenv("SHOP2_URL"), "token": os.getenv("SHOP2_TOKEN")},
    "shop3": {"name": os.getenv("SHOP3_NAME"), "url": os.getenv("SHOP3_URL"), "token": os.getenv("SHOP3_TOKEN")},
}

def shopify_headers(access_token):
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token,
    }

def shopify_request(query, shop_url, access_token, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    headers = shopify_headers(access_token=access_token)
    shopify_graphql_url = f"{shop_url}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
    response = requests.post(shopify_graphql_url, json=payload, headers=headers)
    return response

class ShopifyGIDBuilder:
    def __init__(self, object_type: str):
        self.object_type = object_type

    def build(self, object_id: str) -> str:
        return f"gid://shopify/{self.object_type}/{object_id}"

def get_normalized_name(url):
    filename = os.path.basename(urlparse(url).path)
    normalized_name = unquote(filename).replace(" ", "_20")
    return normalized_name

# Helper to resolve variant info from index
def resolve_variant_info(idx, payload, data):
    variant_info = payload[idx] if idx is not None and idx < len(payload) else {}
    variant_id = variant_info.get("ownerId", "unknown")
    variant_title = next(
        (v.get("variant_title") for v in data if v.get("variant_id") == variant_id),
        ""
    )
    return variant_id, variant_title

def fetch_single_product(query, variables, store):
    try:
        response = shopify_request(
            query=query,
            shop_url=store['url'],
            access_token=store['token'],
            variables=variables
        )
        json_data = response.json()
        if "errors" in json_data:
            return {"errors": json_data["errors"]}
        
        product_data = json_data.get("data", {}).get("product")
        product = ShopifyProductBuilder(product_data, store)
        return product

    except Exception as e:
        return {"errors": [f"Request or JSON parsing error: {e}"]}

class ShopifyProductBuilder:
    def __init__(self, product_data, store):
        self.product_data = product_data
        self.errors = []
        self.store = store
        self.product_id = self.product_data['id']
        self._check_errors()

    def _check_errors(self):
        variants = self.get_variants()
        all_variant_image_count = 0
        
        for idx, variant in enumerate(variants, start=1):
            title = variant.get("variant_title") or f"Variant {idx}"
            assets = variant.get("asset_images_json") or []
            urls = variant.get("raw_image_urls") or []
            count_assets, count_urls = len(assets), len(urls)
            all_variant_image_count += count_urls

            # Case 1: Both empty
            if count_assets == 0 and count_urls == 0:
                self.errors.append(
                    f"❌ {title} has neither asset images nor image URLs."
                )
                continue  # skip other checks

            # Case 2: Only asset images missing
            if count_assets == 0 and count_urls > 0:
                self.errors.append(
                    f"⚠️ {title} has {count_urls} image URLs but no asset images."
                )
                continue

            # Case 3: Only image URLs missing
            if count_urls == 0 and count_assets > 0:
                self.errors.append(
                    f"⚠️ {title} has {count_assets} asset images but no image URLs."
                )
                continue

            # Case 4: Mismatch counts (both > 0 but unequal)
            if count_assets != count_urls:
                self.errors.append(
                    f"⚠️ {title} has {count_assets} asset images but {count_urls} image URLs."
                )

    def get_title(self):
        return self.product_data.get("title") if self.product_data else None

    def get_preview_url(self):
        return self.product_data.get("onlineStorePreviewUrl") if self.product_data else None

    def get_media_count(self):
        if not self.product_data:
            return False
        count = self.product_data.get("mediaCount", {}).get("count")
        return count

    def get_variant_count(self):
        if not self.product_data:
            return False
        count = self.product_data.get("variantsCount", {}).get("count")
        return count

    def get_media(self):
        if not self.product_data:
            return []

        media_nodes = self.product_data.get("media", {}).get("nodes", [])
        formatted = []

        for node in media_nodes:
            media_id = node.get("id")
            img_url = node.get("image", {}).get("url")
            assumed_name = get_normalized_name(img_url)
            formatted.append({"id": media_id, "img_url": img_url, "name": assumed_name})
        return formatted

    def get_id_from_image_url(self, url):
        for media in self.get_media():
            if media.get("name") == get_normalized_name(url):
                return media.get("id")
        
        # build GraphQL query
        image_builder = ImageMutationBuilder()
        query = image_builder.build()

        # prepare input for Shopify
        files_input = [
            {
                "contentType": "IMAGE",
                "originalSource": url
            }
        ]

        try:
            response = shopify_request(
                query=query,
                shop_url=self.store['url'],
                access_token=self.store['token'],
                variables={"files": files_input}
            )
            json_data = response.json()

            file_create = json_data.get("data", {}).get("fileCreate", {})
            returned_files = file_create.get("files", [])
            user_errors = file_create.get("userErrors", [])

            # map success back to images
            for f in returned_files:
                return f["id"]

        except Exception as e:
            return None

    def get_variants(self):
        if not self.product_data:
            return []

        variants = self.product_data.get("variants", {}).get("nodes", [])

        variant_data = []
        for variant in variants:
            raw_image_urls = []
            image_urls = (variant.get("imagesUrl") or {}).get("jsonValue", [])
            asset_images_json = (variant.get("assetImagesJson") or {}).get("jsonValue", [])
            raw_asset_images = variant.get("assetImages") or []
            nodes = []

            if isinstance(raw_asset_images, dict):
                nodes = (
                    raw_asset_images.get("images") or {}
                ).get("nodes", [])

            asset_images = []
            for node in nodes:
                media_id = node.get("id")
                img_url = node.get("image", {}).get("url")
                if media_id and img_url:
                    asset_images.append({
                        "id": media_id,
                        "image_url": img_url
                    })

            # Ensure it's a list
            if isinstance(image_urls, list):
                for url in image_urls:
                    raw_image_urls.append({"url": url, "name": get_normalized_name(url)})

            variant_data.append({
                "variant_title": variant.get("title"),
                "variant_id": variant.get("id"),
                "raw_image_urls": raw_image_urls,
                "asset_images": asset_images,
                "asset_images_json": asset_images_json,
                "images_count": len(raw_image_urls),
                # "all_data": variant,
                "filled_images": bool(asset_images_json)
            })

        return variant_data

    def is_filled_images(self):
        variants = self.get_variants()
        if not variants:
            return False

        for variant in variants:
            if variant.get("filled_images"):
                return True
        return False

    def get_total_variant_images_count(self):
        variants = self.get_variants()
        if not variants:
            return False

        total = 0
        for variant in variants:
            total += variant.get("images_count", 0)
        return total
    
    def details(self):
        return {
            "title": self.get_title(),
            "preview_url": self.get_preview_url(),
            "media_count": self.get_media_count(),
            "variant_count": self.get_variant_count(),
            "media": self.get_media(),
            "total_variant_images_count": self.get_total_variant_images_count(),
            "variants": self.get_variants(),
            "is_filled_images": self.is_filled_images(),
            "has_errors": self.has_errors(),
            "errors": self.get_errors(),
            "id": self.product_id,
            "store_name": self.store['name'],
            "featured_image": self.get_featured_image()
        }
    
    def get_featured_image(self):
        if not self.product_data:
            return False
        media = self.product_data.get("featuredMedia")
        if not media:
            return False
        return media['image']['url']
    
    def has_errors(self):
        return len(self.errors) > 0

    def save_product_with_variants(self):
        """
        Save or update product with its variants.
        Handles:
        - Creating shop if missing
        - Creating product if missing
        - Creating/updating variants
        - Only commits if there are changes
        - Flushes to ensure product.id exists for variants
        """

        anything_changed = False  # Track if we need to commit

        try:
            # --- 1. Get or create shop ---
            shop_domain = self.store['url']
            shop_name = self.store['name']

            with db.session.no_autoflush:
                shop = Shop.query.filter_by(domain=shop_domain).first()
                if not shop:
                    shop = Shop(domain=shop_domain, name=shop_name)
                    db.session.add(shop)
                    anything_changed = True
                    print(f"[DB] Created new shop: {shop_name}")

            # --- 2. Get or create product ---
            with db.session.no_autoflush:
                product = Product.query.filter_by(shopify_id=self.product_id).first()
                if not product:
                    product = Product(
                        shop_id=shop.id,
                        title=self.get_title(),
                        shopify_id=self.product_id
                    )
                    db.session.add(product)
                    anything_changed = True
                    print(f"[DB] Created new product: {self.get_title()}")

            # Flush here to ensure product.id exists for variants (FK)
            if anything_changed:
                db.session.flush()

            # --- 3. Process variants ---
            for variant_info in self.get_variants():
                with db.session.no_autoflush:
                    variant = Variant.query.filter_by(shopify_id=variant_info['variant_id']).first()

                incoming_urls = variant_info.get('raw_image_urls') or []
                asset_images_json = variant_info.get('asset_images_json') or []

                if not variant:
                    # New variant
                    variant = Variant(
                        product_id=product.id,
                        shopify_id=variant_info['variant_id'],
                        urls=incoming_urls
                    )
                    db.session.add(variant)
                    anything_changed = True
                    print(f"[DB] Created new variant ID: {variant_info['variant_id']}")

                    # Call your upload functions here (metafields etc.)
                    try:
                        data_to_upload = self.data_for_put_into_metafield()
                        if data_to_upload.get("results"):
                            if data_to_upload.get("unmatched_count", 0) > 0:
                                self.create_not_found_images_1(data_to_upload["results"], parent_dict=data_to_upload)
                            self.put_images_into_metafield(data_to_upload["results"], delete_existing=False)
                    except Exception as e:
                        print(f"[Shopify] Error during upload for variant {variant_info['variant_id']}: {e}")

                else:
                    # Existing variant, check for changes
                    existing_urls = variant.urls or []
                    changes, removed = [], []

                    # Compare incoming URLs with existing
                    for idx, url in enumerate(incoming_urls):
                        if idx >= len(existing_urls) or existing_urls[idx] != url:
                            changes.append((idx, existing_urls[idx] if idx < len(existing_urls) else None, url))

                    for idx in range(len(incoming_urls), len(existing_urls)):
                        removed.append((idx, existing_urls[idx]))

                    if changes or removed:
                        # Apply changes/removals
                        variant.urls = incoming_urls
                        db.session.add(variant)
                        anything_changed = True

                        # Push updates to Shopify
                        try:
                            metafields_payload = [{
                                "ownerId": variant_info['variant_id'],
                                "namespace": "custom",
                                "key": "variant_images",
                                "type": "list.file_reference",
                                "value": json.dumps(asset_images_json)
                            }]
                            response = shopify_request(
                                query=MetafieldMutationBuilder().build(),
                                shop_url=self.store['url'],
                                access_token=self.store['token'],
                                variables={"metafields": metafields_payload}
                            )
                            print(f"[Shopify] Updated variant {variant_info['variant_id']} with {asset_images_json}")
                            print("[Shopify] Response:", response.json())
                        except Exception as e:
                            print(f"[Shopify] Error updating variant {variant_info['variant_id']}: {e}")

            # --- 4. Commit only if something changed ---
            if anything_changed:
                db.session.commit()
                print("[DB] All changes committed.")
            else:
                print("[DB] No changes detected, skipping commit.")

        except Exception as e:
            db.session.rollback()
            print(f"[DB] Error during save_product_with_variants: {e}")
            raise

    def get_errors(self):
        return self.errors

    def data_for_put_into_metafield(self):
        product_image_cache = {}
        for img in self.get_media():
            url = img.get("img_url")
            name = img.get("name")
            product_image_cache[name] = {
                "id": img.get("id"),
                "img_url": url
            }

        results = []
        unmatched_count = 0

        # Match variant images
        for var in self.get_variants():
            variant_id = var.get("variant_id")
            variant_title = var.get("variant_title")
            data_images = []

            for img in var.get("raw_image_urls", []):
                old_url = img.get("url")
                normalized_old_name = img.get("name")
                match = product_image_cache.get(normalized_old_name)

                matched = bool(match)
                needs_upload = not matched
                if needs_upload:
                    unmatched_count += 1

                data_images.append({
                    "raw_img_url": old_url,
                    "product_img_url": match.get("img_url") if matched else "",
                    "product_img_id": match.get("id") if matched else "",
                    "matched": matched,
                    "needs_upload": needs_upload
                })

            results.append({
                "variant_id": variant_id,
                "variant_title": variant_title,
                "data_images": data_images
            })

        return {
            "results": results,
            "unmatched_count": unmatched_count
        }

    def create_not_found_images_1(self, data: list, parent_dict: dict = None):
        summary = {
            "attempted_to_upload": 0,
            "successfully_uploaded": 0,
            "failed_uploads": 0,
            "failed_images": []
        }

        # collect all images that need upload
        upload_candidates = []
        for variant in data:
            for idx, img in enumerate(variant.get("data_images", [])):
                if img.get("needs_upload"):
                    raw_url = img.get("raw_img_url")
                    summary["attempted_to_upload"] += 1

                    if not raw_url:
                        summary["failed_uploads"] += 1
                        summary["failed_images"].append({
                            "variant_id": variant.get("variant_id"),
                            "raw_url": raw_url,
                            "error": "Missing raw_url"
                        })
                        continue

                    # build identifier for mapping later using normalized name
                    normalized = get_normalized_name(raw_url)
                    alt_key = f"{normalized}_{idx}"

                    upload_candidates.append({
                        "alt": alt_key,
                        "contentType": "IMAGE",
                        "originalSource": raw_url,
                        "variant_id": variant.get("variant_id"),
                        "image_ref": img
                    })

        if not upload_candidates:
            if parent_dict is not None:
                parent_dict["image_creation_summary"] = summary
            return

        # build GraphQL query
        image_builder = ImageMutationBuilder()
        query = image_builder.build()

        # prepare input for Shopify
        files_input = [
            {
                "alt": candidate["alt"],
                "contentType": "IMAGE",
                "originalSource": candidate["originalSource"]
            }
            for candidate in upload_candidates
        ]

        try:
            response = shopify_request(
                query=query,
                shop_url=self.store['url'],
                access_token=self.store['token'],
                variables={"files": files_input}
            )
            json_data = response.json()

            file_create = json_data.get("data", {}).get("fileCreate", {})
            returned_files = file_create.get("files", [])
            user_errors = file_create.get("userErrors", [])

            # map success back to images
            for f in returned_files:
                alt_key = f.get("alt")
                candidate = next((c for c in upload_candidates if c["alt"] == alt_key), None)
                if not candidate:
                    continue
                img = candidate["image_ref"]
                img["product_img_id"] = f["id"]
                img["needs_upload"] = False
                img["matched"] = True
                summary["successfully_uploaded"] += 1

            # map failures from userErrors
            for err in user_errors:
                summary["failed_uploads"] += 1
                summary["failed_images"].append({
                    "error": err.get("message"),
                    "field": err.get("field"),
                    "code": err.get("code")
                })

            # handle unexpected missing files
            if not returned_files and not user_errors:
                summary["failed_uploads"] += len(upload_candidates)
                for c in upload_candidates:
                    summary["failed_images"].append({
                        "variant_id": c["variant_id"],
                        "raw_url": c["originalSource"],
                        "error": "No file returned from Shopify"
                    })

        except Exception as e:
            # global failure
            summary["failed_uploads"] += len(upload_candidates)
            for c in upload_candidates:
                summary["failed_images"].append({
                    "variant_id": c["variant_id"],
                    "raw_url": c["originalSource"],
                    "error": str(e)
                })

        # attach summary to parent dict if provided
        if parent_dict is not None:
            parent_dict["image_creation_summary"] = summary

        print('\n\n', summary, '\n\n')

    def create_not_found_images(self, data: list, parent_dict: dict = None):
        summary = {
            "attempted_to_upload": 0,
            "successfully_uploaded": 0,
            "failed_uploads": 0,
            "failed_images": []
        }

        # collect all images that need upload
        upload_candidates = []
        for variant in data:
            for idx, img in enumerate(variant.get("data_images", [])):
                if img.get("needs_upload"):
                    raw_url = img.get("raw_img_url")
                    summary["attempted_to_upload"] += 1

                    if not raw_url:
                        summary["failed_uploads"] += 1
                        summary["failed_images"].append({
                            "variant_id": variant.get("variant_id"),
                            "raw_url": raw_url,
                            "error": "Missing raw_url"
                        })
                        continue

                    # build identifier for mapping later using normalized name
                    normalized = get_normalized_name(raw_url)
                    alt_key = f"{normalized}_{idx}"

                    upload_candidates.append({
                        "alt": alt_key,
                        "contentType": "IMAGE",
                        "originalSource": raw_url,
                        "variant_id": variant.get("variant_id"),
                        "image_ref": img
                    })

        if not upload_candidates:
            if parent_dict is not None:
                parent_dict["image_creation_summary"] = summary
            return

        # build GraphQL query
        image_builder = ImageMutationBuilder()
        query = image_builder.build()

        # prepare input for Shopify
        files_input = [
            {
                "alt": candidate["alt"],
                "contentType": "IMAGE",
                "originalSource": candidate["originalSource"]
            }
            for candidate in upload_candidates
        ]

        try:
            response = shopify_request(
                query=query,
                shop_url=self.store['url'],
                access_token=self.store['token'],
                variables={"files": files_input}
            )
            json_data = response.json()

            file_create = json_data.get("data", {}).get("fileCreate", {})
            returned_files = file_create.get("files", [])
            user_errors = file_create.get("userErrors", [])

            # map success back to images
            for f in returned_files:
                alt_key = f.get("alt")
                candidate = next((c for c in upload_candidates if c["alt"] == alt_key), None)
                if not candidate:
                    continue
                img = candidate["image_ref"]
                img["product_img_id"] = f["id"]
                img["needs_upload"] = False
                img["matched"] = True
                summary["successfully_uploaded"] += 1

            # map failures from userErrors
            for err in user_errors:
                summary["failed_uploads"] += 1
                summary["failed_images"].append({
                    "error": err.get("message"),
                    "field": err.get("field"),
                    "code": err.get("code")
                })

            # handle unexpected missing files
            if not returned_files and not user_errors:
                summary["failed_uploads"] += len(upload_candidates)
                for c in upload_candidates:
                    summary["failed_images"].append({
                        "variant_id": c["variant_id"],
                        "raw_url": c["originalSource"],
                        "error": "No file returned from Shopify"
                    })

        except Exception as e:
            # global failure
            summary["failed_uploads"] += len(upload_candidates)
            for c in upload_candidates:
                summary["failed_images"].append({
                    "variant_id": c["variant_id"],
                    "raw_url": c["originalSource"],
                    "error": str(e)
                })

        # attach summary to parent dict if provided
        if parent_dict is not None:
            parent_dict["image_creation_summary"] = summary

    def put_images_into_metafield(self, data, delete_existing=False):
        summary = {
            "success": [],
            "skipped": [],
            "errors": []
        }

        metafields_payload = []

        # Loop over variants and build payload
        for variant in data:
            variant_id = variant.get("variant_id")
            variant_title = variant.get("variant_title", "")
            data_images = variant.get("data_images", [])

            if delete_existing:
                image_ids = []
            else:
                image_ids = [
                    img.get("product_img_id") for img in data_images if img.get("product_img_id")
                ]

                if not image_ids:
                    summary["skipped"].append({
                        "variant_id": variant_id,
                        "variant_title": variant_title,
                        "reason": "No valid image IDs found to populate."
                    })
                    continue


            metafields_payload.append({
                "ownerId": variant_id,
                "namespace": "custom",
                "key": "variant_images",
                "type": "list.file_reference",
                "value": json.dumps(image_ids)
            })
        
        # If there's nothing to send
        if not metafields_payload:
            return summary

        variables = {
            "metafields": metafields_payload
        }

        # Send request once
        try:
            builder = MetafieldMutationBuilder()
            query = builder.build()
            response = shopify_request(
                query=query,
                shop_url=self.store['url'],
                access_token=self.store['token'],
                variables=variables
            )
            json_data = response.json()

            # 1. Top-level GraphQL errors
            if "errors" in json_data:
                for idx, graphql_error in enumerate(json_data["errors"]):
                    variant_id, variant_title = resolve_variant_info(idx, metafields_payload, data)
                    summary["errors"].append({
                        "variant_id": variant_id,
                        "variant_title": variant_title,
                        "graphql_error": graphql_error
                    })
                return summary

            metafields_set = json_data.get("data", {}).get("metafieldsSet", {})
            user_errors = metafields_set.get("userErrors", [])
            metafields = metafields_set.get("metafields", [])

            # 2. Process user errors
            for err in user_errors:
                field_path = err.get("field", [])
                idx = None
                try:
                    idx = int(field_path[1])
                except (IndexError, ValueError, TypeError):
                    pass

                variant_id, variant_title = resolve_variant_info(idx, metafields_payload, data)
                summary["errors"].append({
                    "variant_id": variant_id,
                    "variant_title": variant_title,
                    "user_error": err
                })

            # 3. Process successes
            for idx, mf in enumerate(metafields):
                metafield_id = mf.get("id")
                
                # Fall back to index-based mapping since response lacks ownerId
                variant = data[idx] if idx < len(data) else {}

                variant_id = variant.get("variant_id")
                variant_title = variant.get("variant_title", "")
                image_count = len([
                    img for img in variant.get("data_images", [])
                    if img.get("product_img_id")
                ])

                summary["success"].append({
                    "variant_id": variant_id,
                    "variant_title": variant_title,
                    "image_count": image_count,
                    "metafield_id": metafield_id
                })

        except Exception as e:
            summary["errors"].append({
                "type": "exception",
                "message": str(e)
            })

        print('\n\n', summary, '\n\n')

        return summary

    def populate_images(self):
        return "doing nothing for now"

    def delete_asset_images_from_metafield(self):
        data = []
        for var in self.get_variants():
            variant_id = var.get("variant_id")
            variant_title = var.get("variant_title")
            data_images = []
            data.append({
                "variant_id": variant_id,
                "variant_title": variant_title,
                "data_images": data_images
            })

        return self.put_images_into_metafield(data, delete_existing=True)
