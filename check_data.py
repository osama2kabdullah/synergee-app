from app import create_app, db
from app.models import Shop, Product, Variant

app = create_app()

with app.app_context():
    # --- Counts ---
    shop_count = Shop.query.count()
    product_count = Product.query.count()
    variant_count = Variant.query.count()

    print("=== Row Counts ===")
    print(f"Shops: {shop_count}")
    print(f"Products: {product_count}")
    print(f"Variants: {variant_count}")

    # --- Full Data ---
    print("\n=== Shops ===")
    for shop in Shop.query.all():
        print(f"ID: {shop.id}, Name: {shop.name}, Domain: {shop.domain}\n")

    print("\n=== Products ===")
    for product in Product.query.limit(1).all():
        print(f"ID: {product.id}, Title: {product.title}, ShopifyID: {product.shopify_id}, ShopID: {product.shop_id}\n")

    print("\n=== Variants ===")
    for variant in Variant.query.limit(1).all():
        print(f"ID: {variant.id}, ShopifyID: {variant.shopify_id}, ProductID: {variant.product_id}, URLs: {variant.urls}\n")
