def serialize(prefix, suffix):
    markers = ("<|fim_prefix|>", "<|fim_suffix|>", "<|fim_middle|>")
    if any(marker in prefix or marker in suffix for marker in markers):
        raise ValueError("Source contains reserved FIM markers")
    return markers[0] + prefix + markers[1] + suffix + markers[2]
