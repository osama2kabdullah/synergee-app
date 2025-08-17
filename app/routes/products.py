import os
from app.graphql_queries.query_builders.query_builders import AllProductQueryBuilder
from app.utils.helper import STORES, ShopifyProductBuilder, shopify_request
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
    current_store_key = request.args.get('store', 'shop1')
    store = STORES.get(current_store_key)
    if not store:
        return render_template('products.html', data={"ok": False, "errors": [{"store": store['name'] if store else current_store_key, "error": "Store not configured"}]})
    variables = {
        "first": limit if not before else None,
        "last": limit if before else None,
        "after": after,
        "before": before,
        "query": query,
    }
    builder = AllProductQueryBuilder()
    graphql_query = builder.build(
        include_media=True,
        variants_limit=100,
        include_filled_variant_images_assets=False
    )
    response = shopify_request(query=graphql_query, shop_url=store["url"], access_token=store["token"], variables=variables)
    json_data = response.json()
    if "errors" in json_data:
        return render_template('products.html', data={"ok": False, "store": store['name'], "errors": json_data["errors"] })
    
    end = (start + limit) - 1
    current_page = ((start - 1) // limit) + 1

    products = []
    for edge in json_data['data']['products']['edges']:
        product = ShopifyProductBuilder(edge['node'], store)
        if not show_incompleted or not product.is_filled_images():
            products.append(product.details())

    page_info = json_data['data']['products']['pageInfo']
    end_cursor = page_info['endCursor']
    start_cursor = page_info['startCursor']
    total_count = json_data['data']['productsCount']['count']
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
        "current_store_key": current_store_key,
        "total_pages": total_pages
    }
    return render_template('products.html', data=data)
