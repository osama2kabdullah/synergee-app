import os
from app.graphql_queries.query_builders.query_builders import ProductQueryBuilder
from app.utils.helper import STORES, ShopifyGIDBuilder, ShopifyProductBuilder, fetch_single_product
from . import main
from flask import jsonify, request
from app.utils.response import success_response, error_response

ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP_URL = os.getenv("SHOPIFY_STORE_URL")

@main.route('/api/delete-populated-single-product', methods=['POST'])
def delete_populated_single_product():
    data = request.get_json()

    if not data or 'product_id' not in data or 'current_store_key' not in data:
        return error_response("Missing product_id or current_store_key in request body", 400)

    store = STORES.get(data['current_store_key'])
    if not store:
        return error_response(f"Store '{data.get('current_store_key')}' not configured.", 404)

    product_id = ShopifyGIDBuilder('Product').build(data['product_id'])
    builder = ProductQueryBuilder()
    query = builder.build(include_media=False, variants_limit=100, include_filled_variant_images_assets=False)
    variables = {"id": product_id}

    product = fetch_single_product(query, variables, store)

    if isinstance(product, dict) and "errors" in product:
        return error_response("Could not fetch product from Shopify.", data={"errors": product["errors"]})

    if not product.product_data:
        return error_response("Product data not available", 404)

    if not product.is_filled_images():
        return error_response(
            message="No asset images found to delete ⚠️",
            data={"next_step": "populate_first", "details": []}
        )

    result = product.delete_asset_images_from_metafield()

    response_data = {"details": result.get("deleted_images", [])}

    if result.get("errors"):
        response_data["errors"] = result["errors"]
        return error_response(
            "Failed to delete images from Shopify metafields.",
            data=response_data
        )

    return success_response(
        message="Images successfully deleted",
        status="success",
        data=response_data
    )

@main.route('/api/populate-single-product', methods=['POST'])
def populate_single_product():
    data = request.get_json()

    if not data or 'product_id' not in data or 'current_store_key' not in data:
        return error_response("Missing product_id or current_store_key in request body", 400)

    store = STORES.get(data['current_store_key'])
    if not store:
        return error_response(f"Store '{data.get('current_store_key')}' not configured.", 404)

    product_id = ShopifyGIDBuilder('Product').build(data['product_id'])

    builder = ProductQueryBuilder()
    query = builder.build(include_media=True, variants_limit=100, include_filled_variant_images_assets=False)
    variables = {"id": product_id}

    product = fetch_single_product(query, variables, store)

    if isinstance(product, dict) and "errors" in product:
        return error_response("Could not fetch product from Shopify.", data={"errors": product["errors"]})

    if not product.product_data:
        return error_response("Product data not available", 404)

    if product.is_filled_images():
        return success_response(
            message="All images are already populated 🎉",
            status="success",
            data={"details": product.data_for_client_display()}
        )

    data_to_upload = product.data_for_put_into_metafield()

    # Create unmatched images if any
    if data_to_upload.get("unmatched_count", 0) > 0:
        product.create_not_found_images(data_to_upload.get("results"), parent_dict=data_to_upload)

    # No images found to populate
    if not data_to_upload.get("results"):
        return error_response("No images found to populate.", data={"details": data_to_upload.get("results")})

    # Check if any images are still pending upload
    still_pending = any(
        img.get("needs_upload")
        for variant in data_to_upload.get("results", [])
        for img in variant.get("data_images", [])
    )

    if still_pending:
        return error_response(
            message="Some images are still being uploaded. Please retry shortly.",
            data={
                "details": data_to_upload.get("results"),
                "unmatched_count": data_to_upload.get("unmatched_count"),
                "next_step": "retry_upload"
            }
        )

    # Push images into metafield
    result = product.put_images_into_metafield(data_to_upload.get("results"), delete_existing=False)

    response_data = {
        "details": data_to_upload.get("results"),
        "image_creation_summary": data_to_upload.get("image_creation_summary", {})
    }

    if result.get("errors"):
        response_data["errors"] = result["errors"]
        return error_response(
            "Failed to populate images into Shopify metafields.",
            data=response_data
        )

    return success_response(
        message="Images successfully populated",
        status="success",
        data=response_data
    )

@main.route('/api/populate-unmatched-images', methods=['POST'])
def populate_unmatched_images():
    client_data = request.get_json()

    if not client_data or 'product_id' not in client_data:
        return error_response('Missing product_id in request body', 400)

    product_id = client_data['product_id']
    product = ShopifyProductBuilder(product_id=product_id, shop_url=SHOP_URL, access_token=ACCESS_TOKEN)

    if not product.product_data:
        return error_response('Product data not available', 404)
    
    if product.is_filled_images():
        return success_response(data=None, message='Images are already populated', status='success')
    
    variants_data = product.data_for_put_into_metafield()

    if variants_data.get("unmatched_count") > 0:
        # in that case we have to modify and then 
        # call again the put_images_into_metafield
        result = product.put_images_into_metafield(client_data.get("data"), delete_existing=False)

        if result.get("errors"):
            return error_response(
                message="Error while populating images.",
                data=result
            )
        
        return success_response(
            message="Image population attempted.",
            status='success',
            data=result
        )
