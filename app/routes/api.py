import os
from urllib.parse import unquote, urlparse
from app.queries.shopify_graphql_queries import QUERIES
from app.utils.helper import ShopifyGIDBuilder, create_media_from_url, graphql_request
from . import main
from flask import json, jsonify, request

@main.route('/api/populate-single-product', methods=['POST'])
def populate_single_product():
    data = request.get_json()
    product_id = data.get('product_id')

    if product_id.strip() == "":
        # grab product data
        product_gid = ShopifyGIDBuilder("Product")
        product_gid_full = product_gid.build(product_id)  # gid://shopify/Product/:id
        response = graphql_request(QUERIES["single_product"], {"id": product_gid_full})

        # Get the list of variant nodes
        variants = response.get("data", {}).get("product", {}).get("variants", {}).get("nodes", [])
        var_old_images = old_images(variants)
        product_images = get_all_images(response)
        var_old_images_with_new = old_images_with_new(var_old_images, product_images)
        response_of_create_not_found_images, created_count = create_not_found_images(var_old_images_with_new)
        response_of_put_images_into_metafield = put_images_into_metafield(response_of_create_not_found_images)
        
        # Build the sync result object
        result = {
            "message": "Image sync completed",
            "created_images": created_count,
            "metafield_update_summary": response_of_put_images_into_metafield
        }

        # Pass it to the template
        return jsonify({"success": True, "data": result})

    return jsonify({"success": False, "error": "Product ID cannot be empty."})


def old_images_with_new(var_old_images, product_images):
    # Step 1: Build a lookup using new image filenames
    product_lookup = {}
    for img in product_images:
        new_filename = os.path.basename(urlparse(img["url"]).path)
        product_lookup[new_filename] = {
            "id": img.get("id"),
            "new_img_url": img["url"]
        }

    final_variants = []

    # Step 2: Walk through variants
    for var in var_old_images:
        variant_title = var.get("variant_title", "")
        variant_id = var.get("variant_id", "")
        images = []

        for img in var.get("images", []):
            old_url = img.get("url")
            if not old_url:
                continue

            raw_filename = os.path.basename(urlparse(old_url).path)
            decoded_filename = unquote(raw_filename)
            normalized_old_name = decoded_filename.replace(" ", "_20")

            match = product_lookup.get(normalized_old_name)

            images.append({
                "old_img_url": old_url,
                "new_img_url": match["new_img_url"] if match else "",
                "id": match["id"] if match else ""
            })

        final_variants.append({
            "variant_id": variant_id,
            "variant_title": variant_title,
            "images": images
        })

    return final_variants

def get_all_images(response):
    media_nodes = response.get("data", {}).get("product", {}).get("media", {}).get("nodes", [])
    
    images = []
    for node in media_nodes:
        if not node:
            continue  # skip None nodes

        image = node.get("image")
        if image and "url" in image:
          images.append({"id": node.get("id"), "url": image["url"]})

    return images

def old_images(variants):
    # Build the desired format
    variant_data = []
    for variant in variants:
        images = []
        image_urls = variant.get("imagesUrl", {}).get("jsonValue", [])

        # Ensure it's a list
        if isinstance(image_urls, list):
            for url in image_urls:
                images.append({"url": url})

        variant_data.append({
            "variant_title": variant.get("title"),  # or use "id" if you prefer
            "variant_id": variant.get("id"),  # or use "id" if you prefer
            "images": images
        })

    # Now `variant_data` is in the desired format
    return variant_data

def create_not_found_images(var_old_images_with_new):
    created_count = 0
    seen_urls = {}  # Cache for already created media {old_url: {"id": ..., "new_img_url": ...}}

    for variant in var_old_images_with_new:
        for image in variant.get("images", []):
            if not image.get("new_img_url") or not image.get("id"):
                old_url = image.get("old_img_url")
                
                if old_url in seen_urls:
                    # Use the already created info
                    image["id"] = seen_urls[old_url]["id"]
                    image["new_img_url"] = seen_urls[old_url]["new_img_url"]
                    continue

                created = create_media_from_url(old_url)

                if created:
                    image["id"] = created["id"]
                    image["new_img_url"] = created.get("url", "")  # Assuming your create_media_from_url now returns both
                    seen_urls[old_url] = {
                        "id": image["id"],
                        "new_img_url": image["new_img_url"]
                    }
                    created_count += 1
                    print(f"[INFO] File created for: {old_url}")
                else:
                    print(f"[WARN] Could not create media for: {old_url}")

    return var_old_images_with_new, created_count

def put_images_into_metafield(images_with_id):
    summary = {
        "success": [],
        "skipped": [],
        "errors": []
    }

    for variant in images_with_id:
        variant_id = variant.get("variant_id")
        image_ids = [
            img["id"]
            for img in variant.get("images", [])
            if img.get("id")
        ]

        if not variant_id or not image_ids:
            summary["skipped"].append(variant_id or "Unknown variant")
            continue  # skip if no variant ID or no valid images

        metafield_input = {
            "ownerId": variant_id,
            "namespace": "custom",
            "key": "variant_images",
            "value": json.dumps(image_ids)
        }

        try:
            response = graphql_request(QUERIES["metafield_set"], {"metafields": [metafield_input]})
            errors = response.get("data", {}).get("metafieldsSet", {}).get("userErrors", [])

            if errors:
                summary["errors"].append({
                    "variant_id": variant_id,
                    "errors": errors
                })
            else:
                summary["success"].append(variant_id)

        except Exception as e:
            summary["errors"].append({
                "variant_id": variant_id,
                "exception": str(e)
            })

    return summary
