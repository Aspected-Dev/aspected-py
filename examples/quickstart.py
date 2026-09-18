"""
Quickstart example for the aspected-client SDK.

This script demonstrates the full lifecycle of an Aspected index:
1. Create an index with enum resolvers
2. List all indexes
3. Upload documents
4. Perform sparse vector searches (single and multi-aspect)
5. Delete the index

Prerequisites:
    - A running Aspected server (default: http://localhost:8080)
      Start one with: docker run -p 8080:8080 xillio/aspected:latest
    - Install the SDK: pip install -e . (from repo root)

No model downloads are required — this example uses only enum resolvers.

Docs: https://docs.aspected.com
"""

from aspected_client import (
    Aspect,
    AspectedClient,
    CreateIndexPayload,
    Missing,
    QuerySearch,
    UploadDocsPayload,
    UploadDocsPayloadPolicy,
    UpsertOperation,
)

INDEX_NAME = "products"
SERVER_URL = "http://localhost:8080"


def main() -> None:
    with AspectedClient(url=SERVER_URL) as client:
        # --------------------------------------------------------------
        # 1. Create an index
        #
        # We define two enum aspects: "category" and "colour".
        # The enum resolver maps categorical values to radial
        # embeddings. The path uses JSONPath to extract values
        # from documents.
        # --------------------------------------------------------------
        print("Creating index...")
        create_resp = client.create_index(
            INDEX_NAME,
            CreateIndexPayload(
                id_size=36,
                schema_=[
                    Aspect(
                        name="category",
                        type="enum",
                        path="$.category",
                        settings={
                            "values": [
                                "electronics",
                                "clothing",
                                "food",
                                "furniture",
                                "toys",
                            ]
                        },
                        multiplier=1.0,
                    ),
                    Aspect(
                        name="colour",
                        type="enum",
                        path="$.colour",
                        settings={
                            "values": [
                                "red",
                                "green",
                                "blue",
                                "black",
                                "white",
                                "yellow",
                            ]
                        },
                        multiplier=1.0,
                    ),
                ],
            ),
        )
        print(f"  Created: {create_resp.data.created}")

        # --------------------------------------------------------------
        # 2. List all indexes
        # --------------------------------------------------------------
        print("\nListing indexes...")
        list_resp = client.list_indexes()
        print(f"  Total indexes: {list_resp.total}")
        for idx in list_resp.data:
            print(f"    - {idx.name}")

        # --------------------------------------------------------------
        # 3. Upload documents
        #
        # Each document has a category and colour. The enum
        # resolvers extract values via the JSONPath and convert
        # them to radial embeddings that are concatenated into a
        # single composite vector.
        # --------------------------------------------------------------
        print("\nUploading documents...")
        upload_resp = client.upload_docs(
            INDEX_NAME,
            UploadDocsPayload(
                data=[
                    UpsertOperation(
                        id="prod-001",
                        doc={
                            "category": "electronics",
                            "colour": "black",
                        },
                    ),
                    UpsertOperation(
                        id="prod-002",
                        doc={
                            "category": "electronics",
                            "colour": "white",
                        },
                    ),
                    UpsertOperation(
                        id="prod-003",
                        doc={
                            "category": "clothing",
                            "colour": "red",
                        },
                    ),
                    UpsertOperation(
                        id="prod-004",
                        doc={
                            "category": "clothing",
                            "colour": "blue",
                        },
                    ),
                    UpsertOperation(
                        id="prod-005",
                        doc={
                            "category": "food",
                            "colour": "green",
                        },
                    ),
                    UpsertOperation(
                        id="prod-006",
                        doc={
                            "category": "furniture",
                            "colour": "white",
                        },
                    ),
                    UpsertOperation(
                        id="prod-007",
                        doc={
                            "category": "toys",
                            "colour": "red",
                        },
                    ),
                    UpsertOperation(
                        id="prod-008",
                        doc={
                            "category": "toys",
                            "colour": "yellow",
                        },
                    ),
                    UpsertOperation(
                        id="prod-009",
                        doc={
                            "category": "electronics",
                            "colour": "blue",
                        },
                    ),
                    UpsertOperation(
                        id="prod-010",
                        doc={
                            "category": "furniture",
                            "colour": "black",
                        },
                    ),
                ],
                policy=UploadDocsPayloadPolicy(missing=Missing.fail),
            ),
        )
        print(f"  Created: {upload_resp.data.created}")
        print(f"  Updated: {upload_resp.data.updated}")

        # --------------------------------------------------------------
        # 4a. Search — single aspect (sparse query)
        #
        # Search for products in the "electronics" category.
        # Only the category aspect is specified; the colour
        # dimensions are left undefined (sparse). This is the
        # key feature of Aspected: you can query on any subset
        # of aspects.
        # --------------------------------------------------------------
        print("\nSearching for 'electronics' (single aspect)...")
        search_resp = client.search_index(
            INDEX_NAME,
            QuerySearch(
                k=5,
                query={"category": "electronics"},
            ),
        )
        print(f"  Results ({len(search_resp.data)} hits):")
        for hit in search_resp.data:
            print(f"    [{hit.distance:.4f}] {hit.id}")

        # --------------------------------------------------------------
        # 4b. Search — multiple aspects
        #
        # Search for "red toys" — both aspects are specified so
        # results must be close on both dimensions.
        # --------------------------------------------------------------
        print("\nSearching for 'red toys' (both aspects)...")
        search_resp = client.search_index(
            INDEX_NAME,
            QuerySearch(
                k=3,
                query={
                    "category": "toys",
                    "colour": "red",
                },
            ),
        )
        print(f"  Results ({len(search_resp.data)} hits):")
        for hit in search_resp.data:
            print(f"    [{hit.distance:.4f}] {hit.id}")

        # --------------------------------------------------------------
        # 5. Delete the index
        # --------------------------------------------------------------
        print("\nDeleting index...")
        delete_resp = client.delete_index(INDEX_NAME)
        print(f"  Deleted: {delete_resp.data.deleted}")

    print("\nDone!")


if __name__ == "__main__":
    main()
