# Smart-Care-Vital-Ai-Your-Personal-Health-Companion

SmartCare: Vital AI is a responsive personal health companion web app built with HTML, CSS, JavaScript, Bootstrap, PHP, and MySQL.

## Features

- Goal categories with dedicated pages:
  - Fat Burning (`/fat-burning.php`)
  - Cardio (`/cardio.php`)
  - Yoga (`/yoga.php`)
  - Weight Loss (`/weight-loss.php`)
- Card-based responsive UI with suggested workout plans, routines, and health tips
- Goal tracking form that stores records in MySQL
- AI chatbot endpoint backed by OpenAI Chat Completions API for personalized guidance

## Local setup

1. Configure environment variables:
   - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   - `OPENAI_API_KEY` (optional; chatbot falls back to basic guidance if unset)
2. Apply MySQL schema from `/db/schema.sql`.
3. Start PHP server:

```bash
php -S localhost:8000
```

4. Open `http://localhost:8000/index.php`.
