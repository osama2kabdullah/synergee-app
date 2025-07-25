from app.queries.shopify_graphql_queries import QUERIES
from app.utils.helper import graphql_request
from . import main
from flask import render_template, request

@main.route('/products')
def products():
    raw_query = request.args.get('q', '').strip()
    # search_query = f'query=title:{raw_query}' if raw_query else None
    search_query = f'{raw_query}' if raw_query else None
    limit = int(request.args.get('limit', 20))
    after = request.args.get('after')
    before = request.args.get('before')
    start = int(request.args.get('start', 1))

    data = {}

    loaded_data = load_default_products(limit, after, before, start, search_query, raw_query)
    data.update(loaded_data)

    return render_template('products.html', data=data)

def load_default_products(limit, after, before, start, search_query, raw_query):
    variables = {
        "first": limit if not before else None,
        "last": limit if before else None,
        "after": after,
        "before": before,
        "query": search_query,
    }
    response = graphql_request(QUERIES["all_products"], variables)
    # Error handling
    ok = True
    errors = ""
    if "errors" in response:
        ok= False
        errors = response['errors']

    products = []
    for edge in response['data']['products']['edges']:
        node = edge['node']
        variants = [v['node'] for v in node['variants']['edges']]

        # Count all variant-level images from the metafield `variant_images_url`
        all_variant_image_count = 0
        filled_images = False

        for variant in variants:
            asset_images = variant.get("assetImages")
            
            if asset_images is not None:
                file_images = (variant.get("assetImages") or {}).get("jsonValue", [])
                if isinstance(file_images, list) and file_images:
                    filled_images = True
                    break

        for variant in variants:
            images_url = (variant.get("imagesUrl") or {}).get("jsonValue", [])
            if isinstance(images_url, list):
                all_variant_image_count += len(images_url)

        product = {
            "id": node["id"],
            "title": node["title"],
            "url": node["onlineStorePreviewUrl"],
            "variantsCount": node["variantsCount"]["count"],
            "imagesCount": node["mediaCount"]["count"],
            "variants": variants,
            "image_url": node['images']['edges'][0]['node']['originalSrc'] if node['images']['edges'] else None,
            "all_variant_level_image_count": all_variant_image_count,
            "filled_images": filled_images
        }

        products.append(product)

    page_info = response['data']['products']['pageInfo']
    end_cursor = page_info['endCursor']
    start_cursor = page_info['startCursor']
    total_count = response['data']['productsCount']['count']
    end = start + len(products) - 1 if products else start
    data = {
        "ok": ok,
        "errors": errors,
        "end": end,
        "start": start,
        "query": raw_query,
        "end_cursor": end_cursor,
        "start_cursor": start_cursor,
        "total_count": total_count,
        "limit":limit,
        "has_next_page": page_info['hasNextPage'],
        "has_previous_page": page_info['hasPreviousPage'],
        "products": products
    }
    return data
