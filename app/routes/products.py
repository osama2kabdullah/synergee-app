from app.queries.shopify_graphql_queries import QUERIES
from app.utils.helper import graphql_request
from . import main
from flask import render_template, request

@main.route('/products')
def products():
    query = request.args.get('q', '').strip()
    show_incompleted = request.args.get('showIncompleted', '1' if not request.args else '0') == '1'
    limit = int(request.args.get('limit', 20))
    after = request.args.get('after')
    before = request.args.get('before')
    start = int(request.args.get('start', 1))

    data = {}

    loaded_data = load_default_products(limit, after, before, start, query, show_incompleted)
    data.update(loaded_data)

    return render_template('products.html', data=data)

def load_default_products(limit, after, before, start, query, show_incompleted):
    variables = {
        "first": limit if not before else None,
        "last": limit if before else None,
        "after": after,
        "before": before,
        "query": query,
    }
    end = (start + limit) - 1
    current_page = ((start - 1) // limit) + 1
    response = graphql_request(QUERIES["all_products"], variables)
    # response = graphql_request(QUERIES["err_all_products"], variables)
    # Error handling
    if "errors" in response:
        return {
            "ok": False,
            "start": start,
            "end": end,
            "query": query,
            "current_page_showing": 0,
            "total_count": 0,
            "products": [],
            "errors": response["errors"],
            "show_incompleted": show_incompleted,
            "limit": limit,
            "current_page": current_page,
            "total_pages": 1,
            "has_next_page": False,
            "has_previous_page": False,
            "start_cursor": None,
            "end_cursor": None
        }

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
        # print(f"{asset_images}\n\n - {image_urls}\n\n")

        image_has_issue = True  # Assume issue by default

        all_matched = True  # Track if every variant matches

        for variant in variants:
            asset_images = variant.get("assetImages") or {}
            image_urls = variant.get("imagesUrl") or {}

            count_assets = len(asset_images.get("jsonValue", []))
            count_urls = len(image_urls.get("jsonValue", []))

            # print(f"{count_assets} - {count_urls}")

            if count_assets != count_urls:
                all_matched = False  # Found a mismatch

        # Final decision
        if all_matched:
            image_has_issue = False

        # print(node["title"], "\n\nFinal issue flag:", image_has_issue, "\n\n")


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
            "filled_images": filled_images,
            "image_has_issue": image_has_issue
        }
        # Append all products if not filtering; otherwise only incomplete ones
        if not show_incompleted or not filled_images:
            products.append(product)
        # if image_has_issue:
        #     products.append(product)


    page_info = response['data']['products']['pageInfo']
    print('pag', page_info)
    end_cursor = page_info['endCursor']
    start_cursor = page_info['startCursor']
    total_count = response['data']['productsCount']['count']
    total_pages = ((total_count - 1) // limit) + 1

    data = {
        "end": end,
        "end_cursor": end_cursor,
        "start_cursor": start_cursor,
        "total_count": total_count,
        "has_next_page": page_info['hasNextPage'],
        "has_previous_page": page_info['hasPreviousPage'],
        "products": products,
        "ok": True,
        "start": start,
        "query": query,
        "current_page_showing": len(products),
        "show_incompleted": show_incompleted,
        "limit":limit,
        "current_page": current_page,
        "total_pages": total_pages
    }
    return data
