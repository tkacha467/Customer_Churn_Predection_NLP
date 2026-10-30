# Digital Business Card

Independent frontend application for the Digital Business Card product.

## Structure

```text
Digital_Card/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DigitalCard.jsx        # Public business card view
│   │   │   └── DigitalCardEditor.jsx  # Owner card customization & PDF document manager
│   │   ├── lib/
│   │   │   └── api.js                 # API client connecting to Backend
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── assets/
├── clients/
│   ├── nasta-ghar/
│   │   └── brand.json
│   └── README.md
└── README.md
```

## Running Digital Card Frontend

```bash
cd Digital_Card/frontend
npm run dev
# Running on http://127.0.0.1:5174
```

Connects to the shared backend on port 8000 via `/api` proxy.
All authentication, authorization, and document storage are enforced by the shared backend.
