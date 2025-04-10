# portfolio

This template should help get you started developing with Vue 3 in Vite.

## Recommended IDE Setup

[VSCode](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```

## Backend (FastAPI + Gemini)

This project includes a FastAPI backend to interact with Google's Gemini AI models and Pinecone for vector storage.

### Backend Setup

1.  Navigate to the backend directory:

    ```bash
    cd backend
    ```

2.  Install Python dependencies (preferably in a virtual environment):

    ```bash
    pip install -r requirements.txt
    ```

3.  Set up your environment variables:

    - Create a `.env` file in the `backend` directory by copying `.env.example`.
    - Get a Google API key from [Google AI Studio](https://ai.google.dev/).
    - Get a Pinecone API key and environment name from [Pinecone](https://www.pinecone.io/).
    - Add your keys and environment name to the `.env` file:

      ```
      # Gemini API key from Google AI Studio
      GOOGLE_API_KEY=your_google_api_key_here

      # Pinecone API key and environment
      PINECONE_API_KEY=your_pinecone_api_key_here
      PINECONE_ENVIRONMENT=your_pinecone_environment_here
      ```

4.  Run the FastAPI server:
    ```bash
    uvicorn app:app --reload
    ```
    The server will start at http://localhost:8000.

### Backend API Endpoints

- `GET /`: Health check endpoint
- `POST /api/chat`: Chat with Gemini AI
  - Request body:
    ```json
    {
      "message": "Your message here",
      "context": "Optional project context"
    }
    ```
  - Response:
    ```json
    {
      "success": true,
      "response": "AI response here"
    }
    ```

### Backend Documentation

- API documentation is available at http://localhost:8000/docs when the server is running.
