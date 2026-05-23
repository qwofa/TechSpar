from llama_index.embeddings.openai import OpenAIEmbedding

e = OpenAIEmbedding(model_name='text-embedding-3-small', api_key='test', timeout=5.0, max_retries=1)
client = e._client
print('client type:', type(client).__name__)
print('client _timeout:', getattr(client, '_timeout', 'N/A'))
print('client max_retries:', getattr(client, 'max_retries', 'N/A'))
