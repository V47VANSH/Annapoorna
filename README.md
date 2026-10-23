# 🌾 Annapoorna

An assistant for farmers that detects crop diseases from a leaf photo, sends a
daily crop health report for the farmer's own field (satellite + weather), and
answers questions in chat, including by voice in Indian languages.

Built for the Annam.ai hackathon at IIT Ropar (Team 7A).

## Features

- **Disease detection**: a CNN trained on 42 crop disease classes (cotton, wheat,
  maize, rice, sugarcane) predicts the disease from a photo, then the assistant
  explains causes, symptoms, prevention and treatment.
- **Daily field report**: on login and every morning at 5:00 the backend pulls
  Sentinel-2, Landsat 8, Sentinel-1 and MODIS data for the farmer's field from
  Google Earth Engine, computes indices like NDVI, NDWI, NDRE and EVI, finds
  stressed areas with DBSCAN and adds the current weather.
- **Chat**: the latest report is given to the LLM as context, so answers are
  about the farmer's own field. Works with Google Gemini, Ollama, or any
  OpenAI-compatible API.
- **Voice input**: Whisper transcription for English, Hindi, Punjabi, Tamil,
  Telugu, Gujarati, Bengali, Marathi, Kannada and Malayalam.
- **Field from address**: the farmer's address is geocoded to a bounding box
  that is used as the field for the satellite analysis.

More on the problem and the users we built this for:
[docs/cards/project-card.ipynb](docs/cards/project-card.ipynb).

Stack: Next.js 15, FastAPI, MongoDB, TensorFlow/Keras, Whisper, LangChain,
Google Earth Engine, APScheduler.

## Running it

You need Python 3.11, Node.js 22, MongoDB, [ffmpeg](https://ffmpeg.org/download.html)
(for Whisper) and [uv](https://docs.astral.sh/uv/). The model file (~300MB) is not in git,
so the clone stays small. Download it once with `python backend/download_model.py`.

```bash
# backend
cd backend
cp .env.example .env
python download_model.py    # fetches the disease model (~300MB)
uv sync --extra ml          # --extra ml installs TensorFlow
uv run uvicorn main:app --reload

# frontend (another terminal)
cd website
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.

Or with Docker:

```bash
cp backend/.env.example backend/.env
cp website/.env.example website/.env.local
docker compose up --build
```

### Without API keys

The app runs without any keys. On the login page, "Skip registration" opens a
demo farm near Ludhiana. When something isn't configured the app falls back
instead of failing:

| Service | Fallback |
| --- | --- |
| Weather (Tomorrow.io) | Open-Meteo, no key needed |
| Geocoding (geocode.maps.co) | OpenStreetMap Nominatim, no key needed |
| Chat and treatment advice (LLM) | built-in advice for all 42 classes ([offline_advice.py](backend/offline_advice.py)) |
| MongoDB | in-memory store, data is lost on restart |
| Earth Engine | report contains weather only |

Set `ALLOW_KEYLESS_FALLBACKS=false` to turn this off.

## Setup for all features

For everything to work you need two things: a chat model and Google Earth
Engine. Weather doesn't need a key.

1. Add your Gemini key and model to `backend/.env`
2. Set up Earth Engine (below)
3. Check everything:

   ```bash
   cd backend
   uv run python check_setup.py
   ```

   This makes one real request to each service and prints OK / WARN / FAIL.

4. Restart the backend.

### Chat model

Set `LLM_PROVIDER` to `gemini`, `ollama` or `openai`. If you leave it empty the
first one that is configured gets used.

Gemini: get a key at https://aistudio.google.com/apikey and pick a model from
https://ai.google.dev/gemini-api/docs/models.

```env
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.5-flash
```

If replies come back empty, the model probably used its token budget on
"thinking". Increase `LLM_MAX_TOKENS` or set `GEMINI_THINKING_BUDGET=0`.

Ollama runs locally for free:

```bash
ollama pull llama3.2
```

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

Any OpenAI-compatible API works with `LLM_BASE_URL`, `LLM_API_KEY` and
`LLM_MODEL`.

### Google Earth Engine

Earth Engine is free for non-commercial use. It needs a Google Cloud project
that is registered for Earth Engine.

1. Create a project in the [Google Cloud console](https://console.cloud.google.com/)
   and note the project ID (not the display name).
2. Enable the [Earth Engine API](https://console.cloud.google.com/apis/library/earthengine.googleapis.com)
   for it.
3. Register the project at https://code.earthengine.google.com/register
   (choose non-commercial use).
4. Put the ID in `backend/.env`:

   ```env
   PROJECT_ID=your-project-id
   ```

5. Log in once:

   ```bash
   cd backend
   uv run earthengine authenticate
   ```

   This saves credentials in `~/.config/earthengine/` (on Windows
   `%USERPROFILE%\.config\earthengine\`). If the browser login doesn't work,
   try `--auth_mode=notebook`.

To test it:

```bash
uv run python check_setup.py        # quick check
uv run python sattelite_report.py   # full report for the demo farm, takes a minute or two
```

After that, logging in generates a new report (for the demo farm log in with
`demo@annapoorna.local`).

On a server or in Docker, use a service account instead of the browser login:
create one under IAM & Admin > Service Accounts, give it the Earth Engine
Resource Viewer and Service Usage Consumer roles, download a JSON key into
`backend/secrets/` (ignored by git) and set:

```env
GEE_SERVICE_ACCOUNT_KEY=secrets/gee-service-account.json
# in docker compose:
# GEE_SERVICE_ACCOUNT_KEY=/run/secrets/gee/gee-service-account.json
```

### Environment variables

All settings are in [backend/.env.example](backend/.env.example) and
[website/.env.example](website/.env.example). The main ones:

| Variable | Used for |
| --- | --- |
| `MONGODB_URI` | database |
| `LLM_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL` | chat |
| `OLLAMA_MODEL`, `OLLAMA_BASE_URL` | chat with Ollama |
| `PROJECT_ID`, `GEE_SERVICE_ACCOUNT_KEY` | satellite data |
| `TOMORROW_API_KEY` | weather (optional) |
| `WHISPER_MODEL_SIZE` | voice input, `base` is fast, `medium` is more accurate |
| `CORS_ALLOW_ORIGINS` | frontend URL(s) allowed to call the API |
| `GEOCODE_API_KEY` | frontend, optional |
| `NEXT_PUBLIC_API_BASE_URL` | frontend, backend URL (set before `npm run build`) |

## The model

A CNN trained from scratch in
[notebooks/crop-disease-cnn-train.ipynb](notebooks/crop-disease-cnn-train.ipynb).
The trained model is published as a
[release asset](https://github.com/V47VANSH/Annapoorna/releases/tag/model-v1)
(fetched by [backend/download_model.py](backend/download_model.py)) and inference is in [backend/predict.py](backend/predict.py).

```
Conv2D(32)  + BatchNorm + MaxPool
Conv2D(64)  + BatchNorm + MaxPool + Dropout(0.25)
Conv2D(128) + BatchNorm + MaxPool + Dropout(0.3)
Conv2D(256) + BatchNorm + MaxPool + Dropout(0.4)
Flatten + Dense(512) + Dropout(0.5) + Dense(42, softmax)
```

| | |
| --- | --- |
| Dataset | [20K Multi-Class Crop Disease Images](https://www.kaggle.com/datasets/jawadali1045/20k-multi-class-crop-disease-images) |
| Classes | 42 |
| Train / validation | 12,255 / 3,081 images |
| Input | 224x224 RGB, scaled to [0, 1] |
| Training | Adam (lr 1e-4), 25 epochs, 2x Tesla T4 |
| Validation accuracy | 71.7% |
| Validation loss | 4.02 |

The validation loss is high for that accuracy and the accuracy jumped around in
the last epochs, so the model is overconfident. The API returns the confidence
with every prediction and the advice warns when it's low. Fine-tuning a
pretrained network like EfficientNet would probably do a lot better.

You can run the model on images directly:

```bash
cd backend
uv run python predict.py leaf.jpg --top 3
```

The scripts in `data/` and `src/` download and merge four datasets into a
77-class dataset (20K Crop Disease, PlantVillage, PlantDoc, Mendeley). The
current model was only trained on the 20K dataset, retraining on the merged one
is the next step.

```bash
pip install -r requirements.txt
cd data && python data_download.py && cd ..
cd src && python merge.py && python augmentation.py && python datacleaning.py
```

## API

| Method | Path | |
| --- | --- | --- |
| GET | `/health` | status and which services are configured |
| GET | `/demo` | demo farmer id |
| POST | `/register`, `/login`, `/logout` | accounts |
| POST | `/predict` | image -> disease, confidence, advice |
| POST | `/chat` | message -> reply |
| POST | `/transcribe` | audio -> text |
| POST | `/setContext`, `/reset` | chat context |
| GET | `/profile/{id}` | profile |
| GET | `/allReports/{id}`, `/latestReport/{id}` | reports |
| GET | `/allChats/{id}`, `/chatById/{id}` | chat history |

## Tests

```bash
cd backend
uv run pytest tests -q
uv run ruff check .
```

The tests run with `OFFLINE_MODE=true`, so they don't need the model file or
network access.

## Project structure

```
backend/
  main.py               API routes
  config.py             settings from env
  chatbot.py            chat (Gemini / Ollama / OpenAI-compatible)
  offline_advice.py     advice when no LLM is configured
  predict.py            disease model
  sattelite_report.py   Earth Engine analysis
  weather.py            weather
  whisper_transcribe.py voice input
  database.py           MongoDB
  memory_store.py       in-memory fallback for MongoDB
  check_setup.py        checks the configured services
  tests/
website/                Next.js frontend
data/, src/             dataset download and preprocessing
notebooks/              model training
docs/                   metrics and project card
```

## Known issues

- There is no real authentication yet. Login only checks the email and the
  endpoints take the user id from the URL, so this shouldn't be deployed
  publicly with real data until proper auth (passwords + JWT) is added.
- The model's accuracy (71.7%) isn't good enough to rely on without checking.
- Scheduled report jobs and chat history are kept in memory, so they're lost on
  restart and won't work with multiple workers.
- The field is the bounding box of the address, not the actual field boundary.

## Team

Team 7A, Annam.ai x IIT Ropar: Vansh Bansal, Abhipsit, Ayush Anand, Peehu.

Datasets: [20K Multi-Class Crop Disease](https://www.kaggle.com/datasets/jawadali1045/20k-multi-class-crop-disease-images),
[PlantVillage](https://www.kaggle.com/datasets/emmarex/plantdisease),
[PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset),
[Mendeley plant leaf dataset](https://data.mendeley.com/datasets/tywbtsjrjv/1)

## License

[MIT](LICENSE)
