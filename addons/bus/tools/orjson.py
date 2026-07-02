try:
    import orjson

    def dumps(value):
        return orjson.dumps(value)

    def loads(value):
        return orjson.loads(value)
except ImportError:
    import json

    def dumps(value):
        # uuid PKs: bus payloads carry uuid.UUID ids; stdlib json can't
        # serialize them (orjson does natively) -> stringify via default=str.
        return json.dumps(value, separators=(",", ":"), default=str).encode()

    def loads(value):
        return json.loads(value)
