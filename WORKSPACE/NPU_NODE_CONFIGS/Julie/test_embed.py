from sentence_transformers import SentenceTransformer
print('Loading model...')
try:
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    print('Encoding...')
    emb = model.encode(['test'])
    print(f'Success! Shape: {emb.shape}')
except Exception as e:
    print(f'Error: {e}')
