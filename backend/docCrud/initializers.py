from chromadb import HttpClient
from chromadb.config import Settings

client = HttpClient(
    host="https://ws-7a.ml.iit-ropar.truefoundry.cloud",
    settings=Settings(allow_reset=True, anonymized_telemetry=False)
)

api_url = "https://multilingual-e5-small-ws-7a-8000-e57823.ml.iit-ropar.truefoundry.cloud/embeddings"  # replace with actual TrueFoundry URL
