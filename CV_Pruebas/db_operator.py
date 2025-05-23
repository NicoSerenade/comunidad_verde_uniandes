'''Data base modifications'''
import bcrypt # bcrypt is a hashing algorithm
import sqlite3
import datetime
#CUSTOM MODULES
import db_conn

# datetime format ISO 8601 YYYY-MM-DD HH:MM:SS

#USER REGISTRATION
def check_user_exists(conn, email, student_code):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = ? OR student_code = ?", (email, student_code))
    existing_user = cursor.fetchone()
    return existing_user is not None

def register_user(student_code, password, name, email, career=None, interests=None):
    user_id = None
    user_type = "user"

    if student_code == "admin":
        user_type = "admin"

    # 1. Validate Email Domain for non admin users
    elif not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f'Error: Email must end with "@uniandes.edu.co2"')
        return None
    
    try:
        conn = db_conn.create_connection()
        
        if check_user_exists(conn, email, student_code):
             print(f"Error: User with email '{email}' or student code '{student_code}' already exists.")
             return None

        password_bytes = password.encode('utf-8') #ebcode the password so that bcrypt module can handle it.
        salt = bcrypt.gensalt()  # Generates random salt; value that get combined with the password before hashing
        hashed_password = bcrypt.hashpw(password_bytes, salt) #hash the password

        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (user_type, student_code, password, name, email, career, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_type, student_code, hashed_password, name, email, career, interests)) 
        conn.commit()
        user_id = cursor.lastrowid #returns the id of the last manipulated row

    except sqlite3.Error as e:
        print(f"Error registering user: {e}")
    finally:
        conn.close()
        
    return user_id

def authenticate_user(student_code, password):
    """
    Authenticates a user based on student code and password.
    Returns a dict with user data if successful, None otherwise.
    """
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor() #The order of fields in the SELECT statement determines the order in the tuple
            cursor.execute('''
            SELECT user_id, user_type, student_code, name, email, password, career, interests, points, creation_date
            FROM users
            WHERE student_code = ?
            ''', (student_code,)) #the comma is crusial so it is consider a tuple
            
            user = cursor.fetchone()
            if user:
                password_bytes = password.encode('utf-8')
                stored_password = user[5]
                if bcrypt.checkpw(password_bytes, stored_password): #Extracts the salt from the hashed password, embed it into the login password, and compare them.
                    user_data = {
                        'user_id': user[0],
                        'user_type': user[1],
                        'student_code': user[2],
                        'name': user[3],
                        'email': user[4],
                        'career': user[6],
                        'interests': user[7],
                        'points': user[8],
                        'creation_date': user[9]
                    }
        except sqlite3.Error as e:
            print(f"Error authenticating user: {e}")
        finally:
            conn.close()
    return user_data

def update_user_profile(user_id, student_code=None, password=None, name=None, email=None, career=None, interests=None):
    """
    Updates a user's profile information.
    Returns True if successful, False otherwise.
    """
    success = False

    if not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {'@uniandes.edu.co'}")
        return None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if student_code:
                updates.append("student_code = ?")
                params.append(student_code)

            if password:
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password_bytes, salt)
                updates.append("password = ?")
                params.append(hashed_password)
            
            if name:
                updates.append("name = ?")
                params.append(name)
                
            if email:
                updates.append("email = ?")
                params.append(email)

            if career:
                updates.append("career = ?")
                params.append(career)

            if interests:
                updates.append("interests = ?")
                params.append(interests)
                
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, params) #both tuples and list work in sql queries.
            conn.commit()
            success = cursor.rowcount > 0 # rowcount returns how many rows were affected by the most recent SQL operation.
        except sqlite3.Error as e:
            print(f"Error updating user profile: {e}")
        finally:
            conn.close()
    return success

def delete_my_user(student_code, password):
    """Deletes a user after verifying their student_code and password securely

    Returns:
        True if the user was successfully found, password verified, and deleted.
        False otherwiswe"""
    
    success = False
    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE student_code = ?", (student_code,))
        stored_password = cursor.fetchone()

        if stored_password:
            stored_password = stored_password[0]
            password_bytes = password.encode('utf-8')

            if bcrypt.checkpw(password_bytes, stored_password):
                cursor.execute("DELETE FROM users WHERE student_code = ?", (student_code,))
                conn.commit()

                if cursor.rowcount > 0:
                    print(f"User successfully deleted.")
                    success = True

    except sqlite3.Error as e:
        print(f"Database error during user deletion: {e}")

    finally:
        conn.close() 
    return success

#ORG REGISTRATION
def register_org(creator_student_code, password, name, email, description=None, interests=None):
    """
    Registers a new organization, but FIRST checks if the creator_student_code
    exists in the 'users' table.
    Returns:
        int or None: The ID of the newly registered organization if the creator exists
                     and registration is successful, otherwise None.
    """
    user_type = "org"
    org_id = None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            password_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password_bytes, salt) 

            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE student_code = ?", (creator_student_code,))
            creator_user = cursor.fetchone()

            if creator_user:
                cursor.execute('''
                INSERT INTO organizations (user_type, creator_student_code, password, name, email, description, interests)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_type, creator_student_code, hashed_password, name, email, description, interests)) 
                conn.commit()
                org_id = cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error registering organization: {e}")
        finally:
            conn.close()
    return org_id

def authenticate_org(name, password):
    """
    Authenticates an organization based on name and password.
    Returns a dict with organization data if successful, None otherwise.
    """
    org_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT org_id, user_type, creator_student_code, name, email, password, description, interests, points, creation_date
            FROM organizations
            WHERE name = ?
            ''', (name,))
            
            org = cursor.fetchone()
            if org:
                password_bytes = password.encode('utf-8')
                stored_password = org[5]
                if bcrypt.checkpw(password_bytes, stored_password):
                    org_data = {
                        'org_id': org[0],
                        'user_type': org[1],
                        'creator_student_code': org[2],
                        'name': org[3],
                        'email': org[4],
                        'description': org[6],
                        'interests': org[7],
                        'points': org[8],
                        'creation_date': org[9]
                    }
        except sqlite3.Error as e:
            print(f"Error authenticating organization: {e}")
        finally:
            conn.close()
    return org_data

def update_org_profile(org_id, creator_student_code=None, password=None, name=None, email=None, description=None, interests=None):
    success = False

    if not isinstance(email, str) or not email.endswith("@uniandes.edu.co"):
        print(f"Error: Email must end with {'@uniandes.edu.co'}")
        return None

    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if creator_student_code:
                updates.append("creator_student_code = ?")
                params.append(creator_student_code)
            if password:
                password_bytes = password.encode('utf-8')
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password_bytes, salt)
                updates.append("password = ?")
                params.append(hashed_password)
            if name:
                updates.append("name = ?")
                params.append(name)
            if email:
                updates.append("email = ?")
                params.append(email)
            if description:
                updates.append("description = ?")
                params.append(description)
            if interests:
                updates.append("interests = ?")
                params.append(interests)
            
            params.append(org_id)
            
            query = f"UPDATE organizations SET {', '.join(updates)} WHERE org_id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            success = cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error updating organization profile: {e}")
        finally:
            conn.close()
    return success

def delete_my_org(creator_student_code, password):
    """Deletes a or after verifying their creator_student_code and password securely

    Returns:
        True if the user was successfully found, password verified, and deleted.
        False otherwiswe"""
    
    success = False
    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM organizations WHERE creator_student_code = ?", (creator_student_code,))
        stored_password = cursor.fetchone()

        if stored_password:
            stored_password = stored_password[0]
            password_bytes = password.encode('utf-8')

            if bcrypt.checkpw(password_bytes, stored_password):
                cursor.execute("DELETE FROM organizations WHERE creator_student_code = ?", (creator_student_code,))
                conn.commit()

                if cursor.rowcount > 0:
                    print(f"Organization successfully deleted.")
                    success = True

    except sqlite3.Error as e:
        print(f"Database error during org deletion: {e}")

    finally:
        conn.close() 
    return success

#ADMIN FUNCTIONS
def get_user_by_id(user_id):
    """
    Retrieves user information by user ID.
    Returns user data if found, None otherwise.
    """
    user_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, user_type, student_code, name, email, password, career, interests, points
            FROM users
            WHERE user_id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            if user:
                user_data = {
                    'user_id': user[0],
                    'user_type': user[1],
                    'student_code': user[2],
                    'name': user[3],
                    'email': user[4],
                    "password": user[5], #TRY, QUIT
                    'career': user[6],
                    'interests': user[7],
                    'points': user[8]
                }
        except sqlite3.Error as e:
            print(f"Error retrieving user: {e}")
        finally:
            conn.close()
    return user_data

def delete_user_by_id(user_id):
    success = False
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor() #DELETE remove all columns for any rows that match that condition.
            cursor.execute('''
            DELETE FROM users
            WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            if cursor.rowcount > 0:
                success = True

        except sqlite3.Error as e:
            print(f"Error deleting user profile: {e}")
        finally:
            conn.close()
    return success

def get_org_by_id(org_id):
    org_data = None
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT org_id, user_type, creator_student_code, name, email, description, interests, points, creation_date
            FROM organizations
            WHERE org_id = ?
            ''', (org_id,))
            
            org = cursor.fetchone()
            if org:
                org_data = {
                    'org_id': org[0],
                    'user_type': org[1],
                    'creator_student_code': org[2],
                    'name': org[3],
                    'email': org[4],
                    'description': org[5],
                    'interests': org[6],
                    'points': org[7],
                    'creation_date': org[8]
                }
        except sqlite3.Error as e:
            print(f"Error retrieving organization: {e}")
        finally:
            conn.close()
    return org_data

def delete_org_by_id(org_id):
    success = False
    conn = db_conn.create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM organizations
            WHERE org_id = ?
            ''', (org_id,))
            
            conn.commit()
            if cursor.rowcount > 0:
                success = True
        except sqlite3.Error as e:
            print(f"Error deleting organization: {e}")
        finally:
            conn.close()
    return success

def create_achievement(name, description, points_required, badge_icon, user_type):
    """
    Creates a new achievement for users or organizations.
    
    Args:
        name (str): Name of the achievement
        description (str): Description of the achievement
        points_required (int): Points required to unlock the achievement
        badge_icon (str): Path or identifier for the badge icon
        user_type (str): Either 'user' or 'org' to determine which table to use
    
    Returns:
        int: ID of the created achievement if successful, None otherwise
    """
    achievement_id = None
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                table = "achievements_for_users"
            elif user_type == "org":
                table = "achievements_for_orgs"
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return None
                
            cursor.execute(f'''
            INSERT INTO {table} (name, description, points_required, badge_icon)
            VALUES (?, ?, ?, ?)
            ''', (name, description, points_required, badge_icon))
            
            conn.commit()
            achievement_id = cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Error creating achievement: {e}")
        finally:
            conn.close()
            
    return achievement_id

def delete_achievement(achievement_id, user_type):
    """
    Deletes an achievement.
    
    Args:
        achievement_id (int): ID of the achievement
        user_type (str): Either 'user' or 'org' to determine which table to use
    
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                table = "achievements_for_users"
            elif user_type == "org":
                table = "achievements_for_orgs"
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return False
                
            cursor.execute(f'''
            DELETE FROM {table}
            WHERE achievement_id = ?
            ''', (achievement_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error deleting achievement: {e}")
        finally:
            conn.close()
            
    return success

def create_challenge(name, description, goal_type, goal_target, points_reward, time_allowed, user_type):
    """
    Creates a new challenge for users or organizations.
    
    Args:
        name (str): Name of the challenge
        description (str): Description of the challenge
        goal_type (str): Type of goal (e.g., 'events_attended', 'points_earned')
        goal_target (int): Numeric target for the goal
        points_reward (int): Points awarded upon completion
        time_allowed (int): Time allowed in seconds (None for no limit)
        user_type (str): Either 'user' or 'org' to determine which table to use
    
    Returns:
        int: ID of the created challenge if successful, None otherwise
    """
    challenge_id = None
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                table = "challenges_for_users"
            elif user_type == "org":
                table = "challenges_for_orgs"
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return None
                
            cursor.execute(f'''
            INSERT INTO {table} (name, description, goal_type, goal_target, points_reward, time_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, description, goal_type, goal_target, points_reward, time_allowed))
            
            conn.commit()
            challenge_id = cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Error creating challenge: {e}")
        finally:
            conn.close()
            
    return challenge_id

def delete_challenge(challenge_id, user_type):
    """
    Deletes a challenge.
    
    Args:
        challenge_id (int): ID of the challenge
        user_type (str): Either 'user' or 'org' to determine which table to use
    
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                table = "challenges_for_users"
            elif user_type == "org":
                table = "challenges_for_orgs"
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return False
                
            cursor.execute(f'''
            DELETE FROM {table}
            WHERE challenge_id = ?
            ''', (challenge_id,))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error deleting challenge: {e}")
        finally:
            conn.close()
            
    return success

#USER/ORG FUNCTIONS
def search_orgs(query=None, interests=None, sort_by=None, user_id=None):
    """
    Searches for organizations based on various criteria.
    
    Args:
        query (str, optional): Search in name or description fields
        interests (str, optional): Filter by interests (partial match)
        sort_by (str, optional): Sort by field ('name', 'points', 'creation_date')
        user_id (int, optional): If provided, filter to only show orgs where this user is a member
    
    Returns:
        list: List of dictionaries containing organization data
    """
    orgs = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_id is not None:
                # Query to get organizations where the user is a member
                sql_query = '''
                SELECT o.org_id, o.user_type, o.creator_student_code, o.name, o.email, 
                       o.description, o.interests, o.points, o.creation_date
                FROM organizations o
                JOIN organization_members m ON o.org_id = m.org_id
                WHERE m.user_id = ?
                '''
                
                params = [user_id]
                
                if query:
                    sql_query += " AND (o.name LIKE ? OR o.description LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
                    
                if interests:
                    sql_query += " AND o.interests LIKE ?"
                    params.append(f"%{interests}%")
                    
                # Apply sorting
                if sort_by == 'name':
                    sql_query += " ORDER BY o.name"
                elif sort_by == 'points':
                    sql_query += " ORDER BY o.points DESC"
                elif sort_by == 'creation_date':
                    sql_query += " ORDER BY o.creation_date DESC"
                else:
                    sql_query += " ORDER BY o.name"  # Default sorting
            else:
                # Original query without user filter
                sql_query = '''
                SELECT org_id, user_type, creator_student_code, name, email, description, interests, points, creation_date
                FROM organizations
                WHERE 1=1
                '''
                
                params = []
                
                if query:
                    sql_query += " AND (name LIKE ? OR description LIKE ?)"
                    params.extend([f"%{query}%", f"%{query}%"])
                    
                if interests:
                    sql_query += " AND interests LIKE ?"
                    params.append(f"%{interests}%")
                    
                # Apply sorting
                if sort_by == 'name':
                    sql_query += " ORDER BY name"
                elif sort_by == 'points':
                    sql_query += " ORDER BY points DESC"
                elif sort_by == 'creation_date':
                    sql_query += " ORDER BY creation_date DESC"
                else:
                    sql_query += " ORDER BY name"  # Default sorting
                
            cursor.execute(sql_query, params)
            
            for row in cursor.fetchall():
                org = {
                    'org_id': row[0],
                    'user_type': row[1],
                    'creator_student_code': row[2],
                    'name': row[3],
                    'email': row[4],
                    'description': row[5],
                    'interests': row[6],
                    'points': row[7],
                    'creation_date': row[8]
                }
                orgs.append(org)
                
        except sqlite3.Error as e:
            print(f"Error searching organizations: {e}")
        finally:
            conn.close()
            
    return orgs

def get_org_members(org_id):
    """
    Retrieves all members of a specific organization.
    Returns:
        list: List of dictionaries containing member data
    """
    members = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT u.user_id, u.name, u.email, u.career, u.interests, m.registered_date
            FROM organization_members m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.org_id = ?
            ORDER BY m.registered_date
            ''', (org_id,))
            
            for row in cursor.fetchall():
                member = {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'career': row[3],
                    'interests': row[4],
                    'registered_date': row[5]
                }
                members.append(member)
                
        except sqlite3.Error as e:
            print(f"Error retrieving organization members: {e}")
        finally:
            conn.close()
            
    return members

#Only for users
def join_org(org_id, user_id):
    """
    Adds a user to an organization.
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO organization_members (org_id, user_id)
            VALUES (?, ?)
            ''', (org_id, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error joining organization: {e}")
        finally:
            conn.close()
            
    return success

def leave_org(org_id, user_id):
    """
    Removes a user from an organization.
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            DELETE FROM organization_members
            WHERE org_id = ? AND user_id = ?
            ''', (org_id, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error leaving organization: {e}")
        finally:
            conn.close()
            
    return success

#EVENTS
def search_events(query=None, event_type=None, status=None, organizer_type=None, start_date=None, end_date=None):
    """
    Searches for events based on various criteria.
    
    Args:
        query (str, optional): Search in name or description fields
        event_type (str, optional): Filter by event type
        status (str, optional): Filter by event status ('active', 'completed', etc.)
        organizer_type (str, optional): Filter by organizer type ('user' or 'org')
        start_date (str, optional): Filter events on or after this date (ISO format)
        end_date (str, optional): Filter events on or before this date (ISO format)
    
    Returns:
        list: List of dictionaries containing event data
    """
    events = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            sql_query = '''
            SELECT event_id, organizer_id, organizer_type, name, description, 
                   event_type, location, event_datetime, status, points_value, creation_date
            FROM events
            WHERE 1=1
            '''
            
            params = []
            
            if query:
                sql_query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
                
            if event_type:
                sql_query += " AND event_type = ?"
                params.append(event_type)
                
            if status:
                sql_query += " AND status = ?"
                params.append(status)
                
            if organizer_type:
                sql_query += " AND organizer_type = ?"
                params.append(organizer_type)
                
            if start_date:
                sql_query += " AND event_datetime >= ?"
                params.append(start_date)
                
            if end_date:
                sql_query += " AND event_datetime <= ?"
                params.append(end_date)
                
            # Order by event datetime
            sql_query += " ORDER BY event_datetime"
            
            cursor.execute(sql_query, params)
            
            for row in cursor.fetchall():
                event = {
                    'event_id': row[0],
                    'organizer_id': row[1],
                    'organizer_type': row[2],
                    'name': row[3],
                    'description': row[4],
                    'event_type': row[5],
                    'location': row[6],
                    'event_datetime': row[7],
                    'status': row[8],
                    'points_value': row[9],
                    'creation_date': row[10]
                }
                events.append(event)
                
        except sqlite3.Error as e:
            print(f"Error searching events: {e}")
        finally:
            conn.close()
            
    return events

def get_event_participants(event_id):
    """
    Retrieves all participants (users and organizations) for a specific event.
    
    Args:
        event_id (int): ID of the event
    
    Returns:
        dict: Dictionary with 'users' and 'orgs' lists containing participant data
    """
    participants = {'users': [], 'orgs': []}
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Get user participants
            cursor.execute('''
            SELECT u.user_id, u.name, u.email, p.registered_date, p.attended
            FROM user_event_participants p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.event_id = ?
            ''', (event_id,))
            
            for row in cursor.fetchall():
                user = {
                    'user_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'registered_date': row[3],
                    'attended': bool(row[4])
                }
                participants['users'].append(user)
                
            # Get organization participants
            cursor.execute('''
            SELECT o.org_id, o.name, o.email, p.registered_date, p.attended
            FROM org_event_participants p
            JOIN organizations o ON p.org_id = o.org_id
            WHERE p.event_id = ?
            ''', (event_id,))
            
            for row in cursor.fetchall():
                org = {
                    'org_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'registered_date': row[3],
                    'attended': bool(row[4])
                }
                participants['orgs'].append(org)
                
        except sqlite3.Error as e:
            print(f"Error retrieving event participants: {e}")
        finally:
            conn.close()
            
    return participants

def create_event(organizer_id, organizer_type, name, description, event_type, location, event_datetime):
    """
    Creates a new event in the system.
    Returns the event_id if successful, None otherwise.
    """
    event_id = None
    conn = db_conn.create_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO events (organizer_id, organizer_type, name, description, event_type, location, event_datetime)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (organizer_id, organizer_type, name, description, event_type, location, event_datetime))
        conn.commit()
        event_id = cursor.lastrowid

    except sqlite3.Error as e:
        print(f"Error creating event: {e}")
    finally:
        conn.close()
    return event_id

def delete_event(event_id, entity_id, user_type):
    """
    Deletes an event by its ID if the entity matches the organizer.
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT organizer_id, organizer_type 
            FROM events 
            WHERE event_id = ?
            ''', (event_id,))
            
            event_info = cursor.fetchone()
            
            if not event_info:
                print("Error: Event not found.")
                return False
            
            organizer_id, organizer_type = event_info
            
            # Check if entity is authorized to delete this event
            if organizer_id == entity_id and organizer_type == user_type:
                cursor.execute('''
                DELETE FROM events
                WHERE event_id = ?
                ''', (event_id,))
                conn.commit()
                success = cursor.rowcount > 0

                if success:
                    print("Event successfully deleted.")
                else:
                    print("Error: Failed to delete event.")
            else:
                print("Error: You are not authorized to delete this event.")
                
        except sqlite3.Error as e:
            print(f"Error deleting event: {e}")
        finally:
            conn.close()
            
    return success

def join_event(event_id, entity_id, user_type):
    """
    Registers a user or organization for an event.
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                # Register a user for the event
                cursor.execute('''
                INSERT INTO user_event_participants (event_id, user_id)
                VALUES (?, ?)
                ''', (event_id, entity_id))
            elif user_type == "org":
                # Register an organization for the event
                cursor.execute('''
                INSERT INTO org_event_participants (event_id, org_id)
                VALUES (?, ?)
                ''', (event_id, entity_id))
            else:
                print(f"Error: Invalid user_type")
                return success
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error registering for event: {e}")
        finally:
            conn.close()
            
    return success

def leave_event(event_id, entity_id, user_type):
    """
    Removes a user or organization from an event.
    
    Args:
        event_id (int): ID of the event
        entity_id (int): ID of the user or organization
        user_type (str): Either 'user' or 'org'
    
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                cursor.execute('''
                DELETE FROM user_event_participants
                WHERE event_id = ? AND user_id = ?
                ''', (event_id, entity_id))
            elif user_type == "org":
                cursor.execute('''
                DELETE FROM org_event_participants
                WHERE event_id = ? AND org_id = ?
                ''', (event_id, entity_id))
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return False
                
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error leaving event: {e}")
        finally:
            conn.close()
            
    return success

def mark_event_attendance(event_id, entity_id, user_type):
    """
    Marks a participant as having attended an event.
    Note: Points awarding is now handled in the logic layer, not here.
    
    Args:
        event_id (int): ID of the event
        entity_id (int): ID of the participant (user or org)
        user_type (str): Type of entity ('user' or 'org')
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            if user_type == "user":
                cursor.execute('''
                UPDATE user_event_participants
                SET attended = 1
                WHERE event_id = ? AND user_id = ?
                ''', (event_id, entity_id))
            elif user_type == "org":
                cursor.execute('''
                UPDATE org_event_participants
                SET attended = 1
                WHERE event_id = ? AND org_id = ?
                ''', (event_id, entity_id))
            else:
                print(f"Error: Invalid user_type: {user_type}")
                return False
                
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error marking event attendance: {e}")
        finally:
            conn.close()
            
    return success


#ITEMS
def get_available_items(item_type=None, item_terms=None, user_id=None):
    """
    Retrieves available items with optional filtering.
    
    Args:
        item_type (str, optional): Filter by item type
        item_terms (str, optional): Filter by item terms
        user_id (int, optional): Filter by user ID
    
    Returns:
        list: List of dictionaries containing item data
    """
    items = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            query = '''
            SELECT i.item_id, i.user_id, i.name, i.description, 
                   i.item_type, i.item_terms, i.item_status, i.creation_date,
                   u.name as user_name
            FROM items i
            JOIN users u ON i.user_id = u.user_id
            WHERE i.item_status = 'available'
            '''
            
            params = []
            
            if item_type:
                query += " AND i.item_type = ?"
                params.append(item_type)
                
            if item_terms:
                query += " AND i.item_terms = ?"
                params.append(item_terms)
                
            if user_id:
                query += " AND i.user_id = ?"
                params.append(user_id)
                
            # Order by creation date (newest first)
            query += " ORDER BY i.creation_date DESC"
            
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                item = {
                    'item_id': row[0],
                    'user_id': row[1],
                    'name': row[2],
                    'description': row[3],
                    'item_type': row[4],
                    'item_terms': row[5],
                    'item_status': row[6],
                    'creation_date': row[7],
                    'user_name': row[8]
                }
                items.append(item)
                
        except sqlite3.Error as e:
            print(f"Error retrieving available items: {e}")
        finally:
            if conn:
                 conn.close()
            
    return items

def create_item(user_id, name, description, item_type, item_terms):
    """
    Creates a new item for exchange.
    
    Args:
        user_id (int): ID of the user creating the item
        name (str): Name of the item
        description (str): Description of the item
        item_type (str): Type of item --ropa, libros, hogar, otros
        item_terms (str): Terms for the item --regalo, prestamo, intercambio (NO SE PUEDEN VENDER)
    
    Returns:
        int: ID of the created item if successful, None otherwise
    """
    item_id = None
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO items (user_id, name, description, item_type, item_terms)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, description, item_type, item_terms))
            
            conn.commit()
            item_id = cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Error creating item: {e}")
        finally:
            conn.close()
            
    return item_id

def update_item_status(item_id, status):
    """
    Updates the status of an item.
    
    Args:
        item_id (int): ID of the item
        status (str): New status --available, borrowed, unavailable
    
    Returns:
        bool: True if successful, False otherwise
    """
    success = False
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE items
            SET status = ?
            WHERE item_id = ?
            ''', (status, item_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"Error updating item status: {e}")
        finally:
            conn.close()
            
    return success

def get_item_details(item_id):
    """
    Get detailed information about an item.
    
    Args:
        item_id (int): The ID of the item to retrieve.
        
    Returns:
        dict: Item details including owner_id, name, description, status, and item_terms.
        None if the item doesn't exist or an error occurs.
    """
    try:
        conn = db_conn.create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, name, description, item_type, item_terms, item_status
                FROM items
                WHERE item_id = ?
            ''', (item_id,))
            
            item = cursor.fetchone()
            conn.close()
            
            if item:
                return {
                    'owner_id': item[0],  # Map user_id to owner_id for compatibility
                    'name': item[1],
                    'description': item[2],
                    'item_type': item[3],
                    'item_terms': item[4],
                    'status': item[5]  # Map item_status to status for compatibility
                }
            else:
                return None
    except Exception as e:
        print(f"Error getting item details: {e}")
        return None

def create_item_request(requester_id, owner_id, item_id, requested_term, message=""):
    """
    Create a new exchange request with the specified terms.
    
    Args:
        requester_id (int): The ID of the user requesting the item.
        owner_id (int): The ID of the item owner.
        item_id (int): The ID of the requested item.
        requested_term (str): The requested exchange term (regalo, prestamo, intercambio).
        message (str, optional): Optional message from requester.
        
    Returns:
        int: The ID of the newly created exchange request.
        None if creation fails or an error occurs.
    """
    try:
        # Check if a request already exists for this requester and item
        conn = db_conn.create_connection()
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT exchange_id FROM exchange_requests
                WHERE requester_id = ? AND item_id = ? AND status = 'pending'
            ''', (requester_id, item_id))
            
            existing = cursor.fetchone()
            if existing:
                print(f"Exchange request already exists for requester {requester_id} and item {item_id}")
                conn.close()
                return None
            
            # Insert the new exchange request with requested term
            cursor.execute('''
                INSERT INTO exchange_requests 
                (requester_id, owner_id, item_id, requested_term, message, status, request_date) 
                VALUES (?, ?, ?, ?, ?, 'pending', datetime('now'))
            ''', (requester_id, owner_id, item_id, requested_term, message))
            
            exchange_id = cursor.lastrowid
            
            
            conn.commit()
            conn.close()
            
            print(f"Created exchange request ID {exchange_id} with requested term '{requested_term}'")
            return exchange_id
    except Exception as e:
        print(f"Error creating exchange request: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None

def get_item_owner(item_id):
    """
    Retrieves the user_id of the owner of a specific item.

    Args:
        item_id (int): The ID of the item.

    Returns:
        int: The user_id of the item's owner, or None if the item is not found.
    """
    owner_id = None
    conn = db_conn.create_connection()
    if conn is None:
        print("Error: Could not establish database connection.")
        return None

    try:
        cursor = conn.cursor()
        # Assumes 'user_id' column in 'items' table holds the owner's ID
        cursor.execute("SELECT user_id FROM items WHERE item_id = ?", (item_id,))
        result = cursor.fetchone()
        if result:
            owner_id = result[0]

    except sqlite3.Error as e:
        print(f"Error retrieving item owner for item ID {item_id}: {e}")
    finally:
        if conn:
            conn.close()

    return owner_id

def get_exchange_request(exchange_id):
    """
    Retrieves details for a specific exchange request.

    Args:
        exchange_id (int): The ID of the exchange request.

    Returns:
        dict: A dictionary containing the request details (exchange_id, item_id,
              requester_id, owner_id, message, status, request_date, decision_date)
              or None if the request is not found or an error occurs.
    """
    request_details = None
    conn = db_conn.create_connection()
    if conn is None:
        print("Error: Could not establish database connection.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT exchange_id, item_id, requester_id, owner_id, message, status, 
                   request_date, decision_date, requested_term
            FROM exchange_requests
            WHERE exchange_id = ?
        ''', (exchange_id,))
        row = cursor.fetchone()

        if row:
            request_details = {
                'exchange_id': row[0],
                'item_id': row[1],
                'requester_id': row[2],
                'owner_id': row[3],
                'message': row[4],
                'status': row[5],
                'request_date': row[6],
                'decision_date': row[7],
                'requested_term': row[8] if len(row) > 8 else 'intercambio'  # Default if column doesn't exist yet
            }

    except sqlite3.Error as e:
        print(f"Error retrieving exchange request ID {exchange_id}: {e}")
    finally:
        if conn:
            conn.close()

    return request_details

def get_user_exchange_requests(user_id, request_type='received'):
    """
    Retrieves exchange requests associated with a user, either sent or received.

    Args:
        user_id (int): The ID of the user whose requests are being fetched.
        request_type (str): 'received' (requests for user's items) or
                           'sent' (requests made by the user). Defaults to 'received'.

    Returns:
        list: A list of dictionaries, each representing an exchange request with
              details about the item and the other party involved. 
                received: Finds requests made by other users for items owned by the specified user_id.
                sent: Finds requests made by the specified user_id for items owned by other users.
              
              Returns an empty list if no requests are found, or None if an error occurs.

    """
    requests_list = []
    conn = db_conn.create_connection()
    if conn is None:
        print("Error: Could not establish database connection.")
        return None # Indicate error

    try:
        cursor = conn.cursor()
        sql_query = '''
            SELECT
                er.exchange_id, er.item_id, i.name AS item_name,
                er.requester_id, u_req.name AS requester_name,
                er.owner_id, u_own.name AS owner_name,
                er.message, er.status, er.request_date, er.decision_date,
                er.requested_term, i.item_terms AS original_term
            FROM exchange_requests er
            JOIN items i ON er.item_id = i.item_id
            JOIN users u_req ON er.requester_id = u_req.user_id
            JOIN users u_own ON er.owner_id = u_own.user_id
        '''
        params = (user_id,)

        if request_type == 'received':
            sql_query += " WHERE er.owner_id = ?"
        elif request_type == 'sent':
            sql_query += " WHERE er.requester_id = ?"
        else:
            print(f"Error: Invalid request_type '{request_type}' specified.")
            if conn: conn.close()
            return None

        sql_query += " ORDER BY er.request_date DESC" # Show newest first

        cursor.execute(sql_query, params)
        rows = cursor.fetchall()

        for row in rows:
            request_data = {
                'exchange_id': row[0],
                'item_id': row[1],
                'item_name': row[2],
                'requester_id': row[3],
                'requester_name': row[4],
                'owner_id': row[5],
                'owner_name': row[6],
                'message': row[7],
                'status': row[8],
                'request_date': row[9],
                'decision_date': row[10],
                'requested_term': row[11] if len(row) > 11 else 'intercambio',  # Default if column doesn't exist yet
                'original_term': row[12] if len(row) > 12 else None  # Original item term
            }
            requests_list.append(request_data)

    except sqlite3.Error as e:
        print(f"Error retrieving {request_type} exchange requests for user ID {user_id}: {e}")
        requests_list = None
    finally:
        if conn:
            conn.close()

    # Return the list (possibly empty) or None if there was an error
    return requests_list if requests_list is not None else []

def update_exchange_status(exchange_id, new_status):
    """
    Updates the status (and decision_date) of an exchange request.

    Args:
        exchange_id (int): The ID of the exchange request to update.
        new_status (str): The new status ('accepted', 'rejected', 'cancelled').

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    success = False
    conn = db_conn.create_connection()
    if conn is None:
        print("Error: Could not establish database connection.")
        return False

    valid_statuses = ['accepted', 'rejected', 'cancelled', 'pending']
    if new_status not in valid_statuses:
        print(f"Error: Invalid status '{new_status}' provided.")
        return False

    try:
        cursor = conn.cursor()
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if new_status in ['accepted', 'rejected', 'cancelled']:
             cursor.execute('''
                UPDATE exchange_requests
                SET status = ?, decision_date = ?
                WHERE exchange_id = ?
            ''', (new_status, current_time_str, exchange_id))

        conn.commit()
        if cursor.rowcount > 0:
             print(f"Successfully updated exchange request ID {exchange_id} to status '{new_status}'.")
             success = True
        else:
             print(f"Warning: No rows updated for exchange request ID {exchange_id}. It might not exist or was not in a state to be updated to '{new_status}'.")

    except sqlite3.Error as e:
        print(f"Error updating status for exchange request ID {exchange_id}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return success

def accept_exchange_request(exchange_id, requested_term):
    """
    Accepts an exchange request and updates the item status based on the requested term.
    
    Args:
        exchange_id (int): The ID of the exchange request to accept.
        requested_term (str): The requested term ('regalo', 'prestamo', 'intercambio').
        
    Returns:
        bool: True if the exchange was successfully accepted, False otherwise.
    """
    success = False
    conn = db_conn.create_connection()
    if conn is None:
        print("Error: Could not establish database connection.")
        return False

    try:
        cursor = conn.cursor()
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # First, get the exchange request details to find the item
        cursor.execute('''
            SELECT item_id, requester_id 
            FROM exchange_requests 
            WHERE exchange_id = ? AND status = 'pending'
        ''', (exchange_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"Error: Exchange request {exchange_id} not found or not in pending state")
            conn.rollback()
            conn.close()
            return False
            
        item_id, requester_id = row
        
        # Update the exchange request status to accepted
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE exchange_requests
            SET status = 'accepted', decision_date = ?
            WHERE exchange_id = ?
        ''', (current_time_str, exchange_id))
        
        # Update the item status based on the requested term
        new_item_status = ''
        if requested_term == 'regalo':
            new_item_status = 'gifted'
            # Also update the owner to the requester
            cursor.execute('''
                UPDATE items
                SET item_status = ?, user_id = ?
                WHERE item_id = ?
            ''', (new_item_status, requester_id, item_id))
        elif requested_term == 'prestamo':
            new_item_status = 'borrowed'
            # We can't set borrower_id because it doesn't exist in the schema
            # Instead, we'll just update the status
            cursor.execute('''
                UPDATE items
                SET item_status = ?
                WHERE item_id = ?
            ''', (new_item_status, item_id))
            
            # Consider adding a record in a separate borrowers table if needed
            # or extending the schema to add a borrower_id column
        elif requested_term == 'intercambio':
            new_item_status = 'exchanged'
            cursor.execute('''
                UPDATE items
                SET item_status = ?
                WHERE item_id = ?
            ''', (new_item_status, item_id))
        else:
            print(f"Error: Invalid requested term '{requested_term}'")
            conn.rollback()
            conn.close()
            return False
        
        # Reject all other pending requests for this item
        cursor.execute('''
            UPDATE exchange_requests
            SET status = 'rejected', decision_date = ?
            WHERE item_id = ? AND status = 'pending' AND exchange_id != ?
        ''', (current_time_str, item_id, exchange_id))
        
        conn.commit()
        success = True
        print(f"Successfully accepted exchange request {exchange_id} with term '{requested_term}'")
        
    except sqlite3.Error as e:
        print(f"Error accepting exchange request {exchange_id}: {e}")
        if conn:
            conn.rollback()
        success = False
    finally:
        if conn:
            conn.close()
            
    return success


#CHALLENGES
def search_challenges(user_type):
    """
    Retrieves all challenges for "user" or "org" entities, depending on the user_type.

    Args:
        user_type (str): Either 'user' or 'org' to specify which challenges to retrieve.

    Returns:
        list: A list of dictionaries, each containing challenge data (id, name, description, goal, reward, time).
              Returns an empty list if the user_type is invalid or an error occurs.
    """
    challenges = []
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return challenges

    try:
        cursor = conn.cursor()

        if user_type == "user":
            table_name = "challenges_for_users"
        elif user_type == "org":
            table_name = "challenges_for_orgs"
        else:
            print(f"Error: Invalid user_type specified: {user_type}")
            return challenges

        # Select all relevant columns from the appropriate challenges table
        cursor.execute(f'''
        SELECT challenge_id, name, description, goal_type, goal_target, points_reward, time_allowed
        FROM {table_name}
        ORDER BY name -- Optional: order by name or reward
        ''')

        rows = cursor.fetchall()
        for row in rows:
            challenge_data = {
                'challenge_id': row[0],
                'name': row[1],
                'description': row[2],
                'goal_type': row[3],
                'goal_target': row[4],
                'points_reward': row[5],
                'time_allowed': row[6] # Will be None if no time limit
            }
            challenges.append(challenge_data)

    except sqlite3.Error as e:
        print(f"Error retrieving challenges for {user_type}: {e}")
    finally:
        if conn: # Ensure conn exists before closing
            conn.close()

    return challenges

def get_active_challenges(entity_id, user_type):
    """
    Retrieves all currently active challenges for a specific user or organization.

    Args:
        entity_id (int): The ID of the user or organization.
        user_type (str): Either 'user' or 'org'.

    Returns:
        list: A list of dictionaries, each containing details of an active challenge
              including the entity's progress. Returns an empty list on error or
              if no active challenges are found.
    """
    active_challenges = []
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return active_challenges

    try:
        cursor = conn.cursor()

        if user_type == "user":
            progress_table = "user_challenges"
            challenge_table = "challenges_for_users"
            id_column = "user_id"
            active_status = "active" # Status used in user_challenges
        elif user_type == "org":
            progress_table = "org_challenges"
            challenge_table = "challenges_for_orgs"
            id_column = "org_id"
            active_status = "in_progress" # Status used in org_challenges
        else:
            print(f"Error: Invalid user_type specified: {user_type}")
            return active_challenges

        # Join the progress table with the main challenge table
        # Filter by entity_id and active status
        sql_query = f'''
        SELECT
            p.challenge_id, c.name, c.description, c.goal_type, c.goal_target,
            c.points_reward, c.time_allowed,
            p.goal_progress, p.status, p.start_time, p.deadline
        FROM {progress_table} p
        JOIN {challenge_table} c ON p.challenge_id = c.challenge_id
        WHERE p.{id_column} = ? AND p.status = ?
        ORDER BY p.start_time DESC
        '''

        cursor.execute(sql_query, (entity_id, active_status))

        rows = cursor.fetchall()
        for row in rows:
            challenge_data = {
                'challenge_id': row[0],
                'name': row[1],
                'description': row[2],
                'goal_type': row[3],
                'goal_target': row[4],
                'points_reward': row[5],
                'time_allowed': row[6],
                'goal_progress': row[7],
                'status': row[8],
                'start_time': row[9],
                'deadline': row[10]
            }
            active_challenges.append(challenge_data)

    except sqlite3.Error as e:
        print(f"Error retrieving active challenges for {user_type} ID {entity_id}: {e}")
    finally:
        if conn:
            conn.close()

    return active_challenges

def join_challenge(entity_id, user_type, challenge_id):
    """
    Registers a user or organization for a challenge, setting start time and deadline if applicable.

    Args:
        entity_id (int): The ID of the user or organization.
        user_type (str): Either 'user' or 'org'.
        challenge_id (int): The ID of the challenge to join.

    Returns:
        bool: True if successfully registered for the challenge, False otherwise.
    """
    success = False
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return False

    try:
        cursor = conn.cursor()

        if user_type == "user":
            progress_table = "user_challenges"
            challenge_table = "challenges_for_users"
            id_column = "user_id"
            # Default status for user_challenges is 'active'
        elif user_type == "org":
            progress_table = "org_challenges"
            challenge_table = "challenges_for_orgs"
            id_column = "org_id"
             # Default status for org_challenges is 'in_progress'
        else:
            print(f"Error: Invalid user_type specified: {user_type}")
            return False

        # 1. Get challenge details (especially time_allowed)
        cursor.execute(f"SELECT time_allowed FROM {challenge_table} WHERE challenge_id = ?", (challenge_id,))
        challenge_info = cursor.fetchone()

        if not challenge_info:
            print(f"Error: Challenge with ID {challenge_id} not found for {user_type}s.")
            return False

        time_allowed = challenge_info[0]
        deadline = None
        start_time = datetime.datetime.now() # Use current time as start time

        # 2. Calculate deadline if time_allowed is set
        if time_allowed is not None and time_allowed > 0:
            deadline_dt = start_time + datetime.timedelta(seconds=time_allowed)
            deadline = deadline_dt.strftime('%Y-%m-%d %H:%M:%S') # Format for SQLite TEXT

        start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

        # 3. Insert into the progress table
        # The schema handles default values for progress (0) and status ('active'/'in_progress')
        # We explicitly set start_time and deadline (if applicable)
        sql_insert = f'''
        INSERT INTO {progress_table} ({id_column}, challenge_id, start_time, deadline)
        VALUES (?, ?, ?, ?)
        '''

        cursor.execute(sql_insert, (entity_id, challenge_id, start_time_str, deadline))
        conn.commit()

        success = cursor.rowcount > 0
        if success:
             print(f"{user_type.capitalize()} ID {entity_id} successfully joined challenge ID {challenge_id}.")

    except sqlite3.IntegrityError:
        # This likely means the unique constraint (entity_id, challenge_id) was violated
        print(f"Error: {user_type.capitalize()} ID {entity_id} is already participating in challenge ID {challenge_id}.")
    except sqlite3.Error as e:
        print(f"Error joining challenge for {user_type} ID {entity_id}: {e}")
        if conn:
             conn.rollback() # Rollback in case of other errors during transaction
    finally:
        if conn:
            conn.close()

    return success

def update_challenges_progress(entity_id, user_type, challenge_id, progress_increment):
    """
    Updates an entity's progress on an active challenge. If the goal is met,
    marks the challenge as completed, awards points using update_entity_points,
    and records the completion date.

    Args:
        entity_id (int): The ID of the user or organization.
        user_type (str): Either 'user' or 'org'.
        challenge_id (int): The ID of the challenge to update progress for.
        progress_increment (int): The amount of progress made in this update.

    Returns:
        bool: True if the progress was successfully updated (and potentially completed),
              False otherwise (e.g., challenge not active, DB error).
    """
    success = False
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return False

    try:
        cursor = conn.cursor()

        if user_type == "user":
            progress_table = "user_challenges"
            challenge_table = "challenges_for_users"
            id_column = "user_id"
            active_status = "active"
            completed_status = "completed"
        elif user_type == "org":
            progress_table = "org_challenges"
            challenge_table = "challenges_for_orgs"
            id_column = "org_id"
            active_status = "in_progress"
            completed_status = "completed" # Assuming 'completed' is the final status for both
        else:
            print(f"Error: Invalid user_type specified: {user_type}")
            return False

        # 1. Get current progress, status, challenge goal, and reward
        sql_query = f'''
        SELECT
            p.goal_progress, p.status,
            c.goal_target, c.points_reward
        FROM {progress_table} p
        JOIN {challenge_table} c ON p.challenge_id = c.challenge_id
        WHERE p.{id_column} = ? AND p.challenge_id = ?
        '''
        cursor.execute(sql_query, (entity_id, challenge_id))
        progress_info = cursor.fetchone()

        if not progress_info:
            print(f"Error: No active challenge found for {user_type} ID {entity_id} and challenge ID {challenge_id}.")
            return False

        current_progress, current_status, goal_target, points_reward = progress_info

        # 2. Check if challenge is active/in_progress
        if current_status != active_status:
            print(f"Error: Challenge ID {challenge_id} is not currently active ({current_status}) for {user_type} ID {entity_id}.")
            return False

        # 3. Calculate new progress
        new_progress = current_progress + progress_increment

        # 4. Check for completion
        if new_progress >= goal_target:
            # Challenge Completed!
            completion_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            final_progress = goal_target # Cap progress at the target

            sql_update = f'''
            UPDATE {progress_table}
            SET goal_progress = ?,
                status = ?,
                date_completed = ?
            WHERE {id_column} = ? AND challenge_id = ?
            '''
            cursor.execute(sql_update, (final_progress, completed_status, completion_time_str, entity_id, challenge_id))

            if cursor.rowcount > 0:
                print(f"Challenge ID {challenge_id} completed by {user_type} ID {entity_id}!")
                # Award points and check for achievements
                if points_reward > 0:
                    print(f"Awarding {points_reward} points...")
                    achievement_unlocked = update_entity_points(entity_id, user_type, points_reward)
                    if achievement_unlocked:
                         print(f"Congratulations! Unlocked achievement: {achievement_unlocked}")
                success = True
            else:
                 print(f"Error updating challenge status to completed for {user_type} ID {entity_id}.")


        else:
            # Challenge still in progress, just update progress
            sql_update = f'''
            UPDATE {progress_table}
            SET goal_progress = ?
            WHERE {id_column} = ? AND challenge_id = ?
            '''
            cursor.execute(sql_update, (new_progress, entity_id, challenge_id))
            if cursor.rowcount > 0:
                 print(f"Updated progress for challenge ID {challenge_id} for {user_type} ID {entity_id} to {new_progress}.")
                 success = True
            else:
                 print(f"Error updating challenge progress for {user_type} ID {entity_id}.")


        conn.commit()

    except sqlite3.Error as e:
        print(f"Error updating challenge progress for {user_type} ID {entity_id}: {e}")
        if conn:
             conn.rollback()
    finally:
        if conn:
            conn.close()

    return success

#ACHIVEMENTS
def search_achievements(user_type):
    """
    Retrieves all achievements for "user" or "org" entities, depending on the user_type.

    Args:
        user_type (str): Either 'user' or 'org' to specify which achievements to retrieve.

    Returns:
        list: A list of dictionaries, each containing achievement data (id, name, description, points, icon).
              Returns an empty list if the user_type is invalid or an error occurs.
    """
    achievements = []
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return achievements

    try:
        cursor = conn.cursor()

        if user_type == "user":
            table_name = "achievements_for_users"
        elif user_type == "org":
            table_name = "achievements_for_orgs"
        else:
            print(f"Error: Invalid user_type specified: {user_type}")
            return achievements

        # Select all relevant columns from the appropriate achievements table
        cursor.execute(f'''
        SELECT achievement_id, name, description, points_required, badge_icon
        FROM {table_name}
        ORDER BY points_required  -- Optional: order by points or name
        ''')

        rows = cursor.fetchall()
        for row in rows:
            achievement_data = {
                'achievement_id': row[0],
                'name': row[1],
                'description': row[2],
                'points_required': row[3],
                'badge_icon': row[4]
            }
            achievements.append(achievement_data)

    except sqlite3.Error as e:
        print(f"Error retrieving achievements for {user_type}: {e}")
    finally:
        conn.close()

    return achievements

def update_entity_points(entity_id, user_type, points_to_add):
    """
    Awards points to a user or organization and checks for achievement unlocks.
    Returns:
        The name of the highest newly unlocked achievement (str), otherwise None.
    """
    old_points = None
    new_total_points = None
    achievement_unlocked = None

    # Determine table and id column based on user_type
    if user_type == "user":
        table_name = "users"
        id_col = "user_id"
        achievements_table = "achievements_for_users"
        user_achievements_table = "user_achievements"
    elif user_type == "org":
        table_name = "organizations"
        id_col = "org_id"
        achievements_table = "achievements_for_orgs"
        user_achievements_table = "org_achievements"
    else:
        print(f"Error: Invalid user_type: {user_type}")
        return None

    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT points FROM {table_name} WHERE {id_col} = ?", (entity_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"Error: {user_type} with ID {entity_id} not found")
            return None
            
        old_points = result[0]
        new_total_points = old_points + points_to_add

        # Update points
        cursor.execute(f'''
            UPDATE {table_name}
            SET points = ?
            WHERE {id_col} = ?
        ''', (new_total_points, entity_id))
        
        # Check for new achievements based on points
        cursor.execute(f'''
            SELECT achievement_id, name, points_required 
            FROM {achievements_table}
            WHERE points_required <= ?
            ORDER BY points_required DESC
        ''', (new_total_points,))
        
        possible_achievements = cursor.fetchall()
        
        # Get user's existing achievements
        cursor.execute(f'''
            SELECT achievement_id 
            FROM {user_achievements_table}
            WHERE {id_col} = ?
        ''', (entity_id,))
        
        existing_achievements = [row[0] for row in cursor.fetchall()]
        
        # Find the highest achievement not yet unlocked
        for achievement in possible_achievements:
            ach_id, ach_name, ach_points = achievement
            
            if ach_id not in existing_achievements and ach_points > old_points:
                # Award the new achievement
                cursor.execute(f'''
                    INSERT INTO {user_achievements_table} ({id_col}, achievement_id)
                    VALUES (?, ?)
                ''', (entity_id, ach_id))
                
                achievement_unlocked = ach_name
                break
        
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error in update_entity_points: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    return achievement_unlocked

def get_user_points_and_achievements(user_id):
    """
    Retrieves the current points and unlocked achievements for a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary containing 'points' (int) and 'achievements' (list of dicts),
              or None if the user is not found or an error occurs.
              Each achievement dict contains 'achievement_id', 'name', 'description', 'badge_icon'.
    """
    user_data = None
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return None

    try:
        cursor = conn.cursor()

        # 1. Get user's current points
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        points_result = cursor.fetchone()

        if not points_result:
            print(f"Error: User with ID {user_id} not found.")
            return None

        current_points = points_result[0]

        # 2. Get user's unlocked achievements - removing date_unlocked which doesn't exist
        cursor.execute('''
            SELECT
                ua.achievement_id,
                a.name,
                a.description,
                a.badge_icon
            FROM user_achievements ua
            JOIN achievements_for_users a ON ua.achievement_id = a.achievement_id
            WHERE ua.user_id = ?
        ''', (user_id,))

        achievements_list = []
        for row in cursor.fetchall():
            achievement = {
                'achievement_id': row[0],
                'name': row[1],
                'description': row[2],
                'badge_icon': row[3]
            }
            achievements_list.append(achievement)

        user_data = {
            'points': current_points,
            'achievements': achievements_list
        }

    except sqlite3.Error as e:
        print(f"Error retrieving points and achievements for user ID {user_id}: {e}")
    finally:
        if conn:
            conn.close()

    return user_data

#USER TO USER FUNCTIONS
def search_users(query=None, career=None, interests=None):
    """
    Searches for users based on various criteria.
    
    Args:
        query (str, optional): Search in name or email fields
        career (str, optional): Filter by career
        interests (str, optional): Filter by interests (partial match)
    
    Returns:
        list: List of dictionaries containing user data
    """
    users = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            sql_query = '''
            SELECT user_id, student_code, name, email, career, interests, points, creation_date
            FROM users
            WHERE user_type != 'admin'
            '''
            
            params = []
            
            if query:
                sql_query += " AND (name LIKE ? OR email LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
                
            if career:
                sql_query += " AND career = ?"
                params.append(career)
                
            if interests:
                sql_query += " AND interests LIKE ?"
                params.append(f"%{interests}%")
                
            # Order by name
            sql_query += " ORDER BY name"
            
            cursor.execute(sql_query, params)
            
            for row in cursor.fetchall():
                user = {
                    'user_id': row[0],
                    'student_code': row[1],
                    'name': row[2],
                    'email': row[3],
                    'career': row[4],
                    'interests': row[5],
                    'points': row[6],
                    'creation_date': row[7]
                }
                users.append(user)
                
        except sqlite3.Error as e:
            print(f"Error searching users: {e}")
        finally:
            conn.close()
            
    return users

def get_top_users_by_points(limit=10):
    """
    Retrieves users sorted by points in descending order.
    
    Args:
        limit (int, optional): Maximum number of users to return. Defaults to 10.
    
    Returns:
        list: List of dictionaries containing user data, sorted by points.
    """
    users = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Query to get users sorted by points in descending order
            sql_query = '''
            SELECT user_id, student_code, name, email, career, interests, points, creation_date
            FROM users
            WHERE user_type != 'admin'
            ORDER BY points DESC
            '''
            
            if limit:
                sql_query += f" LIMIT {limit}"
            
            cursor.execute(sql_query)
            
            for row in cursor.fetchall():
                user = {
                    'user_id': row[0],
                    'student_code': row[1],
                    'name': row[2],
                    'email': row[3],
                    'career': row[4],
                    'interests': row[5],
                    'points': row[6],
                    'creation_date': row[7]
                }
                users.append(user)
                
        except sqlite3.Error as e:
            print(f"Error retrieving top users by points: {e}")
            return None
        finally:
            conn.close()
            
    return users

#MAP FUNCTIONS
def add_map_point(user_id, permission_code, name, description, point_type, latitude, longitude, address=None):
    """
    Adds a new map point if the user has the permission code for doing so. (admin2000)
    Returns:
        int: The point_id of the newly created map point if successful, None otherwise.
    """

    point_id = None
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO map_points (creator_id, name, description, point_type, latitude, longitude, address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, description, point_type, latitude, longitude, address))

        conn.commit()
        point_id = cursor.lastrowid
        print(f"Successfully added map point '{name}' with ID: {point_id} by user ID: {user_id}")

    except sqlite3.Error as e:
        print(f"Error adding map point: {e}")
        if conn:
            conn.rollback() # Rollback on error
    finally:
        if conn:
            conn.close()

    return point_id

def delete_map_point(user_id, user_type, point_id):
    """
    Deletes a map point based on user permissions.
    - Admins can delete any point.
    - Other users can only delete points they created.

    Args:
        user_id (int): The ID of the user attempting the deletion.
        user_type (str): The type of the user -- 'admin', 'user'
        point_id (int): The ID of the map point to delete.

    Returns:
        bool: True if the point was successfully deleted, False otherwise.
    """
    deleted = False
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return False

    try:
        cursor = conn.cursor()
        if user_type == "admin":
            # Admin can delete any point by its ID
            cursor.execute("DELETE FROM map_points WHERE point_id = ?", (point_id,))
        else:
            # Non-admin users can only delete points they created
            cursor.execute("DELETE FROM map_points WHERE point_id = ? AND creator_id = ?", (point_id, user_id))
        conn.commit()
        if cursor.rowcount > 0:
            deleted = True
        else:
            print("You don't own that point.")
    except sqlite3.Error as e:
        print(f"Error deleting map point: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return deleted

def get_map_points(point_type=None):
    """
    Retrieves map points from the database, optionally filtered by type.

    Args:
        point_type (str, optional): The type of point to filter by
                                    (e.g., 'tienda', 'reciclaje').
                                    If None, retrieves all points. Defaults to None.

    Returns:
        list: A list of dictionaries, where each dictionary represents a map point
              matching the criteria. Includes 'creator_id'. Returns an empty list
              if no points are found or an error occurs.
    """
    map_points_list = []
    conn = db_conn.create_connection()

    if conn is None:
        print("Error: Could not establish database connection.")
        return map_points_list # Return empty list on connection error

    try:
        cursor = conn.cursor()

        # Select all relevant columns including creator_id
        sql_query = '''
            SELECT point_id, creator_id, name, description, point_type, latitude, longitude, address, creation_date
            FROM map_points
        '''
        params = []

        if point_type:
            # Add WHERE clause if filtering by type
            sql_query += " WHERE point_type = ?"
            params.append(point_type)

        sql_query += " ORDER BY name" # Order results alphabetically by name

        cursor.execute(sql_query, params)
        rows = cursor.fetchall()

        # Fetch column names to create dictionaries more robustly (optional but good practice)
        # columns = [description[0] for description in cursor.description]

        for row in rows:
            # Create dictionary for each point using index access (consistent with user functions)
            point_data = {
                'point_id': row[0],
                'creator_id': row[1], # Added creator_id
                'name': row[2],
                'description': row[3],
                'point_type': row[4],
                'latitude': row[5],
                'longitude': row[6],
                'address': row[7],
                'creation_date': row[8]
            }
            map_points_list.append(point_data)

        # print(f"Retrieved {len(map_points_list)} map points.") # Optional: print count

    except sqlite3.Error as e:
        print(f"Error retrieving map points: {e}")
        # Return empty list on SQL error as well
        map_points_list = []
    finally:
        if conn:
            conn.close()

    return map_points_list

def update_exchange_requests_schema():
    """
    Updates the exchange_requests table schema.
    Warning: This function requires careful invocation.
    """
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            
            # Check if the column exists already
            cursor.execute("PRAGMA table_info(exchange_requests)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            if 'requested_term' not in column_names:
                cursor.execute("ALTER TABLE exchange_requests ADD COLUMN requested_term TEXT")
                conn.commit()
                print("Added 'requested_term' column to exchange_requests table.")
            else:
                print("Column 'requested_term' already exists in exchange_requests table.")
        
        except sqlite3.Error as e:
            print(f"Error updating schema: {e}")
        finally:
            conn.close()

def setup_map_points_table():
    """Setup the map_points table with updated structure"""
    try:
        conn = db_conn.create_connection()
        cursor = conn.cursor()

        # Eliminar la tabla si existe
        cursor.execute('DROP TABLE IF EXISTS map_points')

        # Crear la tabla con la nueva estructura
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS map_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            point_type TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            added_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            creator_id INTEGER DEFAULT 1
        )
        ''')

        conn.commit()
    except Exception as e:
        print(f"Error setting up map_points table: {e}")
    finally:
        if conn:
            conn.close()

# --- Statistics Functions ---

def get_users_count():
    """Returns the total number of registered users."""
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE user_type != 'admin'")
            count = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting users count: {e}")
        finally:
            conn.close()
    
    return count

def get_orgs_count():
    """Returns the total number of registered organizations."""
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM organizations")
            count = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting organizations count: {e}")
        finally:
            conn.close()
    
    return count

def get_events_count():
    """Returns the total number of events."""
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting events count: {e}")
        finally:
            conn.close()
    
    return count

def get_items_count():
    """Returns the total number of exchange items."""
    conn = db_conn.create_connection()
    count = 0
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM exchange_items")
            count = cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"Error getting items count: {e}")
        finally:
            conn.close()
    
    return count

def users_view():
    """
    Retrieves all users from the database for admin viewing.
    Returns all user information except passwords.
    
    Returns:
        list: A list of dictionaries containing user data without passwords.
    """
    users_list = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, student_code, name, email, career, 
                       interests, points, creation_date, user_type
                FROM users
                ORDER BY creation_date DESC
            ''')
            
            for row in cursor.fetchall():
                user_data = {
                    'user_id': row[0],
                    'student_code': row[1],
                    'name': row[2],
                    'email': row[3],
                    'career': row[4],
                    'interests': row[5],
                    'points': row[6],
                    'creation_date': row[7],
                    'user_type': row[8]
                }
                users_list.append(user_data)
                
            print(f"Retrieved {len(users_list)} users for admin view.")
            
        except sqlite3.Error as e:
            print(f"Error retrieving users for admin view: {e}")
        finally:
            conn.close()
    
    return users_list

def orgs_view():
    """
    Retrieves all organizations from the database for admin viewing.
    Returns all organization information except passwords.
    
    Returns:
        list: A list of dictionaries containing organization data without passwords.
    """
    orgs_list = []
    conn = db_conn.create_connection()
    
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT org_id, name, email, description, 
                       interests, points, creation_date, creator_student_code
                FROM organizations
                ORDER BY creation_date DESC
            ''')
            
            for row in cursor.fetchall():
                org_data = {
                    'org_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'description': row[3],
                    'interests': row[4],
                    'points': row[5],
                    'creation_date': row[6],
                    'creator_student_code': row[7]
                }
                orgs_list.append(org_data)
                
            print(f"Retrieved {len(orgs_list)} organizations for admin view.")
            
        except sqlite3.Error as e:
            print(f"Error retrieving organizations for admin view: {e}")
        finally:
            conn.close()
    
    return orgs_list
