import pickle
import sys
sys.path.insert(0, '.')
with open('index/chunks.pkl', 'rb') as f:
    chunks = pickle.load(f)

# 找 GAME8 相关 chunks
for i, c in enumerate(chunks):
    gn = (c.gene_name or '')
    ct = (c.content or '')
    if 'GAME8' in gn or 'GAME8' in ct[:2000]:
        print('=' * 80)
        print(f'idx={i} gene_name={gn!r}')
        print(f'chunk_type={c.chunk_type!r}')
        print(f'paper_title={(c.paper_title or "")[:80]}')
        print(f'content_len={len(ct)}')
        print('--- content head 2000 ---')
        print(ct[:2000])
        print('--- content tail 500 ---')
        print(ct[-500:])
        break
