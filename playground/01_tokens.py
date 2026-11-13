import tiktoken

enc = tiktoken.get_encoding("o200k_base")

samples = {
    "english": "The payment service is returning errors.",
    "persian": "سرویس پرداخت خطا برمی‌گرداند.",
    "log_line": (
        '2026-11-13T14:02:11.532Z ERROR order-svc '
        '[req=9f1c2e7a-4b1d-4c8e-a2f3-77d0e1b9c4aa] '
        'psycopg.OperationalError: connection to server at "10.0.3.17", '
        'port 5432 failed: Connection refused'
    ),
    "stack_frame": 'File "/app/orders/service.py", line 142, in create_order',
}

for name, text in samples.items():
    ids = enc.encode(name)
    text_enc = enc.encode(text)
    print('text ---->', text_enc)
    ratio = len(text) / len(ids)
    print(f"\n== {name}: {len(text)} chars -> {len(ids)} tokens ({ratio:.1f} chars/token)")
    print([enc.decode([i]) for i in ids])

