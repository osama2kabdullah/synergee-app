import os
from app.utils.helper import ShopifyProductBuilder
from . import main
from flask import jsonify, request
from app.utils.response import success_response, error_response

ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP_URL = os.getenv("SHOPIFY_STORE_URL")

@main.route('/api/delete-populated-single-product', methods=['POST'])
def delete_populated_single_product():
    data = request.get_json()

    if not data or 'product_id' not in data:
        return error_response('Missing product_id in request body', 400)
    
    product_id = data['product_id']
    product = ShopifyProductBuilder(product_id=product_id, shop_url=SHOP_URL, access_token=ACCESS_TOKEN)
    if not product.product_data:
        return error_response('Product data not available', 404)
    if not product.is_filled_images():
        return error_response('Product images are not populated', 400)
    result = product.delete_asset_images_from_metafield()
    
    if result.get("errors"):
        return error_response(
            message="Error while deleting images.",
            data=result
        )
    
    return success_response(
        message="Image deletion attempted.",
        status='success',
        data=result
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

@main.route('/api/populate-single-product', methods=['POST'])
def populate_single_product():
    data = request.get_json()

    if not data or 'product_id' not in data:
        return error_response('Missing product_id in request body', 400)

    product_id = data['product_id']
    product = ShopifyProductBuilder(product_id=product_id, shop_url=SHOP_URL, access_token=ACCESS_TOKEN)

    if not product.product_data:
        return error_response('Product data not available', 404)
    
    if product.is_filled_images():
        return success_response(data=None, message='Images are already populated', status='success')
    
    data = product.data_for_put_into_metafield()

    if data.get("unmatched_count") > 0:
        # in that case we have to modify and then 
        # call again the put_images_into_metafield
        return error_response(
            message=f"Some images are unmatched. Please review before populating. Unmatched count: {data.get('unmatched_count')}",
            # data=data.get("results")
            data={
                "unmatched_count": data.get("unmatched_count"),
                "product_title": product.get_title(),
                "media": product.get_media(),
                "results": data.get("results"),
            }
            # data = product.as_summary_dict()
        )
    
    if not data.get("results"):
        return error_response(
            message="No images Found to populate."
        )
    
    result = product.put_images_into_metafield(data.get("results"), delete_existing=False)
    
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
