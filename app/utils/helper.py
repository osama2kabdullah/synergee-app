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
        anything_changed = False

        # Defensive: ensure required attributes exist
        try:
            store = getattr(self, "store", None)
            if not store or not isinstance(store, dict):
                print("[DB] Invalid store info on self.store")
                return False

            shop_domain = store.get("url")
            shop_name = store.get("name")
            if not shop_domain:
                print("[DB] store['url'] (shop domain) is missing")
                return False

            if not hasattr(self, "product_id") or not self.product_id:
                print("[DB] Missing self.product_id")
                return False
        except Exception as e:
            print(f"[DB] Pre-check failure: {e}")
            return False

        try:
            # --- 1. Get or create shop ---
            shop = None
            shop = Shop.query.filter_by(domain=shop_domain).first()
            if not shop:
                shop = Shop(domain=shop_domain, name=shop_name)
                db.session.add(shop)
                # flush immediately so shop.id is available
                try:
                    db.session.flush()
                except Exception as fe:
                    # If flush fails, rollback and abort safely
                    db.session.rollback()
                    print(f"[DB] Failed to flush new Shop: {fe}")
                    return False
                anything_changed = True
                print(f"[DB] Created new shop: {shop_name}")

            # --- 2. Get or create product ---
            product = Product.query.filter_by(shopify_id=self.product_id).first()
            if not product:
                # Ensure shop.id exists (it should after the flush above)
                if not getattr(shop, "id", None):
                    # try flush again defensively
                    try:
                        db.session.flush()
                    except Exception as fe:
                        db.session.rollback()
                        print(f"[DB] Failed to flush before creating Product: {fe}")
                        return False

                # create product; use shop_id directly to avoid model-relationship assumptions
                product = Product(
                    shop_id=shop.id,
                    title=self.get_title() if callable(getattr(self, "get_title", None)) else None,
                    shopify_id=self.product_id
                )
                db.session.add(product)
                # flush to ensure product.id exists for variants
                try:
                    db.session.flush()
                except Exception as fe:
                    db.session.rollback()
                    print(f"[DB] Failed to flush new Product: {fe}")
                    return False
                anything_changed = True
                print(f"[DB] Created new product: {product.title}")

            # --- 3. Process variants ---
            variants_iterable = []
            try:
                variants_iterable = list(self.get_variants() or [])
            except Exception:
                print("[DB] self.get_variants() failed or returned bad data; treating as empty list")
                variants_iterable = []

            for variant_info in variants_iterable:
                # Defensive extraction of expected fields
                try:
                    variant_id = variant_info.get("variant_id")
                    incoming_urls = variant_info.get("raw_image_urls") or []
                    asset_images_json = variant_info.get("asset_images_json") or []
                except Exception:
                    print("[DB] bad variant_info structure, skipping this variant:", variant_info)
                    continue

                if not variant_id:
                    print("[DB] variant_info missing variant_id, skipping:", variant_info)
                    continue

                # isolate per-variant work to avoid a single failure bringing everything down
                try:
                    variant = Variant.query.filter_by(shopify_id=variant_id).first()

                    if not variant:
                        # New variant
                        variant = Variant(
                            product_id=product.id,
                            shopify_id=variant_id,
                            urls=incoming_urls
                        )
                        db.session.add(variant)
                        anything_changed = True
                        # flush to persist the variant id if other logic later depends on it
                        try:
                            db.session.flush()
                        except Exception as fe:
                            # record and continue; variant may not have id but we still marked change
                            db.session.rollback()
                            print(f"[DB] flush failed after adding variant {variant_id}: {fe}")
                            # re-add and attempt to continue to next variant
                            db.session.add(variant)
                            continue

                        print(f"[DB] Created new variant ID: {variant_id}")

                        # After creating variant, perform uploads/metafields if needed.
                        # Wrap Shopify operations to prevent external errors causing crashes.
                        try:
                            data_to_upload = {}
                            if callable(getattr(self, "data_for_put_into_metafield", None)):
                                data_to_upload = self.data_for_put_into_metafield()
                            if isinstance(data_to_upload, dict) and data_to_upload.get("results"):
                                if data_to_upload.get("unmatched_count", 0) > 0 and callable(getattr(self, "create_not_found_images", None)):
                                    try:
                                        self.create_not_found_images(data_to_upload["results"], parent_dict=data_to_upload)
                                    except Exception as e:
                                        print(f"[Shopify] create_not_found_images failed for variant {variant_id}: {e}")

                                if callable(getattr(self, "put_images_into_metafield", None)):
                                    try:
                                        self.put_images_into_metafield(data_to_upload["results"], delete_existing=False)
                                    except Exception as e:
                                        print(f"[Shopify] put_images_into_metafield failed for variant {variant_id}: {e}")
                        except Exception as e:
                            print(f"[Shopify] Error preparing uploads for new variant {variant_id}: {e}")

                    else:
                        # --- Existing variant: check for changes ---
                        # Load existing urls from DB (JSON string)
                        existing_urls = []

                        if variant.urls:
                            try:
                                if isinstance(variant.urls, str):
                                    parsed = json.loads(variant.urls)
                                else:
                                    parsed = variant.urls  # already a list/dict

                                # Normalize: keep only string URLs
                                existing_urls = [
                                    u["url"] if isinstance(u, dict) else u
                                    for u in parsed
                                ]
                            except Exception as e:
                                print(f"[DB] Failed to parse variant.urls for {variant.id}: {e}")
                                existing_urls = []
                                continue

                        # Normalize incoming urls (raw_image_urls may be dicts or strings)
                        incoming_urls = [
                            u["url"] if isinstance(u, dict) else u
                            for u in (variant_info.get("raw_image_urls") or [])
                        ]

                        changes, removed = [], []

                        # Make a working copy of existing URLs
                        updated_urls = list(existing_urls)

                        # Ensure asset_images_json aligns with existing_urls
                        trimmed_or_padded = False
                        print(len(asset_images_json), len(existing_urls), '\n')
                        if len(asset_images_json) > len(existing_urls):
                            asset_images_json = asset_images_json[:len(existing_urls)]
                            print(asset_images_json, '\n')
                            trimmed_or_padded = True
                        elif len(asset_images_json) < len(existing_urls):
                            asset_images_json.extend([None] * (len(existing_urls) - len(asset_images_json)))
                            print(asset_images_json, '\n')
                            trimmed_or_padded = True

                        # Compare incoming URLs with existing
                        for idx, url in enumerate(incoming_urls):
                            if idx >= len(updated_urls):
                                # New URL → append URL and generate new ID
                                updated_urls.append(url)
                                new_id = self.get_id_from_image_url(url)
                                asset_images_json.append(new_id)
                                changes.append((idx, None, url))
                            elif updated_urls[idx] != url:
                                # URL changed → replace URL and generate new ID
                                old_url = updated_urls[idx]
                                updated_urls[idx] = url
                                new_id = self.get_id_from_image_url(url)
                                asset_images_json[idx] = new_id
                                changes.append((idx, old_url, url))
                            # else: URL unchanged → keep existing ID

                        # Handle removals (existing longer than incoming)
                        while len(updated_urls) > len(incoming_urls):
                            removed_idx = len(updated_urls) - 1
                            removed_url = updated_urls.pop()
                            asset_images_json.pop()
                            removed.append((removed_idx, removed_url))

                        # Fill any None IDs (from external service or padding)
                        for idx, aid in enumerate(asset_images_json):
                            if aid is None:
                                asset_images_json[idx] = self.get_id_from_image_url(updated_urls[idx])

                        # Update existing_urls
                        existing_urls[:] = updated_urls

                        # --- Debug print before any DB or Shopify updates ---
                        print(f"\n=== Variant: {variant_id} ===")
                        print("\nChanges:", changes)
                        print("\nRemoved:", removed)
                        # print("\nExisting URLs:", existing_urls)
                        # print("\nIncoming URLs:", incoming_urls)
                        print("\nAsset Images JSON:", asset_images_json)
                        print("\npassing:", trimmed_or_padded)
                        print("===============================\n")
                        # continue

                        if changes or removed or trimmed_or_padded:
                            # Save full dicts back into DB, not just urls
                            variant.urls = json.dumps(variant_info.get("raw_image_urls") or [])
                            db.session.add(variant)
                            anything_changed = True

                            # Push updates to Shopify (metafield)
                            try:
                                metafields_payload = [{
                                    "ownerId": variant_id,
                                    "namespace": "custom",
                                    "key": "variant_images",
                                    "type": "list.file_reference",
                                    "value": json.dumps(asset_images_json)
                                }]
                                response = shopify_request(
                                    query=MetafieldMutationBuilder().build(),
                                    shop_url=store.get('url'),
                                    access_token=store.get('token'),
                                    variables={"metafields": metafields_payload}
                                )
                                try:
                                    print(f"[Shopify] Updated variant {variant_id} with {asset_images_json}")
                                    print("[Shopify] Response:", response.json())
                                except Exception:
                                    print("[Shopify] Response (non-json or empty) for variant", variant_id)
                            except Exception as e:
                                print(f"[Shopify] Error updating variant {variant_id}: {e}")

                except Exception as e:
                    # Catch-all per-variant error — do not crash the whole process
                    print(f"[DB] Error processing variant {variant_info!r}: {e}")
                    # attempt to continue to next variant
                    continue

            # --- 4. Commit only if something changed ---
            try:
                if anything_changed:
                    db.session.commit()
                    print("[DB] All changes committed.")
                else:
                    # explicit rollback to clear any pending transactional state
                    db.session.rollback()
                    print("[DB] No changes detected, nothing to commit.")
            except Exception as e:
                # final safeguard
                try:
                    db.session.rollback()
                except Exception:
                    pass
                print(f"[DB] Failed to commit changes: {e}")
                return False

            return True

        except Exception as e:
            # Top-level unexpected failure: rollback and return False (do not re-raise)
            try:
                db.session.rollback()
            except Exception:
                pass
            print(f"[DB] Fatal error in save_product_with_variants: {e}")
            return False

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

    def create_not_found_images(self, data: list, parent_dict: dict = None):
        summary = {
            "attempted_to_upload": 0,
            "successfully_uploaded": 0,
            "failed_uploads": 0,
            "failed_images": []
        }

        # collect all images that need upload
        upload_candidates = []
        for v_idx, variant in enumerate(data):
            for i_idx, img in enumerate(variant.get("data_images", [])):
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
                    alt_key = f"{v_idx}_{i_idx}_{normalized}"

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
