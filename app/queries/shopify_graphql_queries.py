QUERIES = {
  "single_product": """
    query GetProduct($id: ID!) {
      product(id: $id) {
      title
      media(query: "media_type:IMAGE", sortKey: POSITION, first: 250) {
        nodes {
          ... on MediaImage {
            id
            image { url }
          }
        }
      }
      variants(first: 249) {
        nodes {
          title
          id
            imagesUrl: metafield(namespace: "custom", key: "variant_images_url") {
              jsonValue
            }
          }
        }
      }
    }
  """,

  "reorder": """
    mutation ReorderProductImages($productId: ID!, $moves: [MoveInput!]!) {
      productReorderMedia(id: $productId, moves: $moves) {
      job { id }
      mediaUserErrors { field message }
      }
    }
  """,

  "file_create": """
    mutation CreateFile($originalSource: String!) {
      fileCreate(files: [{ originalSource: $originalSource }]) {
      files { id fileStatus }
      userErrors { field message }
      }
    }
  """,

  "product_set": """
    mutation AssociateFilesWithProduct($productId: ID!, $files: [FileReferenceInput!]!) {
      productSet(input: { id: $productId, files: $files }) {
      product { id }
      userErrors { field message }
      }
    }
  """,

  "metafield_set": """
    mutation metafieldSet($metafields: [MetafieldsSetInput!]!) {
      metafieldsSet(metafields: $metafields) {
        metafields { id key namespace }
        userErrors { field message }
      }
    }
  """,

  "all_products": """
    query GetAllProducts (
      $first: Int, 
      $last: Int, 
      $after: String, 
      $before: String,
      $query: String
    ) {
      productsCount(query: $query) {
        count
      }
      products(first: $first, last: $last, after: $after, before: $before, query: $query) {
        edges {
          cursor
          node {
            id
            title
            images(first: 1) {
              edges {
                node {
                  originalSrc
                }
              }
            }
            variantsCount {
              count
            }
            onlineStorePreviewUrl
            mediaCount {
              count
            }
            variants(first: 250) {
              edges {
                node {
                  id
                  title
                  imagesUrl: metafield(namespace: "custom", key: "variant_images_url") {
                    jsonValue
                  }
                  assetImages: metafield(namespace: "custom", key: "variant_images") {
                    jsonValue
                  }
                }
              }
            }
          }
        }
        pageInfo {
          hasNextPage
          hasPreviousPage
          endCursor
          startCursor
        }
      }
    }
  """,
}