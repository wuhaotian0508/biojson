"""兼容 shim — pickle 反序列化旧索引时需要 `data_loader.GeneChunk`"""
from utils.data_loader import GeneChunk, DataLoader  # noqa: F401
