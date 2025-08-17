from jinja2 import Environment, FileSystemLoader
import os

class GraphQLQueryBuilder:
    def __init__(self, template_filename):
        base_dir = os.path.dirname(os.path.dirname(__file__))  # /graphql_queries/
        template_dir = os.path.join(base_dir, 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template(template_filename)

    def render(self, **kwargs):
        return self.template.render(**kwargs)

class ProductQueryBuilder(GraphQLQueryBuilder):
    def __init__(self):
        super().__init__("get_product.graphql.j2")

    def build(self, include_media=False,
              variants_limit=2, include_filled_variant_images_assets=False):
        return self.render(
            include_media=include_media,
            include_filled_variant_images_assets=include_filled_variant_images_assets,
            variants_limit=variants_limit
        )

class AllProductQueryBuilder(GraphQLQueryBuilder):
    def __init__(self):
        super().__init__("get_all_product.graphql.j2")

    def build(self, include_media=False,
              variants_limit=2, include_filled_variant_images_assets=False):
        return self.render(
            include_media=include_media,
            include_filled_variant_images_assets=include_filled_variant_images_assets,
            variants_limit=variants_limit
        )

class MetafieldMutationBuilder(GraphQLQueryBuilder):
    def __init__(self):
        super().__init__("metafield_set.graphql.j2")

    def build(self):
        return self.render()
