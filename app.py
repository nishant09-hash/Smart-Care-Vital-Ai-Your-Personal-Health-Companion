from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb
from MySQLdb.cursors import DictCursor
from werkzeug.security import generate_password_hash, check_password_hash
import google.genai as genai
from dotenv import load_dotenv
import re
import logging
import os
import time
from functools import wraps

# Load environment variables
load_dotenv()

# Get the absolute path to the templates and static directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR, static_url_path='/static')
CORS(app, 
     resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}},
     supports_credentials=True)

# ================= LOGGING CONFIG =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.secret_key = "smartcare_secret_key"

# ================= DATABASE CONFIG =================
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', '3306'))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'smartcare_db')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_AUTOCOMMIT'] = False
app.config['MYSQL_CONNECT_TIMEOUT'] = 5

mysql = MySQL(app)

_db_initialized = False
_db_error = None
_connection_attempts = 0
_max_connection_attempts = 3


def bootstrap_database_from_sql():
    """Create/initialize database from database/smartcare_db.sql."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(base_dir, 'database', 'smartcare_db.sql')

    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"SQL initialization file not found: {sql_path}")

    setup_conn = MySQLdb.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        passwd=app.config['MYSQL_PASSWORD'],
        port=app.config['MYSQL_PORT'],
        connect_timeout=app.config['MYSQL_CONNECT_TIMEOUT'],
    )

    setup_cursor = None
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        setup_cursor = setup_conn.cursor()
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement:
                setup_cursor.execute(statement)

        setup_conn.commit()
        logger.info("✅ Database bootstrap completed from smartcare_db.sql")
    finally:
        try:
            if setup_cursor:
                setup_cursor.close()
            setup_conn.close()
        except Exception:
            pass


def create_direct_db_connection():
    """Create a direct MySQLdb connection (reliable with XAMPP/MariaDB)."""
    return MySQLdb.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        passwd=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        port=app.config['MYSQL_PORT'],
        connect_timeout=app.config['MYSQL_CONNECT_TIMEOUT'],
        cursorclass=DictCursor,
    )

def check_and_init_db():
    """Check if database is accessible and initialize if needed"""
    global _db_initialized, _db_error, _connection_attempts
    
    if _db_initialized:
        return True
    
    _connection_attempts += 1
    
    try:
        logger.info(f"🔄 Database connection attempt #{_connection_attempts}...")
        conn = create_direct_db_connection()
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database connection successful!")
        _db_initialized = True
        _db_error = None
        return True
        
    except Exception as e:
        _db_error = str(e)
        logger.error(f"❌ Database connection failed (Attempt {_connection_attempts}): {str(e)}")

        # Auto-heal first-run setup when DB does not exist yet.
        mysql_error_code = e.args[0] if getattr(e, 'args', None) else None
        if mysql_error_code == 1049:
            try:
                logger.warning("Database does not exist. Attempting automatic bootstrap...")
                bootstrap_database_from_sql()

                conn = create_direct_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()

                _db_initialized = True
                _db_error = None
                logger.info("✅ Database connection successful after bootstrap")
                return True
            except Exception as bootstrap_err:
                _db_error = f"{str(e)} | bootstrap failed: {str(bootstrap_err)}"
                logger.error(f"❌ Automatic database bootstrap failed: {str(bootstrap_err)}")
        
        if _connection_attempts == 1:
            logger.error("=" * 70)
            logger.error("🔧 CRITICAL: DATABASE CONNECTION FAILED")
            logger.error("=" * 70)
            logger.error("SOLUTIONS:")
            logger.error("")
            logger.error("1️⃣  START MYSQL SERVER:")
            logger.error("   Option A: XAMPP Control Panel → Start MySQL")
            logger.error("   Option B: Open Services → Start MySQL service")
            logger.error("")
            logger.error("2️⃣  VERIFY DATABASE EXISTS:")
            logger.error("   mysql -u root")
            logger.error("   SHOW DATABASES;")
            logger.error("   USE smartcare_db;")
            logger.error("   SHOW TABLES;")
            logger.error("")
            logger.error("3️⃣  CREATE DATABASE IF NOT EXISTS:")
            logger.error("   mysql -u root")
            logger.error("   CREATE DATABASE smartcare_db;")
            logger.error("   USE smartcare_db;")
            logger.error("   CREATE TABLE users (")
            logger.error("     user_id INT AUTO_INCREMENT PRIMARY KEY,")
            logger.error("     name VARCHAR(255) NOT NULL,")
            logger.error("     email VARCHAR(255) UNIQUE NOT NULL,")
            logger.error("     password VARCHAR(255) NOT NULL,")
            logger.error("     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            logger.error("   );")
            logger.error("")
            logger.error("4️⃣  TEST CONNECTION:")
            logger.error("   Visit: http://127.0.0.1:5000/test_db")
            logger.error("   If XAMPP uses a custom port, set MYSQL_PORT in .env")
            logger.error("")
            logger.error("=" * 70)
        
        return False

def get_db_connection():
    """Get database connection with detailed error handling"""
    global _db_error
    try:
        return create_direct_db_connection()
    except Exception as e:
        _db_error = str(e)
        logger.error(f"❌ Cannot get DB connection: {str(e)}")
        raise

# ================= GEMINI API CONFIG =================
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables. Chatbot will not work.")
    client = None
else:
    # Initialize Gemini client with new API
    client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_PRIMARY_MODEL = os.getenv('GEMINI_PRIMARY_MODEL', 'gemini-2.5-flash')
GEMINI_FALLBACK_MODEL = os.getenv('GEMINI_FALLBACK_MODEL', 'gemini-2.0-flash')
GEMINI_MODELS = [model for model in [GEMINI_PRIMARY_MODEL, GEMINI_FALLBACK_MODEL] if model]
GEMINI_MAX_RETRIES = int(os.getenv('GEMINI_MAX_RETRIES', '2'))
GEMINI_RETRY_DELAY_SECONDS = float(os.getenv('GEMINI_RETRY_DELAY_SECONDS', '1.0'))


def generate_gemini_response(conversation):
    """Generate chatbot response with retry and model fallback for transient API failures."""
    last_error = None

    for model_name in GEMINI_MODELS:
        for attempt in range(GEMINI_MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=conversation
                )
                response_text = getattr(response, 'text', None)

                if response_text and response_text.strip():
                    return response_text

                raise ValueError("Gemini returned an empty response")
            except Exception as api_err:
                last_error = api_err
                err_text = str(api_err).upper()
                is_transient = any(token in err_text for token in [
                    '503', 'UNAVAILABLE', '429', 'RATE', 'RESOURCE_EXHAUSTED', 'TIMEOUT'
                ])
                has_more_attempts = attempt < GEMINI_MAX_RETRIES

                if is_transient and has_more_attempts:
                    sleep_seconds = GEMINI_RETRY_DELAY_SECONDS * (attempt + 1)
                    logger.warning(
                        f"Transient Gemini error on model {model_name} (attempt {attempt + 1}/{GEMINI_MAX_RETRIES + 1}): {str(api_err)}. "
                        f"Retrying in {sleep_seconds:.1f}s"
                    )
                    time.sleep(sleep_seconds)
                    continue

                logger.error(
                    f"Gemini error on model {model_name} (attempt {attempt + 1}/{GEMINI_MAX_RETRIES + 1}): {str(api_err)}"
                )
                break

    if last_error:
        raise last_error
    raise RuntimeError("Gemini response generation failed")


def generate_local_fallback_response(user_message):
    """Return a useful local response when external AI is unavailable."""
    msg = user_message.lower()

    if any(greet in msg for greet in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return (
            "Hi! The AI service is temporarily unavailable, but I can still help.\n\n"
            "You can ask me for:\n"
            "- Weight gain diet plan\n"
            "- Fat loss diet plan\n"
            "- BMI guidance\n"
            "- Basic workout routine"
        )

    if 'weight gain' in msg or ('gain' in msg and 'weight' in msg):
        return (
            "The AI service is busy, so here is a practical 1-day weight-gain starter plan:\n\n"
            "1. Early morning: 1 banana + 5 soaked almonds + milk\n"
            "2. Breakfast: 3-egg omelet (or paneer bhurji) + 2 whole wheat toasts + peanut butter\n"
            "3. Mid-morning snack: smoothie (milk + oats + banana + peanut butter)\n"
            "4. Lunch: 2 cups rice + dal/chicken + 1 cup curd + vegetables\n"
            "5. Evening snack: roasted chana or nuts + fruit + lassi\n"
            "6. Dinner: 2-3 rotis + paneer/chicken/fish + veggies + salad\n"
            "7. Bedtime: warm milk + 1 tbsp seeds/nut mix\n\n"
            "Tips: target calorie surplus, add protein in each meal, and do strength training 3-4 days/week.\n"
            "If you share your age, height, weight, and food preference, I can tailor this exactly for you."
        )

    if 'workout' in msg or 'exercise' in msg or 'training plan' in msg or 'gym plan' in msg:
        if '4 day' in msg or '4-day' in msg or '4 days' in msg:
            return (
                "The AI service is busy, so here is a practical 4-day workout starter plan:\n\n"
                "Day 1 (Upper Body Push):\n"
                "- Push-ups: 4 x 10-15\n"
                "- Dumbbell/Barbell bench press: 4 x 8-12\n"
                "- Shoulder press: 3 x 10\n"
                "- Triceps dips/pushdowns: 3 x 12\n\n"
                "Day 2 (Lower Body):\n"
                "- Squats: 4 x 8-12\n"
                "- Lunges: 3 x 10 each leg\n"
                "- Romanian deadlift: 3 x 10\n"
                "- Calf raises: 3 x 15\n\n"
                "Day 3 (Rest or light walk/mobility): 20-30 min\n\n"
                "Day 4 (Upper Body Pull):\n"
                "- Pull-ups/lat pulldown: 4 x 8-12\n"
                "- Rows: 4 x 10\n"
                "- Face pulls: 3 x 12\n"
                "- Biceps curls: 3 x 12\n\n"
                "Day 5 (Full Body + Core):\n"
                "- Deadlift (light/moderate): 3 x 6-8\n"
                "- Incline press: 3 x 10\n"
                "- Plank: 3 x 45-60 sec\n"
                "- Bicycle crunches: 3 x 20\n\n"
                "Progression: increase weight/reps slightly each week and keep 1-2 rest days."
            )

        return (
            "The AI service is busy, but here is a simple weekly workout structure:\n"
            "- 3-4 strength days (push, pull, legs, full body)\n"
            "- 2 cardio days (20-30 min brisk walk/cycle)\n"
            "- 1 full rest day\n\n"
            "Tell me your goal (muscle gain, fat loss, or fitness), and I will give a day-by-day plan."
        )

    if 'bmi' in msg or 'body mass index' in msg:
        return (
            "BMI means Body Mass Index. It estimates weight category using height and weight.\n\n"
            "Formula:\n"
            "BMI = weight (kg) / [height (m)]^2\n\n"
            "BMI ranges (adults):\n"
            "- Below 18.5: Underweight\n"
            "- 18.5 to 24.9: Normal\n"
            "- 25 to 29.9: Overweight\n"
            "- 30 and above: Obesity\n\n"
            "Share your height and weight, and I will calculate your BMI for you."
        )

    if 'fat loss' in msg or 'weight loss' in msg:
        return (
            "The AI service is busy, so here is a simple fat-loss starter plan:\n\n"
            "1. Breakfast: oats + boiled eggs/sprouts + fruit\n"
            "2. Lunch: 1-2 rotis + dal/chicken + large salad\n"
            "3. Snack: buttermilk + handful of nuts\n"
            "4. Dinner: grilled paneer/chicken/fish + sauteed vegetables\n\n"
            "Daily habits: 8-10k steps, avoid sugary drinks, and keep dinner light."
        )

    if 'diet plan' in msg or 'meal plan' in msg:
        return (
            "The AI service is busy right now, but I can still help with a starter meal plan.\n"
            "Tell me your goal (weight gain, fat loss, or maintenance), and share age, height, weight, and veg/non-veg preference."
        )

    return (
        "The AI service is busy at the moment due to quota/high demand.\n"
        "I can still provide basic health guidance if you ask a specific question about diet, workout, BMI, or wellness."
    )

# System prompt for the chatbot
SYSTEM_PROMPT = """You are a helpful health and diet assistant for SmartCare, a health and wellness platform. 
Your role is to provide advice and information ONLY about:
- Diet and nutrition
- Health and wellness
- Fitness and exercise
- BMI and weight management
- Healthy eating habits
- Meal planning
- Nutritional information
- General health tips

IMPORTANT INSTRUCTIONS FOR DETAILED PLANS:
When a user asks for a diet plan, meal plan, workout plan, or any detailed recommendation:
1. DO NOT block the answer with many questions.
2. If the user gives at least basic details (for example weight/height or a clear goal like fat loss), provide a SIMPLE, ACTIONABLE starter plan immediately.
3. Assume a balanced non-extreme diet if preferences/allergies are not provided.
4. Add a short safety note like: "If you have allergies, medical conditions, or specific dietary preferences, tell me and I'll adjust this plan."
5. Ask at most ONE optional follow-up question after giving the initial plan.
6. If the user asks for a detailed personalized version, then provide a DETAILED, TIME-SPECIFIC plan with:
   - Specific meal times (e.g., 7:00 AM, 10:00 AM, 1:00 PM, etc.)
   - Exact food items with portions
   - Nutritional benefits of each meal
   - Hydration reminders
   - Snack options between meals

For simple fat-loss queries (examples: "give me diet plan for fat loss" and "height 189 cm, weight 100 kg"):
- Give a direct 1-day sample plan (breakfast, lunch, snack, dinner)
- Include simple portion guidance and hydration target
- Include 2-3 practical habits for fat loss
- Keep tone concise and supportive

EXAMPLE FORMAT for meal plans:
🌅 Early Morning (6:30 AM):
- Warm water with lemon (1 glass)
- Benefits: Aids digestion, boosts metabolism

🍳 Breakfast (8:00 AM):
- Oatmeal with fruits and nuts (1 bowl)
- Green tea (1 cup)
- Benefits: Provides energy, rich in fiber

[Continue with Mid-Morning Snack, Lunch, Evening Snack, Dinner, etc.]

Always be conversational and ask follow-up questions when needed. Make your responses detailed, structured, and easy to follow.
If a user asks about anything outside health/diet topics, politely decline and redirect them to health and diet-related questions.
Always prioritize user safety and recommend consulting healthcare professionals for serious medical concerns."""

# ================= VALIDATION FUNCTIONS =================
def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """Validate password - min 6 chars"""
    return len(password) >= 6

def is_valid_name(name):
    """Validate name - at least 2 characters, no special chars"""
    return len(name.strip()) >= 2 and name.isalpha() or ' ' in name


def login_required(route_func):
    """Require user session for protected pages/API routes."""
    @wraps(route_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return route_func(*args, **kwargs)
    return wrapper

# ================= PAGES =================
@app.route("/")
def main_page():
    """Main dashboard"""
    return render_template("main.html")

@app.route("/login")
def login_page():
    """Serve login page"""
    # Don't redirect - let them see the login page
    return render_template("login.html")

@app.route("/register")
def register_page():
    """Serve registration page"""
    # Don't redirect - let them see the registration page
    return render_template("register.html")

@app.route("/about")
def about_page():
    """About page"""
    return render_template("about.html")

@app.route("/blog")
def blog_page():
    """Legacy blog route; keep users on homepage blog cards."""
    return redirect(url_for('main_page') + '#health-blogs')

@app.route("/blogs/<blog_name>")
def blog_detail(blog_name):
    """Individual blog posts"""
    try:
        return render_template(f"Blogs/{blog_name}.html")
    except:
        return render_template("blog.html")

@app.route("/goals/<goal_name>")
def goal_page(goal_name):
    """Goal detail pages"""
    try:
        return render_template(f"Blogs/goals/{goal_name}.html")
    except:
        return render_template("main.html")

@app.route("/diet")
@login_required
def diet_page():
    """Diet recommendation page"""
    return render_template("diet.html")

@app.route("/chatbot")
@login_required
def chatbot_page():
    """Chatbot page"""
    return render_template("chatbot.html")

@app.route("/admin/messages")
def admin_messages_page():
    """Simple admin panel to view contact messages."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT contact_id, name, email, subject, message, sent_at
            FROM contact_messages
            ORDER BY sent_at DESC
            """
        )
        messages = cursor.fetchall() or []
        return render_template("admin_messages.html", messages=messages)
    except Exception as e:
        logger.error(f"Admin messages error: {str(e)}")
        return jsonify({"error": "Unable to load contact messages"}), 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass


@app.route("/admin/users")
def admin_users_page():
    """Simple admin panel to view registered users."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, name, email, created_at
            FROM users
            ORDER BY created_at DESC
            """
        )
        users = cursor.fetchall() or []
        return render_template("admin_users.html", users=users)
    except Exception as e:
        logger.error(f"Admin users error: {str(e)}")
        return jsonify({"error": "Unable to load users"}), 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass

# ================= REGISTER API =================
@app.route("/api/register", methods=["POST", "OPTIONS"])
def register():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    try:
        logger.info(f"Registration request received")
        
        # Check content type
        if not request.is_json:
            logger.error(f"Invalid content type: {request.content_type}")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        try:
            data = request.get_json(force=True, silent=False)
            logger.info(f"JSON parsed successfully: {list(data.keys()) if data else 'empty'}")
        except Exception as json_err:
            logger.error(f"JSON parsing error: {str(json_err)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        logger.info(f"Attempting registration for: {email}")

        # ================= VALIDATION =================
        if not name or not email or not password:
            logger.warning(f"Missing fields - Name: {bool(name)}, Email: {bool(email)}, Password: {bool(password)}")
            return jsonify({"error": "All fields are required"}), 400

        if len(name) < 2:
            return jsonify({"error": "Name must be at least 2 characters"}), 400

        if not is_valid_email(email):
            logger.warning(f"Invalid email format: {email}")
            return jsonify({"error": "Invalid email format"}), 400

        if not is_valid_password(password):
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # ================= DATABASE OPERATIONS =================
        cursor = None
        conn = None
        try:
            logger.info(f"Checking database connection for registration...")
            
            # Force database check
            if not check_and_init_db():
                logger.error(f"❌ Cannot register - Database not connected")
                return jsonify({
                    "error": "Database connection failed. Ensure MySQL is running and smartcare_db is initialized.",
                    "details": _db_error,
                    "help": "If this is first run, initialize DB with database/init_db.py or allow auto-bootstrap from smartcare_db.sql"
                }), 503
            
            logger.info(f"✅ Database is connected, proceeding with registration")
            conn = get_db_connection()
            cursor = conn.cursor()
            logger.info("✅ Database cursor created")

            # Check if email already exists
            logger.info(f"Checking if email exists: {email}")
            cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.close()
                logger.warning(f"Email already registered: {email}")
                return jsonify({"error": "Email already registered. Please login or use a different email"}), 409

            # Hash password and insert user
            hashed_password = generate_password_hash(password)
            logger.info("Password hashed")

            logger.info(f"Inserting user into database: {email}")
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                (name, email, hashed_password)
            )
            conn.commit()
            new_user_id = cursor.lastrowid
            cursor.close()

            logger.info(f"✅✅✅ USER REGISTERED: {email} (ID: {new_user_id})")

            return jsonify({
                "message": "Registration successful! Redirecting to login...",
                "userId": new_user_id,
                "redirect": "/login"
            }), 201

        except Exception as db_err:
            logger.error(f"❌ Database operation failed: {str(db_err)}")
            logger.error(f"Error type: {type(db_err).__name__}")
            
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.rollback()
            except:
                pass
            
            return jsonify({
                "error": f"Database error: {str(db_err)}",
                "help": "Check Flask console logs for details"
            }), 500

    except Exception as e:
        logger.error(f"❌ Register Error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ================= CONTACT API =================
@app.route("/contact", methods=["POST"])
def save_contact_message():
    """Save contact form messages into contact_messages table."""
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) if request.is_json else request.form

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        subject = (data.get("subject") or "").strip()
        message = (data.get("message") or "").strip()

        if not name or not email or not subject or not message:
            return jsonify({"error": "All fields are required"}), 400

        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO contact_messages (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, subject, message)
        )
        conn.commit()

        return jsonify({"message": "Message sent successfully"}), 201
    except Exception as e:
        logger.error(f"Contact form save error: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({"error": "Unable to save message right now"}), 500
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass

# ================= LOGIN API =================
@app.route("/api/login", methods=["POST"])
def login():
    try:
        # Check content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        # ================= VALIDATION =================
        if not email or not password:
            logger.warning("Login attempt with missing email or password")
            return jsonify({"error": "Email and password are required"}), 400

        # Validate email format
        if not is_valid_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        # ================= DATABASE OPERATIONS =================
        cursor = None
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, name, password FROM users WHERE email=%s",
                (email,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Check if user exists and password is correct
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return jsonify({"error": "Invalid email or password"}), 401

            # Verify password hash
            stored_password = user["password"] if isinstance(user, dict) else user[2]
            if not check_password_hash(stored_password, password):
                logger.warning(f"Failed login attempt for user: {email}")
                return jsonify({"error": "Invalid email or password"}), 401

            # ✅ SET SESSION
            session['user_id'] = user["user_id"] if isinstance(user, dict) else user[0]
            session['user_name'] = user["name"] if isinstance(user, dict) else user[1]
            session.permanent = False  # Session expires when browser closes

            logger.info(f"Successful login for user: {email}")

            return jsonify({
                "message": "Login successful",
                "userName": user["name"] if isinstance(user, dict) else user[1],
                "userId": user["user_id"] if isinstance(user, dict) else user[0]
            }), 200

        except Exception as db_err:
            logger.error(f"Database error during login: {str(db_err)}")
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception:
                pass
            return jsonify({"error": "Database error. Please try again"}), 500

    except Exception as e:
        logger.error(f"Login Error: {str(e)}")
        return jsonify({"error": "Server error. Please try again"}), 500

# ================= LOGOUT ROUTE =================
@app.route("/logout")
def logout():
    session.clear()
    logger.info("User logged out")
    return redirect(url_for('login_page'))

# ================= CHATBOT API =================
@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chatbot messages"""
    try:
        # Check if API key is configured
        if not client:
            return jsonify({"error": "Chatbot is not configured. Please contact administrator."}), 503

        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({"error": "Please login to use the chatbot"}), 401

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Initialize chat history in session if it doesn't exist
        if 'chat_history' not in session:
            session['chat_history'] = []

        # Check if message is health/diet related
        health_keywords = [
            'diet', 'health', 'fitness', 'exercise', 'nutrition', 'food', 'meal',
            'weight', 'bmi', 'calorie', 'protein', 'carb', 'fat', 'vitamin',
            'wellness', 'workout', 'yoga', 'cardio', 'muscle', 'body', 'eating',
            'vegetable', 'fruit', 'water', 'sleep', 'stress', 'mental', 'physical'
        ]

        # Check if the message contains any health-related keywords
        message_lower = user_message.lower()
        is_health_related = any(keyword in message_lower for keyword in health_keywords)

        # If not health-related and doesn't look like a greeting, refuse politely
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        is_greeting = any(greeting in message_lower for greeting in greetings)

        if not is_health_related and not is_greeting and len(user_message) > 10:
            return jsonify({
                "response": "I'm sorry, but I can only help with health and diet-related questions. Please ask me about nutrition, fitness, diet plans, health tips, or wellness advice!"
            }), 200

        # Build conversation context with history
        conversation = f"{SYSTEM_PROMPT}\n\n"
        
        # Add previous conversation history (keep last 10 exchanges to avoid token limits)
        chat_history = session['chat_history'][-10:]  # Last 10 exchanges
        for exchange in chat_history:
            conversation += f"User: {exchange['user']}\nAssistant: {exchange['bot']}\n\n"
        
        # Add current message
        conversation += f"User: {user_message}\n\nAssistant:"

        # Generate response using Gemini
        try:
            bot_response = generate_gemini_response(conversation)
        except Exception as api_err:
            logger.error(f"Gemini API error: {str(api_err)}")
            bot_response = generate_local_fallback_response(user_message)
            logger.warning("Serving local fallback response due to Gemini unavailability")

            session['chat_history'].append({
                'user': user_message,
                'bot': bot_response
            })
            session.modified = True

            return jsonify({
                "response": bot_response,
                "fallback": True
            }), 200

        # Save this exchange to chat history
        session['chat_history'].append({
            'user': user_message,
            'bot': bot_response
        })
        session.modified = True  # Ensure session is saved

        logger.info(f"Chat message from user {session['user_id']}: {user_message[:50]}...")

        return jsonify({
            "response": bot_response
        }), 200

    except Exception as e:
        logger.error(f"Chat Error: {str(e)}")
        return jsonify({"error": "Server error. Please try again"}), 500

@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    """Clear chat history"""
    try:
        if 'user_id' not in session:
            return jsonify({"error": "Please login to use the chatbot"}), 401
        
        session['chat_history'] = []
        session.modified = True
        
        return jsonify({"message": "Chat history cleared"}), 200
    except Exception as e:
        logger.error(f"Clear chat error: {str(e)}")
        return jsonify({"error": "Server error"}), 500

# ================= DB TEST =================
@app.route("/test_db")
def test_db():
    """Test database connection"""
    try:
        logger.info("Testing database connection...")
        # Force check
        check_and_init_db()
        
        if not _db_initialized:
            logger.error(f"DB init failed: {_db_error}")
            return jsonify({
                "error": "❌ Database NOT connected",
                "details": _db_error,
                "help": "Start MySQL server and ensure smartcare_db exists with 'users' table"
            }), 500
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database connection test successful")
        return jsonify({"status": "✅ Database connected successfully"}), 200
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return jsonify({
            "error": f"Database connection failed: {str(e)}",
            "steps": [
                "1. Start MySQL from XAMPP Control Panel",
                "2. Run this SQL: CREATE DATABASE smartcare_db;",
                "3. Run this SQL: CREATE TABLE users (user_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255) UNIQUE, password VARCHAR(255), created_at TIMESTAMP)",
                "4. If XAMPP uses port other than 3306, set MYSQL_PORT in .env"
            ]
        }), 500

# ================= ERROR HANDLERS =================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

@app.before_request
def before_request():
    """Initialize DB and add security headers"""
    # Initialize database on first request
    check_and_init_db()
    
    # Validate JSON content type for API endpoints
    if request.path.startswith('/api/') and request.method in ['POST', 'PUT']:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

@app.after_request
def after_request(response):
    """Add security headers to response"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
