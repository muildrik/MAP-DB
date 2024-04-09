default_template = {
    "SchemaInfo": {
        "schema_name": "default",
        "system_fields": [
            "thumbnail",
            "text_search",
            "timestamp",
            "last_modified"
        ],
        "indexed_fields": [
            "text_search"
        ],
        "unindexed_fields": [],
        "index_log": {
            "indexed": {
                "text_search": []
            },
            "dropped": {
                "text_search": []
            }
        }
    },
    "Schema": {
        "thumbnail": {
            "type": "string",
            "required": True,
            "minlength": 1
        },
        "text_search": {
            "type": "string",
            "required": True,
            "minlength": 1
        },
        "timestamp": {
            "type": "timestamp",
            "required": True
        },
        "last_modified": {
            "type": "timestamp",
            "required": True
        }
    },
    "FieldNames": [
        { "thumbnail" : "Thumbnail" },
        { "text_search" : "All text" },
        { "timestamp" : "Creation" },
        { "last_modified" : "Last modified" }
    ]
}