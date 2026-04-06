from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db_config import get_connection
import hashlib

app = Flask(__name__)
app.secret_key = "hospitalfinder_secret_key"


# ================================================
# HELPER - PASSWORD HASH
# ================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ================================================
# TEST DATABASE CONNECTION
# ================================================
@app.route('/test')
def test_db():
    try:
        conn = get_connection()
        if conn.is_connected():
            conn.close()
            return "✅ Database Connected Successfully!"
    except Exception as e:
        return f"❌ Connection Failed: {str(e)}"


# ================================================
# HOME PAGE
# ================================================
@app.route('/')
def home():
    return render_template('home.html')


# ================================================
# USER SIGN UP
# ================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        phone    = request.form['phone']
        password = hash_password(request.form['password'])
        city     = request.form['city']
        area     = request.form['area']
        address  = request.form['address']
        pincode  = request.form['pincode']

        conn   = get_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for('signup'))

        # Insert new user
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, city, area, address, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, password, city, area, address, pincode))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


# ================================================
# USER LOGIN
# ================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = hash_password(request.form['password'])

        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user_id']   = user['user_id']
            session['user_name'] = user['name']
            session['user_city'] = user['city']
            session['role']      = 'user'
            flash("Login successful! Welcome " + user['name'], "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


# ================================================
# USER LOGOUT
# ================================================
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))


# ================================================
# ADMIN LOGIN
# ================================================
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']

        conn   = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admins WHERE email = %s AND password = %s", (email, password))
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin:
            session['admin_id']   = admin['admin_id']
            session['admin_name'] = admin['name']
            session['role']       = 'admin'
            flash("Welcome Admin " + admin['name'], "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials.", "error")
            return redirect(url_for('admin_login'))

    return render_template('admin/admin_login.html')


# ================================================
# ADMIN LOGOUT
# ================================================
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Admin logged out successfully.", "success")
    return redirect(url_for('admin_login'))


# ================================================
# ADMIN DASHBOARD
# ================================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ------------------------------------------------
    # OVERVIEW STATS
    # ------------------------------------------------
    cursor.execute("SELECT COUNT(*) AS total_hospitals FROM hospitals")
    total_hospitals = cursor.fetchone()['total_hospitals']

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    cursor.execute("SELECT COUNT(*) AS total_reviews FROM reviews")
    total_reviews = cursor.fetchone()['total_reviews']

    cursor.execute("SELECT COUNT(*) AS total_saved FROM saved_hospitals")
    total_saved = cursor.fetchone()['total_saved']

    stats = {
        'total_hospitals' : total_hospitals,
        'total_users'     : total_users,
        'total_reviews'   : total_reviews,
        'total_saved'     : total_saved
    }

    # ------------------------------------------------
    # ALL USERS
    # ------------------------------------------------
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()

    # ------------------------------------------------
    # USERS PER CITY (for chart)
    # ------------------------------------------------
    cursor.execute("SELECT city, COUNT(*) AS total FROM users GROUP BY city ORDER BY total DESC")
    user_city_rows    = cursor.fetchall()
    user_city_labels  = [row['city'] for row in user_city_rows]
    user_city_data    = [row['total'] for row in user_city_rows]

    # ------------------------------------------------
    # MOST SAVED HOSPITALS
    # ------------------------------------------------
    cursor.execute("""
        SELECT hospitals.name, hospitals.city, COUNT(*) AS total_saves
        FROM saved_hospitals
        JOIN hospitals ON saved_hospitals.hospital_id = hospitals.hospital_id
        GROUP BY saved_hospitals.hospital_id
        ORDER BY total_saves DESC
        LIMIT 5
    """)
    most_saved             = cursor.fetchall()
    saved_hospital_labels  = [row['name'] for row in most_saved]
    saved_hospital_data    = [row['total_saves'] for row in most_saved]

    # ------------------------------------------------
    # MOST REVIEWED HOSPITALS
    # ------------------------------------------------
    cursor.execute("""
        SELECT hospitals.name, hospitals.city,
               COUNT(*) AS total_reviews,
               ROUND(AVG(reviews.rating), 1) AS avg_rating
        FROM reviews
        JOIN hospitals ON reviews.hospital_id = hospitals.hospital_id
        GROUP BY reviews.hospital_id
        ORDER BY total_reviews DESC
        LIMIT 5
    """)
    most_reviewed             = cursor.fetchall()
    reviewed_hospital_labels  = [row['name'] for row in most_reviewed]
    reviewed_hospital_data    = [row['total_reviews'] for row in most_reviewed]

    cursor.close()
    conn.close()

    return render_template('admin/admin_dashboard.html',
        stats                    = stats,
        users                    = users,
        most_saved               = most_saved,
        most_reviewed            = most_reviewed,
        user_city_labels         = user_city_labels,
        user_city_data           = user_city_data,
        saved_hospital_labels    = saved_hospital_labels,
        saved_hospital_data      = saved_hospital_data,
        reviewed_hospital_labels = reviewed_hospital_labels,
        reviewed_hospital_data   = reviewed_hospital_data
    )


# ================================================
# HOSPITAL LIST / SEARCH RESULTS PAGE
# ================================================
@app.route('/hospitals')
def hospital_list():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get search inputs
    search_query = request.args.get('q', '').strip()
    specialty    = request.args.get('specialty', '').strip()
    hosp_type    = request.args.get('type', '').strip()
    emergency    = request.args.get('emergency', '').strip()

    # ------------------------------------------------
    # Fetch specialties for category buttons
    # Only for logged in users
    # ------------------------------------------------
    specialties = []
    if session.get('role') == 'user':
        cursor.execute("SELECT * FROM specialties")
        specialties = cursor.fetchall()

    # ------------------------------------------------
    # TOP HOSPITALS
    # Major hospitals matching search / specialty
    # ------------------------------------------------
    top_query  = "SELECT * FROM hospitals WHERE 1=1"
    top_params = []

    if search_query:
        top_query += " AND (name LIKE %s OR city LIKE %s)"
        top_params.extend(['%' + search_query + '%', '%' + search_query + '%'])

    if specialty:
        top_query += " AND specialties LIKE %s"
        top_params.append('%' + specialty + '%')

    if hosp_type:
        top_query += " AND type = %s"
        top_params.append(hosp_type)

    if emergency == 'Yes':
        top_query += " AND emergency = 'Yes'"

    # Sort by rating for top hospitals
    top_query += " ORDER BY rating DESC LIMIT 10"

    cursor.execute(top_query, top_params)
    top_hospitals = cursor.fetchall()

    # ------------------------------------------------
    # NEARBY HOSPITALS
    # Only for logged in users filtered by registered city
    # ------------------------------------------------
    nearby_hospitals = []
    if session.get('role') == 'user':
        user_city     = session.get('user_city', '')
        nearby_query  = "SELECT * FROM hospitals WHERE city = %s"
        nearby_params = [user_city]

        if specialty:
            nearby_query += " AND specialties LIKE %s"
            nearby_params.append('%' + specialty + '%')

        if hosp_type:
            nearby_query += " AND type = %s"
            nearby_params.append(hosp_type)

        if emergency == 'Yes':
            nearby_query += " AND emergency = 'Yes'"

        nearby_query += " ORDER BY rating DESC"

        cursor.execute(nearby_query, nearby_params)
        nearby_hospitals = cursor.fetchall()

    # ------------------------------------------------
    # ALL HOSPITALS for map markers
    # Only for logged in users
    # ------------------------------------------------
    all_hospitals = []
    if session.get('role') == 'user':
        cursor.execute("""
            SELECT hospital_id, name, address, city,
                   latitude, longitude, emergency, rating
            FROM hospitals
        """)
        all_hospitals = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('hospital_list.html',
        specialties      = specialties,
        top_hospitals    = top_hospitals,
        nearby_hospitals = nearby_hospitals,
        all_hospitals    = all_hospitals,
        search_query     = search_query
    )


# ================================================
# EMERGENCY PAGE
# ================================================
@app.route('/emergency')
def emergency():
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM hospitals WHERE emergency = 'Yes' ORDER BY rating DESC")
    emergency_hospitals = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('hospital_list.html',
        specialties      = [],
        top_hospitals    = emergency_hospitals,
        nearby_hospitals = [],
        all_hospitals    = emergency_hospitals,
        search_query     = 'Emergency'
    )


# ================================================
# HOSPITAL DETAIL PAGE
# ================================================
@app.route('/hospital/<int:hospital_id>')
def hospital_detail(hospital_id):
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch hospital
    cursor.execute("SELECT * FROM hospitals WHERE hospital_id = %s", (hospital_id,))
    hospital = cursor.fetchone()

    if not hospital:
        flash("Hospital not found.", "error")
        cursor.close()
        conn.close()
        return redirect(url_for('hospital_list'))

    # Fetch reviews with user name
    cursor.execute("""
        SELECT reviews.*, users.name AS user_name
        FROM reviews
        JOIN users ON reviews.user_id = users.user_id
        WHERE reviews.hospital_id = %s
        ORDER BY reviews.created_at DESC
    """, (hospital_id,))
    reviews = cursor.fetchall()

    # Check if logged in user already reviewed
    already_reviewed = False
    if session.get('role') == 'user':
        cursor.execute("""
            SELECT * FROM reviews
            WHERE user_id = %s AND hospital_id = %s
        """, (session.get('user_id'), hospital_id))
        already_reviewed = cursor.fetchone() is not None

    # Fetch user phone for whatsapp
    user_phone = ''
    if session.get('role') == 'user':
        cursor.execute("SELECT phone FROM users WHERE user_id = %s", (session.get('user_id'),))
        user_data  = cursor.fetchone()
        user_phone = user_data['phone'] if user_data else ''
        session['user_phone'] = user_phone

    cursor.close()
    conn.close()

    return render_template('hospital_detail.html',
        hospital        = hospital,
        reviews         = reviews,
        already_reviewed = already_reviewed
    )


# ================================================
# SAVE HOSPITAL
# ================================================
@app.route('/hospital/<int:hospital_id>/save', methods=['POST'])
def save_hospital(hospital_id):
    if session.get('role') != 'user':
        flash("Please login to save hospitals.", "error")
        return redirect(url_for('login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if already saved
    cursor.execute("""
        SELECT * FROM saved_hospitals
        WHERE user_id = %s AND hospital_id = %s
    """, (session.get('user_id'), hospital_id))
    already_saved = cursor.fetchone()

    if already_saved:
        flash("Hospital already saved!", "error")
    else:
        cursor.execute("""
            INSERT INTO saved_hospitals (user_id, hospital_id)
            VALUES (%s, %s)
        """, (session.get('user_id'), hospital_id))
        conn.commit()
        flash("Hospital saved successfully!", "success")

    cursor.close()
    conn.close()

    return redirect(url_for('hospital_detail', hospital_id=hospital_id))


# ================================================
# SUBMIT REVIEW
# ================================================
@app.route('/hospital/<int:hospital_id>/review', methods=['POST'])
def submit_review(hospital_id):
    if session.get('role') != 'user':
        flash("Please login to submit a review.", "error")
        return redirect(url_for('login'))

    rating          = request.form['rating']
    cleanliness     = request.form['cleanliness']
    waiting_time    = request.form['waiting_time']
    service_quality = request.form['service_quality']
    comment         = request.form['comment']

    conn   = get_connection()
    cursor = conn.cursor()

    # Check if already reviewed
    cursor.execute("""
        SELECT * FROM reviews
        WHERE user_id = %s AND hospital_id = %s
    """, (session.get('user_id'), hospital_id))
    already_reviewed = cursor.fetchone()

    if already_reviewed:
        flash("You have already submitted a review for this hospital.", "error")
    else:
        cursor.execute("""
            INSERT INTO reviews (user_id, hospital_id, rating, cleanliness, waiting_time, service_quality, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (session.get('user_id'), hospital_id, rating, cleanliness, waiting_time, service_quality, comment))
        conn.commit()
        flash("Review submitted successfully! Thank you.", "success")

    cursor.close()
    conn.close()

    return redirect(url_for('hospital_detail', hospital_id=hospital_id))


# ================================================
# SAVED HOSPITALS PAGE
# ================================================
@app.route('/saved')
def saved_hospitals():
    if session.get('role') != 'user':
        flash("Please login to view saved hospitals.", "error")
        return redirect(url_for('login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch user phone for whatsapp
    cursor.execute("SELECT phone FROM users WHERE user_id = %s", (session.get('user_id'),))
    user_data = cursor.fetchone()
    if user_data:
        session['user_phone'] = user_data['phone']

    # Fetch saved hospitals
    cursor.execute("""
        SELECT hospitals.*
        FROM saved_hospitals
        JOIN hospitals ON saved_hospitals.hospital_id = hospitals.hospital_id
        WHERE saved_hospitals.user_id = %s
        ORDER BY saved_hospitals.saved_at DESC
    """, (session.get('user_id'),))
    saved = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('saved_hospitals.html', saved=saved)


# ================================================
# RUN APP
# ================================================
# ================================================
# REMOVE SAVED HOSPITAL
# ================================================
@app.route('/saved/remove/<int:hospital_id>', methods=['POST'])
def remove_saved_hospital(hospital_id):
    if session.get('role') != 'user':
        flash("Please login first.", "error")
        return redirect(url_for('login'))

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM saved_hospitals
        WHERE user_id = %s AND hospital_id = %s
    """, (session.get('user_id'), hospital_id))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Hospital removed from saved list.", "success")
    return redirect(url_for('saved_hospitals'))



# ================================================
# MANAGE HOSPITALS PAGE
# ================================================
@app.route('/admin/hospitals')
def manage_hospitals():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    search_query = request.args.get('q', '').strip()
    hosp_type    = request.args.get('type', '').strip()
    emergency    = request.args.get('emergency', '').strip()

    query  = "SELECT * FROM hospitals WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE %s OR city LIKE %s)"
        params.extend(['%' + search_query + '%', '%' + search_query + '%'])

    if hosp_type:
        query += " AND type = %s"
        params.append(hosp_type)

    if emergency:
        query += " AND emergency = %s"
        params.append(emergency)

    query += " ORDER BY hospital_id DESC"

    cursor.execute(query, params)
    hospitals = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/manage_hospitals.html', hospitals=hospitals)


# ================================================
# DELETE HOSPITAL
# ================================================
@app.route('/admin/hospital/delete/<int:hospital_id>', methods=['POST'])
def delete_hospital(hospital_id):
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM hospitals WHERE hospital_id = %s", (hospital_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Hospital deleted successfully.", "success")
    return redirect(url_for('manage_hospitals'))


# ================================================
# UPLOAD CSV
# ================================================
@app.route('/admin/hospitals/upload', methods=['POST'])
def upload_csv():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    import csv
    import io

    file = request.files.get('csv_file')

    if not file or file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('manage_hospitals'))

    if not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file.", "error")
        return redirect(url_for('manage_hospitals'))

    conn   = get_connection()
    cursor = conn.cursor()

    stream  = io.StringIO(file.stream.read().decode("utf-8"))
    reader  = csv.DictReader(stream)
    count   = 0

    for row in reader:
        try:
            emergency = 'Yes' if row['emergency'].strip().lower() == 'yes' else 'No'
            cursor.execute("""
                INSERT INTO hospitals (name, address, city, area, latitude, longitude, type, specialties, emergency, phone, rating)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['name'].strip(),
                row['address'].strip(),
                row['city'].strip(),
                row['area'].strip(),
                float(row['latitude']),
                float(row['longitude']),
                row['type'].strip(),
                row['specialties'].strip(),
                emergency,
                row['phone'].strip(),
                float(row['rating'])
            ))
            count += 1
        except Exception as e:
            flash(f"Error in row: {str(e)}", "error")
            continue

    conn.commit()
    cursor.close()
    conn.close()

    flash(f"✅ Successfully imported {count} hospitals from CSV!", "success")
    return redirect(url_for('manage_hospitals'))


# ================================================
# ADD HOSPITAL
# ================================================
@app.route('/admin/hospital/add', methods=['GET', 'POST'])
def add_hospital():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name        = request.form['name']
        address     = request.form['address']
        city        = request.form['city']
        area        = request.form['area']
        latitude    = request.form['latitude']
        longitude   = request.form['longitude']
        hosp_type   = request.form['type']
        specialties = request.form['specialties']
        emergency   = request.form['emergency']
        phone       = request.form['phone']
        rating      = request.form['rating']

        conn   = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hospitals (name, address, city, area, latitude, longitude, type, specialties, emergency, phone, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, address, city, area, float(latitude), float(longitude), hosp_type, specialties, emergency, phone, float(rating)))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Hospital added successfully!", "success")
        return redirect(url_for('manage_hospitals'))

    return render_template('admin/add_hospital.html')


# ================================================
# EDIT HOSPITAL
# ================================================
@app.route('/admin/hospital/edit/<int:hospital_id>', methods=['GET', 'POST'])
def edit_hospital(hospital_id):
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "error")
        return redirect(url_for('admin_login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name        = request.form['name']
        address     = request.form['address']
        city        = request.form['city']
        area        = request.form['area']
        latitude    = request.form['latitude']
        longitude   = request.form['longitude']
        hosp_type   = request.form['type']
        specialties = request.form['specialties']
        emergency   = request.form['emergency']
        phone       = request.form['phone']
        rating      = request.form['rating']

        cursor.execute("""
            UPDATE hospitals
            SET name=%s, address=%s, city=%s, area=%s,
                latitude=%s, longitude=%s, type=%s,
                specialties=%s, emergency=%s, phone=%s, rating=%s
            WHERE hospital_id=%s
        """, (name, address, city, area, float(latitude), float(longitude), hosp_type, specialties, emergency, phone, float(rating), hospital_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash("Hospital updated successfully!", "success")
        return redirect(url_for('manage_hospitals'))

    # GET — fetch hospital details
    cursor.execute("SELECT * FROM hospitals WHERE hospital_id = %s", (hospital_id,))
    hospital = cursor.fetchone()

    cursor.close()
    conn.close()

    if not hospital:
        flash("Hospital not found.", "error")
        return redirect(url_for('manage_hospitals'))

    return render_template('admin/edit_hospital.html', hospital=hospital)

if __name__ == '__main__':
    app.run(debug=False)
