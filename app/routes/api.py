from app.graphql_queries.query_builders.query_builders import AllProductQueryBuilder, ProductQueryBuilder
from app.models import Shop
from app.utils.helper import STORES, ShopifyGIDBuilder, ShopifyProductBuilder, fetch_single_product, shopify_request
from . import main
from flask import jsonify, request
from app.utils.response import success_response, error_response

@main.route('/api/print', methods=['POST'])
def print_api():
    print('API button was clicked!')
    loop_over_all_stores()
    return jsonify({"message": "API button was clicked!"}), 200

    shops_data = []

    shops = Shop.query.all()
    for shop in shops:
        shop_dict = {
            "id": shop.id,
            "name": shop.name,
            "domain": shop.domain,
            "products": []
        }

        for product in shop.products:
            product_dict = {
                "id": product.id,
                "title": product.title,
                "shopify_id": product.shopify_id,
                "variants": []
            }

            for variant in product.variants:
                variant_dict = {
                    "id": variant.id,
                    "shopify_id": variant.shopify_id,
                    "urls": variant.urls
                }
                product_dict["variants"].append(variant_dict)

            shop_dict["products"].append(product_dict)

        shops_data.append(shop_dict)

    return jsonify({
        "ok": True,
        "shops": shops_data
    }), 200

def fetch_all_products(store, limit=250, after=None, before=None):
    builder = AllProductQueryBuilder()
    graphql_query = builder.build(
        include_media=True,
        variants_limit=100,
        include_filled_variant_images_assets=False
    )

    products = []
    has_next_page = True
    after_cursor = after  # Start cursor (None by default)

    while has_next_page:
        variables = {
            "first": limit if not before else None,
            "last": limit if before else None,
            "after": after_cursor,
            "before": before,
        }

        response = shopify_request(
            query=graphql_query,
            shop_url=store["url"],
            access_token=store["token"],
            variables=variables
        )
        json_data = response.json()

        if "errors" in json_data:
            raise Exception(f"Shopify API error: {json_data['errors']}")

        # Add products from this page
        for edge in json_data['data']['products']['edges']:
            product = ShopifyProductBuilder(edge['node'], store)
            products.append(product)

        # Pagination info
        page_info = json_data['data']['products']['pageInfo']
        has_next_page = page_info.get('hasNextPage', False)
        after_cursor = json_data['data']['products']['edges'][-1]['cursor'] if has_next_page else None

    return products

def loop_over_all_stores():
    for store in STORES.values():
        products = fetch_all_products(store)
        for product in products:
            product.save_product_with_variants()

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

@main.route('/api/canada-webhook', methods=['POST'])
def canada_webhook():
    data = request.json
    store = STORES.get('shop2')
    response = handle_product_change(data, store)
    return jsonify({"status": "received"}), 200

@main.route('/api/us-webhook', methods=['POST'])
def us_webhook():
    data = request.json
    store = STORES.get('shop1')
    response = handle_product_change(data, store)
    return jsonify({"status": "received"}), 200

def handle_product_change(data, store):
    print("\n\nproduct id: ", data.get('admin_graphql_api_id'), ", store: ", store["name"])
    print("\n\n")
    product_id = data.get('admin_graphql_api_id')
    builder = ProductQueryBuilder()
    query = builder.build(include_media=True, variants_limit=100, include_filled_variant_images_assets=False)
    variables = {"id": product_id}
    product = fetch_single_product(query, variables, store)
    saving = product.save_product_with_variants()

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

    # No images found to populate
    if not any(variant.get("data_images") for variant in data_to_upload.get("results", [])):
        return error_response(
            "No images found to populate.",
            data={"details": data_to_upload.get("results"), "next_step": "populate_first"}
        )

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
    return error_response('API archived', 404)

    if not client_data or 'product_id' not in client_data:
        return error_response('Missing product_id in request body', 400)

    product_id = client_data['product_id']
    # product = ShopifyProductBuilder(product_id=product_id, shop_url=SHOP_URL, access_token=ACCESS_TOKEN)

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
