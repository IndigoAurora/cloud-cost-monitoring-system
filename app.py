from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root@1234'),
    'host': os.getenv('DB_HOST', '127.0.0.1'),
}
DB_NAME = os.getenv('DB_NAME', 'cloud_cost_monitoring')

def get_db_connection(with_db=True):
    config = db_config.copy()
    if with_db:
        config['database'] = DB_NAME
    return mysql.connector.connect(**config)

def init_db():
    """Initializes the database, tables, and seeds sample data."""
    try:
        conn = get_db_connection(with_db=False)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # Create Tables
        tables = {}
        tables['companies'] = (
            "CREATE TABLE IF NOT EXISTS `companies` ("
            "  `company_id` int(11) NOT NULL AUTO_INCREMENT,"
            "  `company_name` varchar(255) NOT NULL,"
            "  `total_spend` decimal(15,2) DEFAULT '0.00',"
            "  `trend_direction` enum('up', 'down') DEFAULT 'up',"
            "  `trend_percentage` float DEFAULT '0.00',"
            "  `industry` varchar(255) DEFAULT NULL,"
            "  `contact_email` varchar(255) DEFAULT NULL,"
            "  PRIMARY KEY (`company_id`)"
            ") ENGINE=InnoDB"
        )
        
        tables['cost_records'] = (
            "CREATE TABLE IF NOT EXISTS `cost_records` ("
            "  `record_id` int(11) NOT NULL AUTO_INCREMENT,"
            "  `company_id` int(11) NOT NULL,"
            "  `service_id` int(11) NOT NULL,"
            "  `team_id` int(11) NOT NULL,"
            "  `amount_spent` decimal(15,2) NOT NULL,"
            "  `usage_hours` int(11) NOT NULL,"
            "  `billing_month` date NOT NULL,"
            "  PRIMARY KEY (`record_id`)"
            ") ENGINE=InnoDB"
        )
        
        tables['alerts'] = (
            "CREATE TABLE IF NOT EXISTS `alerts` ("
            "  `id` int(11) NOT NULL AUTO_INCREMENT,"
            "  `company_name` varchar(255) NOT NULL,"
            "  `title` varchar(255) NOT NULL,"
            "  `message` text NOT NULL,"
            "  PRIMARY KEY (`id`)"
            ") ENGINE=InnoDB"
        )
        
        tables['teams'] = (
            "CREATE TABLE IF NOT EXISTS `teams` ("
            "  `team_id` int(11) NOT NULL AUTO_INCREMENT,"
            "  `company_id` int(11) NOT NULL,"
            "  `team_name` varchar(255) NOT NULL,"
            "  `department` varchar(255) NOT NULL,"
            "  `monthly_budget` decimal(15,2) NOT NULL,"
            "  PRIMARY KEY (`team_id`)"
            ") ENGINE=InnoDB"
        )

        tables['cloud_services'] = (
            "CREATE TABLE IF NOT EXISTS `cloud_services` ("
            "  `service_id` int(11) NOT NULL AUTO_INCREMENT,"
            "  `service_name` varchar(255) NOT NULL,"
            "  `provider` varchar(50) NOT NULL,"
            "  PRIMARY KEY (`service_id`)"
            ") ENGINE=InnoDB"
        )

        for name, ddl in tables.items():
            cursor.execute(ddl)
            
        # Seed Data (if empty)
        cursor.execute("SELECT COUNT(*) FROM companies")
        if cursor.fetchone()[0] == 0:
            # Seed Companies
            companies_data = [
                ('TechCorp India', 1240500.00, 'up', 12.5, 'Technology', 'it@techcorp.in'),
                ('Zomato Ltd', 850200.00, 'up', 8.2, 'FoodTech', 'finance@zomato.com'),
                ('Paytm Services', 620000.00, 'down', 2.4, 'FinTech', 'cloud@paytm.com'),
                ('Byjus Learning', 940800.00, 'up', 15.7, 'EdTech', 'admin@byjus.com')
            ]
            cursor.executemany("INSERT INTO companies (company_name, total_spend, trend_direction, trend_percentage, industry, contact_email) VALUES (%s, %s, %s, %s, %s, %s)", companies_data)
            
            # Seed Teams
            teams_data = [
                (1, 'Platform Team', 'Engineering', 10000.00),
                (1, 'Payments Team', 'Engineering', 15000.00),
                (2, 'Data Science', 'Analytics', 20000.00)
            ]
            cursor.executemany("INSERT INTO teams (company_id, team_name, department, monthly_budget) VALUES (%s, %s, %s, %s)", teams_data)
            
            # Seed Services
            services_data = [
                ('EC2 Compute', 'AWS'),
                ('S3 Storage', 'AWS'),
                ('Azure SQL', 'Azure'),
                ('Cloud Run', 'GCP')
            ]
            cursor.executemany("INSERT INTO cloud_services (service_name, provider) VALUES (%s, %s)", services_data)

            # Seed Cost Records
            records_data = [
                (1, 1, 1, 1200.00, 720, '2026-03-01'),
                (1, 2, 1, 450.00, 240, '2026-03-01'),
                (2, 3, 3, 2100.00, 160, '2026-03-01'),
                (3, 4, 3, 800.00, 90, '2026-03-01')
            ]
            cursor.executemany("INSERT INTO cost_records (company_id, service_id, team_id, amount_spent, usage_hours, billing_month) VALUES (%s, %s, %s, %s, %s, %s)", records_data)

        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error initializing DB: {err}")

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Get month from query param
        selected_month = request.args.get('month')
        
        if selected_month == 'all':
            # Cumulative total spend across all time
            query = """
                SELECT 
                    c.company_id,
                    c.company_name as name, 
                    c.industry,
                    c.contact_email,
                    IFNULL(SUM(cr.amount_spent), 0) as total_spend
                FROM companies c
                LEFT JOIN cost_records cr ON c.company_id = cr.company_id
                GROUP BY c.company_id, c.company_name, c.industry, c.contact_email
            """
            cursor.execute(query)
        elif selected_month:
            # Spend for a specific month
            query = """
                SELECT 
                    c.company_id,
                    c.company_name as name, 
                    c.industry,
                    c.contact_email,
                    IFNULL(SUM(cr.amount_spent), 0) as total_spend
                FROM companies c
                LEFT JOIN cost_records cr ON c.company_id = cr.company_id 
                    AND DATE_FORMAT(cr.billing_month, '%Y-%m') = %s
                GROUP BY c.company_id, c.company_name, c.industry, c.contact_email
            """
            cursor.execute(query, (selected_month,))
        else:
            # Default: Latest month
            query = """
                SELECT 
                    c.company_id,
                    c.company_name as name, 
                    c.industry,
                    c.contact_email,
                    IFNULL(SUM(cr.amount_spent), 0) as total_spend
                FROM companies c
                LEFT JOIN cost_records cr ON c.company_id = cr.company_id 
                    AND cr.billing_month = (SELECT MAX(billing_month) FROM cost_records)
                GROUP BY c.company_id, c.company_name, c.industry, c.contact_email
            """
            cursor.execute(query)
        companies = cursor.fetchall()

        # Calculate trends based on selected or latest month
        for company in companies:
            if selected_month and selected_month != 'all':
                base_month = selected_month
            else:
                base_month = "(SELECT MAX(billing_month) FROM cost_records)"

            # Use raw string for subquery or %s for value
            if base_month.startswith("("):
                query = f"""
                    SELECT billing_month, SUM(amount_spent) as monthly_total
                    FROM cost_records
                    WHERE company_id = %s AND billing_month <= {base_month}
                    GROUP BY billing_month
                    ORDER BY billing_month DESC
                    LIMIT 2
                """
                cursor.execute(query, (company['company_id'],))
            else:
                query = """
                    SELECT billing_month, SUM(amount_spent) as monthly_total
                    FROM cost_records
                    WHERE company_id = %s AND DATE_FORMAT(billing_month, '%Y-%m') <= %s
                    GROUP BY billing_month
                    ORDER BY billing_month DESC
                    LIMIT 2
                """
                cursor.execute(query, (company['company_id'], base_month))
            
            recent_months = cursor.fetchall()
            
            # Reset to zero/default
            company['trend_percentage'] = 0.0
            company['trend_direction'] = 'up'
            
            if len(recent_months) >= 2:
                latest = float(recent_months[0]['monthly_total'])
                previous = float(recent_months[1]['monthly_total'])
                if previous > 0:
                    change = ((latest - previous) / previous) * 100
                    company['trend_percentage'] = round(abs(change), 1)
                    company['trend_direction'] = 'up' if change >= 0 else 'down'
            elif len(recent_months) == 1:
                # If only one month of data, we show 0.0% but indicate it's new data
                company['trend_percentage'] = 0.0
                company['trend_direction'] = 'up'

        cursor.close()
        conn.close()
        return jsonify(companies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cost-records', methods=['GET'])
def get_cost_records():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch cost records aggregated by company and month
        # Use %b %Y correctly for MySQL DATE_FORMAT
        selected_month = request.args.get('month')
        
        query = """
            SELECT 
                SUM(cr.amount_spent) as amount, 
                c.company_name,
                DATE_FORMAT(cr.billing_month, '%b %Y') as month
            FROM cost_records cr
            JOIN companies c ON cr.company_id = c.company_id
        """
        
        if selected_month and selected_month != 'all':
            # Rule 1: Show full preceding history up to selected month
            query += """
                WHERE DATE_FORMAT(cr.billing_month, '%Y-%m') <= %s
            """
            query += " GROUP BY c.company_name, cr.billing_month ORDER BY cr.billing_month ASC "
            cursor.execute(query, (selected_month,))
        else:
            query += " GROUP BY c.company_name, cr.billing_month ORDER BY cr.billing_month ASC "
            cursor.execute(query)
            
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get month from query param
        selected_month = request.args.get('month')
        
        if selected_month == 'all':
            # Breaches across all history
            query_auto = """
                SELECT 
                    comp.company_name,
                    t.team_name,
                    t.monthly_budget,
                    SUM(cr.amount_spent) as actual_spend
                FROM teams t
                JOIN cost_records cr ON t.team_id = cr.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(cr.amount_spent) > t.monthly_budget
            """
            cursor.execute(query_auto)
        elif selected_month:
            # Breaches for a specific month
            query_auto = """
                SELECT 
                    comp.company_name,
                    t.team_name,
                    t.monthly_budget,
                    SUM(cr.amount_spent) as actual_spend
                FROM teams t
                JOIN cost_records cr ON t.team_id = cr.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                WHERE DATE_FORMAT(cr.billing_month, '%Y-%m') = %s
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(cr.amount_spent) > t.monthly_budget
            """
            cursor.execute(query_auto, (selected_month,))
        else:
            # Default: Latest month
            query_auto = """
                SELECT 
                    comp.company_name,
                    t.team_name,
                    t.monthly_budget,
                    SUM(cr.amount_spent) as actual_spend
                FROM teams t
                JOIN cost_records cr ON t.team_id = cr.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                WHERE cr.billing_month = (SELECT MAX(billing_month) FROM cost_records)
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(cr.amount_spent) > t.monthly_budget
            """
            cursor.execute(query_auto)
        breaches = cursor.fetchall()
        
        # Convert breaches to alert format with comma formatting
        alerts = []
        for b in breaches:
            budget_fmt = "{:,.0f}".format(float(b['monthly_budget']))
            spend_fmt = "{:,.0f}".format(float(b['actual_spend']))
            alerts.append({
                "company_name": b['company_name'],
                "message": f"{b['company_name']} — {b['team_name']} has exceeded monthly budget of ${budget_fmt} with actual spend of ${spend_fmt}"
            })

        cursor.close()
        conn.close()
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/teams-over-budget', methods=['GET'])
def get_teams_over_budget():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        selected_month = request.args.get('month')
        
        if selected_month == 'all':
            query = """
                SELECT 
                    t.team_name, 
                    comp.company_name,
                    t.monthly_budget, 
                    SUM(c.amount_spent) as actual_spend, 
                    (SUM(c.amount_spent) - t.monthly_budget) as amount_over
                FROM teams t
                JOIN cost_records c ON t.team_id = c.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(c.amount_spent) > t.monthly_budget
            """
            cursor.execute(query)
        elif selected_month:
            query = """
                SELECT 
                    t.team_name, 
                    comp.company_name,
                    t.monthly_budget, 
                    SUM(c.amount_spent) as actual_spend, 
                    (SUM(c.amount_spent) - t.monthly_budget) as amount_over
                FROM teams t
                JOIN cost_records c ON t.team_id = c.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                WHERE DATE_FORMAT(c.billing_month, '%Y-%m') = %s
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(c.amount_spent) > t.monthly_budget
            """
            cursor.execute(query, (selected_month,))
        else:
            query = """
                SELECT 
                    t.team_name, 
                    comp.company_name,
                    t.monthly_budget, 
                    SUM(c.amount_spent) as actual_spend, 
                    (SUM(c.amount_spent) - t.monthly_budget) as amount_over
                FROM teams t
                JOIN cost_records c ON t.team_id = c.team_id
                JOIN companies comp ON t.company_id = comp.company_id
                WHERE c.billing_month = (SELECT MAX(billing_month) FROM cost_records)
                GROUP BY t.team_id, t.team_name, comp.company_name, t.monthly_budget
                HAVING SUM(c.amount_spent) > t.monthly_budget
            """
            cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/months', methods=['GET'])
def get_months():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Query distinct billing months from cost_records
        cursor.execute("SELECT DISTINCT billing_month FROM cost_records ORDER BY billing_month ASC")
        rows = cursor.fetchall()
        
        months = []
        for row in rows:
            date_obj = row['billing_month']
            # Format: 'January 2026'
            label = date_obj.strftime("%B %Y")
            value = date_obj.strftime("%Y-%m-%d")
            months.append({"label": label, "value": value})
            
        cursor.close()
        conn.close()
        return jsonify(months)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/all-teams', methods=['GET'])
def get_all_teams():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.team_id, t.team_name, t.department, t.monthly_budget, c.company_name 
            FROM teams t 
            JOIN companies c ON t.company_id = c.company_id
            ORDER BY c.company_name, t.team_name
        """)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/services', methods=['GET'])
def get_services():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cloud_services ORDER BY service_name")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/all-companies', methods=['GET'])
def get_all_companies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT company_id, company_name FROM companies ORDER BY company_name")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-team', methods=['POST'])
def add_team():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teams (company_id, team_name, department, monthly_budget)
            VALUES (%s, %s, %s, %s)
        """, (data['company_id'], data['team_name'], data['department'], data['monthly_budget']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Team added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-billing', methods=['POST'])
def add_billing():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cost_records (company_id, service_id, team_id, amount_spent, usage_hours, billing_month)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['company_id'], data['service_id'], data['team_id'], data['amount_spent'], data['usage_hours'], data['billing_month']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Billing record added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        selected_month = request.args.get('month')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Provider Costs
        p_query = """
            SELECT s.provider, SUM(cr.amount_spent) as total_cost
            FROM cost_records cr
            JOIN cloud_services s ON cr.service_id = s.service_id
        """
        p_params = []
        if selected_month and selected_month != 'all':
            p_query += " WHERE DATE_FORMAT(cr.billing_month, '%Y-%m') = %s"
            p_params.append(selected_month)
        p_query += " GROUP BY s.provider"
        cursor.execute(p_query, p_params)
        provider_costs = cursor.fetchall()

        # 2. Service Usage
        s_query = """
            SELECT s.service_name, SUM(cr.usage_hours) as total_hours
            FROM cost_records cr
            JOIN cloud_services s ON cr.service_id = s.service_id
        """
        s_params = []
        if selected_month and selected_month != 'all':
            s_query += " WHERE DATE_FORMAT(cr.billing_month, '%Y-%m') = %s"
            s_params.append(selected_month)
        s_query += " GROUP BY s.service_name ORDER BY total_hours DESC LIMIT 5"
        cursor.execute(s_query, s_params)
        service_usage = cursor.fetchall()

        cursor.close()
        conn.close()
        
        return jsonify({
            "provider_costs": provider_costs,
            "service_usage": service_usage
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/records', methods=['GET'])
def get_all_records():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Get month from query param
        selected_month = request.args.get('month')
        
        query = """
            SELECT 
                cr.record_id, 
                cr.team_id,
                c.company_name, 
                t.team_name, 
                s.service_name, 
                cr.amount_spent, 
                cr.usage_hours, 
                cr.billing_month
            FROM cost_records cr
            JOIN companies c ON cr.company_id = c.company_id
            JOIN teams t ON cr.team_id = t.team_id
            JOIN cloud_services s ON cr.service_id = s.service_id
        """
        
        if selected_month and selected_month != 'all':
            query += " WHERE DATE_FORMAT(cr.billing_month, '%Y-%m') = %s "
            query += " ORDER BY cr.billing_month DESC "
            cursor.execute(query, (selected_month,))
        else:
            query += " ORDER BY cr.billing_month DESC "
            cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/cost-records/<int:record_id>', methods=['DELETE'])
def delete_cost_record(record_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cost_records WHERE record_id = %s", (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/companies', methods=['POST'])
def add_company():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO companies (company_name, industry, contact_email)
            VALUES (%s, %s, %s)
        """, (data['company_name'], data['industry'], data['contact_email']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Company added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Add industry/email columns if they don't exist
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS industry VARCHAR(255)")
        cursor.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)")
        conn.commit()
        cursor.close()
        conn.close()
    except:
        pass
    app.run(debug=True, port=5001)
